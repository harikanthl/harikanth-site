/**
 * Kekasatori Stripe webhook — Cloudflare Pages Function.
 *
 * POST /api/stripe-webhook  (called by Stripe only)
 *
 * Events handled:
 *   checkout.session.completed   → mint an Ed25519-signed license key, store it
 *                                  in the LICENSES KV, make it claimable by the
 *                                  checkout session id (success page polls
 *                                  /api/license/claim?session_id=…).
 *   invoice.paid                 → extend a subscription license's paid-through.
 *   customer.subscription.deleted→ mark the license canceled (key lapses at exp).
 *   charge.refunded              → revoke the license bought with that charge.
 *
 * Secrets:  STRIPE_WEBHOOK_SECRET (whsec_…), LICENSE_SIGNING_KEY (pkcs8 base64).
 * KV layout: session:<cs_id> → {key,kind,email}   (claim handle, 30-day TTL)
 *            lic:<lid>       → LicenseRecord      (server-side truth)
 *            sub:<sub_id>    → lid                (renewal/cancel index)
 *            pi:<pi_id>      → lid                (refund index)
 *            email:<email>:<lid> → ""             (support lookup index)
 */

import {
  LicenseEnv,
  LicensePayload,
  LicenseRecord,
  SUB_GRACE_DAYS,
  addDays,
  isoDate,
  json,
  mintKey,
} from "../_lib/license";

const SIG_TOLERANCE_SECONDS = 300;
const CLAIM_TTL_SECONDS = 30 * 86_400;

