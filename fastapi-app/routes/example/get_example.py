from fastapi import APIRouter

get_example = APIRouter()


@get_example.get("/HelloWorld", summary="this is get example")
async def hello_world():
    return {"message": "Hello World"}


@get_example.get("/data")
def get_data():
    return {"message": "Hello from FastAPI", "data": [1, 2, 3, 4, 5]}
