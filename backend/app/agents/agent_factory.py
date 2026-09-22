import json
import re
import logging
from openai import AsyncOpenAI, AsyncAzureOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class MockAgentClient:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    async def get_response(self, system_prompt: str, user_prompt: str) -> str:
        logger.info(f"[TEST-MODE] [{self.agent_name}] Generating mock LLM response.")
        
        user_prompt_lower = user_prompt.lower()
        
        # Agent 2 Mock Logic (Intent parsing)
        if self.agent_name == settings.AGENT2_NAME:
            # Check for customer ID pattern (e.g. syn-cust-1006, 1006, syn-cust-9999, 9999)
            id_match = re.search(r"(?:syn-cust-)?(\d{4})", user_prompt_lower)
            if id_match:
                cust_id = f"SYN-CUST-{id_match.group(1)}"
                return json.dumps({
                    "intent": "get_customer_details",
                    "requested_fields": ["id", "phone"],
                    "search_parameters": {"id": cust_id}
                })

            if "germany" in user_prompt_lower:
                return json.dumps({
                    "intent": "list_customer_names",
                    "requested_fields": ["name", "country"],
                    "search_parameters": {"country": "Germany"}
                })
            elif "emma evans" in user_prompt_lower:
                return json.dumps({
                    "intent": "get_customer_details",
                    "requested_fields": ["id", "phone"],
                    "search_parameters": {"name": "Emma Evans"}
                })
            elif "hans russo" in user_prompt_lower:
                return json.dumps({
                    "intent": "get_customer_details",
                    "requested_fields": ["id", "phone"],
                    "search_parameters": {"name": "Hans Russo"}
                })
            else:
                return json.dumps({
                    "intent": "unknown",
                    "requested_fields": [],
                    "search_parameters": {}
                })
                
        # Agent 1 is handled deterministically via DB queries, 
        # so LLM mocking for Agent 1 is not used for data retrieval.
        return "{}"

class AgentClientWrapper:
    def __init__(self, client, model: str, provider: str = "openai"):
        self.client = client
        self.model = model
        self.provider = provider

    async def get_response(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

def get_agent_client(
    agent_name: str,
    openai_key: str = None,
    model: str = "",
    azure_endpoint: str = "",
    azure_deployment: str = "",
    azure_api_version: str = ""
):
    # If caller explicitly passed openai_key as empty string (""), return MockAgentClient immediately
    if openai_key == "":
        logger.warning(f"[TEST-MODE] Empty API key specified for {agent_name}. Using MockAgentClient.")
        return MockAgentClient(agent_name)

    # Resolve Azure and OpenAI configuration based on agent name and settings
    if agent_name == settings.AGENT1_NAME:
        resolved_azure_endpoint = (azure_endpoint or settings.AGENT1_AZURE_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT).strip()
        resolved_key = (openai_key or settings.AGENT1_AZURE_API_KEY or settings.AGENT1_OPENAI_API_KEY or settings.AZURE_OPENAI_API_KEY).strip()
        resolved_azure_deployment = (azure_deployment or settings.AGENT1_AZURE_DEPLOYMENT or settings.AZURE_OPENAI_DEPLOYMENT or model or settings.AGENT1_MODEL).strip()
        resolved_azure_version = (azure_api_version or settings.AGENT1_AZURE_API_VERSION or settings.AZURE_OPENAI_API_VERSION or "2024-08-01-preview").strip()
        resolved_model = (model or settings.AGENT1_MODEL).strip()
    elif agent_name == settings.AGENT2_NAME:
        resolved_azure_endpoint = (azure_endpoint or settings.AGENT2_AZURE_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT).strip()
        resolved_key = (openai_key or settings.AGENT2_AZURE_API_KEY or settings.AGENT2_OPENAI_API_KEY or settings.AZURE_OPENAI_API_KEY).strip()
        resolved_azure_deployment = (azure_deployment or settings.AGENT2_AZURE_DEPLOYMENT or settings.AZURE_OPENAI_DEPLOYMENT or model or settings.AGENT2_MODEL).strip()
        resolved_azure_version = (azure_api_version or settings.AGENT2_AZURE_API_VERSION or settings.AZURE_OPENAI_API_VERSION or "2024-08-01-preview").strip()
        resolved_model = (model or settings.AGENT2_MODEL).strip()
    else:
        resolved_azure_endpoint = (azure_endpoint or settings.AZURE_OPENAI_ENDPOINT).strip()
        resolved_key = (openai_key or settings.AZURE_OPENAI_API_KEY).strip()
        resolved_azure_deployment = (azure_deployment or settings.AZURE_OPENAI_DEPLOYMENT or model or "gpt-4o").strip()
        resolved_azure_version = (azure_api_version or settings.AZURE_OPENAI_API_VERSION or "2024-08-01-preview").strip()
        resolved_model = (model or "gpt-4o").strip()

    if not resolved_key:
        logger.warning(f"[TEST-MODE] No API key configured for {agent_name}. Using MockAgentClient.")
        return MockAgentClient(agent_name)

    # 1. If Azure endpoint is provided, use AsyncAzureOpenAI
    if resolved_azure_endpoint:
        # Normalize Azure endpoint (strip /openai/v1 or trailing slash, map domain to match SSL cert)
        clean_endpoint = re.sub(r"/openai/v1/?$", "", resolved_azure_endpoint.strip()).rstrip("/")
        if "agent2gdpr.openai.azure.com" in clean_endpoint:
            clean_endpoint = clean_endpoint.replace("agent2gdpr.openai.azure.com", "agent2gdpr.cognitiveservices.azure.com")

        logger.info(f"[REAL-AZURE-MODE] Azure OpenAI client configured for {agent_name} using deployment '{resolved_azure_deployment}'.")
        client = AsyncAzureOpenAI(
            azure_endpoint=clean_endpoint,
            api_key=resolved_key,
            api_version=resolved_azure_version
        )
        return AgentClientWrapper(client, resolved_azure_deployment, provider="azure")

    # If key appears to be Azure-format (base64 token / >50 chars, not starting with 'sk-') but endpoint is missing
    if len(resolved_key) > 50 and not resolved_key.startswith("sk-"):
        logger.warning(
            f"[TEST-MODE] Azure-format key detected for {agent_name}, but AZURE_OPENAI_ENDPOINT is not configured. "
            f"Please set AZURE_OPENAI_ENDPOINT in backend/.env to enable Azure OpenAI mode. Falling back to MockAgentClient."
        )
        return MockAgentClient(agent_name)

    logger.info(f"[REAL-OPENAI-MODE] OpenAI client configured for {agent_name} using model '{resolved_model}'.")
    client = AsyncOpenAI(api_key=resolved_key)
    return AgentClientWrapper(client, resolved_model, provider="openai")