async function hmacSha256Hex(secret: string, message: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/** Verify the Stripe-Signature header against the raw body. */
async function verifyStripeSignature(
  rawBody: string,
  header: string | null,
  secret: string,
): Promise<boolean> {
  if (!header) return false;
  const parts = new Map<string, string[]>();
  for (const kv of header.split(",")) {
    const [k, v] = kv.split("=", 2);
    if (!k || !v) continue;
    parts.set(k.trim(), [...(parts.get(k.trim()) ?? []), v.trim()]);
  }
  const t = parts.get("t")?.[0];
  const v1s = parts.get("v1") ?? [];
  if (!t || v1s.length === 0) return false;
  const age = Math.abs(Date.now() / 1000 - Number(t));
  if (!Number.isFinite(age) || age > SIG_TOLERANCE_SECONDS) return false;
  const expected = await hmacSha256Hex(secret, `${t}.${rawBody}`);
  return v1s.some((v1) => timingSafeEqual(v1, expected));
}

export const onRequestPost: PagesFunction<LicenseEnv> = async ({ request, env }) => {
  if (!env.STRIPE_WEBHOOK_SECRET || !env.LICENSE_SIGNING_KEY || !env.LICENSES) {
    return json({ ok: false, error: "Licensing isn't configured." }, 500);
  }

  const rawBody = await request.text();
  const valid = await verifyStripeSignature(
    rawBody,
    request.headers.get("stripe-signature"),
    env.STRIPE_WEBHOOK_SECRET,
  );
  if (!valid) return json({ ok: false, error: "Invalid signature." }, 400);

  let event: any;
  try {
    event = JSON.parse(rawBody);
  } catch {
    return json({ ok: false, error: "Invalid JSON." }, 400);
  }

  switch (event.type) {
    case "checkout.session.completed":
      return handleCheckoutCompleted(event.data.object, env);
    case "invoice.paid":
      return handleInvoicePaid(event.data.object, env);
    case "customer.subscription.deleted":
      return handleSubscriptionDeleted(event.data.object, env);
    case "charge.refunded":
      return handleChargeRefunded(event.data.object, env);
    default:
      return json({ ok: true, ignored: event.type });
  }
};

async function handleCheckoutCompleted(session: any, env: LicenseEnv): Promise<Response> {
  // Idempotent on the session id — Stripe retries deliveries.
  const existing = await env.LICENSES.get(`session:${session.id}`);
  if (existing) return json({ ok: true, already: true });

  const email = String(session.customer_details?.email ?? session.customer_email ?? "")
    .trim()
    .toLowerCase();
  if (!email) return json({ ok: false, error: "No customer email on session." }, 400);

  const kind: "lifetime" | "sub" = session.mode === "subscription" ? "sub" : "lifetime";
  const now = new Date();
  const lid = crypto.randomUUID();

  // Subscription paid-through: prefer the first invoice's billing-period end —
  // it's the only place the real interval (monthly vs yearly) appears, and
  // Stripe doesn't order deliveries, so invoice.paid may have landed first and
  // stashed it under subperiod:<sub_id>. Fall back to ~a month; a yearly buyer
  // in that rare path is corrected by the invoice.paid retry/refresh cycle
  // before the 31-day key (+grace) runs out.
  let paidThroughDate: Date | null = null;
  if (kind === "sub") {
    paidThroughDate = addDays(now, 31);
    if (session.subscription) {
      const stashed = await env.LICENSES.get(`subperiod:${session.subscription}`);
      const end = Number(stashed);
      if (stashed && Number.isFinite(end) && end > 0) paidThroughDate = new Date(end * 1000);
    }
  }

  const payload: LicensePayload = {
    v: 1,
    lid,
    email,
    kind,
    major: 1,
    iat: isoDate(now),
  };
  if (paidThroughDate) payload.exp = isoDate(addDays(paidThroughDate, SUB_GRACE_DAYS));

  const key = await mintKey(payload, env.LICENSE_SIGNING_KEY!);

  const record: LicenseRecord = {
    lid,
    email,
    kind,
    status: "active",
    stripeCustomer: String(session.customer ?? ""),
    stripeSubscription: session.subscription ? String(session.subscription) : undefined,
    paidThrough: paidThroughDate ? isoDate(paidThroughDate) : undefined,
    sessionId: session.id,
    created: now.toISOString(),
  };

  await env.LICENSES.put(`lic:${lid}`, JSON.stringify(record));
  await env.LICENSES.put(
    `session:${session.id}`,
    JSON.stringify({ key, kind, email }),
    { expirationTtl: CLAIM_TTL_SECONDS },
  );
  await env.LICENSES.put(`email:${email}:${lid}`, "");
  if (record.stripeSubscription) {
    await env.LICENSES.put(`sub:${record.stripeSubscription}`, lid);
  }
  if (session.payment_intent) {
    await env.LICENSES.put(`pi:${session.payment_intent}`, lid);
  }

  return json({ ok: true });
}

async function handleInvoicePaid(invoice: any, env: LicenseEnv): Promise<Response> {
  const subId = invoice.subscription ? String(invoice.subscription) : "";
  if (!subId) return json({ ok: true, ignored: "no subscription" });
  const lid = await env.LICENSES.get(`sub:${subId}`);
  if (!lid) {
    // checkout.session.completed may simply not have landed yet (Stripe doesn't
    // order deliveries). Stash the billing-period end so the checkout handler
    // can mint the first key with the REAL interval — critical for yearly,
    // whose next invoice is a year away.
    const periodEnd = invoice.lines?.data?.[0]?.period?.end;
    if (periodEnd) {
      await env.LICENSES.put(`subperiod:${subId}`, String(periodEnd), {
        expirationTtl: 30 * 86_400,
      });
    }
    return json({ ok: true, deferred: "unknown subscription" });
  }

  const raw = await env.LICENSES.get(`lic:${lid}`);
  if (!raw) return json({ ok: true, ignored: "missing record" });
  const record = JSON.parse(raw) as LicenseRecord;

  // Extend to the invoice period end (fall back to +31 days from now).
  const periodEnd = invoice.lines?.data?.[0]?.period?.end;
  const paidThrough = periodEnd
    ? isoDate(new Date(periodEnd * 1000))
    : isoDate(addDays(new Date(), 31));
  record.paidThrough = paidThrough;
  record.status = "active";
  await env.LICENSES.put(`lic:${lid}`, JSON.stringify(record));

  // Index the renewal charge for refund handling.
  if (invoice.payment_intent) {
    await env.LICENSES.put(`pi:${invoice.payment_intent}`, lid);
  }
  return json({ ok: true });
}

async function handleSubscriptionDeleted(sub: any, env: LicenseEnv): Promise<Response> {
  const lid = await env.LICENSES.get(`sub:${sub.id}`);
  if (!lid) return json({ ok: true, ignored: "unknown subscription" });
  const raw = await env.LICENSES.get(`lic:${lid}`);
  if (!raw) return json({ ok: true, ignored: "missing record" });
  const record = JSON.parse(raw) as LicenseRecord;
  record.status = "canceled";
  await env.LICENSES.put(`lic:${lid}`, JSON.stringify(record));
  return json({ ok: true });
}

async function handleChargeRefunded(charge: any, env: LicenseEnv): Promise<Response> {
  const pi = charge.payment_intent ? String(charge.payment_intent) : "";
  if (!pi) return json({ ok: true, ignored: "no payment intent" });
  const lid = await env.LICENSES.get(`pi:${pi}`);
  if (!lid) return json({ ok: true, ignored: "unknown charge" });
  const raw = await env.LICENSES.get(`lic:${lid}`);
  if (!raw) return json({ ok: true, ignored: "missing record" });
  const record = JSON.parse(raw) as LicenseRecord;
  record.status = "revoked";
  await env.LICENSES.put(`lic:${lid}`, JSON.stringify(record));
  return json({ ok: true });
}
