import os
import pathlib

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.store import make_store

BASE = pathlib.Path(__file__).parent
app = FastAPI(title="Request workflow")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals["sf"] = {"expires": os.environ.get("SF_EXPIRES", ""), "env": os.environ.get("SF_ENV", "local")}
store = make_store()

ROLES = ("submitter", "approver")
STATUSES = ("submitted", "approved", "rejected")


def role_of(request: Request) -> str:
    role = request.cookies.get("role", "submitter")
    return role if role in ROLES else "submitter"


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.post("/role")
def set_role(role: str = Form(...)):
    if role not in ROLES:
        raise HTTPException(400, "Unknown role")
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("role", role, samesite="lax", httponly=True)
    return resp


@app.get("/")
def index(request: Request, status: str | None = None):
    filters = {"status": status} if status in STATUSES else {}
    rows = store.list("requests", order_by="-created_at", **filters)
    return templates.TemplateResponse(request, "index.html", {"requests": rows, "role": role_of(request),
                                                              "status": status})


@app.post("/requests")
def submit(requester: str = Form(..., max_length=80), title: str = Form(..., max_length=120),
           details: str = Form("", max_length=1000)):
    store.create("requests", {"requester": requester.strip(), "title": title.strip(), "details": details.strip(),
                              "status": "submitted", "history": [{"status": "submitted", "by": requester.strip()}]})
    return RedirectResponse("/", status_code=303)


@app.post("/requests/{req_id}/decision")
def decide(request: Request, req_id: str, decision: str = Form(...), note: str = Form("", max_length=500)):
    if role_of(request) != "approver":
        raise HTTPException(403, "Only approvers can decide")
    if decision not in ("approved", "rejected"):
        raise HTTPException(400, "Unknown decision")
    current = store.get("requests", req_id)
    if not current:
        raise HTTPException(404, "Not found")
    if current["status"] != "submitted":
        raise HTTPException(409, "Already decided")
    history = current.get("history", []) + [{"status": decision, "by": "approver", "note": note.strip()}]
    store.update("requests", req_id, {"status": decision, "history": history, "decision_note": note.strip()})
    return RedirectResponse("/", status_code=303)
