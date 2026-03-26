from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _auth_headers():
    r = client.post("/auth/login", json={"username": "admin", "password": "change-me-now"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auth_login_and_me():
    headers = _auth_headers()
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_match_requires_auth():
    payload = {"left": [{"id": "l1", "name": "Acme"}], "right": [{"id": "r1", "name": "Acme"}]}
    r = client.post("/match", json=payload)
    assert r.status_code == 401


def test_match_basic():
    payload = {
        "left": [{"id": "l1", "name": "Acme Holdings LLC"}],
        "right": [
            {"id": "r1", "name": "ACME Holding Co."},
            {"id": "r2", "name": "Globex International Ltd"},
        ],
        "options": {"top_k": 2, "auto_accept_threshold": 0.9, "review_threshold": 0.7},
    }

    r = client.post("/match", json=payload, headers=_auth_headers())
    assert r.status_code == 200

    data = r.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["best_match"]["id"] == "r1"


def test_match_csv_basic():
    left_csv = "id,name,website,country\nl1,Acme Holdings LLC,acme.com,US\n"
    right_csv = (
        "id,name,website,country\n"
        "r1,ACME Holding Co.,acme.com,US\n"
        "r2,Globex International Ltd,globex.com,US\n"
    )

    files = {
        "left_file": ("left.csv", left_csv, "text/csv"),
        "right_file": ("right.csv", right_csv, "text/csv"),
    }

    r = client.post("/match/csv", files=files, headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["results"][0]["best_match"]["id"] == "r1"
