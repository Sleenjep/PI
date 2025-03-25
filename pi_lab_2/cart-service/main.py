from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
import jwt
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHM = "HS256"

app = FastAPI(title="Cart Service", version="1.0.0")

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


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    return decode_jwt_token(token)


@app.get("/cart", response_model=List[CartItem], tags=["cart"])
async def get_cart_items(current_user: str = Depends(get_current_user)):
    return fake_cart_db.get(current_user, [])


@app.post("/cart", tags=["cart"])
async def add_item_to_cart(
    item: CartItem, current_user: str = Depends(get_current_user)
):
    user_cart = fake_cart_db.get(current_user, [])
    for cart_item in user_cart:
        if cart_item["product_id"] == item.product_id:
            cart_item["quantity"] += item.quantity
            break
    else:
        user_cart.append(item.dict())
    fake_cart_db[current_user] = user_cart
    return {"message": "Item added to cart", "cart": user_cart}
