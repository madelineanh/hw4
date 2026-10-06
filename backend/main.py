from pathlib import Path
import hashlib
import hmac
import json
import secrets
import sqlite3
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import run_shop_agent
from models import ChatHistoryRecord, ChatHistoryResponse, ChatRequest, ChatResponse, CustomerContext, ProductCard


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATABASE = DATA_DIR / "campus_customs.db"
PBKDF2_ITERATIONS = 120_000
ACTIVE_SESSIONS: dict[str, int] = {}

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/images", StaticFiles(directory=DATA_DIR), name="images")


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def parse_json_array(value: str | None) -> list[str]:
    import json

    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def product_record(row: sqlite3.Row) -> dict[str, Any]:
    product = dict(row)
    product["colors"] = parse_json_array(product.get("colors"))
    product["search_tags"] = parse_json_array(product.get("search_tags"))
    return product


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


def hash_password(password: str, salt: str | None = None) -> str:
    """Store an independently salted PBKDF2-SHA256 password hash."""
    chosen_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), chosen_salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${chosen_salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def public_user(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "first_name": row["first_name"] or row["name"].split(" ", 1)[0],
        "last_name": row["last_name"] or "",
        "email": row["email"],
    }


def customer_context(user_id: int | None, session_token: str | None = None) -> CustomerContext | None:
    if user_id is None:
        return None
    if not session_token or ACTIVE_SESSIONS.get(session_token) != user_id:
        raise HTTPException(status_code=401, detail="Please log in to access saved chat history")
    with connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Account not found")
    user = public_user(row)
    return CustomerContext(**user)


def session_response(row: sqlite3.Row) -> dict[str, Any]:
    """Return a public profile plus an opaque, process-local session credential."""
    token = secrets.token_urlsafe(32)
    ACTIVE_SESSIONS[token] = row["id"]
    return {"user": public_user(row), "session_token": token}


def chat_history(user_id: int, limit: int = 40) -> list[ChatHistoryRecord]:
    query = """
        SELECT role, content, products_json, created_at
        FROM chat_messages WHERE user_id = ?
        ORDER BY id DESC LIMIT ?
    """
    with connect() as connection:
        rows = list(reversed(connection.execute(query, (user_id, limit)).fetchall()))
    messages: list[ChatHistoryRecord] = []
    for row in rows:
        try:
            products = [ProductCard.model_validate(item) for item in json.loads(row["products_json"] or "[]")]
        except (json.JSONDecodeError, ValueError, TypeError):
            products = []
        messages.append(ChatHistoryRecord(role=row["role"], content=row["content"], products=products, created_at=row["created_at"]))
    return messages


def save_chat_message(user_id: int, role: str, content: str, products: list[ProductCard] | None = None) -> None:
    products_json = json.dumps([product.model_dump() for product in products or []]) if products else None
    with connect() as connection:
        connection.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )
        connection.commit()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_session_token: str | None = Header(default=None)) -> ChatResponse:
    """Send a shopper message through the Campus Concierge agent."""
    try:
        customer = customer_context(request.user_id, x_session_token)
        history = (
            [{"role": item.role, "content": item.content} for item in chat_history(customer.id)]
            if customer else [turn.model_dump() for turn in request.history]
        )
        response = await run_shop_agent(
            request.message,
            history,
            customer=customer,
            page_context=request.page_context,
        )
        if customer:
            save_chat_message(customer.id, "user", request.message)
            save_chat_message(customer.id, "assistant", response.reply, response.products)
        return response
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=502, detail="The Campus Concierge is temporarily unavailable")


@app.get("/api/chat/history/{user_id}", response_model=ChatHistoryResponse)
def get_chat_history(user_id: int, x_session_token: str | None = Header(default=None)) -> ChatHistoryResponse:
    """Reload persisted conversation history for a signed-in shopper."""
    customer_context(user_id, x_session_token)
    return ChatHistoryResponse(messages=chat_history(user_id))


@app.post("/api/auth/register", status_code=201)
def register(request: RegisterRequest) -> dict[str, Any]:
    first_name = request.first_name.strip()
    last_name = request.last_name.strip()
    email = request.email.strip().lower()
    if not first_name or not last_name:
        raise HTTPException(status_code=422, detail="First and last name are required")
    with connect() as connection:
        try:
            cursor = connection.execute(
                """INSERT INTO users (name, email, password_hash, first_name, last_name)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"{first_name} {last_name}", email, hash_password(request.password), first_name, last_name),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="An account with that email already exists")
        row = connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return session_response(row)


@app.post("/api/auth/login")
def login(request: LoginRequest) -> dict[str, Any]:
    email = request.email.strip().lower()
    with connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
    if row is None or not verify_password(request.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return session_response(row)


@app.post("/api/auth/logout", status_code=204)
def logout(x_session_token: str | None = Header(default=None)) -> None:
    """Invalidate the current in-memory session without exposing account data."""
    if x_session_token:
        ACTIVE_SESSIONS.pop(x_session_token, None)


@app.get("/api/products")
def products() -> list[dict[str, Any]]:
    query = """
        SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
        FROM catalogue c
        LEFT JOIN inventory i ON i.product_id = c.product_id
        GROUP BY c.product_id
        ORDER BY c.name COLLATE NOCASE
    """
    with connect() as connection:
        return [product_record(row) for row in connection.execute(query).fetchall()]


@app.get("/api/products/{product_id}")
def product(product_id: str) -> dict[str, Any]:
    query = """
        SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
        FROM catalogue c
        LEFT JOIN inventory i ON i.product_id = c.product_id
        WHERE c.product_id = ?
        GROUP BY c.product_id
    """
    inventory_query = """
        SELECT size, quantity FROM inventory
        WHERE product_id = ? ORDER BY CASE size
          WHEN 'XS' THEN 1 WHEN 'S' THEN 2 WHEN 'M' THEN 3
          WHEN 'L' THEN 4 WHEN 'XL' THEN 5 ELSE 6 END, size
    """
    with connect() as connection:
        row = connection.execute(query, (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        result = product_record(row)
        result["inventory"] = [dict(item) for item in connection.execute(inventory_query, (product_id,))]
        return result
