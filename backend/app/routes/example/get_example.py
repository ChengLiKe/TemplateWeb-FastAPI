from fastapi import APIRouter

get_example = APIRouter()


@get_example.get("/HelloWorld", summary="this is get example")
async def hello_world():
    return {"message": "Hello World"}
