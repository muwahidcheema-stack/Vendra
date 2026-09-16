import enum 
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, Text, Enum, ForeignKey, DateTime, Numeric, CheckConstraint, UniqueConstraint
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"
    DELIVERED = "delivered"

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[UserRole]= mapped_column(Enum(UserRole), default=UserRole.CUSTOMER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    orders: Mapped[list[Order]] = relationship(back_populates="user")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    wishlist_items: Mapped[list["WishList"]] = relationship(back_populates="user" , cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user", cascade="all, delete-orphan",)
    
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("stock >= 0", name="check_product_stock_nonnegative"),
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product",),
        CheckConstraint("quantity > 0" , name="check_cart_quantity_positive")
    )

class WishList(Base):
    __tablename__ = "wishlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product",)
    )

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String, default="COD")
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user: Mapped["User"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)    
    price: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)

    product: Mapped["Product"] = relationship()
    order: Mapped["Order"] = relationship(back_populates = "items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_item_quantity_positive",)
    )

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text,nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="reviews")
    user: Mapped["User"] = relationship()
    order: Mapped["Order"] = relationship()

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        UniqueConstraint("user_id", "product_id", "order_id", name="uq_review_user_product_order")
    )