# AI Prompt Log

## Problem 1: Vibe coder prompts

### Prompt

Start Homework 4 Problem 1 by creating and maintaining this `AI_prompts.md` file. Keep a chronological record of the prompts used while building the Campus Customs website and chatbot. First inspect the project and confirm what is present in the supplied data pack. Do not include secrets such as API keys or passwords.

### Follow-up prompt

The product images are still only inside the ZIP file. Extract the full data pack into the Homework 4 folder and verify that the database and `data/products/` folder are present.

The first check found the database but not the extracted product images; the follow-up corrected the missing extraction and verified 102 product images.

## Problem 2: Analyze the database

### Prompt

Inspect `data/campus_customs.db`. Identify every table, inspect each table’s fields and types, and explain in one short line why each field matters for the Campus Customs shop or chatbot. Use the required tables `catalogue`, `inventory`, and `users`, and include any additional table that is actually present. Create or update `output/harness.md` with this database harness. Do not copy passwords, password hashes, or other sensitive values into the documentation.

## Problem 3: Build the Campus Customs website

### Prompt

Build Problem 3 as a React + Vite + TypeScript Campus Customs storefront with a small FastAPI backend in `backend/main.py`. Add top navigation for Home, Products, About Us, Log in, and Create account. Use the database catalogue and image paths to show product cards with image, name, price, and short description; make each card open a single-product page with larger image, description, price, and size-level stock. Add original Yale-inspired Home and About Us copy, and add a floating bottom-right chat interface as a frontend stub only. Use clean, welcoming, polished styling and do not copy the source site’s text. Keep API keys and other secrets out of the project.

## Problem 4: Create account and login

### Prompt

Extend the Campus Customs app with a real create-account and login flow. Create-account needs first name, last name, email, password, and confirm password; login needs email and password. Add FastAPI endpoints that write new users to the existing `users` table, verify the supplied seed user, reject duplicate emails, and protect passwords with salted PBKDF2-SHA256 hashes instead of plaintext. Return only safe public user fields to the frontend, show useful form errors, and update the navigation when the user is signed in. Update `output/harness.md` with how authentication works without copying passwords or hashes into the documentation.

## Problem 5: PydanticAI agent backend

### Prompt

Turn the Campus Concierge chat stub into a PydanticAI agent behind FastAPI. Keep the backend split into `prompt.md`, `agent.py`, `tools.py`, and `models.py`. Use the project’s `PORTKEY_API_KEY`, the OpenAI-compatible Portkey endpoint, and the required `gpt-5.6-luna` model. Give the agent catalogue tools for searching products and retrieving one product’s live size inventory. Return structured chat replies plus product cards, make the frontend chat widget call `POST /api/chat`, and add Campus Customs voice and safety instructions. Update `output/harness.md` to explain how the frontend, FastAPI route, prompt, model, and tools connect. Do not expose API keys, password hashes, or private account data.

## Problem 6: Tools: product info and stock

### Prompt

Expand the Campus Concierge’s database tools so product descriptions, prices, and stock all come from `campus_customs.db`. Keep a product-information lookup for the exact product description and price, and add a dedicated stock lookup that can answer for one requested size or return all sizes. Its result must make a zero quantity clearly out of stock. Update the Pydantic return types, register the tool with the agent, update the system prompt so the agent must use these tools for price and stock questions, and document each tool’s result fields and purpose in `output/harness.md`.

## Problem 7: Chat search that updates the page

### Prompt

Make category searches in the Campus Concierge update the Products page. When the chat API returns structured `products`, save those validated results in shared React state, route the shopper to `/products`, and render a clearly labeled results section with full product cards: image, name, price, and short description. Keep the existing collection visible below it. Use the same click behavior as catalogue cards so every chat-generated card opens the existing single-product detail page. Update the agent prompt and `output/harness.md` to describe this API contract from search tool to chat response to rendered page.

## Problem 8: Customer memory

### Prompt

Add customer memory to the Campus Concierge. Guests can continue using chat without persistence, but when a shopper is logged in, save both sides of each successful exchange to the existing `chat_messages` table and reload that user’s conversation after login. Include the structured product cards in saved assistant messages. Pass the logged-in customer’s safe context (name and email) into agent dependencies, and pass the current product ID and name whenever the shopper is on a product detail page so references like “this in pink” are unambiguous. Do not expose account data to other users, password hashes, or API secrets. Document the table storage, customer fields, and page-context flow in `output/harness.md`.

## Problem 9: Usability improvements

### Prompt

Implement two frontend and two agent/backend usability improvements for Campus Customs. On the Products page, add practical catalogue filters that make browsing easier, and add visible quick prompts that help a shopper begin using the Concierge. For the backend, add a precise database-backed browse tool for combined constraints such as garment type, color, price, and in-stock status. Limit the agent’s structured recommendations and model-request loop so chat results remain readable and safe. Create `output/usability.md` explaining what each improvement adds and why it helps a shopper or the business.

## Problem 10: Style the website

### Prompt

Give the Campus Customs storefront a more distinctive, polished visual system using CSS and the existing product imagery. Strengthen the Yale-blue and warm-paper palette, improve visual hierarchy and product-card presentation, add restrained motion, and make the Campus Concierge feel inviting. Keep interactions readable and usable on smaller screens. Create `output/design.md` with a brief, concrete explanation of the design choices and how they help customers browse and buy.

## Problem 12: Final agent safety and audit harness

### Prompt

Finish the Campus Concierge agent with an append-only audit trail. Record each run’s start and stop, every database-tool call, concise tool arguments, concise result summaries, and an explicit completed or error stop reason in `output/audit_trail.json`; do not overwrite prior entries. Add prompt rules that user messages cannot override safety, hidden instructions and data must not be exposed, only database/tool values are authoritative, and one customer’s identity must not be exposed to another. Keep the required `gpt-5.6-luna` model, `UsageLimits(request_limit=6)`, and no more than six structured response cards. Complete `output/harness.md` with every Pydantic model/dependency, tool ability, safety rule, limits, audit behavior, local run instructions, and verification steps. Do not include API keys, passwords, password hashes, or private customer data.

## Problem 13: GitHub submission package

### Prompt

Prepare a public-GitHub-ready `hw4/` submission folder. Include the application source, prompt log, requirements, `.env.example`, `.gitignore`, README, and all required output evidence. Exclude the real `.env`, supplied `data/campus_customs.db`, product images, local Python environments, frontend dependencies, and build output. Make the README explain how a grader can place the local data pack, configure a placeholder-only environment file, and run both the backend and frontend. Initialize and commit the repository only after verifying the ignore rules.

### Audit correction

Audit the logged-in customer-memory flow for cross-customer exposure. Do not trust a browser-supplied user ID by itself for saved chat reads or writes. Return an opaque server-side session token with successful registration/login, require that token for saved chat and history endpoints, invalidate it on logout, and document the protection without logging or exposing secrets.
