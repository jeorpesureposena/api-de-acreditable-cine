from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Tabla intermedia N a N: Peliculas <-> Generos
pelicula_genero = Table(
    "pelicula_genero",
    Base.metadata,
    Column("pelicula_id", Integer, ForeignKey("peliculas.id"), primary_key=True),
    Column("genero_id", Integer, ForeignKey("generos.id"), primary_key=True),
)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), default="usuario")  # admin, usuario
    activo = Column(Boolean, default=True)


class Genero(Base):
    __tablename__ = "generos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    peliculas = relationship("Pelicula", secondary=pelicula_genero, back_populates="generos")


class Pelicula(Base):
    __tablename__ = "peliculas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    duracion_min = Column(Integer, nullable=False)
    clasificacion = Column(String(10), nullable=False)
    activo = Column(Boolean, default=True)

    generos = relationship("Genero", secondary=pelicula_genero, back_populates="peliculas")
    funciones = relationship("Funcion", back_populates="pelicula")


class Sala(Base):
    __tablename__ = "salas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    capacidad = Column(Integer, nullable=False)
    tipo = Column(String(20), nullable=False)
    activo = Column(Boolean, default=True)

    funciones = relationship("Funcion", back_populates="sala")


class Funcion(Base):
    __tablename__ = "funciones"

    id = Column(Integer, primary_key=True, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    precio = Column(Float, nullable=False)
    activo = Column(Boolean, default=True)

    pelicula_id = Column(Integer, ForeignKey("peliculas.id"), nullable=False)
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=False)

    pelicula = relationship("Pelicula", back_populates="funciones")
    sala = relationship("Sala", back_populates="funciones")
    reservas = relationship("Reserva", back_populates="funcion")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(20), nullable=True)
    activo = Column(Boolean, default=True)

    reservas = relationship("Reserva", back_populates="cliente")


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    numero_asiento = Column(String(10), nullable=False)
    estado = Column(String(20), default="confirmada")
    activo = Column(Boolean, default=True)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    funcion_id = Column(Integer, ForeignKey("funciones.id"), nullable=False)

    cliente = relationship("Cliente", back_populates="reservas")
    funcion = relationship("Funcion", back_populates="reservas")