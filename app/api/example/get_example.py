from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from app.middlewares import limiter

from app.utils import logger
from typing import List

from fastapi import Depends

from app.models.response import SuccessResponse
from app.models.pagination import PageQuery
from app.services.auth import get_current_user, User

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
    resp = SuccessResponse[dict](data={"message": "Hello World"})
    return resp.model_dump()


@get_example.get("/ErrorHelloWorld")
async def error_hello_world(request: Request):
    raise HTTPException(status_code=400, detail="Bad Request")


@get_example.get("/loggingInfo")
async def logging_info(request: Request):
    logger.debug("logging debug")
    logger.info("logging info")
    for i in range(10):
        logger.info(f"logging info {i}")
    logger.warning("logging warning")
    logger.error("logging error")
    logger.critical("logging critical")
    resp = SuccessResponse[dict](data={"message": "logging info"})
    return resp.model_dump()


@get_example.get("/data")
def get_data():
    resp = SuccessResponse[dict](data={"message": "Hello from FastAPI", "data": [1, 2, 3, 4, 5]})
    return resp.model_dump()


# GET 接口：获取所有项目
@get_example.get("/items/", response_model=List[Item])
async def read_items():
    resp = SuccessResponse[List[Item]](data=items)
    return resp.model_dump()


# GET 接口：根据 ID 获取单个项目
@get_example.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    for item in items:
        if item.id == item_id:
            resp = SuccessResponse[Item](data=item)
            return resp.model_dump()
    raise HTTPException(status_code=404, detail={"code": "E_NOT_FOUND", "message": "Item not found"})


# POST 接口：新增项目
@get_example.post("/items/", response_model=Item)
async def create_item(item: Item):
    # 检查是否已存在相同 ID 的项目
    for existing_item in items:
        if existing_item.id == item.id:
            raise HTTPException(status_code=400, detail={"code": "E_BAD_REQUEST", "message": "Item with this ID already exists"})

    items.append(item)  # 将新项目添加到列表中
    resp = SuccessResponse[Item](data=item)
    return resp.model_dump()


# PUT 接口：更新项目
@get_example.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, updated_item: Item):
    for index, item in enumerate(items):
        if item.id == item_id:
            items[index] = updated_item
            resp = SuccessResponse[Item](data=updated_item)
            return resp.model_dump()
    raise HTTPException(status_code=404, detail={"code": "E_NOT_FOUND", "message": "Item not found"})


# DELETE 接口：删除项目
@get_example.delete("/items/{item_id}", response_model=Item)
async def delete_item(item_id: int):
    for index, item in enumerate(items):
        if item.id == item_id:
            removed = items.pop(index)
            resp = SuccessResponse[Item](data=removed)
            return resp.model_dump()
    raise HTTPException(status_code=404, detail={"code": "E_NOT_FOUND", "message": "Item not found"})


@get_example.get("/secure/profile")
async def secure_profile(user: User = Depends(get_current_user)):
    resp = SuccessResponse[User](data=user)
    return resp.model_dump()


@get_example.get("/items-paged")
async def items_paged(paging: PageQuery = Depends()):
    # Demo data; replace with DB query and total count
    items = [
        {"id": i, "name": f"item-{i}"} for i in range(1, 201)
    ]
    total = len(items)
    slice_ = items[paging.offset : paging.offset + paging.limit]
    resp = SuccessResponse[List[dict]](data=slice_, meta=paging.to_meta(total))
    return resp.model_dump()
