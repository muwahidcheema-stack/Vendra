from fastapi import FastAPI
from .api.v1.endpoints import auth,categories,products

app = FastAPI(title="Vendra API")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")

@app.get('/')
def home():
    return {"Message": "Hello World"}
