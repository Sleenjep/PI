from typing import List

import jwt
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from config import settings
from init_data import fill_test_data
from models import ProductCreate, ProductDB
from mongo_utils import get_products_collection, init_mongo


app = FastAPI(title="Product Service")

init_mongo()
fill_test_data()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.oauth2_token_url)


def decode_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    username = decode_jwt_token(token)
    return username


@app.get("/products", response_model=List[ProductDB], tags=["products"])
async def get_products():
    col = get_products_collection()
    products = []
    for doc in col.find():
        products.append(
            ProductDB(id=str(doc["_id"]), name=doc["name"], price=doc["price"])
        )
    return products


@app.get("/products/{product_id}", response_model=ProductDB, tags=["products"])
async def get_product_by_id(product_id: str):
    col = get_products_collection()
    doc = col.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")

    return ProductDB(id=str(doc["_id"]), name=doc["name"], price=doc["price"])


@app.post("/products", response_model=ProductDB, tags=["products"])
async def create_product(
    product: ProductCreate,
    current_user: str = Depends(get_current_user),
):
    col = get_products_collection()
    existing = col.find_one({"name": product.name})
    if existing:
        raise HTTPException(
            status_code=400, detail="Product with this name already exists"
        )

    result = col.insert_one({"name": product.name, "price": product.price})
    new_id = result.inserted_id
    return ProductDB(id=str(new_id), name=product.name, price=product.price)


@app.put("/products/{product_id}", response_model=ProductDB, tags=["products"])
async def update_product(
    product_id: str,
    product: ProductCreate,
    current_user: str = Depends(get_current_user),
):
    col = get_products_collection()
    updated = col.find_one_and_update(
        {"_id": ObjectId(product_id)},
        {"$set": {"name": product.name, "price": product.price}},
        return_document=True,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductDB(
        id=str(updated["_id"]), name=updated["name"], price=updated["price"]
    )


@app.delete("/products/{product_id}", tags=["products"])
async def delete_product(
    product_id: str,
    current_user: str = Depends(get_current_user),
):
    col = get_products_collection()
    result = col.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted"}
