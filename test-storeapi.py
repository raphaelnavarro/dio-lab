from fastapi import FastAPI, HTTPException, APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional, List

app = FastAPI()
router = APIRouter()

# --- Configuração do MongoDB ---
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.storeapi

# --- Schemas ---
class ProductCreate(BaseModel):
    name: str
    price: float

class ProductUpdate(BaseModel):
    name: Optional[str]
    price: Optional[float]
    updated_at: Optional[datetime]

class ProductOut(ProductCreate):
    id: str = Field(alias="_id")
    updated_at: Optional[datetime]

# --- Services ---
async def create_product(data: ProductCreate):
    try:
        product = data.dict()
        product["updated_at"] = datetime.utcnow()
        result = await db.products.insert_one(product)
        product["_id"] = str(result.inserted_id)
        return product
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao inserir produto.")

async def patch_product(id: str, data: ProductUpdate):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if "updated_at" not in update_data:
        update_data["updated_at"] = datetime.utcnow()

    result = await db.products.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    product = await db.products.find_one({"_id": ObjectId(id)})
    product["_id"] = str(product["_id"])
    return product

async def filter_products_by_price(min_price: float, max_price: float):
    cursor = db.products.find({"price": {"$gt": min_price, "$lt": max_price}})
    results = []
    async for product in cursor:
        product["_id"] = str(product["_id"])
        results.append(product)
    return results

# --- Controllers ---
@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product_controller(product: ProductCreate):
    return await create_product(product)

@router.patch("/products/{id}", response_model=ProductOut)
async def patch_product_controller(id: str, product: ProductUpdate):
    return await patch_product(id, product)

@router.get("/products/filter/price", response_model=List[ProductOut])
async def get_by_price(min_price: float, max_price: float):
    return await filter_products_by_price(min_price, max_price)

# --- Registro das rotas ---
app.include_router(router)
