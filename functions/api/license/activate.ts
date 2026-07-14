/**
 * Kekasatori device activation — Cloudflare Pages Function.
 *
 * POST /api/license/activate   { key, device, deviceName? }
 *   → { ok, key }   a re-signed key bound to this Mac (payload gains `dev`)
 *   → 400           malformed request / invalid key / bad device hash
 *   → 403           revoked license, or a canceled sub binding a NEW device
 *   → 404           license unknown to the server
 *   → 409           device caps hit (3 concurrent Macs / 10 lifetime activations)
 *
 * `device` is a SHA-256 hex hash the app derives from the Mac's platform UUID;
 * the raw identifier never leaves the machine. Re-activating an already-
 * registered Mac is idempotent and never consumes an activation. The presented
 * key must verify against the signing key, so this endpoint can't be used to
 * fish for licenses.
 */

import {
  LicenseEnv,
  LicensePayload,
  LicenseRecord,
  LIFETIME_LEASE_DAYS,
  MAX_CONCURRENT_DEVICES,
  MAX_TOTAL_ACTIVATIONS,
  SUB_GRACE_DAYS,
  addDays,
  isoDate,
  json,
  mintKey,
  verifyKey,
} from "../../_lib/license";

const DEVICE_HASH_RE = /^[a-f0-9]{64}$/;

export const onRequestPost: PagesFunction<LicenseEnv> = async ({ request, env }) => {
  if (!env.LICENSES || !env.LICENSE_SIGNING_KEY) {
    return json({ ok: false, error: "Licensing isn't configured." }, 500);
  }

  let body: { key?: string; device?: string; deviceName?: string };
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "Invalid request body." }, 400);
  }

  const device = String(body.device ?? "").toLowerCase();
  if (!DEVICE_HASH_RE.test(device)) {
    return json({ ok: false, error: "Invalid device identifier." }, 400);
  }

  const presented = await verifyKey(String(body.key ?? ""), env.LICENSE_SIGNING_KEY);
  if (!presented) return json({ ok: false, error: "Invalid license key." }, 400);

  const raw = await env.LICENSES.get(`lic:${presented.lid}`);
  if (!raw) return json({ ok: false, error: "Unknown license." }, 404);
  const record = JSON.parse(raw) as LicenseRecord;

  if (record.status === "revoked") {
    return json({ ok: false, error: "This license has been revoked." }, 403);
  }

  const now = new Date();
  const today = isoDate(now);
  const devices = record.devices ?? [];
  const existing = devices.find((d) => d.hash === device);

  if (existing) {
    // Idempotent re-activation of a known Mac — refresh its bookkeeping only.
    existing.last = today;
    if (body.deviceName) existing.name = String(body.deviceName).slice(0, 80);
  } else {
    // A canceled subscription keeps working on its registered Macs until it
    // lapses, but must not spread to new ones.
    if (record.status === "canceled") {
      return json({ ok: false, error: "This subscription has ended." }, 403);
    }
    if (devices.length >= MAX_CONCURRENT_DEVICES) {
      return json(
        {
          ok: false,
          error: `This license is already active on ${MAX_CONCURRENT_DEVICES} Macs. Contact support@harikanth.site to move it to a new machine.`,
        },
        409,
      );
    }
    const total = record.totalActivations ?? devices.length;
    if (total >= MAX_TOTAL_ACTIVATIONS) {
      return json(
        {
          ok: false,
          error: "This license has reached its lifetime activation limit. Contact support@harikanth.site.",
        },
        409,
      );
    }
    devices.push({
      hash: device,
      name: body.deviceName ? String(body.deviceName).slice(0, 80) : undefined,
      first: today,
      last: today,
    });
    record.totalActivations = total + 1;
  }

  record.devices = devices;
  await env.LICENSES.put(`lic:${record.lid}`, JSON.stringify(record));

  // Mint the device-bound key. EVERY bound key is a lease: sub keys run to
  // paid-through + grace, lifetime keys to a rolling window the app silently
  // renews — which is what keeps a lifetime license revocable.
  const payload: LicensePayload = {
    v: 1,
    lid: record.lid,
    email: record.email,
    kind: record.kind,
    major: presented.major,
    iat: today,
    dev: device,
  };
  if (record.kind === "sub") {
    const paidThrough = record.paidThrough
      ? new Date(`${record.paidThrough}T00:00:00Z`)
      : null;
    payload.exp = paidThrough
      ? isoDate(addDays(paidThrough, SUB_GRACE_DAYS))
      : presented.exp;
    if (!payload.exp) return json({ ok: false, error: "License record is incomplete." }, 500);
  } else {
    payload.exp = isoDate(addDays(now, LIFETIME_LEASE_DAYS));
  }

  const key = await mintKey(payload, env.LICENSE_SIGNING_KEY);
  return json({ ok: true, key });
};
