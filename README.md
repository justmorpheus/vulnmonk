# VulnMonk SAST Dashboard

A full-stack dashboard for managing SAST scan results and secret scanning across GitHub repositories.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, JWT auth
- **Frontend:** React 19, JavaScript, CSS
- **SAST Scanner:** OpenGrep
- **Secret Scanner:** TruffleHog

## Setup

### Step 1 — Configure Environment Variables

Create `backend/.env` before starting the backend or running Docker:

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env`:

```env
# Required — generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRE_DAYS=30

# GitHub App — required for PR scan checks and private repo access
# See https://github.com/settings/apps to create your GitHub App
GITHUB_APP_ID=
GITHUB_APP_SLUG=
GITHUB_APP_PRIVATE_KEY=backend/your-app.private-key.pem

# Frontend URL (used for GitHub App OAuth callback)
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
```

> **GitHub App setup:** Create a GitHub App at https://github.com/settings/apps. Set the Webhook URL to `YOUR_SERVER_URL/webhooks/github`. Download the private key `.pem` file and place it in the `backend/` directory.

> **TruffleHog:** Required for secret scanning. Install from https://github.com/trufflesecurity/trufflehog or via `brew install trufflehog` on macOS. The Docker image installs TruffleHog automatically.

---

### Step 2 — Backend

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload      # runs on http://localhost:8000
```

> **Scanners:** Make sure `opengrep` and `trufflehog` are on your `PATH` for local development.
> - OpenGrep: https://github.com/opengrep/opengrep/releases/latest
> - TruffleHog: `brew install trufflehog` (macOS) or https://github.com/trufflesecurity/trufflehog/releases/latest
> 
> Both are installed automatically in the Docker image.

### Step 3 — Frontend

```bash
cd frontend
npm install
npm start   # runs on http://localhost:3000
```

---

### First Login — Create an Admin User

After the backend starts, create your first admin user:

```bash
python3 add_user.py <username> <password> admin
```

---

## Docker

```bash
docker compose up --build
```

> **If you get a `Module not found` build error**, Docker may be using a stale cache layer. Force a clean build:
> ```bash
> docker compose build --no-cache
> docker compose up
> ```

Data is persisted in Docker named volumes (`vulnmonk-data`, `vulnmonk-projects`).

Make sure `backend/.env` exists with the values from Step 1 above — it is loaded automatically at runtime.

For overriding the frontend API URL at build time (non-Docker or custom deployments):

```
REACT_APP_API_BASE_URL=http://<your-host>:8000
```

**CLI tools inside the container:**
```bash
docker exec -it vulnmonk-backend python add_user.py <username> <password> admin
docker exec -it vulnmonk-backend python add_user.py --list
```

## User Management (CLI)

```bash
python3 add_user.py          # create a user
python3 add_user.py --list   # list all users
python3 view_db.py           # view database contents
```

## API Docs

Swagger UI: http://YOUR_SERVER_IP_OR_DOMAIN:8000/docs

## Features

- **SAST scanning** with OpenGrep — on-demand per project, with per-project and global exclude/include YAML rules
- **Secret scanning** with TruffleHog — on-demand per project, with per-project and global exclude detector lists
- **PR scan checks** — automatic SAST + TruffleHog scans on pull requests via GitHub App webhooks
- **PR blocking** — fail the `vulnmonk/pr-scan` GitHub status check based on:
  - SAST severity threshold (INFO / WARNING / ERROR)
  - TruffleHog findings (Verified only, or all secrets)
- **False positive management** — mark/unmark findings as false positives (keyed by path, rule/detector)
- **Role-based access** — Admin (full control) and User (view-only)
- **GitHub OAuth** — connect GitHub App for private repo access and PR webhooks
- **Scan history** — per-project scan history with finding counts and timestamps

## Permissions

| Action                             | Admin | User |
|------------------------------------|:-----:|:----:|
| Trigger SAST / secret scans        | ✅    | ❌   |
| Add / manage projects              | ✅    | ❌   |
| Mark false positives               | ✅    | ❌   |
| Configure PR scan settings         | ✅    | ❌   |
| Configure exclude rules/detectors  | ✅    | ❌   |
| Manage users                       | ✅    | ❌   |
| View projects & scan results       | ✅    | ✅   |
| Change own password                | ✅    | ✅   |

## Project Structure

```
vulnmonk/
├── backend/
│   ├── main.py         # FastAPI app entry point
│   ├── models.py       # ORM models (projects, scans, TruffleHog results, PR checks)
│   ├── schemas.py      # Pydantic schemas
│   ├── crud.py         # Database operations
│   ├── auth.py         # JWT auth helpers
│   └── routes/
│       ├── projects.py  # Project, SAST & TruffleHog scan endpoints
│       ├── webhooks.py  # GitHub App webhook handler (PR scans)
│       ├── auth.py      # Login / token endpoints
│       └── integrations.py  # GitHub integration endpoints
├── frontend/      # React app (src/components/, App.js, api.js)
├── projects/      # Cloned repos (auto-created at runtime)
├── add_user.py    # CLI user management
├── view_db.py     # Database viewer
└── vulnmonk.db    # SQLite database (auto-created)
```

## Scanners

### OpenGrep (SAST)

Runs `opengrep` against the full repo clone. Per-project and global exclude/include rules are merged as YAML at scan time. Findings are stored with file, line, severity, and rule metadata. False positives are tracked by `path@rule_id`.

### TruffleHog (Secret Scanning)

Runs `trufflehog git file://{repo_path} --json` for on-demand scans. For PR scans, runs `trufflehog filesystem {scan_dir} --json` on the changed files only, then filters findings to the exact changed lines of the PR.

- **Exclude detectors** — configure per-project or globally (e.g. `AWS`, `Npm`, `CloudflareApiToken`)
- **False positives** — tracked by `path@raw_hash@detector`
- **PR blocking** — configurable per-project and globally: block on Verified secrets only, or all secrets (verified + unverified)

## License

MIT — see [LICENSE](LICENSE).
