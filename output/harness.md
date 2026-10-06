# Campus Customs Harness

## Problem 2: Analyze the database

Database inspected: `data/campus_customs.db`

The database contains four tables: `catalogue`, `inventory`, `users`, and `chat_messages`.

### `catalogue`

| Field | Why it matters |
|---|---|
| `product_id` (TEXT, primary key) | Stable identifier used to connect a product to inventory and to identify products in the shop and chatbot results. |
| `name` (TEXT) | Customer-facing product name for browsing and recommendations. |
| `garment_type` (TEXT) | Supports filtering and helps the chatbot describe the kind of garment. |
| `description` (TEXT) | Supplies product details for the product page and accurate chatbot answers. |
| `colors` (TEXT, JSON array) | Stores available color information for display and search. |
| `search_tags` (TEXT, JSON array) | Provides searchable terms for matching customer requests to products. |
| `image_file_path` (TEXT) | Points the frontend to the product image in `data/products/`. |
| `price` (REAL) | The authoritative product price shown to customers and used by the chatbot. |

### `inventory`

| Field | Why it matters |
|---|---|
| `id` (INTEGER, primary key) | Uniquely identifies an inventory row. |
| `product_id` (TEXT) | Links a size-specific stock record to a catalogue product. |
| `size` (TEXT) | Identifies the size whose availability is being shown or requested. |
| `quantity` (INTEGER) | Gives the authoritative stock count so the shop and chatbot can answer honestly. |

### `users`

| Field | Why it matters |
|---|---|
| `id` (INTEGER, primary key) | Identifies an account internally. |
| `name` (TEXT) | Stores the account’s display name. |
| `email` (TEXT) | Identifies the customer for account creation and login. |
| `password_hash` (TEXT) | Stores a one-way password hash for authentication; the plaintext password must never be stored or shown. |
| `created_at` (TEXT) | Records when the account was created. |
| `first_name` (TEXT, nullable) | Supports personalized greetings and account displays. |
| `last_name` (TEXT, nullable) | Complements the first name for the customer’s full name. |

### `chat_messages`

| Field | Why it matters |
|---|---|
| `id` (INTEGER, primary key) | Uniquely identifies a saved chat message. |
| `user_id` (INTEGER) | Associates a message with the customer account or conversation owner. |
| `role` (TEXT) | Distinguishes the customer’s message from the assistant’s response. |
| `content` (TEXT) | Stores the text needed to display and continue the conversation. |
| `products_json` (TEXT, nullable) | Preserves product matches returned with a response so the frontend can display them. |
| `created_at` (TEXT) | Records the message timestamp and preserves conversation order. |

## Problem 4: Create account and login

The frontend submits account forms to `POST /api/auth/register` and `POST /api/auth/login`. Registration writes a user’s first name, last name, email, display name, and password hash to `users`. Login looks up the normalized email and returns only public account fields (`id`, names, and email) after verifying the password.

Passwords are never stored in plaintext. The backend creates a fresh random salt for every new account and stores a PBKDF2-SHA256 record in the form `pbkdf2_sha256$salt$digest`, using 120,000 iterations. Verification uses a constant-time digest comparison. The frontend stores only the returned public user object for its signed-in display; it does not store the password or password hash.

The supplied seed account was used to confirm the login path, and newly registered accounts use the same secure hash format. Duplicate emails are rejected, invalid credentials return a generic error, and the database’s unique email constraint prevents duplicate accounts.

## Problem 5: PydanticAI agent backend

The frontend chat widget sends `POST /api/chat` to FastAPI with the current message and a short conversation history. FastAPI passes that request to the PydanticAI agent in `backend/agent.py`. The agent loads `backend/prompts/prompt.md`, uses the required `gpt-5.6-luna` model through the project’s `PORTKEY_API_KEY`, and receives the database path through `ShopDeps`.

The agent has two catalogue tools in `backend/tools.py`: `search_products` searches names, descriptions, garment types, colors, and tags; `get_product` retrieves one product with current size-level inventory. Both return validated `ProductCard` models. The structured response contains a concise `reply` and matching product cards, which the frontend renders in the chat panel. The agent is instructed to use database values for price and stock, avoid guessing, and never expose credentials, password hashes, or private account details.

## Problem 6: Product information and stock tools

The Campus Concierge has three database-backed tools, each using `data/campus_customs.db` as its source of truth:

| Tool | Lookup result fields | Why these fields are returned |
|---|---|---|
| `search_products(query, limit)` | `product_id`, `name`, `garment_type`, `description`, `price`, `image_file_path`, `colors`, `total_stock` | Finds a shopper’s likely matches and provides enough trusted information to recommend and render product cards. `product_id` supports a follow-up exact lookup. |
| `get_product(product_id)` | All `ProductCard` fields plus size-level `inventory` (`size`, `quantity`) | Answers exact description, color, and price questions from `catalogue`, then joins the product to live stock records. |
| `get_size_stock(product_id, size?)` | `product_id`, `name`, optional `requested_size`, `quantity`, `in_stock`, and complete `inventory` | Answers stock questions precisely. When a shopper specifies a size, `quantity` and `in_stock` make a zero quantity unambiguous; the full inventory still lets the agent suggest another available size. |

