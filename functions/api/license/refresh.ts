/**
 * Kekasatori subscription refresh — Cloudflare Pages Function.
 *
 * POST /api/license/refresh   { key }  → { ok, key }   (a re-signed key with a
 * new exp) while the subscription is active, 403 once it is canceled past its
 * paid-through date or revoked.
 *
 * Only subscription keys refresh; lifetime keys never need to (the app treats
 * a 403 as "license lapsed" and re-enters trial/soft-lock). The presented key
 * must verify against the signing key, so this endpoint can't be used to
 * fish for licenses.
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
  verifyKey,
} from "../../_lib/license";

export const onRequestPost: PagesFunction<LicenseEnv> = async ({ request, env }) => {
  if (!env.LICENSES || !env.LICENSE_SIGNING_KEY) {
    return json({ ok: false, error: "Licensing isn't configured." }, 500);
  }

  let body: { key?: string };
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "Invalid request body." }, 400);
  }

  const presented = await verifyKey(String(body.key ?? ""), env.LICENSE_SIGNING_KEY);
  if (!presented) return json({ ok: false, error: "Invalid license key." }, 400);
  if (presented.kind !== "sub") {
    return json({ ok: false, error: "Only subscription keys refresh." }, 400);
  }

  const raw = await env.LICENSES.get(`lic:${presented.lid}`);
  if (!raw) return json({ ok: false, error: "Unknown license." }, 404);
  const record = JSON.parse(raw) as LicenseRecord;

  if (record.status === "revoked") {
    return json({ ok: false, error: "License revoked." }, 403);
  }
  // A device-bound key only refreshes while its Mac is still registered —
  // support-side deactivation therefore also cuts off future refreshes.
  if (presented.dev && (record.devices?.length ?? 0) > 0 &&
      !record.devices!.some((d) => d.hash === presented.dev)) {
    return json({ ok: false, error: "This Mac is no longer registered to the license." }, 403);
  }
  const paidThrough = record.paidThrough ? new Date(`${record.paidThrough}T00:00:00Z`) : null;
  const lapsed = !paidThrough || addDays(paidThrough, SUB_GRACE_DAYS) < new Date();
  if (record.status === "canceled" && lapsed) {
    return json({ ok: false, error: "Subscription ended." }, 403);
  }
  if (lapsed) {
    return json({ ok: false, error: "Subscription payment lapsed." }, 403);
  }

  const payload: LicensePayload = {
    v: 1,
    lid: record.lid,
    email: record.email,
    kind: "sub",
    major: 1,
    iat: isoDate(new Date()),
    exp: isoDate(addDays(paidThrough!, SUB_GRACE_DAYS)),
  };
  if (presented.dev) payload.dev = presented.dev;   // keep the key device-bound
  const key = await mintKey(payload, env.LICENSE_SIGNING_KEY);
  return json({ ok: true, key });
};
