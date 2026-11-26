"""Pipecat voice agent package (prompts, tools, provider factories, and pipeline)."""

from .prompts import RECEPTIONIST_SYSTEM_PROMPT, CLINIC_KEYTERMS
from .tool_registry import TOOL_SCHEMAS, handle_tool_call, build_llm_tools
from .mock import MockPipelineTask
from .pipeline import create_bot_pipeline
from .providers.pipecat_imports import PIPECAT_AVAILABLE

__all__ = [
    "RECEPTIONIST_SYSTEM_PROMPT",
    "CLINIC_KEYTERMS",
    "TOOL_SCHEMAS",
    "handle_tool_call",
    "build_llm_tools",
    "MockPipelineTask",
    "create_bot_pipeline",
    "PIPECAT_AVAILABLE",
]
