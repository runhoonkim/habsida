from fastapi import FastAPI
from enum import Enum

app = FastAPI(title="Client API", version="0.1.0")

class OrderStatus(str, Enum):
    # the order statuses from the SQL chapter's schema (orders.status)
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


@app.get("/")
def read_root():
    return {"message": "Client API is running"}


@app.get("/orders/{order_id}")
def read_order(order_id: int):
    return {"order_id": order_id, "status": "pending"}


@app.get("/orders/status/{status}")
def orders_by_status(status: OrderStatus):
    return {"filtering_by": status}


@app.get("/orders")
def list_orders(skip: int = 0, limit: int = 10):
    # GET /orders?skip=20&limit=5
    return {"skip": skip, "limit": limit}


@app.get("/products")
def list_products(category: str | None = None, max_price: float | None = None):
    filters = {}
    if category is not None:
        filters["category"] = category
    if max_price is not None:
        filters["max_price"] = max_price
    return {"filters": filters}


@app.get("/users/{user_id}/orders")
def user_orders(user_id: int, skip: int = 0, limit: int = 10):
    return {
        "user_id": user_id,
        "skip": skip,
        "limit": limit,
    }

