import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import (
    router_generos, router_peliculas, router_salas,
    router_funciones, router_clientes, router_reservas,
)
from app.auth import router_auth
from app.boleteria import router_boleteria
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
Base.metadata.create_all(bind=engine)
 
app = FastAPI(title="API Cine 🎬")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Routers existentes
app.include_router(router_generos)
app.include_router(router_peliculas)
app.include_router(router_salas)
app.include_router(router_funciones)
app.include_router(router_clientes)
app.include_router(router_reservas)
 
# Nuevos routers
app.include_router(router_auth)
app.include_router(router_boleteria)
 
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
 
@app.get("/admin", tags=["Frontend"])
def frontend():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))
 
@app.get("/", tags=["Root"])
def root():
    return {"mensaje": "Bienvenido a la API del Cine 🎬", "docs": "/docs"}