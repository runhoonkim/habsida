from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int = Field(gt=0)


class OrderUpdate(BaseModel):
    quantity: int | None = Field(default=None, gt=0)
    status: str | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    quantity: int
    status: str
    created_at: datetime

