from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
import jwt
from fastapi.security import OAuth2PasswordBearer
import requests

app = FastAPI(title="Cart service")

SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHM = "HS256"

PRODUCT_SERVICE_URL = "http://product-service:8002"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/login")

fake_cart_db = {}


class CartItem(BaseModel):
    product_id: int
    quantity: int


def decode_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
    return decode_jwt_token(token)


def fetch_product_info(product_id: int):
    url = f"{PRODUCT_SERVICE_URL}/products/{product_id}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        return None


@app.post("/cart", tags=["cart"])
async def add_item_to_cart(
    item: CartItem, current_user: str = Depends(get_current_user)
):
    product_data = fetch_product_info(item.product_id)
    if not product_data:
        raise HTTPException(
            status_code=400,
            detail=f"Product with ID={item.product_id} does not exist in Product Service",
        )

    user_cart = fake_cart_db.get(current_user, [])

    for cart_item in user_cart:
        if cart_item["product_id"] == item.product_id:
            cart_item["quantity"] += item.quantity
            break
    else:
        user_cart.append(item.dict())

    fake_cart_db[current_user] = user_cart
    return {"message": "Item added to cart", "cart": user_cart}


@app.get("/cart", tags=["cart"])
async def get_cart_items(current_user: str = Depends(get_current_user)):
    user_cart = fake_cart_db.get(current_user, [])

    detailed_items = []
    for cart_item in user_cart:
        pid = cart_item["product_id"]
        product_data = fetch_product_info(pid)
        if product_data:
            item_info = {
                "product_id": pid,
                "quantity": cart_item["quantity"],
                "name": product_data["name"],
                "price": product_data["price"],
            }
            detailed_items.append(item_info)
        else:
            item_info = {
                "product_id": pid,
                "quantity": cart_item["quantity"],
                "name": "Unknown product",
                "price": None,
            }
            detailed_items.append(item_info)

    return detailed_items
