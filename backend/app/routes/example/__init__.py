from fastapi import APIRouter

from .get_example import get_example

router = APIRouter()

router.include_router(
    get_example,
    prefix="/get"
)