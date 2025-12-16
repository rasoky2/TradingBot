"""
Modelos de base de datos para el Trading Bot
Migrado y simplificado desde Freqtrade
"""
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base para todos los modelos"""
    pass


class Order(Base):
    """
    Modelo de órdenes
    Mantiene registro de todas las órdenes colocadas en el exchange
    """
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("ft_pair", "order_id", name="_order_pair_order_id"),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ft_trade_id: Mapped[int] = mapped_column(Integer, ForeignKey("trades.id"), index=True)
    
    # Relación con Trade
    trade: Mapped["Trade"] = relationship("Trade", back_populates="orders")
    
    # Campos principales
    ft_order_side: Mapped[str] = mapped_column(String(25), nullable=False)  # buy, sell, stoploss
    ft_pair: Mapped[str] = mapped_column(String(25), nullable=False)
    ft_is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    ft_amount: Mapped[float] = mapped_column(Float(), nullable=False)
    ft_price: Mapped[float] = mapped_column(Float(), nullable=False)
    
    # Datos del exchange (CCXT)
    order_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(25), nullable=True)
    order_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # market, limit
    side: Mapped[str] = mapped_column(String(25), nullable=True)
    price: Mapped[float | None] = mapped_column(Float(), nullable=True)
    average: Mapped[float | None] = mapped_column(Float(), nullable=True)
    amount: Mapped[float | None] = mapped_column(Float(), nullable=True)
    filled: Mapped[float | None] = mapped_column(Float(), nullable=True)
    remaining: Mapped[float | None] = mapped_column(Float(), nullable=True)
    cost: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Fechas
    order_date: Mapped[datetime] = mapped_column(nullable=True, default=datetime.now)
    order_filled_date: Mapped[datetime | None] = mapped_column(nullable=True)
    order_update_date: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Fees
    ft_fee_base: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    @property
    def safe_price(self) -> float:
        """Precio seguro de la orden"""
        return self.average or self.price or self.ft_price
    
    @property
    def safe_filled(self) -> float:
        """Cantidad llenada segura"""
        return self.filled if self.filled is not None else 0.0
    
    @property
    def safe_cost(self) -> float:
        """Costo seguro"""
        return self.cost or 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convierte la orden a diccionario"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "pair": self.ft_pair,
            "side": self.ft_order_side,
            "type": self.order_type,
            "price": self.safe_price,
            "amount": self.ft_amount,
            "filled": self.safe_filled,
            "remaining": self.remaining,
            "cost": self.safe_cost,
            "status": self.status,
            "is_open": self.ft_is_open,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "filled_date": self.order_filled_date.isoformat() if self.order_filled_date else None,
        }
    
    def __repr__(self):
        return (
            f"Order(id={self.id}, order_id={self.order_id}, "
            f"pair={self.ft_pair}, side={self.ft_order_side}, "
            f"filled={self.safe_filled}, price={self.safe_price})"
        )


class Trade(Base):
    """
    Modelo de trades
    Representa una operación de trading completa
    """
    __tablename__ = "trades"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relación con órdenes
    orders: Mapped[list[Order]] = relationship("Order", back_populates="trade", cascade="all, delete-orphan")
    
    # Información básica
    exchange: Mapped[str] = mapped_column(String(25), nullable=False, default="binance")
    pair: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    base_currency: Mapped[str | None] = mapped_column(String(25), nullable=True)
    stake_currency: Mapped[str | None] = mapped_column(String(25), nullable=True)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    
    # Fees
    fee_open: Mapped[float] = mapped_column(Float(), nullable=False, default=0.0)
    fee_open_cost: Mapped[float | None] = mapped_column(Float(), nullable=True)
    fee_close: Mapped[float | None] = mapped_column(Float(), nullable=True, default=0.0)
    fee_close_cost: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Precios
    open_rate: Mapped[float] = mapped_column(Float(), nullable=False)
    open_rate_requested: Mapped[float | None] = mapped_column(Float(), nullable=True)
    close_rate: Mapped[float | None] = mapped_column(Float(), nullable=True)
    close_rate_requested: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Cantidades
    stake_amount: Mapped[float] = mapped_column(Float(), nullable=False)
    amount: Mapped[float] = mapped_column(Float(), nullable=False)
    amount_requested: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Fechas
    open_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    close_date: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Stop Loss
    stop_loss: Mapped[float] = mapped_column(Float(), nullable=False, default=0.0)
    stop_loss_pct: Mapped[float | None] = mapped_column(Float(), nullable=True)
    initial_stop_loss: Mapped[float | None] = mapped_column(Float(), nullable=True)
    initial_stop_loss_pct: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Profit
    close_profit: Mapped[float | None] = mapped_column(Float(), nullable=True)
    close_profit_abs: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Precios máximos/mínimos
    max_rate: Mapped[float | None] = mapped_column(Float(), nullable=True)
    min_rate: Mapped[float | None] = mapped_column(Float(), nullable=True)
    
    # Metadata
    exit_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timeframe: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    # Leverage (para futuros)
    is_short: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    leverage: Mapped[float] = mapped_column(Float(), nullable=False, default=1.0)
    
    @property
    def open_date_utc(self) -> datetime:
        """Fecha de apertura con UTC"""
        return self.open_date.replace(tzinfo=UTC)
    
    @property
    def close_date_utc(self) -> datetime | None:
        """Fecha de cierre con UTC"""
        return self.close_date.replace(tzinfo=UTC) if self.close_date else None
    
    @property
    def profit_pct(self) -> float | None:
        """Profit en porcentaje"""
        if self.close_profit:
            return round(self.close_profit * 100, 2)
        return None
    
    @property
    def duration(self) -> int | None:
        """Duración del trade en minutos"""
        if self.close_date:
            return int((self.close_date_utc - self.open_date_utc).total_seconds() // 60)
        return None
    
    @property
    def is_profitable(self) -> bool:
        """Retorna True si el trade es rentable"""
        return self.close_profit_abs > 0 if self.close_profit_abs else False
    
    def to_dict(self, include_orders: bool = True) -> dict[str, Any]:
        """Convierte el trade a diccionario"""
        data = {
            "id": self.id,
            "pair": self.pair,
            "exchange": self.exchange,
            "is_open": self.is_open,
            "stake_amount": round(self.stake_amount, 8),
            "amount": round(self.amount, 8),
            "open_rate": self.open_rate,
            "close_rate": self.close_rate,
            "open_date": self.open_date.isoformat(),
            "close_date": self.close_date.isoformat() if self.close_date else None,
            "stop_loss": self.stop_loss,
            "stop_loss_pct": self.stop_loss_pct,
            "profit_pct": self.profit_pct,
            "profit_abs": self.close_profit_abs,
            "duration": self.duration,
            "exit_reason": self.exit_reason,
            "strategy": self.strategy,
            "is_short": self.is_short,
            "leverage": self.leverage,
        }
        
        if include_orders:
            data["orders"] = [order.to_dict() for order in self.orders]
        
        return data
    
    @staticmethod
    def get_open_trades():
        """Obtiene todos los trades abiertos"""
        from app import db
        from sqlalchemy import select
        return db.session.execute(select(Trade).where(Trade.is_open == True)).scalars().all()
    
    @staticmethod
    def get_closed_trades(limit: int = 100):
        """Obtiene los trades cerrados"""
        from app import db
        from sqlalchemy import select
        return db.session.execute(
            select(Trade)
            .where(Trade.is_open == False)
            .order_by(Trade.close_date.desc())
            .limit(limit)
        ).scalars().all()
    
    @staticmethod
    def get_trade_by_id(trade_id: int):
        """Obtiene un trade por ID"""
        from app import db
        return db.session.get(Trade, trade_id)
    
    def __repr__(self):
        status = "OPEN" if self.is_open else "CLOSED"
        return (
            f"Trade(id={self.id}, pair={self.pair}, "
            f"amount={round(self.amount, 8)}, "
            f"open_rate={self.open_rate}, status={status})"
        )

