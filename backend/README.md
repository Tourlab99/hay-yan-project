# Hayqyan Travel — backend

Flask app that serves the site in `../site` and records every contact-form
submission and newsletter signup in a SQLite database, viewable at `/admin`.

## Run it locally

```
pip install -r requirements.txt
python app.py
```

- Website: http://localhost:5000
- Who contacted you: http://localhost:5000/admin (default login `admin` / `changeme`)

## Deploy on Render

Your repo should look like this (site and backend as siblings):

```
your-repo/
  render.yaml
  site/
    index.html, tours.html, about.html, contact.html, style.css, script.js, Assets/
  backend/
    app.py, requirements.txt
```

### Option A — one-click with the included `render.yaml`

1. Push this repo (including `render.yaml` at the root) to GitHub.
2. Render dashboard → **New** → **Blueprint** → connect your repo.
3. Render reads `render.yaml` and creates the web service for you.
4. When prompted, set `ADMIN_USERNAME` and `ADMIN_PASSWORD` (these are
   marked `sync: false` so Render asks you for them instead of committing
   them to the repo).
5. Deploy. Render gives you a URL like `https://hayqyan-travel.onrender.com`.

**Note:** persistent disks (used for `DATABASE_PATH=/data/submissions.db`
in `render.yaml`) require a paid instance type — the Free plan does not
support them. If you're on Free, remove the `disk:` block from
`render.yaml` and the `DATABASE_PATH` env var; the database will then
live on the app's local disk and **reset on every redeploy/restart**.
Fine for testing, not for relying on it to capture real inquiries —
upgrade the plan once you're getting real bookings.

### Option B — manual setup (no `render.yaml`)

1. Render dashboard → **New** → **Web Service** → connect your repo.
2. **Root Directory**: `backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn app:app`
5. **Environment** tab → add `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
6. (Optional, paid plans only) **Disks** tab → add a disk mounted at
   `/data`, then add env var `DATABASE_PATH` = `/data/submissions.db`.
7. Deploy.

### After deploying

- Site: `https://<your-app>.onrender.com`
- Submissions: `https://<your-app>.onrender.com/admin`

Every contact-form submission is stored with name, email, message, which
tour they were interested in, their IP, and a timestamp — newest first
on `/admin`.
