from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
import re
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import math
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

    # Asientos ya ocupados en esta función (reservas activas y confirmadas)
    reservas = db.query(models.Reserva).filter(
        models.Reserva.funcion_id == funcion_id,
        models.Reserva.activo == True,
        models.Reserva.estado == "confirmada"
    ).all()

    # Conteo de asientos por cliente en esta función
    client_counts = {}
    for r in reservas:
        client_counts[r.cliente_id] = client_counts.get(r.cliente_id, 0) + 1

    # Mapear asiento -> info de reserva
    reserva_por_asiento = {}
    for r in reservas:
        boleto = None
        try:
            boleto = r.boletos[0] if getattr(r, 'boletos', None) and len(r.boletos) > 0 else None
        except Exception:
            boleto = db.query(models.Boleto).filter(models.Boleto.reserva_id == r.id).first()
        reserva_por_asiento[r.numero_asiento] = {
            'reserva_id': r.id,
            'cliente_id': r.cliente_id,
            'cliente_nombre': getattr(r.cliente, 'nombre', None),
            'cliente_email': getattr(r.cliente, 'email', None),
            'cliente_telefono': getattr(r.cliente, 'telefono', None),
            'cliente_reservas_count': client_counts.get(r.cliente_id, 1),
            'boleto_id': boleto.id if boleto else None,
        }

    ocupados = set(reserva_por_asiento.keys())

    # Generar mapa de asientos
    asientos = []
    total = 0
    for i in range(filas_count):
        fila = letras[i]
        for j in range(1, cols + 1):
            if total >= capacidad:
                break
            codigo = f"{fila}{j}"
            seat_obj = {
                "codigo": codigo,
                "fila": fila,
                "columna": j,
                "numero": j,
                "asiento": total + 1,
                "ocupado": codigo in ocupados
            }
            if codigo in reserva_por_asiento:
                seat_obj.update(reserva_por_asiento[codigo])
            asientos.append(seat_obj)
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


@router_boleteria.get("/boleto/{boleto_id}/pdf")
def descargar_boleto_pdf(boleto_id: int, db: Session = Depends(get_db)):
    boleto = db.query(models.Boleto).filter(models.Boleto.id == boleto_id).first()
    if not boleto:
        raise HTTPException(status_code=404, detail="Boleto no encontrado")

    funcion = db.query(models.Funcion).filter(models.Funcion.id == boleto.funcion_id).first()
    pelicula = funcion.pelicula if funcion else None
    sala = funcion.sala if funcion else None
    cliente = db.query(models.Cliente).filter(models.Cliente.id == boleto.cliente_id).first()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 50, "Boleto — Cine")
    c.setFont("Helvetica", 12)
    y = height - 90
    c.drawString(40, y, f"Boleto ID: {boleto.id}")
    y -= 18
    if cliente:
        c.drawString(40, y, f"Cliente: {cliente.nombre} — {cliente.email}")
        y -= 18
    if pelicula:
        c.drawString(40, y, f"Película: {pelicula.titulo}")
        y -= 18
    if funcion and funcion.fecha_hora:
        c.drawString(40, y, f"Función: {funcion.fecha_hora.strftime('%Y-%m-%d %H:%M')}")
        y -= 18
    if sala:
        c.drawString(40, y, f"Sala: {sala.nombre}")
        y -= 18
    c.drawString(40, y, f"Asiento: {boleto.numero_asiento} (Fila {boleto.fila or '-'} — Col {boleto.columna or '-'})")
    y -= 18
    c.drawString(40, y, f"Precio: ${boleto.precio:.2f}")
    y -= 28
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(40, y, f"Emitido: {boleto.fecha_emision.strftime('%Y-%m-%d %H:%M:%S')}")

    c.showPage()
    c.save()
    buffer.seek(0)

    headers = {"Content-Disposition": f"attachment; filename=boleto_{boleto.id}.pdf"}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)


