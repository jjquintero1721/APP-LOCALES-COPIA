import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.middleware.logging_middleware import LoggingMiddleware
from app.routers.auth import auth_router
from app.routers.users import users_router
from app.routers.employees import employees_router
from app.routers.attendance import attendance_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend Multi-Tenant SaaS para cafeterías, restaurantes y negocios similares",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware
app.add_middleware(LoggingMiddleware)

# Incluir routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(employees_router.router)
app.include_router(attendance_router.router)


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz.
    Verifica que la API está funcionando.
    """
    return {
        "message": "Multi-Tenant SaaS API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Usado por Docker y orquestadores para verificar salud del servicio.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
