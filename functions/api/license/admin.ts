/**
 * Kekasatori license admin — Cloudflare Pages Function. OWNER-ONLY.
 *
 * POST /api/license/admin      Authorization: Bearer <LICENSE_ADMIN_TOKEN>
 *   { action: "info" | "revoke" | "restore" | "remove-device",
 *     lid?, email?, device? }
 *
 *   info           → the license record(s) (by lid, or every license under an email)
 *   revoke         → status = "revoked": activations stop immediately, and every
 *                    bound key dies when its lease/paid-through runs out
 *   restore        → status = "active" (undo a revoke)
 *   remove-device  → frees one concurrent Mac slot (device = full hash, or a
 *                    unique prefix of one); the Mac's key stops refreshing
 *
 * Setup (one time): npx wrangler pages secret put LICENSE_ADMIN_TOKEN
 * Usage examples:
 *   curl -s https://harikanth.site/api/license/admin \
 *     -H "authorization: Bearer $TOKEN" -H "content-type: application/json" \
 *     -d '{"action":"info","email":"buyer@example.com"}'
 *   curl … -d '{"action":"revoke","lid":"<lid>"}'
 *   curl … -d '{"action":"remove-device","lid":"<lid>","device":"a1b2c3"}'
 */

import { LicenseEnv, LicenseRecord, json } from "../../_lib/license";

interface AdminEnv extends LicenseEnv {
  LICENSE_ADMIN_TOKEN?: string;
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/** Public view of a record: everything the owner needs, nothing more. */
function summarize(record: LicenseRecord) {
  return {
    lid: record.lid,
    email: record.email,
    kind: record.kind,
    status: record.status,
    created: record.created,
    paidThrough: record.paidThrough,
    totalActivations: record.totalActivations ?? record.devices?.length ?? 0,
    devices: (record.devices ?? []).map((d) => ({
      hash: d.hash,
      name: d.name,
      first: d.first,
      last: d.last,
    })),
  };
}

export const onRequestPost: PagesFunction<AdminEnv> = async ({ request, env }) => {
  if (!env.LICENSES || !env.LICENSE_ADMIN_TOKEN) {
    return json({ ok: false, error: "Admin isn't configured." }, 500);
  }
  const auth = request.headers.get("authorization") ?? "";
  if (!timingSafeEqual(auth, `Bearer ${env.LICENSE_ADMIN_TOKEN}`)) {
    return json({ ok: false, error: "Unauthorized." }, 401);
  }

  let body: { action?: string; lid?: string; email?: string; device?: string };
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "Invalid request body." }, 400);
  }
  const action = String(body.action ?? "");

  // Resolve target lids: an explicit lid, or every license under an email.
  let lids: string[] = [];
  if (body.lid) {
    lids = [String(body.lid)];
  } else if (body.email) {
    const email = String(body.email).trim().toLowerCase();
    const listed = await env.LICENSES.list({ prefix: `email:${email}:` });
    lids = listed.keys.map((k) => k.name.slice(`email:${email}:`.length));
  }
  if (lids.length === 0) {
    return json({ ok: false, error: "Provide a lid or an email with licenses." }, 400);
  }

  const records: LicenseRecord[] = [];
  for (const lid of lids) {
    const raw = await env.LICENSES.get(`lic:${lid}`);
    if (raw) records.push(JSON.parse(raw) as LicenseRecord);
  }
  if (records.length === 0) {
    return json({ ok: false, error: "No matching license records." }, 404);
  }

  switch (action) {
    case "info":
      return json({ ok: true, licenses: records.map(summarize) });

    case "revoke":
    case "restore": {
      for (const record of records) {
        record.status = action === "revoke" ? "revoked" : "active";
        await env.LICENSES.put(`lic:${record.lid}`, JSON.stringify(record));
      }
      return json({ ok: true, licenses: records.map(summarize) });
    }

    case "remove-device": {
      const needle = String(body.device ?? "").toLowerCase();
      if (!needle) return json({ ok: false, error: "Provide the device hash (or a unique prefix)." }, 400);
      if (records.length !== 1) {
        return json({ ok: false, error: "remove-device needs a single license — pass its lid." }, 400);
      }
      const record = records[0];
      const matches = (record.devices ?? []).filter((d) => d.hash.startsWith(needle));
      if (matches.length === 0) return json({ ok: false, error: "No device matches that hash." }, 404);
      if (matches.length > 1) return json({ ok: false, error: "Prefix matches several devices — use more characters." }, 400);
      record.devices = (record.devices ?? []).filter((d) => d !== matches[0]);
      await env.LICENSES.put(`lic:${record.lid}`, JSON.stringify(record));
      return json({ ok: true, removed: matches[0].hash, licenses: [summarize(record)] });
    }

    default:
      return json({ ok: false, error: "Unknown action. Use info | revoke | restore | remove-device." }, 400);
  }
};
