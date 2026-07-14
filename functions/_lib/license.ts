/**
 * Kekasatori licensing — shared helpers for the Pages Functions.
 *
 * License key format (KS1):
 *   KS1.<base64url(payload JSON bytes)>.<base64url(Ed25519 signature)>
 *
 * The signature is over the exact payload bytes embedded in the key, so
 * verifiers never need to re-serialize JSON. Payload fields:
 *   v      1 (format version)
 *   lid    license id (uuid) — KV lookup handle
 *   email  purchaser email (lowercase)
 *   kind   "lifetime" | "sub"
 *   major  highest app major version this key covers
 *   iat    issue date, YYYY-MM-DD
 *   exp    (sub only) paid-through + grace, YYYY-MM-DD — absent for lifetime
 *
 * Signing key: LICENSE_SIGNING_KEY secret, base64 PKCS#8 Ed25519 private key.
 * The matching raw public key is embedded in the app.
 */

export interface LicensePayload {
  v: 1;
  lid: string;
  email: string;
  kind: "lifetime" | "sub";
  major: number;
  iat: string;
  exp?: string;
  /** Device-bound keys only: SHA-256 hash (hex) of the Mac's platform UUID.
   *  The app refuses a key whose `dev` doesn't match the machine it runs on;
   *  keys fresh from checkout have no `dev` and must pass through
   *  /api/license/activate to get bound. */
  dev?: string;
}

/** One activated Mac under a license. */
export interface LicenseDevice {
  hash: string;
  name?: string;
  first: string;   // ISO date of first activation
  last: string;    // ISO date of most recent activation
}

/** KV record at `lic:<lid>` — the server-side truth behind a key. */
export interface LicenseRecord {
  lid: string;
  email: string;
  kind: "lifetime" | "sub";
  status: "active" | "canceled" | "revoked";
  stripeCustomer: string;
  stripeSubscription?: string;
  /** sub only — ISO date the subscription is paid through (no grace). */
  paidThrough?: string;
  sessionId: string;
  created: string;
  /** Macs this license has been activated on (see /api/license/activate). */
  devices?: LicenseDevice[];
  /** Lifetime count of activations (concurrent slots free up on support
   *  deactivation, this never decrements — the resale backstop). */
  totalActivations?: number;
}

/** Concurrent Macs allowed per license. */
export const MAX_CONCURRENT_DEVICES = 3;
/** Total activations ever, across hardware churn — the resale backstop. */
export const MAX_TOTAL_ACTIVATIONS = 10;

export interface LicenseEnv {
  LICENSES: KVNamespace;
  LICENSE_SIGNING_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
}

/** Grace window appended to a subscription's paid-through date. */
export const SUB_GRACE_DAYS = 7;

export function b64urlEncode(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64urlDecode(s: string): Uint8Array {
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/");
  const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
  const bin = atob(b64 + pad);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function b64Decode(s: string): Uint8Array {
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function addDays(d: Date, days: number): Date {
  return new Date(d.getTime() + days * 86_400_000);
}

async function importSigningKey(pkcs8b64: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "pkcs8",
    b64Decode(pkcs8b64).buffer as ArrayBuffer,
    { name: "Ed25519" },
    false,
    ["sign"],
  );
}

/** Mint a KS1 license key string from a payload. */
export async function mintKey(payload: LicensePayload, pkcs8b64: string): Promise<string> {
  const key = await importSigningKey(pkcs8b64);
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  const sig = new Uint8Array(await crypto.subtle.sign("Ed25519", key, bytes));
  return `KS1.${b64urlEncode(bytes)}.${b64urlEncode(sig)}`;
}

/**
 * Parse + verify a KS1 key against the signing key's own public half
 * (derived server-side so the functions never need a second secret).
 * Returns the payload, or null if the key is malformed or the signature fails.
 */
export async function verifyKey(key: string, pkcs8b64: string): Promise<LicensePayload | null> {
  const parts = key.trim().split(".");
  if (parts.length !== 3 || parts[0] !== "KS1") return null;
  let payloadBytes: Uint8Array, sig: Uint8Array;
  try {
    payloadBytes = b64urlDecode(parts[1]);
    sig = b64urlDecode(parts[2]);
  } catch {
    return null;
  }
  // Derive the public key from the private key by importing as a keypair via JWK round-trip.
  const priv = await crypto.subtle.importKey(
    "pkcs8",
    b64Decode(pkcs8b64).buffer as ArrayBuffer,
    { name: "Ed25519" },
    true,
    ["sign"],
  );
  const jwk = (await crypto.subtle.exportKey("jwk", priv)) as JsonWebKey;
  const pub = await crypto.subtle.importKey(
    "jwk",
    { kty: "OKP", crv: "Ed25519", x: jwk.x },
    { name: "Ed25519" },
    false,
    ["verify"],
  );
  const ok = await crypto.subtle.verify(
    "Ed25519",
    pub,
    sig.buffer as ArrayBuffer,
    payloadBytes.buffer as ArrayBuffer,
  );
  if (!ok) return null;
  try {
    const payload = JSON.parse(new TextDecoder().decode(payloadBytes)) as LicensePayload;
    if (payload.v !== 1 || !payload.lid || !payload.kind) return null;
    return payload;
  } catch {
    return null;
  }
}

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}
