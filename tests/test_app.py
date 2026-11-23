from fastapi.testclient import TestClient

from app.main import app, store


def client(role="submitter"):
    c = TestClient(app)
    c.cookies.set("role", role)
    return c


def test_health():
    assert client().get("/healthz").text == "ok"


def test_banner():
    assert "sf-banner.js" in client().get("/").text


def test_submit_and_approve():
    client().post("/requests", data={"requester": "Ana", "title": "New chairs", "details": "x"})
    req = [r for r in store.list("requests") if r["title"] == "New chairs"][0]
    assert req["status"] == "submitted"
    r = client("approver").post(f"/requests/{req['id']}/decision", data={"decision": "approved"},
                                follow_redirects=False)
    assert r.status_code == 303
    assert store.get("requests", req["id"])["status"] == "approved"


def test_submitter_cannot_decide():
    client().post("/requests", data={"requester": "Bo", "title": "Desk", "details": ""})
    req = [r for r in store.list("requests") if r["title"] == "Desk"][0]
    r = client("submitter").post(f"/requests/{req['id']}/decision", data={"decision": "approved"})
    assert r.status_code == 403
