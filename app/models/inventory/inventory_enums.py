"""
Enums para el módulo de inventario.
Define los tipos de movimiento, estados de traslado y estados de relación entre negocios.
"""
from enum import Enum


class MovementType(str, Enum):
    """Tipos de movimiento de inventario"""
    MANUAL_IN = "manual_in"  # Entrada manual (compra, ajuste positivo)
    MANUAL_OUT = "manual_out"  # Salida manual (merma, ajuste negativo)
    SALE = "sale"  # Venta de producto
    TRANSFER_IN = "transfer_in"  # Entrada por traslado desde otro negocio
    TRANSFER_OUT = "transfer_out"  # Salida por traslado a otro negocio
    RECIPE_CONSUMPTION = "recipe_consumption"  # Consumo por receta/producto
    REVERT = "revert"  # Reversión de un movimiento


class TransferStatus(str, Enum):
    """Estados de traslado entre negocios"""
    PENDING = "pending"  # Traslado creado, esperando aceptación
    COMPLETED = "completed"  # Traslado aceptado y completado
    CANCELLED = "cancelled"  # Traslado cancelado por el creador
    REJECTED = "rejected"  # Traslado rechazado por el destinatario


class RelationshipStatus(str, Enum):
    """Estados de relación entre negocios"""
    PENDING = "pending"  # Solicitud de relación enviada, esperando aceptación
    ACTIVE = "active"  # Relación aceptada y activa (permite traslados)
    REJECTED = "rejected"  # Solicitud de relación rechazada
