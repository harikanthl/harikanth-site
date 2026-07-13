/**
 * Kekasatori license claim — Cloudflare Pages Function.
 *
 * GET /api/license/claim?session_id=cs_…  → { ok, key, kind, email }
 *
 * Called by the post-checkout success page (/kekasatori/thanks). The Stripe
 * checkout session id is unguessable and acts as the bearer token; the claim
 * record expires from KV after 30 days. Returns 404 until the webhook has
 * processed the session (the page polls briefly).
 */

import { LicenseEnv, json } from "../../_lib/license";

export const onRequestGet: PagesFunction<LicenseEnv> = async ({ request, env }) => {
  if (!env.LICENSES) return json({ ok: false, error: "Licensing isn't configured." }, 500);

  const sessionId = new URL(request.url).searchParams.get("session_id") ?? "";
  if (!/^cs_[A-Za-z0-9_]+$/.test(sessionId)) {
    return json({ ok: false, error: "Invalid session id." }, 400);
  }

  const raw = await env.LICENSES.get(`session:${sessionId}`);
  if (!raw) return json({ ok: false, error: "Not ready." }, 404);

  const { key, kind, email } = JSON.parse(raw);
  return json({ ok: true, key, kind, email });
};