@router_boleteria.get("/factura")
def generar_factura(
    boletos: str = Query(..., description="IDs de boletos separados por coma"),
    empresa_nombre: str = Query("CINE LOCAL, C.A."),
    rif: str = Query(None, description="RIF de la empresa (ej: J-12345678-9)"),
    direccion: str = Query("Av. Principal, Ciudad, Venezuela"),
    iva_rate: float = Query(0.16, description="Tasa de IVA (por ejemplo 0.16 para 16%)"),
    moneda_label: str = Query("Bs.", description="Etiqueta de moneda"),
    db: Session = Depends(get_db),
):
    """Genera una factura PDF con formato venezolano y 'importe en letra'. Acepta parámetros opcionales de empresa y tasa de IVA."""
    ids = [int(x) for x in boletos.split(',') if x.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="Parámetro 'boletos' inválido")
    registros = db.query(models.Boleto).filter(models.Boleto.id.in_(ids)).all()
    if not registros:
        raise HTTPException(status_code=404, detail="No se encontraron boletos")

    cliente = registros[0].cliente if registros[0].cliente else None

    subtotal = sum((r.precio or 0.0) for r in registros)
    iva = round(subtotal * float(iva_rate), 2)
    total = round(subtotal + iva, 2)

    def _convert_hundreds(n: int) -> str:
        unidades = ("", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieciseis", "diecisiete", "dieciocho", "diecinueve")
        decenas = ("", "", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa")
        centenas = ("", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos")
        if n == 0:
            return ""
        if n == 100:
            return "cien"
        words = ""
        c = n // 100
        r = n % 100
        if c:
            words += centenas[c]
            if r:
                words += " "
        if r:
            if r < 20:
                words += unidades[r]
            elif r < 30:
                if r == 20:
                    words += "veinte"
                else:
                    words += "veinti" + unidades[r - 20]
            else:
                d = r // 10
                u = r % 10
                words += decenas[d]
                if u:
                    words += " y " + unidades[u]
        return words

    def number_to_words_es(n: int) -> str:
        if n == 0:
            return "cero"
        parts = []
        millones = n // 1000000
        miles = (n % 1000000) // 1000
        resto = n % 1000
        if millones:
            if millones == 1:
                parts.append("un millón")
            else:
                parts.append(number_to_words_es(millones) + " millones")
        if miles:
            if miles == 1:
                parts.append("mil")
            else:
                parts.append(_convert_hundreds(miles) + " mil")
        if resto:
            parts.append(_convert_hundreds(resto))
        return ' '.join([p for p in parts if p]).strip()

    def numero_a_letras(amount: float, currency_word: str = "BOLÍVARES") -> str:
        entero = int(math.floor(abs(amount)))
        centavos = int(round((abs(amount) - entero) * 100))
        texto_entero = number_to_words_es(entero).upper()
        moneda = currency_word if entero != 1 else currency_word.rstrip('S')
        return f"{texto_entero} {moneda} {centavos:02d}/100"

    # PDF generation
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Try to draw logo if exists in static/logo.png
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, '..', 'static', 'logo.png')
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, height - 90, width=140, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, empresa_nombre)
    c.setFont("Helvetica", 9)
    if rif:
        c.drawString(200, height - 66, f"RIF: {rif}")
    c.drawString(200, height - 80, direccion)
    c.drawRightString(width - 40, height - 50, f"FACTURA: {int(datetime.utcnow().timestamp())}")
    c.drawRightString(width - 40, height - 66, f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

    y = height - 110
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Cliente:")
    c.setFont("Helvetica", 10)
    c.drawString(120, y, cliente.nombre if cliente else "—")
    y -= 14
    if cliente and getattr(cliente, 'email', None):
        c.drawString(120, y, cliente.email)
        y -= 14
    if cliente and getattr(cliente, 'telefono', None):
        c.drawString(120, y, cliente.telefono)
        y -= 14

    # Table header
    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Cant")
    c.drawString(80, y, "Descripción")
    c.drawRightString(430, y, "Precio Unitario")
    c.drawRightString(520, y, "Importe")
    y -= 12
    c.setFont("Helvetica", 10)

    for r in registros:
        c.drawString(40, y, "1")
        desc = f"Boleto {r.numero_asiento} — Función #{r.funcion_id}"
        c.drawString(80, y, desc)
        c.drawRightString(430, y, f"{moneda_label}{(r.precio or 0.0):.2f}")
        c.drawRightString(520, y, f"{moneda_label}{(r.precio or 0.0):.2f}")
        y -= 14
        if y < 140:
            c.showPage()
            y = height - 40

    # Totals and amount in words
    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(470, y, "Subtotal:")
    c.drawRightString(520, y, f"{moneda_label}{subtotal:.2f}")
    y -= 14
    c.drawRightString(470, y, f"IVA {int(float(iva_rate)*100)}%:")
    c.drawRightString(520, y, f"{moneda_label}{iva:.2f}")
    y -= 14
    c.drawRightString(470, y, "TOTAL:")
    c.drawRightString(520, y, f"{moneda_label}{total:.2f}")

    # Importe con letra (mayúsculas)
    y -= 26
    c.setFont("Helvetica-Bold", 9)
    importe_letras = numero_a_letras(total, currency_word="BOLÍVARES")
    c.drawString(40, y, "Importe con letra:")
    c.setFont("Helvetica", 9)
    c.drawString(160, y, importe_letras)

    # Moneda
    y -= 14
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Moneda: Bolívares (VES) — Etiqueta: {moneda_label}")

    c.showPage()
    c.save()
    buffer.seek(0)
    headers = {"Content-Disposition": f"attachment; filename=factura_{int(datetime.utcnow().timestamp())}.pdf"}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)


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
    boletos_creados = []
    for asiento in data.asientos:
        reserva = models.Reserva(
            numero_asiento=asiento,
            cliente_id=data.cliente_id,
            funcion_id=data.funcion_id,
            estado="confirmada"
        )
        db.add(reserva)
        # flush to get reserva.id
        db.flush()

        # parse seat code to fila/columna
        m = re.match(r"^([A-Za-z]+)(\d+)$", asiento)
        fila = None
        columna = None
        asiento_idx = None
        if m:
            fila = m.group(1).upper()
            try:
                columna = int(m.group(2))
            except ValueError:
                columna = None

        # calcular asiento index secuencial (igual que en asientos_por_funcion)
        cols = 10
        capacidad = funcion.sala.capacidad
        filas_count = (capacidad + cols - 1) // cols
        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if fila and columna:
            try:
                row_index = letras.index(fila)
                asiento_idx = row_index * cols + (columna)
                if asiento_idx > capacidad:
                    asiento_idx = None
            except ValueError:
                asiento_idx = None

        # crear boleto asociado
        boleto = models.Boleto(
            reserva_id=reserva.id,
            funcion_id=data.funcion_id,
            cliente_id=data.cliente_id,
            numero_asiento=asiento,
            fila=fila,
            columna=columna,
            asiento=asiento_idx,
            precio=funcion.precio,
            fecha_emision=datetime.utcnow()
        )
        db.add(boleto)
        reservas_creadas.append(asiento)
        boletos_creados.append(boleto)

    db.commit()

    total = funcion.precio * len(data.asientos)
    return {
        "mensaje": f"¡Compra exitosa! {len(data.asientos)} boleto(s) adquirido(s)",
        "asientos": reservas_creadas,
        "boletos": [b.id for b in boletos_creados],
        "total": round(total, 2),
        "pelicula": funcion.pelicula.titulo,
        "cliente": cliente.nombre
    }