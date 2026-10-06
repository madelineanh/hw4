import os
import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from models import ChatResponse, CustomerContext, PageContext, ShopDeps
from tools import browse_products, get_product, get_size_stock, search_products


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
PROMPT_FILE = ROOT / "prompts" / "prompt.md"
MODEL_NAME = "gpt-5.6-luna"
AUDIT_FILE = ROOT.parent / "output" / "audit_trail.json"


def append_audit(events: list[dict[str, str]]) -> None:
    """Append new agent events without ever replacing prior runs."""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(AUDIT_FILE.read_text(encoding="utf-8")) if AUDIT_FILE.exists() else []
        if not isinstance(existing, list):
            existing = []
    except json.JSONDecodeError:
        existing = []
    existing.extend(events)
    AUDIT_FILE.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


@lru_cache(maxsize=1)
def shop_agent() -> Agent[ShopDeps, ChatResponse]:
    """Build the configured PydanticAI agent once per backend process."""
    load_dotenv(PROJECT_ROOT / ".env")
    portkey_key = os.environ.get("PORTKEY_API_KEY")
    if not portkey_key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the project .env file")
    client = AsyncOpenAI(
        api_key=portkey_key,
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-api-key": portkey_key},
        timeout=60,
        max_retries=2,
    )
    model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    agent = Agent(
        model,
        system_prompt=PROMPT_FILE.read_text(encoding="utf-8"),
        deps_type=ShopDeps,
        output_type=ChatResponse,
    )
    agent.tool(search_products)
    agent.tool(browse_products)
    agent.tool(get_product)
    agent.tool(get_size_stock)
    return agent


async def run_shop_agent(
    message: str,
    history: list[dict[str, str]] | None = None,
    customer: CustomerContext | None = None,
    page_context: PageContext | None = None,
) -> ChatResponse:
    run_id = str(uuid.uuid4())
    events: list[dict[str, str]] = [{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "run_started",
        "run_id": run_id,
        "tool_name": "",
        "args": "Campus Concierge chat request",
        "result": "Agent run started",
    }]
    conversation = "\n".join(f"{turn['role']}: {turn['content']}" for turn in (history or [])[-12:])
    context: list[str] = []
    if customer:
        context.append(f"Logged-in shopper: {customer.first_name} {customer.last_name} ({customer.email})")
    else:
        context.append("Shopper is a guest; do not assume an account or saved history.")
    if page_context:
        context.append(f"Current product page: {page_context.product_name} (product_id: {page_context.product_id})")
    context_text = "\n".join(context)
    prompt = f"{context_text}\n\nConversation so far:\n{conversation}\n\nNew shopper message:\n{message}" if conversation else f"{context_text}\n\nNew shopper message:\n{message}"
    deps = ShopDeps(
        database=PROJECT_ROOT / "data" / "campus_customs.db",
        customer=customer,
        page_context=page_context,
        audit_events=events,
    )
    try:
        result = await shop_agent().run(prompt, deps=deps, usage_limits=UsageLimits(request_limit=6))
        output = result.output if isinstance(result.output, ChatResponse) else ChatResponse.model_validate(result.output)
        events.append({"timestamp": datetime.now(timezone.utc).isoformat(), "event": "run_stopped", "run_id": run_id, "tool_name": "", "args": "", "result": f"completed; {len(output.products)} product cards; stop_reason=completed"})
        return output
    except Exception as exc:
        events.append({"timestamp": datetime.now(timezone.utc).isoformat(), "event": "run_stopped", "run_id": run_id, "tool_name": "", "args": "", "result": f"stop_reason=error; {type(exc).__name__}"})
        raise
    finally:
        append_audit(events)