`get_product` and `get_size_stock` never invent availability: they query the `catalogue` and `inventory` tables every time. The agent prompt requires a stock lookup for stock questions and requires it to state clearly when a requested size has quantity zero or is unavailable.

## Problem 7: Chat search that updates the page

For category requests, the agent calls `search_products` and returns tool-validated `ProductCard` objects in the `products` field of `ChatResponse`. The chat widget saves that response in root React state and routes the shopper to `/products`. The Products page renders a “Campus Concierge Picks” section with full product cards: image, name, price, and short description.

Those dynamic cards use the same `ProductGrid` and `go('/products/:product_id')` behavior as the catalogue cards. Selecting any chat-generated card therefore opens the existing single-item page with its large image, full product information, and size inventory.

## Problem 8: Customer memory

Guests can chat without an account, but their messages remain only in the browser during that visit. For a logged-in shopper, the backend writes two rows per successful exchange to `chat_messages`: the customer message (`role = user`) and the Concierge reply (`role = assistant`). The reply’s structured product cards are serialized in `products_json`; this lets the chat panel restore both the text and any prior product suggestions.

When the frontend recognizes a signed-in user, it calls `GET /api/chat/history/{user_id}` and reloads that user’s stored conversation. For a new chat request, FastAPI loads the same database history rather than trusting browser history as the source of record.

The agent receives a `CustomerContext` dependency containing only the logged-in shopper’s `id`, first name, last name, and email. It may use a first name for a natural greeting but is instructed never to repeat the email or reveal private details. On a product detail page, the frontend sends `PageContext` with the current product ID and name. The agent uses that context to resolve “this” or “it” with a product or stock tool before answering.

Saved chat access is session-protected. Registration and login return a public user profile plus an opaque server-side session token; the browser sends that token in `X-Session-Token` for a logged-in chat request or a history reload. The backend verifies that the token belongs to the requested user ID before reading or writing any saved messages, and logout invalidates the token. A bare or guessed user ID therefore cannot reveal another customer’s history.

## Problem 12: Final agent harness and safety controls

### Validated models and dependencies

| Model / dependency | Purpose |
|---|---|
| `InventoryItem` | A validated size and quantity pair used wherever size-level stock is shown. |
| `ProductCard` | The safe, UI-ready catalogue shape: identifier, name, garment type, description, price, image path, colors, aggregate stock, and size inventory. |
| `StockLookup` | The authoritative stock response for a product or requested size, including `quantity` and `in_stock` so zero stock is explicit. |
| `ChatTurn` | One role/content turn supplied as short-lived conversation context. |
| `PageContext` | Current product ID and name, allowing “this” to be resolved safely on a detail page. |
| `CustomerContext` | Minimal signed-in shopper context (`id`, first name, last name, email); it is never shared across customers. |
| `ChatHistoryRecord` / `ChatHistoryResponse` | Validated stored conversation messages and their optional saved product cards. |
| `ChatRequest` | Validates an incoming message, limited history, optional user ID, and optional product-page context. |
| `ChatResponse` | Requires a reply and caps structured product cards at six for a readable chat and results page. |
| `ShopDeps` | Passes the database path, safe shopper/page context, and a mutable per-run audit-event list into tools. |

### Agent abilities and guardrails

The Campus Concierge can use four database-backed tools: `search_products` for catalogue keyword matches, `browse_products` for combined garment/color/budget/in-stock constraints, `get_product` for one exact product and its inventory, and `get_size_stock` for authoritative full or size-specific availability. Prices, descriptions, product facts, and stock must come from these tools; a zero quantity is always treated as unavailable.

The system prompt states that shopper text cannot override safety instructions, hidden prompts or data must not be revealed, tool/database values are the only authoritative shop facts, and one customer’s identity or account information must never be exposed to another customer. Credentials, API keys, password hashes, and private account details are not returned.

The API enforces that privacy boundary as well: private chat history and persistent chat writes require the matching opaque session token, rather than relying on a browser-supplied user ID alone.

### Runtime limits and audit trail

The agent is configured with the required `gpt-5.6-luna` model through the OpenAI-compatible Portkey client. Each run applies `UsageLimits(request_limit=6)`, and `ChatResponse.products` is capped at six cards. `output/audit_trail.json` is an append-only JSON event array: every run records `run_started`, every tool call records concise arguments and a result summary, and every completion or error records `run_stopped` and its stop reason. The live validation run recorded both a stock lookup for `baseball-left-chest-crewneck` in `XS` (quantity 0) and a hoodie browse result; the file retains both runs rather than replacing earlier evidence.

### Local run and verification

Start the backend from `backend/` with the project `.env` present:

```bash
/private/tmp/campus-customs-appcheck/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

Start the frontend from `frontend/`:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Then open `http://127.0.0.1:5173`, ask the Concierge a product or stock question, and inspect `output/audit_trail.json`. The production frontend check is `npx vite build --logLevel info` from `frontend/`.
