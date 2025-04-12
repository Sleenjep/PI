from pydantic import BaseModel
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    price: float


class ProductDB(ProductCreate):
    id: str
