"""LLM tool schemas, execution dispatcher, and Pipecat FunctionSchema registration."""

import logging
from typing import Any, Dict

from ..core.event_bus import EventBus, global_event_bus
from ..services import (
    check_doctor_availability,
    book_appointment,
    cancel_appointment,
)

logger = logging.getLogger(__name__)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_doctor_availability",
            "description": "Checks available doctors and their open time slots by doctor name, specialty, or date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name": {
                        "type": "string",
                        "description": "Doctor's name or partial name, e.g. 'Vance' or 'Dr. Marcus Chen'",
                    },
                    "specialty": {
                        "type": "string",
                        "description": "Medical specialty (Cardiology, Dermatology, Pediatrics, Orthopedics, General Medicine)",
                    },
                    "date": {
                        "type": "string",
                        "description": "Target date: 'today', 'tomorrow', or 'YYYY-MM-DD'",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Atomically books a confirmed appointment after verifying the phone number verbally.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name": {
                        "type": "string",
                        "description": "Doctor's full or partial name",
                    },
                    "date": {
                        "type": "string",
                        "description": "Appointment date ('today', 'tomorrow', or 'YYYY-MM-DD')",
                    },
                    "time_slot": {
                        "type": "string",
                        "description": "Requested time slot, e.g. '09:00 AM' or '02:00 PM'",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Patient's phone number as spoken and confirmed verbally",
                    },
                    "patient_name": {
                        "type": "string",
                        "description": "Patient's full name",
                    },
                },
                "required": ["doctor_name", "date", "time_slot", "phone_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancels an active appointment for a patient and reopens the time slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Patient's phone number associated with the appointment",
                    },
                    "appointment_id": {
                        "type": "string",
                        "description": "Optional specific appointment ID, e.g. 'APT-20261124-78A1'",
                    },
                },
                "required": ["phone_number"],
            },
        },
    },
]


async def handle_tool_call(
    function_name: str,
    arguments: Dict[str, Any],
    event_bus: EventBus = global_event_bus,
) -> Dict[str, Any]:
    """
    Executes appointment service functions and broadcasts live events
    (tool_call_start, tool_call_result, appointment_booked, appointment_cancelled).
    """
    await event_bus.broadcast("tool_call_start", {
        "tool": function_name,
        "arguments": arguments,
    })

    result: Dict[str, Any] = {}

    try:
        if function_name == "check_doctor_availability":
            result = await check_doctor_availability(
                doctor_name=arguments.get("doctor_name"),
                specialty=arguments.get("specialty"),
                date=arguments.get("date"),
            )

        elif function_name == "book_appointment":
            result = await book_appointment(
                doctor_name=arguments.get("doctor_name", ""),
                date=arguments.get("date", ""),
                time_slot=arguments.get("time_slot", ""),
                phone_number=arguments.get("phone_number", ""),
                patient_name=arguments.get("patient_name"),
            )
            if result.get("status") == "success":
                await event_bus.broadcast("appointment_booked", result.get("appointment", {}))

        elif function_name == "cancel_appointment":
            result = await cancel_appointment(
                phone_number=arguments.get("phone_number", ""),
                appointment_id=arguments.get("appointment_id"),
            )
            if result.get("status") == "success":
                await event_bus.broadcast("appointment_cancelled", result.get("cancelled_appointment", {}))

        else:
            result = {
                "status": "error",
                "error_code": "UNKNOWN_FUNCTION",
                "message": f"Unknown tool function '{function_name}'.",
            }

    except Exception as e:
        logger.exception("Error executing tool function %s: %s", function_name, e)
        result = {
            "status": "error",
            "error_code": "EXECUTION_ERROR",
            "message": str(e),
        }

    await event_bus.broadcast("tool_call_result", {
        "tool": function_name,
        "result": result,
    })

    return result


def build_llm_tools(event_bus: EventBus, llm: Any) -> Any:
    """Builds Pipecat FunctionSchema objects (or falls back to TOOL_SCHEMAS + register_function)."""
    async def _on_check_availability(params, *args, **kwargs):
        call_args = getattr(params, "arguments", kwargs) if hasattr(params, "arguments") else kwargs
        result = await handle_tool_call("check_doctor_availability", call_args, event_bus)
        if hasattr(params, "result_callback") and callable(params.result_callback):
            await params.result_callback(result)
        return result

    async def _on_book_appointment(params, *args, **kwargs):
        call_args = getattr(params, "arguments", kwargs) if hasattr(params, "arguments") else kwargs
        result = await handle_tool_call("book_appointment", call_args, event_bus)
        if hasattr(params, "result_callback") and callable(params.result_callback):
            await params.result_callback(result)
        return result

    async def _on_cancel_appointment(params, *args, **kwargs):
        call_args = getattr(params, "arguments", kwargs) if hasattr(params, "arguments") else kwargs
        result = await handle_tool_call("cancel_appointment", call_args, event_bus)
        if hasattr(params, "result_callback") and callable(params.result_callback):
            await params.result_callback(result)
        return result

    try:
        from pipecat.adapters.llm.schemas.function_schema import FunctionSchema
    except ImportError:
        try:
            from pipecat.adapters.schemas.function_schema import FunctionSchema
        except ImportError:
            FunctionSchema = None

    if FunctionSchema:
        return [
            FunctionSchema(
                name="check_doctor_availability",
                description="Checks available doctors and their open time slots by doctor name, specialty, or date.",
                properties={
                    "doctor_name": {"type": "string", "description": "Doctor's name or partial name, e.g. 'Vance' or 'Dr. Marcus Chen'"},
                    "specialty": {"type": "string", "description": "Medical specialty (Cardiology, Dermatology, Pediatrics, Orthopedics, General Medicine)"},
                    "date": {"type": "string", "description": "Target date: 'today', 'tomorrow', or 'YYYY-MM-DD'"},
                },
                required=[],
                handler=_on_check_availability,
            ),
            FunctionSchema(
                name="book_appointment",
                description="Atomically books a confirmed appointment after verifying the phone number verbally.",
                properties={
                    "doctor_name": {"type": "string", "description": "Doctor's full or partial name"},
                    "date": {"type": "string", "description": "Appointment date ('today', 'tomorrow', or 'YYYY-MM-DD')"},
                    "time_slot": {"type": "string", "description": "Requested time slot, e.g. '09:00 AM' or '02:00 PM'"},
                    "phone_number": {"type": "string", "description": "Patient's phone number as spoken and confirmed verbally"},
                    "patient_name": {"type": "string", "description": "Patient's full name"},
                },
                required=["doctor_name", "date", "time_slot", "phone_number"],
                handler=_on_book_appointment,
            ),
            FunctionSchema(
                name="cancel_appointment",
                description="Cancels an active appointment for a patient and reopens the time slot.",
                properties={
                    "phone_number": {"type": "string", "description": "Patient's phone number associated with the appointment"},
                    "appointment_id": {"type": "string", "description": "Optional specific appointment ID, e.g. 'APT-20261124-78A1'"},
                },
                required=["phone_number"],
                handler=_on_cancel_appointment,
            ),
        ]

    if hasattr(llm, "register_function"):
        llm.register_function("check_doctor_availability", _on_check_availability)
        llm.register_function("book_appointment", _on_book_appointment)
        llm.register_function("cancel_appointment", _on_cancel_appointment)
    return TOOL_SCHEMAS
