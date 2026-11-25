from pydantic import BaseModel, ConfigDict
from decimal import Decimal

class LowStockProduct(BaseModel):
    id: int
    name: str
    stock: int
    price: Decimal
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

class OrderStatusCount(BaseModel):
    pending: int = 0
    processing: int = 0
    confirmed: int = 0
    delivered: int = 0
    shipped: int = 0
    cancelled: int = 0

class AdminDashboardResponse(BaseModel):
    total_revenue: Decimal
    total_orders: int
    total_products: int
    total_users: int
    orders_by_status: OrderStatusCount
    low_stock_products: list[LowStockProduct]