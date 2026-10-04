from fastapi import FastAPI
from .api.v1.endpoints import auth,categories,products, cart, wishlist

app = FastAPI(title="Vendra API", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(cart.router, prefix="/api/v1")
app.include_router(wishlist.router, prefix="/api/v1")

@app.get('/')
def home():
    return {"Message": "Hello World"}