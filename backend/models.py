from pathlib import Path

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    price: float
    image_file_path: str
    colors: list[str] = Field(default_factory=list)
    total_stock: int = 0
    inventory: list[InventoryItem] = Field(default_factory=list)


class StockLookup(BaseModel):
    """Authoritative availability for one product, optionally narrowed to one size."""

    product_id: str
    name: str
    requested_size: str | None = None
    quantity: int | None = None
    in_stock: bool | None = None
    inventory: list[InventoryItem] = Field(default_factory=list)


class ChatTurn(BaseModel):
    role: str
    content: str


class PageContext(BaseModel):
    product_id: str
    product_name: str


class CustomerContext(BaseModel):
    id: int
    first_name: str
    last_name: str = ""
    email: str


class ChatHistoryRecord(ChatTurn):
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[ChatHistoryRecord] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    user_id: int | None = None
    page_context: PageContext | None = None


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list, max_length=6)


class ShopDeps:
    def __init__(
        self,
        database: Path,
        customer: CustomerContext | None = None,
        page_context: PageContext | None = None,
        audit_events: list[dict[str, str]] | None = None,
    ):
        self.database = database
        self.customer = customer
        self.page_context = page_context
        self.audit_events = audit_events if audit_events is not None else []
