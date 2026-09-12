from fastapi import FastAPI

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.routes.user_routes import router as user_router
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router

app = FastAPI(
    title="device_systems",
    description="API REST para administrar usuarios con FastAPI y SQLAlchemy.",
    version="1.0.0",
)

app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)


@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    return {"message": "device_systems API activa"}