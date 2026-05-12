import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from sqlalchemy import text
from app.routers import (
    router_generos, router_peliculas, router_salas,
    router_funciones, router_clientes, router_reservas,
)
from app.auth import router_auth
from app.boleteria import router_boleteria
from app.admin import router_admin
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
Base.metadata.create_all(bind=engine)

# Backfill: si la columna `activo` fue añadida al modelo pero no existe en la tabla
# (Base.metadata.create_all no altera columnas), intentar crearla para compatibilidad.
try:
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'boletos' AND column_name = 'activo' ")).fetchone()
        if not exists:
            conn.execute(text("ALTER TABLE boletos ADD COLUMN activo boolean DEFAULT true"))
except Exception as e:
    # No detener el arranque; mostrar advertencia para que el desarrollador la vea
    print('Warning: unable to add `activo` column to boletos:', e)
 
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
app.include_router(router_admin)
 
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
 
@app.get("/admin", tags=["Frontend"])
def frontend():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))
 
@app.get("/", tags=["Root"])
def root():
    return {"mensaje": "Bienvenido a la API del Cine 🎬", "docs": "/docs"}