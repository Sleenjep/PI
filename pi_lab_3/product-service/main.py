from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt

app = FastAPI(title="Product Service")

SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/login")

fake_products_db = [
    {"id": 1, "name": "Phone", "price": 1000},
    {"id": 2, "name": "Laptop", "price": 2000},
]


class Product(BaseModel):
    id: int
    name: str
    price: float


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


@app.get("/products", tags=["products"])
async def get_products():
    return fake_products_db


@app.post("/products", tags=["products"])
async def create_product(
    product: Product, current_user: str = Depends(get_current_user)
):
    for p in fake_products_db:
        if p["id"] == product.id:
            raise HTTPException(400, "Product with this ID already exists")
    fake_products_db.append(product.dict())
    return {"message": "Product created", "product": product}


@app.get("/products/{product_id}")
def get_product_by_id(product_id: int):
    for p in fake_products_db:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Not found")
