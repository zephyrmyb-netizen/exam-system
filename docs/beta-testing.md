# Windows local Beta testing with Cloudflare Tunnel

The Beta server has one local address only: `http://localhost:8080`.
The Vue app is served from the compiled `frontend/dist` directory; `/api/*`
is proxied to FastAPI on `127.0.0.1:8000`; `/uploads/*` is proxied to the
same backend. Do not publish Vite's development port.

## Before the first run

1. Create `backend/.env` from `backend/.env.example`.
2. Set a unique `SECRET_KEY` and `INVITE_CODE`; never use `dev-invite`.
3. Install `cloudflared` from Cloudflare's official Windows instructions.
4. In Cloudflare, create a named Tunnel and publish `beta.your-domain.com`
   to `http://localhost:8080`.

The Tunnel token is a secret. Prefer the Windows `cloudflared` service
installed by Cloudflare. If using the script-started option instead, set the
token only in the current PowerShell session:

```powershell
$env:CLOUDFLARE_TUNNEL_TOKEN = "paste-your-token-here"
```

Do not place it in this repository, `.env.example`, screenshots, or chat.

## Start and stop

```powershell
.\scripts\start-beta.ps1 -PublicUrl "https://beta.your-domain.com"
.\scripts\stop-beta.ps1
```

The script builds the frontend, starts the backend without reload, starts the
same-origin gateway, checks `/api/health`, and backs up the primary SQLite
database (`backend/xuexibao.db`) to `data/beta/backups/` before it starts.
Beta and the local development server intentionally use this same database, so
existing accounts, question banks, and learning records remain available from
both entry points. All of `data/beta/` is ignored by Git.

## Test users

The Beta build shows a **游客试用** entry on the login page. It creates an
isolated student account from a nickname only and persists through the browser
session. It exists only when `APP_ENV=testing`; it is absent in normal and
production builds. A guest can remove only their own account and data from
`我的` > `清除测试数据并退出`; normal accounts continue to use the existing
invite-code registration.

## Risks to check before inviting friends

- The Windows computer, its network, FastAPI, gateway, and Tunnel must stay
  online. Disable sleep while testing.
- Anyone who receives the link can open the site. Do not share an administrator
  account or a weak invite code.
- Beta writes directly to the primary database. Guest accounts, registrations,
  imports, and practice records created through the public link are real data;
  review the automatic backup before restoring or deleting anything.
- This is a small beta setup, not a long-running production deployment.
- Test on mobile data after the Cloudflare route is healthy; local success does
  not prove external access.
