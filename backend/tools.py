import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai import RunContext

from models import InventoryItem, ProductCard, ShopDeps, StockLookup


def _audit_tool(ctx: RunContext[ShopDeps], name: str, args: str, result: str) -> None:
    ctx.deps.audit_events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "tool_call",
        "tool_name": name,
        "args": args[:180],
        "result": result[:180],
    })


def _connect(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    return connection


def _array(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _card(row: sqlite3.Row, inventory: list[sqlite3.Row] | None = None) -> ProductCard:
    stock = inventory or []
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        price=row["price"],
        image_file_path=row["image_file_path"],
        colors=_array(row["colors"]),
        total_stock=row["total_stock"] if "total_stock" in row.keys() else sum(item["quantity"] for item in stock),
        inventory=[InventoryItem(size=item["size"], quantity=item["quantity"]) for item in stock],
    )


def search_products(ctx: RunContext[ShopDeps], query: str, limit: int = 6) -> list[ProductCard]:
    """Search catalogue names, descriptions, garment types, colors, and tags for relevant products."""
    clean_query = query.strip()
    if not clean_query:
        return []
    terms = [term for term in clean_query.lower().split() if len(term) > 1][:8]
    clauses: list[str] = []
    values: list[str] = []
    for term in terms:
        pattern = f"%{term}%"
        clauses.append("(lower(c.name) LIKE ? OR lower(c.description) LIKE ? OR lower(c.garment_type) LIKE ? OR lower(c.colors) LIKE ? OR lower(c.search_tags) LIKE ?)")
        values.extend([pattern] * 5)
    if not clauses:
        return []
    query_sql = f"""
        SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
        FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
        WHERE {' OR '.join(clauses)}
        GROUP BY c.product_id ORDER BY c.name COLLATE NOCASE LIMIT ?
    """
    with _connect(ctx.deps.database) as connection:
        rows = connection.execute(query_sql, (*values, max(1, min(limit, 8)))).fetchall()
    cards = [_card(row) for row in rows]
    _audit_tool(ctx, "search_products", f"query={clean_query!r}; limit={limit}", f"returned {len(cards)} products")
    return cards


def browse_products(
    ctx: RunContext[ShopDeps],
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    in_stock: bool = True,
    limit: int = 6,
) -> list[ProductCard]:
    """Find products using shopper constraints such as garment type, color, budget, and availability."""
    clauses: list[str] = []
    values: list[object] = []
    if garment_type and garment_type.strip():
        clauses.append("lower(c.garment_type) LIKE ?")
        values.append(f"%{garment_type.strip().lower()}%")
    if color and color.strip():
        clauses.append("lower(c.colors) LIKE ?")
        values.append(f"%{color.strip().lower()}%")
    if max_price is not None:
        clauses.append("c.price <= ?")
        values.append(max(0, max_price))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    having = "HAVING COALESCE(SUM(i.quantity), 0) > 0" if in_stock else ""
    query = f"""
        SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
        FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
        {where}
        GROUP BY c.product_id
        {having}
        ORDER BY c.price ASC, c.name COLLATE NOCASE LIMIT ?
    """
    with _connect(ctx.deps.database) as connection:
        rows = connection.execute(query, (*values, max(1, min(limit, 6)))).fetchall()
    cards = [_card(row) for row in rows]
    _audit_tool(ctx, "browse_products", f"type={garment_type!r}; color={color!r}; max_price={max_price!r}; in_stock={in_stock}", f"returned {len(cards)} products")
    return cards


def get_product(ctx: RunContext[ShopDeps], product_id: str) -> ProductCard | None:
    """Look up one exact product's description, price, colors, and current inventory."""
    with _connect(ctx.deps.database) as connection:
        row = connection.execute(
            """SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
               FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
               WHERE c.product_id = ? GROUP BY c.product_id""", (product_id,)
        ).fetchone()
        if row is None:
            _audit_tool(ctx, "get_product", f"product_id={product_id!r}", "not found")
            return None
        inventory = connection.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY size", (product_id,)
        ).fetchall()
    card = _card(row, inventory)
    _audit_tool(ctx, "get_product", f"product_id={product_id!r}", f"price=${card.price:.2f}; {len(card.inventory)} sizes")
    return card


def get_size_stock(
    ctx: RunContext[ShopDeps], product_id: str, size: str | None = None
) -> StockLookup | None:
    """Look up live stock for a product, or one requested size. A quantity of zero means out of stock."""
    with _connect(ctx.deps.database) as connection:
        product = connection.execute(
            "SELECT product_id, name FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if product is None:
            _audit_tool(ctx, "get_size_stock", f"product_id={product_id!r}; size={size!r}", "not found")
            return None
        inventory = connection.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY size", (product_id,)
        ).fetchall()
    inventory_items = [InventoryItem(size=item["size"], quantity=item["quantity"]) for item in inventory]
    if size is None:
        result = StockLookup(
            product_id=product["product_id"], name=product["name"], inventory=inventory_items
        )
        _audit_tool(ctx, "get_size_stock", f"product_id={product_id!r}; size=None", f"returned {len(inventory_items)} sizes")
        return result
    requested_size = size.strip().upper()
    match = next((item for item in inventory_items if item.size.upper() == requested_size), None)
    quantity = match.quantity if match else 0
    result = StockLookup(
        product_id=product["product_id"],
        name=product["name"],
        requested_size=requested_size,
        quantity=quantity,
        in_stock=quantity > 0,
        inventory=inventory_items,
    )
    _audit_tool(ctx, "get_size_stock", f"product_id={product_id!r}; size={requested_size!r}", f"quantity={quantity}; in_stock={quantity > 0}")
    return result
