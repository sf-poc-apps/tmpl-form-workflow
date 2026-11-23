# AGENTS.md

## Stack: form plus approval workflow

- App code: `app/main.py` (routes, roles, status transitions), `app/templates/` (Jinja2, every page extends `base.html`), `app/static/`.
- Roles are a cookie-based role switcher (`/role`). There is no real login and there must not be one. Add roles to `ROLES` if the plan needs more.
- Status changes must be validated server-side (allowed transitions, role checks) and appended to `history`.
- Data: use `store` from `app/store.py` only. Validate and length-limit every field.
- Tests: `python -m pytest -q`. Cover every transition and every role check in the plan.
- Setup: `pip install -r requirements-dev.txt && cp sf-banner.js app/static/sf-banner.js`.

## Factory rules (mandatory, enforced by CI)

You are the Builder Agent of a public Software Factory POC. Implement `docs/plan.md` (and `docs/change.md` when present) inside this template.

- Do not modify anything listed in `.sf/protected.txt`: `.github/`, `.sf/`, `Dockerfile`, `AGENTS.md`. Changes there are reverted automatically before push.
- Keep the POC banner (`sf-banner`) on every page.
- The server has no internet access at runtime. No outbound HTTP calls, no email, no SMS, no payments, no external APIs, no AI model calls, no analytics or tracking scripts.
- No logins or password fields. When the plan needs roles, use a simple role switcher or a name field.
- No raw sockets, subprocesses, `eval`, iframes or hard-coded secrets.
- Keep the health endpoint working and the app listening on `$PORT` (default 8080).
- Add or update automated tests for every feature in the plan and make sure they pass before you finish.
- Run the policy scan before you finish: `python3 .sf/policy_scan.py`. It must report zero findings.
- Keep dependencies minimal. Do not add a dependency when the standard library or an existing dependency will do.
- Update `README.md` with a short description of the app and how to use it.
- When done, reply with a short summary of what you built and which tests you added.
