"""Pinned-SDK shape and optional setup regressions, with no remote services."""

from types import SimpleNamespace

import pandas as pd
import pytest

from backend.core.config import settings
from backend.services.anthropic_service import (
    AnthropicService,
    ProviderNotConfiguredError,
)
from backend.services.business_intelligence import BusinessIntelligenceEngine
from backend.services.cache import IntelligentCache
from backend.services.sql_generation import SQLGenerationEngine


@pytest.mark.asyncio
async def test_completion_uses_pinned_sdk_beta_messages_without_network():
    calls = []

    async def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="SELECT 1;")],
            model="configured-model",
            usage=SimpleNamespace(input_tokens=0, output_tokens=3),
        )

    # anthropic 0.8.1 exposes beta.messages, not the newer client.messages.
    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    result = await AnthropicService(client=client).generate_completion(
        "Review this schema", max_tokens=900, model="configured-model"
    )
    assert calls == [{
        "model": "configured-model",
        "max_tokens": settings.ANTHROPIC_MAX_OUTPUT_TOKENS,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": "Review this schema"}],
    }]
    assert result.text == "SELECT 1;"
    assert result.provider == "anthropic"
    assert result.model == "configured-model"
    assert result.input_tokens == 0
    assert result.output_tokens == 3


@pytest.mark.asyncio
async def test_missing_provider_configuration_is_explicit(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    service = AnthropicService()
    assert service.client is None
    with pytest.raises(ProviderNotConfiguredError):
        await service.generate_completion("List products")


@pytest.mark.asyncio
async def test_pinned_beta_response_without_usage_remains_unknown():
    async def create(**kwargs):
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="SELECT 0;")],
            model="configured-model",
        )

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    result = await AnthropicService(client=client).generate_completion("List products")
    assert result.text == "SELECT 0;"
    assert result.input_tokens is None
    assert result.output_tokens is None


@pytest.mark.asyncio
async def test_unconfigured_cache_is_a_miss_without_connecting(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", None)
    cache = IntelligentCache()
    assert cache.redis_client is None
    assert await cache.get("fixture") is None
    assert await cache.set("fixture", {"value": 1}) is False
    assert await cache.delete("fixture") is False
    assert await cache.exists("fixture") is False
    assert await cache.invalidate_pattern("fixture:*") == 0
    assert await cache.get_similar_queries("list products", "fixture") == []
    assert await cache.get_cache_stats() == {}
    await cache.close()


@pytest.mark.asyncio
async def test_reference_engines_inspect_numeric_data_without_provider_setup(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    frame = pd.DataFrame({
        "units": [1, 2, 3, 4],
        "value": [2, 4, 6, 8],
        "name": ["a", "b", "c", "d"],
    })
    insights = BusinessIntelligenceEngine()
    sql = SQLGenerationEngine()
    assert insights.anthropic is None
    assert sql.anthropic is None
    correlation = insights._analyze_correlations(frame)["strong_correlations"]
    assert len(correlation) == 1
    assert correlation[0]["correlation"] == pytest.approx(1.0)
    assert correlation[0]["direction"] == "positive"
    schema = await sql.infer_schema_from_csv(frame)
    assert schema["tables"]["data"]["row_count"] == 4
    assert schema["tables"]["data"]["columns"]["units"]["semantic_type"] == "numeric"
