from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from enum import Enum

# =====================================================
# Define pydantic models for User ORM model
# =====================================================

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    # role will be added at the endpoint

# =====================================================
# Define pydantic models for Order ORM model
# =====================================================

class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid" 
    shipped = "shipped" 
    delivered = "delivered" 
    cancelled = "cancelled"

class OrderCreate(BaseModel):
    # user_id will be added at the endpoint
    product_id: int
    quantity: int = Field(default=1, gt=0)
    # status will be added at the endpoint

class OrderUpdate(BaseModel):
    quantity: int | None = Field(default=None, gt=0)
    status: OrderStatus | None = None

class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    quantity: int
    status: OrderStatus
    created_at: datetime