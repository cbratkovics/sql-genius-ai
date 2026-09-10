import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.api import demo
from backend.services.anthropic_service import (
    AnthropicService,
    CompletionResult,
    ProviderNotConfiguredError,
    ProviderResponseError,
)


def schema_payload():
    return demo.SchemaContext(
        id="commerce-v1",
        dialect="sqlite",
        tables=[
            demo.SchemaTable(
                name="orders",
                columns=[
                    demo.SchemaColumn(name="order_id", type="INTEGER"),
                    demo.SchemaColumn(name="total_amount", type="REAL"),
                ],
            )
        ],
    )


def test_parse_provider_json_accepts_fenced_json_and_zero_values():
    parsed = demo._parse_provider_json(
        '```json\n{"sql":"SELECT 0 AS value","explanation":"zero","assumptions":[]}\n```'
    )
    assert parsed == {"sql": "SELECT 0 AS value", "explanation": "zero", "assumptions": []}


@pytest.mark.parametrize(
    "payload",
    ["not json", "{}", '{"sql":"","explanation":"x","assumptions":[]}', '{"sql":"SELECT 1","explanation":[],"assumptions":[]}'],
)
def test_parse_provider_json_rejects_malformed_outputs(payload):
    with pytest.raises(ProviderResponseError):
        demo._parse_provider_json(payload)


@pytest.mark.asyncio
async def test_no_key_never_becomes_fixture_success(monkeypatch):
    monkeypatch.setattr("backend.services.anthropic_service.settings.ANTHROPIC_API_KEY", None)
    service = AnthropicService()
    with pytest.raises(ProviderNotConfiguredError):
        await service.generate_completion("test")


@pytest.mark.asyncio
async def test_generation_passes_schema_and_returns_provenance(monkeypatch):
    captured = {}

    async def completion(self, prompt, **kwargs):
        captured["prompt"] = prompt
        return CompletionResult(
            text=json.dumps({"sql": "SELECT order_id FROM orders", "explanation": "Lists IDs", "assumptions": []}),
            provider="anthropic",
            model="stub-model",
            input_tokens=0,
            output_tokens=12,
        )

    monkeypatch.setattr(AnthropicService, "generate_completion", completion)
    monkeypatch.setattr(demo.demo_limiter, "check", lambda key: _true())
    response = await demo.demo_sql_generation(
        demo.DemoSQLRequest(query="List every order identifier", schema=schema_payload()),
        SimpleNamespace(client=SimpleNamespace(host="test")),
    )
    assert '"dialect":"sqlite"' in captured["prompt"]
    assert '"total_amount"' in captured["prompt"]
    assert response.metadata.model == "stub-model"
    assert response.metadata.input_tokens == 0
    assert response.metadata.execution_status == "not_run"


async def _true():
    return True


@pytest.mark.asyncio
async def test_compatibility_execution_endpoint_is_explicitly_disabled():
    result = await demo.execute_fixture_response(demo.CompatibilityExecutionRequest(sql="SELECT 1"))
    assert result["success"] is False
    assert result["execution_status"] == "not_run"
    assert result["rows"] == []


@pytest.mark.asyncio
async def test_metrics_endpoint_is_gone():
    with pytest.raises(HTTPException) as error:
        await demo.get_demo_metrics()
    assert error.value.status_code == 410
