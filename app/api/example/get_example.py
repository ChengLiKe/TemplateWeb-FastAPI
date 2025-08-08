from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from app.middlewares import limiter

get_example = APIRouter()


# 数据模型
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


# 存储数据的简单列表
items = []


@get_example.get("/HelloWorld", summary="this is get example")
@limiter.limit("5/minute")
async def hello_world(request: Request):   # ← 加上 request
    return {"message": "Hello World"}


@get_example.get("/data")
def get_data():
    return {"message": "Hello from FastAPI", "data": [1, 2, 3, 4, 5]}


# GET 接口：获取所有项目
@get_example.get("/items/", response_model=List[Item])
async def read_items():
    return items


# GET 接口：根据 ID 获取单个项目
@get_example.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


# POST 接口：新增项目
@get_example.post("/items/", response_model=Item)
async def create_item(item: Item):
    # 检查是否已存在相同 ID 的项目
    for existing_item in items:
        if existing_item.id == item.id:
            raise HTTPException(status_code=400, detail="Item with this ID already exists")

    items.append(item)  # 将新项目添加到列表中
    return item  # 返回新增的项目


# PUT 接口：更新项目
@get_example.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, updated_item: Item):
    for index, item in enumerate(items):
        if item.id == item_id:
            items[index] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")


# DELETE 接口：删除项目
@get_example.delete("/items/{item_id}", response_model=Item)
async def delete_item(item_id: int):
    for index, item in enumerate(items):
        if item.id == item_id:
            return items.pop(index)
    raise HTTPException(status_code=404, detail="Item not found")
