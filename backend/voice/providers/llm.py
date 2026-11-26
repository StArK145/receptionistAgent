"""LLM provider factory (OpenRouter primary, Google Gemini fallback)."""

import logging
from typing import Any

from ...core.config import (
    get_gemini_api_key,
    get_gemini_model,
    get_openrouter_api_key,
    get_openrouter_model,
)
from .pipecat_imports import (
    GoogleLLMService,
    OpenRouterLLMService,
    OpenRouterProviderPreferences,
)

logger = logging.getLogger(__name__)


def create_llm_service(system_instruction: str) -> Any:
    """Creates the OpenRouter LLM service if configured, otherwise falls back to Google Gemini."""
    openrouter_key = get_openrouter_api_key()
    openrouter_model = get_openrouter_model()

    if openrouter_key and openrouter_key.strip() and OpenRouterLLMService:
        logger.info("Using OpenRouter LLM Service with model: %s", openrouter_model)
        if hasattr(OpenRouterLLMService, "Settings"):
            settings_kwargs = dict(
                model=openrouter_model,
                max_tokens=250,
                system_instruction=system_instruction,
            )
            if OpenRouterProviderPreferences is not None:
                settings_kwargs["provider"] = OpenRouterProviderPreferences(sort="latency")
            return OpenRouterLLMService(
                api_key=openrouter_key.strip(),
                settings=OpenRouterLLMService.Settings(**settings_kwargs),
            )
        return OpenRouterLLMService(
            api_key=openrouter_key.strip(),
            model=openrouter_model,
            system_instruction=system_instruction,
        )

    gemini_key = get_gemini_api_key()
    model_name = get_gemini_model()
    logger.info("Using Google LLM Service with model: %s", model_name)
    if hasattr(GoogleLLMService, "Settings"):
        return GoogleLLMService(
            api_key=gemini_key,
            settings=GoogleLLMService.Settings(
                model=model_name,
                system_instruction=system_instruction,
            ),
        )
    return GoogleLLMService(
        api_key=gemini_key,
        system_instruction=system_instruction,
        model=model_name,
    )
