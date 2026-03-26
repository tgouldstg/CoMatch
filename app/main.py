from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .auth import authenticate, create_token, require_user
from .auth_schemas import LoginRequest, LoginResponse
from .csv_io import parse_company_csv
from .matcher import match_records
from .schemas import MatchOptions, MatchRequest, MatchResponse

APP_VERSION = "0.1.0"

app = FastAPI(title="Company Match API", version=APP_VERSION)
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not authenticate(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(payload.username)
    return LoginResponse(access_token=token)


@app.get("/auth/me")
def me(user=Depends(require_user)) -> dict:
    return {"username": user["username"]}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    return {"version": APP_VERSION}


def _build_response(payload: MatchRequest) -> MatchResponse:
    results = match_records(payload.left, payload.right, payload.options)

    summary = {"auto_accept": 0, "review": 0, "reject": 0}
    for r in results:
        summary[r.decision] += 1

    return MatchResponse(results=results, summary=summary)


@app.post("/match", response_model=MatchResponse)
def match(payload: MatchRequest, _user=Depends(require_user)) -> MatchResponse:
    return _build_response(payload)


@app.post("/match/csv", response_model=MatchResponse)
async def match_csv(
    left_file: UploadFile = File(..., description="CSV with at least id,name"),
    right_file: UploadFile = File(..., description="CSV with at least id,name"),
    top_k: int = Form(3),
    auto_accept_threshold: float = Form(0.92),
    review_threshold: float = Form(0.75),
    include_alternatives: bool = Form(True),
    _user=Depends(require_user),
) -> MatchResponse:
    try:
        left_records = parse_company_csv(await left_file.read())
        right_records = parse_company_csv(await right_file.read())

        options = MatchOptions(
            top_k=top_k,
            auto_accept_threshold=auto_accept_threshold,
            review_threshold=review_threshold,
            include_alternatives=include_alternatives,
        )
        payload = MatchRequest(left=left_records, right=right_records, options=options)
        return _build_response(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
