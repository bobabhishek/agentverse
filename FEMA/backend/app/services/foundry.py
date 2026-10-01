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
        # Normalize base_url for AsyncOpenAI client
        clean_endpoint = endpoint.rstrip("/")
        if clean_endpoint.endswith("/responses"):
            base_url = clean_endpoint[:-len("/responses")].rstrip("/")
        elif clean_endpoint.endswith("/chat/completions"):
            base_url = clean_endpoint[:-len("/chat/completions")].rstrip("/")
        else:
            base_url = clean_endpoint

        # Standard OpenAI client pointing to Foundry base_url
        client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={"api-key": api_key},
            timeout=20.0
        )

        logger.info(f"Calling Foundry endpoint at {base_url} for model {model}...")
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
        logger.warning(f"Foundry chat completion call failed: {e}. Trying direct Responses API if applicable...")
        
        # If the endpoint is specifically an Azure Foundry Responses endpoint, try direct REST call
        if "/responses" in endpoint:
            try:
                responses_url = clean_endpoint if clean_endpoint.endswith("/responses") else f"{clean_endpoint}/responses"
                headers = {
                    "Content-Type": "application/json",
                    "api-key": api_key,
                    "Authorization": f"Bearer {api_key}"
                }
                body = {
                    "model": model,
                    "input": user_prompt,
                    "instructions": system_prompt
                }
                async with httpx.AsyncClient(timeout=20.0) as http_client:
                    resp = await http_client.post(responses_url, json=body, headers=headers)
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        text = data.get("output") or data.get("response") or data.get("content") or ""
                        if isinstance(text, list) and text:
                            text = str(text[0])
                        return (str(text), False, None)
                    else:
                        logger.warning(f"Direct Responses API returned status {resp.status_code}: {resp.text[:150]}")
            except Exception as direct_err:
                logger.warning(f"Direct Responses API fallback also failed: {direct_err}")

        logger.warning("Falling back to internal deterministic rogue agent logic.")
        return ("", False, None)
