"""Public generation routes. SQL execution remains in the browser playground."""

import json
import time
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, Field

from backend.services.anthropic_service import (
    AnthropicService,
    ProviderNotConfiguredError,
    ProviderResponseError,
)

router = APIRouter(prefix="/demo", tags=["demo"])


class RateLimiter:
    """Best-effort, per-process limiter; it is not distributed enforcement."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}

    async def check(self, key: str) -> bool:
        now = time.monotonic()
        recent = [t for t in self.requests.get(key, []) if t > now - self.window_seconds]
        if len(recent) >= self.max_requests:
            self.requests[key] = recent
            return False
        recent.append(now)
        self.requests[key] = recent
        return True


demo_limiter = RateLimiter()


class SchemaColumn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    type: str = Field(..., min_length=1, max_length=40)


class SchemaTable(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    columns: List[SchemaColumn] = Field(..., min_length=1, max_length=50)


class SchemaRelationship(BaseModel):
    source: str = Field(..., max_length=170)
    target: str = Field(..., max_length=170)


class SchemaContext(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    dialect: Literal["sqlite"]
    tables: List[SchemaTable] = Field(..., min_length=1, max_length=20)
    relationships: List[SchemaRelationship] = Field(default_factory=list, max_length=50)


class DemoSQLRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)
    schema: SchemaContext


class GenerationMetadata(BaseModel):
    source: Literal["provider"]
    provider: str
    model: str
    dialect: Literal["sqlite"]
    schema_id: str
    response_parsed: bool
    policy_status: Literal["not_checked"] = "not_checked"
    execution_status: Literal["not_run"] = "not_run"
    provider_round_trip_ms: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class DemoSQLResponse(BaseModel):
    success: Literal[True] = True
    sql: str
    explanation: str
    assumptions: List[str]
    metadata: GenerationMetadata


def _parse_provider_json(text: str) -> Dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            candidate = "\n".join(lines[1:-1])
            if candidate.lstrip().lower().startswith("json\n"):
                candidate = candidate.lstrip()[5:]
    try:
        value = json.loads(candidate)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ProviderResponseError("The provider returned malformed JSON.") from exc
    if not isinstance(value, dict) or not isinstance(value.get("sql"), str) or not value["sql"].strip():
        raise ProviderResponseError("The provider response did not include non-empty SQL.")
    explanation = value.get("explanation")
    assumptions = value.get("assumptions", [])
    if not isinstance(explanation, str) or not isinstance(assumptions, list) or not all(
        isinstance(item, str) for item in assumptions
    ):
        raise ProviderResponseError("The provider response metadata was malformed.")
    return value


@router.post("/sql-generate", response_model=DemoSQLResponse)
async def demo_sql_generation(request: DemoSQLRequest, req: Request):
    client_key = req.client.host if req.client else "unknown"
    if not await demo_limiter.check(client_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    schema_json = request.schema.model_dump_json()
    prompt = (
        "Return only one JSON object with string keys sql and explanation and an array of "
        "string assumptions. Generate one read-only SQLite SELECT statement (a read-only CTE "
        "is allowed). Use only the supplied schema. Do not execute it. If the business meaning "
        "is ambiguous, explain the assumption instead of inventing a table.\n\n"
        f"Schema: {schema_json}\n\nQuestion: {request.query}"
    )
    started = time.monotonic()
    try:
        completion = await AnthropicService().generate_completion(prompt=prompt)
        parsed = _parse_provider_json(completion.text)
    except ProviderNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Do not leak SDK exception bodies, credentials, or upstream request details.
        raise HTTPException(status_code=502, detail="Live generation provider request failed.") from exc

    return DemoSQLResponse(
        sql=parsed["sql"].strip(),
        explanation=parsed["explanation"],
        assumptions=parsed["assumptions"],
        metadata=GenerationMetadata(
            source="provider",
            provider=completion.provider,
            model=completion.model,
            dialect="sqlite",
            schema_id=request.schema.id,
            response_parsed=True,
            provider_round_trip_ms=round((time.monotonic() - started) * 1000, 2),
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
        ),
    )


class CompatibilityExecutionRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=20_000)


@router.post("/execute-sandbox", deprecated=True)
async def execute_fixture_response(payload: CompatibilityExecutionRequest = Body(...)):
    """Compatibility route: it deliberately does not execute caller SQL."""
    return {
        "success": False,
        "execution_status": "not_run",
        "execution_engine": None,
        "data_source_kind": "none",
        "illustrative_fixture": False,
        "rows": [],
        "detail": "Remote demo execution is disabled. Run supported SQL locally in the browser playground.",
    }


@router.get("/metrics", deprecated=True)
async def get_demo_metrics():
    raise HTTPException(status_code=410, detail="Fabricated aggregate demo metrics were removed.")
