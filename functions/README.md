# Cloudflare Pages Functions

Server endpoints that deploy automatically with the site (same Workers runtime).

## `api/beta-signup.ts` — Kekasatori beta signups

The `/kekasatori/beta` form POSTs here; signups are stored in the `BETA_SIGNUPS`
KV namespace. Honeypot + email de-dupe built in.

### One-time setup

1. **Create the KV namespace** and paste its id into `wrangler.toml`:
   ```bash
   npx wrangler kv namespace create BETA_SIGNUPS
   # copy the printed id → wrangler.toml [[kv_namespaces]] id = "…"
   ```
2. **Set the admin token** (guards the GET export):
   ```bash
   npx wrangler pages secret put ADMIN_TOKEN --project-name harikanth-site
   ```
   If you deploy via the GitHub → Pages integration, you can instead add
   `ADMIN_TOKEN` under **Pages → Settings → Variables and Secrets** (encrypted).
3. **Deploy** — push to `main` (auto-build), or manually:
   ```bash
   npm run build && npx wrangler pages deploy dist --project-name harikanth-site
   ```

### Read your signups

```bash
# JSON
curl "https://harikanth.site/api/beta-signup?token=YOUR_ADMIN_TOKEN"
# CSV download
curl -O -J "https://harikanth.site/api/beta-signup?token=YOUR_ADMIN_TOKEN&format=csv"
```

### Test locally

```bash
npm run build
npx wrangler pages dev dist   # serves the function + a local KV
```
