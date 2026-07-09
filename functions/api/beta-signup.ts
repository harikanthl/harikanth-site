/**
 * Kekasatori beta signup — Cloudflare Pages Function (Workers runtime + KV).
 *
 * POST /api/beta-signup   { email, name?, useCase?, website? }  → { ok: true }
 *   Stores the signup in the BETA_SIGNUPS KV namespace. Same-origin, so no CORS
 *   dance. `website` is a honeypot: if a bot fills it, we return success but
 *   store nothing. Signups are de-duplicated by email.
 *
 * GET  /api/beta-signup?token=…&format=csv|json   → export for the owner
 *   Requires the ADMIN_TOKEN secret. Lists every stored signup.
 *   Set the secret with:  npx wrangler pages secret put ADMIN_TOKEN
 */

interface Env {
  BETA_SIGNUPS: KVNamespace;
  ADMIN_TOKEN?: string;
}

interface SignupRecord {
  email: string;
  name: string;
  useCase: string;
  ts: string; // ISO timestamp
  country: string;
  userAgent: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_NAME = 120;
const MAX_USECASE = 2000;

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  let body: Record<string, unknown>;
  try {
    const ct = request.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      body = (await request.json()) as Record<string, unknown>;
    } else {
      const form = await request.formData();
      body = Object.fromEntries(form.entries());
    }
  } catch {
    return json({ ok: false, error: "Invalid request body." }, 400);
  }

  // Honeypot: real users never see or fill this field.
  if (typeof body.website === "string" && body.website.trim() !== "") {
    return json({ ok: true });
  }

  const email = String(body.email ?? "").trim().toLowerCase();
  if (!EMAIL_RE.test(email) || email.length > 254) {
    return json({ ok: false, error: "Please enter a valid email address." }, 400);
  }

  const name = String(body.name ?? "").trim().slice(0, MAX_NAME);
  const useCase = String(body.useCase ?? "").trim().slice(0, MAX_USECASE);

  if (!env.BETA_SIGNUPS) {
    return json({ ok: false, error: "Signups aren't configured yet." }, 500);
  }

  // De-dupe by email — idempotent, so a double submit is harmless.
  const emailKey = `email:${email}`;
  const existing = await env.BETA_SIGNUPS.get(emailKey);
  if (existing) {
    return json({ ok: true, already: true });
  }

  const record: SignupRecord = {
    email,
    name,
    useCase,
    ts: new Date().toISOString(),
    country: (request.cf?.country as string) ?? "",
    userAgent: request.headers.get("user-agent")?.slice(0, 300) ?? "",
  };

  const id = `${record.ts}-${crypto.randomUUID()}`;
  await env.BETA_SIGNUPS.put(`signup:${id}`, JSON.stringify(record));
  await env.BETA_SIGNUPS.put(emailKey, record.ts);

  return json({ ok: true });
};

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  const url = new URL(request.url);
  const token = url.searchParams.get("token") ?? "";

  if (!env.ADMIN_TOKEN || token !== env.ADMIN_TOKEN) {
    return json({ ok: false, error: "Unauthorized." }, 401);
  }

  const records: SignupRecord[] = [];
  let cursor: string | undefined;
  do {
    const list = await env.BETA_SIGNUPS.list({ prefix: "signup:", cursor });
    for (const key of list.keys) {
      const value = await env.BETA_SIGNUPS.get(key.name);
      if (value) {
        try {
          records.push(JSON.parse(value) as SignupRecord);
        } catch {
          /* skip malformed */
        }
      }
    }
    cursor = list.list_complete ? undefined : list.cursor;
  } while (cursor);

  records.sort((a, b) => a.ts.localeCompare(b.ts));

  if (url.searchParams.get("format") === "csv") {
    const esc = (s: string) => `"${s.replace(/"/g, '""')}"`;
    const rows = [
      "ts,email,name,country,useCase",
      ...records.map((r) =>
        [r.ts, r.email, r.name, r.country, r.useCase].map((v) => esc(String(v ?? ""))).join(",")
      ),
    ];
    return new Response(rows.join("\n"), {
      headers: {
        "content-type": "text/csv; charset=utf-8",
        "content-disposition": 'attachment; filename="kekasatori-beta-signups.csv"',
      },
    });
  }

  return json({ ok: true, count: records.length, signups: records });
};
