import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
import httpx
from app.config import settings
from app.tools.wire_transfer import WIRE_TRANSFER_TOOL_DEFINITION

logger = logging.getLogger("fema.foundry")

async def call_foundry_agent(
    system_prompt: str,
    user_prompt: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, bool, Optional[Dict[str, Any]]]:
    """
    Calls Azure AI Foundry / OpenAI-compatible endpoint with tool calling.
    Returns: (agent_text_response, tool_called_flag, tool_arguments_dict)
    Falls back gracefully if Foundry is unconfigured, unreachable, or errors.
    """
    endpoint = settings.FOUNDRY_ENDPOINT.strip() if settings.FOUNDRY_ENDPOINT else ""
    api_key = settings.FOUNDRY_API_KEY.strip() if settings.FOUNDRY_API_KEY else ""
    model = settings.FOUNDRY_MODEL or "gpt-4o"

    if not endpoint or not api_key:
        logger.info("Foundry endpoint or API key not configured in .env. Using autonomous rogue agent core.")
        return ("", False, None)

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for msg in conversation_history:
            messages.append(msg)
    messages.append({"role": "user", "content": user_prompt})

    try:
        # Standard OpenAI client pointing to Foundry base_url
        client = AsyncOpenAI(
            base_url=endpoint.rstrip("/"),
            api_key=api_key,
            timeout=15.0
        )

        logger.info(f"Calling Foundry endpoint for model {model}...")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[WIRE_TRANSFER_TOOL_DEFINITION],
            tool_choice="auto",
            temperature=0.2
        )

        choice = response.choices[0]
        message = choice.message
        agent_content = message.content or ""

        tool_called = False
        tool_args = None

        if message.tool_calls:
            for tc in message.tool_calls:
                if tc.function.name == "submit_domestic_wire":
                    tool_called = True
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except Exception:
                        tool_args = {}
                    break

        return (agent_content, tool_called, tool_args)

    except Exception as e:
        logger.warning(f"Foundry call failed: {e}. Falling back to internal rogue agent logic.")
        return ("", False, None)
