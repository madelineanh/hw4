# Problem 9: Usability improvements

## Front end: Catalogue filters

Added a garment-style menu and an “In stock” checkbox alongside the existing product search. The product count updates immediately as a shopper filters.

This helps shoppers narrow a large catalogue without needing to know exact product names, and avoids the frustration of browsing items that have no remaining inventory.

## Front end: Concierge quick prompts

Added visible quick-prompt buttons in the chat panel: “Show me hoodies,” “Yale gifts under $50,” and “What is in stock?” Selecting one places a useful starter question into the chat input.

This makes the Concierge easier to discover and gives shoppers a clear starting point when they are unsure what the chat can help with.

## Agent/backend: Constraint-aware product browsing

Added the `browse_products` tool. It accepts garment type, color, maximum price, and in-stock preferences, uses parameterized database queries, and returns at most six validated product cards.

This gives the agent a precise way to answer multi-part requests such as “blue hoodies under $60 that are in stock,” producing more relevant recommendations and avoiding broad, loosely matched results.

## Agent/backend: Bounded, readable agent output

Limited structured chat responses to six product cards and capped each PydanticAI run at six model requests. The prompt tells the agent to choose the constraint-aware tool when a shopper provides filters.

This keeps the product panel readable, prevents an excessive set of cards from overwhelming shoppers, and guards against long, costly tool/model loops while retaining enough room for useful recommendations.
