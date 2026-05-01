from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app import models

router_boleteria = APIRouter(prefix="/boleteria", tags=["Boletería"])


class CompraSchema(BaseModel):
    funcion_id: int
    cliente_id: int
    asientos: List[str]  # ["A1", "A2", "B3"]


@router_boleteria.get("/funcion/{funcion_id}/asientos")
def asientos_por_funcion(funcion_id: int, db: Session = Depends(get_db)):
    """Devuelve todos los asientos de la sala con su estado (libre/ocupado)"""
    funcion = db.query(models.Funcion).filter(
        models.Funcion.id == funcion_id, models.Funcion.activo == True
    ).first()
    if not funcion:
        raise HTTPException(status_code=404, detail="Función no encontrada")

    sala = funcion.sala
    capacidad = sala.capacidad

    # Calcular filas y columnas según capacidad
    cols = 10
    filas_count = (capacidad + cols - 1) // cols
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Asientos ya ocupados en esta función
    reservas = db.query(models.Reserva).filter(
        models.Reserva.funcion_id == funcion_id,
        models.Reserva.activo == True,
        models.Reserva.estado == "confirmada"
    ).all()
    ocupados = {r.numero_asiento for r in reservas}

    # Generar mapa de asientos
    asientos = []
    total = 0
    for i in range(filas_count):
        fila = letras[i]
        for j in range(1, cols + 1):
            if total >= capacidad:
                break
            codigo = f"{fila}{j}"
            asientos.append({
                "codigo": codigo,
                "fila": fila,
                "numero": j,
                "ocupado": codigo in ocupados
            })
            total += 1

    return {
        "funcion_id": funcion_id,
        "pelicula": funcion.pelicula.titulo,
        "sala": sala.nombre,
        "fecha_hora": funcion.fecha_hora,
        "precio": funcion.precio,
        "capacidad": capacidad,
        "disponibles": capacidad - len(ocupados),
        "asientos": asientos
    }


@router_boleteria.post("/comprar", status_code=201)
def comprar_boletos(data: CompraSchema, db: Session = Depends(get_db)):
    """Compra uno o varios asientos para una función"""
    funcion = db.query(models.Funcion).filter(
        models.Funcion.id == data.funcion_id, models.Funcion.activo == True
    ).first()
    if not funcion:
        raise HTTPException(status_code=404, detail="Función no encontrada")

    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == data.cliente_id, models.Cliente.activo == True
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Verificar que los asientos no estén ocupados
    ocupados = db.query(models.Reserva).filter(
        models.Reserva.funcion_id == data.funcion_id,
        models.Reserva.numero_asiento.in_(data.asientos),
        models.Reserva.activo == True,
        models.Reserva.estado == "confirmada"
    ).all()

    if ocupados:
        asientos_ocupados = [r.numero_asiento for r in ocupados]
        raise HTTPException(status_code=400, detail=f"Asientos ya ocupados: {asientos_ocupados}")

    # Crear reservas
    reservas_creadas = []
    for asiento in data.asientos:
        reserva = models.Reserva(
            numero_asiento=asiento,
            cliente_id=data.cliente_id,
            funcion_id=data.funcion_id,
            estado="confirmada"
        )
        db.add(reserva)
        reservas_creadas.append(asiento)

    db.commit()

    total = funcion.precio * len(data.asientos)
    return {
        "mensaje": f"¡Compra exitosa! {len(data.asientos)} boleto(s) adquirido(s)",
        "asientos": reservas_creadas,
        "total": round(total, 2),
        "pelicula": funcion.pelicula.titulo,
        "cliente": cliente.nombre
    }