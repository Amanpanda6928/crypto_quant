from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime
import uuid


class SignalSchema(BaseModel):
    """
    Institutional-grade trading signal schema.
    """

    # 🔑 Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Signal generation timestamp (UTC)"
    )

    # 📊 Market Info
    symbol: str = Field(
        ...,
        description="Trading pair symbol (e.g., BTCUSDT)"
    )

    side: Literal["LONG", "SHORT", "NEUTRAL"] = Field(
        ...,
        description="Trade direction"
    )

    regime: Literal["trending", "mean_reverting", "volatile", "neutral"] = Field(
        ...,
        description="Market regime classification"
    )

    # 📈 Signal Strength
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0 to 1)"
    )

    alpha: float = Field(
        ...,
        description="Expected edge (alpha)"
    )

    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Position size allocation (0 to 1)"
    )

    # 💰 Price Levels
    entry_price: Optional[float] = Field(
        None,
        description="Suggested entry price"
    )

    stop_loss: Optional[float] = Field(
        None,
        description="Stop-loss level"
    )

    take_profit: Optional[float] = Field(
        None,
        description="Take-profit level"
    )

    # 📉 Performance Tracking
    pnl: float = Field(
        0.0,
        description="Realized or unrealized PnL"
    )

    # ⚠️ Risk Metrics
    risk_reward_ratio: Optional[float] = Field(
        None,
        description="Risk/Reward ratio"
    )

    max_drawdown: Optional[float] = Field(
        None,
        description="Expected or observed drawdown"
    )

    # 🧠 Explainability
    reasons: List[str] = Field(
        default_factory=list,
        description="Reasons behind signal"
    )

    # 📡 Metadata
    source: Optional[str] = Field(
        "model",
        description="Signal source (model, manual, hybrid)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "confidence": 0.82,
                "alpha": 0.015,
                "weight": 0.25,
                "entry_price": 67200,
                "stop_loss": 66000,
                "take_profit": 69500,
                "regime": "trending",
                "reasons": ["Breakout", "High volume", "Momentum strong"]
            }
        }
