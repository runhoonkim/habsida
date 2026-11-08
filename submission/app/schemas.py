from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from enum import Enum

# =====================================================
# Define pydantic models for token
# =====================================================
class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)

# =====================================================
# Define pydantic models for User ORM model
# =====================================================

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    # role will be added at the endpoint

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime

# =====================================================
# Define pydantic models for Product ORM model
# =====================================================
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    description: str | None
    price: float
    stock: int
    created_at: datetime

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