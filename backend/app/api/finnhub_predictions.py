"""
Finnhub Predictions API
Real-time crypto predictions using Finnhub API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.services.finnhub_service import get_finnhub_service, COINS, TIMEFRAMES

router = APIRouter()

# Get Finnhub service instance
finnhub_service = get_finnhub_service()


@router.get("/status")
async def get_finnhub_status():
    """Get Finnhub service status"""
    return {
        "service": "Finnhub Crypto Predictions",
        "api_key_configured": bool(finnhub_service.api_key),
        "coins_tracked": len(COINS),
        "timeframes": list(TIMEFRAMES.keys()),
        "last_update": finnhub_service.last_update.isoformat() if finnhub_service.last_update else None,
        "technical_indicators": [
            "EMA 9/21/50/200",
            "RSI (14)",
            "MACD",
            "Bollinger Bands",
            "Stochastic RSI",
            "ATR (14)",
            "Volume MA"
        ]
    }


@router.get("/all")
async def get_all_finnhub_predictions():
    """Get predictions for all coins and timeframes"""
    try:
        predictions = finnhub_service.get_all_predictions()

        # Format for frontend
        result = {}
        for coin in COINS.keys():
            result[coin] = {
                "coin": coin,
                "name": COINS[coin],
                "predictions": {},
                "summary": {}
            }
            for tf in TIMEFRAMES.keys():
                if tf in predictions and coin in predictions[tf]:
                    pred = predictions[tf][coin]
                    result[coin]["predictions"][tf] = pred
                    if tf == "1h":
                        result[coin]["summary"] = pred

        return {
            "predictions": result,
            "count": len(COINS),
            "coins_tracked": list(COINS.keys()),
            "timeframes": list(TIMEFRAMES.keys()),
            "last_updated": datetime.now().isoformat(),
            "source": "Finnhub API",
            "method": "Technical Analysis (EMA, RSI, MACD, Bollinger, StochRSI)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coin/{coin}")
async def get_coin_predictions(coin: str):
    """Get predictions for a specific coin"""
    coin = coin.upper()
    if coin not in COINS:
        raise HTTPException(status_code=404, detail=f"Coin {coin} not found")

    try:
        predictions = finnhub_service.get_prediction_for_coin(coin)

        return {
            "coin": coin,
            "name": COINS[coin],
            "predictions": predictions,
            "summary": predictions.get("1h", {}),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeframe/{timeframe}")
async def get_timeframe_predictions(timeframe: str):
    """Get predictions for a specific timeframe"""
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=404, detail=f"Timeframe {timeframe} not found")

    try:
        predictions = {}
        for coin in COINS.keys():
            pred = finnhub_service.get_prediction_for_coin(coin)
            if timeframe in pred:
                predictions[coin] = pred[timeframe]

        return {
            "timeframe": timeframe,
            "label": TIMEFRAMES[timeframe]["label"],
            "predictions": predictions,
            "count": len(predictions),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-signals")
async def get_top_signals(
    min_confidence: int = Query(60, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    signal_type: Optional[str] = Query(None, regex="^(BUY|SELL|HOLD)$")
):
    """Get top trading signals by confidence"""
    try:
        all_predictions = finnhub_service.get_all_predictions()

        signals = []
        for tf, coins in all_predictions.items():
            for coin, pred in coins.items():
                if "error" in pred:
                    continue
                if pred["confidence"] >= min_confidence:
                    if signal_type is None or pred["signal"] == signal_type:
                        signals.append({
                            "coin": coin,
                            "name": COINS[coin],
                            "timeframe": tf,
                            **pred
                        })

        # Sort by confidence
        signals.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "signals": signals[:limit],
            "count": len(signals[:limit]),
            "filters": {
                "min_confidence": min_confidence,
                "signal_type": signal_type
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/{coin}")
async def get_backtest_results(
    coin: str,
    timeframe: Optional[str] = Query(None)
):
    """Get backtest results for a coin"""
    coin = coin.upper()
    if coin not in COINS:
        raise HTTPException(status_code=404, detail=f"Coin {coin} not found")

    try:
        results = []

        if timeframe:
            if timeframe not in TIMEFRAMES:
                raise HTTPException(status_code=404, detail=f"Timeframe {timeframe} not found")

            from app.services.finnhub_service import TIMEFRAMES as TF_CONFIG
            df = finnhub_service.fetch_candles(coin, TF_CONFIG[timeframe]["resolution"], TF_CONFIG[timeframe]["bars"])
            if not df.empty:
                df = finnhub_service.compute_indicators(df)
                result = finnhub_service.backtest(df, coin, TF_CONFIG[timeframe]["label"])
                if "error" not in result:
                    results.append(result)
        else:
            results = finnhub_service.get_backtest_results(coin)

        return {
            "coin": coin,
            "name": COINS[coin],
            "backtests": results,
            "count": len(results),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest-all")
async def get_all_backtest_results():
    """Get backtest results for all coins"""
    try:
        results = finnhub_service.get_backtest_results()

        return {
            "backtests": results,
            "count": len(results),
            "coins": list(COINS.keys()),
            "timeframes": list(TIMEFRAMES.keys()),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_predictions():
    """Force refresh all predictions"""
    try:
        predictions = finnhub_service.get_all_predictions()

        # Count signals
        buy_count = sum(1 for tf in predictions.values() for p in tf.values()
                        if p.get("signal") == "BUY")
        sell_count = sum(1 for tf in predictions.values() for p in tf.values()
                         if p.get("signal") == "SELL")
        hold_count = sum(1 for tf in predictions.values() for p in tf.values()
                         if p.get("signal") == "HOLD")

        return {
            "status": "success",
            "message": "Predictions refreshed from Finnhub API",
            "predictions_generated": len(COINS) * len(TIMEFRAMES),
            "signals": {
                "BUY": buy_count,
                "SELL": sell_count,
                "HOLD": hold_count
            },
            "last_updated": finnhub_service.last_update.isoformat() if finnhub_service.last_update else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
