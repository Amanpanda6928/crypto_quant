# =========================
# api/export.py - Excel Export Endpoint
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from app.services.ai_model import ai_model
from app.services.binance_client import binance_client
import pandas as pd
import io
import time
from datetime import datetime

router = APIRouter()

# All 17 coins
COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE",
    "DOT", "LINK", "MATIC", "LTC", "BCH", "UNI", "ATOM", "XLM", "ICP"
]

TIMEFRAMES = ["30m", "1h", "4h", "1d"]

@router.get("/predictions/excel")
async def export_predictions_excel(
    coins: Optional[str] = None,
    timeframes: Optional[str] = None,
    format: str = "xlsx"
):
    """
    Export predictions to Excel/CSV
    
    Query params:
    - coins: Comma-separated list (default: all 17 coins)
    - timeframes: Comma-separated list (default: 30m,1h,4h,1d)
    - format: xlsx or csv (default: xlsx)
    
    Returns: Excel file with predictions for each coin and timeframe
    """
    try:
        # Parse parameters
        coin_list = coins.split(",") if coins else COINS
        timeframe_list = timeframes.split(",") if timeframes else TIMEFRAMES
        
        # Validate timeframes
        valid_timeframes = ["30m", "1h", "4h", "1d"]
        timeframe_list = [tf for tf in timeframe_list if tf in valid_timeframes]
        if not timeframe_list:
            timeframe_list = ["30m", "1h", "4h", "1d"]
        
        # Collect prediction data
        data_rows = []
        
        for coin in coin_list:
            symbol = coin.upper() + "USDT"
            
            # Get current price
            try:
                current_price = binance_client._mock_price(symbol)
            except:
                current_price = 0
            
            for tf in timeframe_list:
                try:
                    # Get prediction from AI model
                    prediction = ai_model.predict(symbol, [current_price] * 50)
                    
                    pred_price = prediction.get("price", current_price)
                    change_pct = ((pred_price - current_price) / current_price * 100) if current_price else 0
                    confidence = prediction.get("confidence", 60)
                    signal = prediction.get("signal", "HOLD")
                    
                    data_rows.append({
                        "Coin": coin.upper(),
                        "Timeframe": tf,
                        "Current_Price": round(current_price, 4),
                        "Predicted_Price": round(pred_price, 4),
                        "Change_Percent": round(change_pct, 2),
                        "Signal": signal,
                        "Confidence_Percent": round(confidence, 1),
                        "Direction": "UP" if change_pct > 0 else "DOWN" if change_pct < 0 else "NEUTRAL",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                except Exception as e:
                    # Add row with error info
                    data_rows.append({
                        "Coin": coin.upper(),
                        "Timeframe": tf,
                        "Current_Price": round(current_price, 4),
                        "Predicted_Price": None,
                        "Change_Percent": None,
                        "Signal": "ERROR",
                        "Confidence_Percent": 0,
                        "Direction": "ERROR",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Error": str(e)
                    })
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "csv":
            # Export to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=predictions_{timestamp}.csv"
                }
            )
        else:
            # Export to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Predictions', index=False)
                
                # Add summary sheet
                summary_data = []
                for coin in coin_list:
                    coin_data = [r for r in data_rows if r["Coin"] == coin.upper()]
                    if coin_data:
                        avg_change = sum([r["Change_Percent"] for r in coin_data if r["Change_Percent"] is not None]) / len([r for r in coin_data if r["Change_Percent"] is not None]) if any(r["Change_Percent"] is not None for r in coin_data) else 0
                        buy_count = sum([1 for r in coin_data if r["Signal"] == "BUY"])
                        sell_count = sum([1 for r in coin_data if r["Signal"] == "SELL"])
                        
                        summary_data.append({
                            "Coin": coin.upper(),
                            "Avg_Change_Percent": round(avg_change, 2),
                            "Buy_Signals": buy_count,
                            "Sell_Signals": sell_count,
                            "Overall_Signal": "BUY" if avg_change > 0.5 else "SELL" if avg_change < -0.5 else "HOLD"
                        })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=predictions_{timestamp}.xlsx"
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/predictions/json")
async def export_predictions_json(
    coins: Optional[str] = None,
    timeframes: Optional[str] = None
):
    """Export predictions as JSON"""
    try:
        coin_list = coins.split(",") if coins else COINS
        timeframe_list = timeframes.split(",") if timeframes else TIMEFRAMES
        
        results = {}
        
        for coin in coin_list:
            symbol = coin.upper() + "USDT"
            results[coin.upper()] = {}
            
            try:
                current_price = binance_client._mock_price(symbol)
            except:
                current_price = 0
            
            for tf in timeframe_list:
                try:
                    prediction = ai_model.predict(symbol, [current_price] * 50)
                    pred_price = prediction.get("price", current_price)
                    change_pct = ((pred_price - current_price) / current_price * 100) if current_price else 0
                    
                    results[coin.upper()][tf] = {
                        "current_price": round(current_price, 4),
                        "predicted_price": round(pred_price, 4),
                        "change_percent": round(change_pct, 2),
                        "signal": prediction.get("signal", "HOLD"),
                        "confidence": round(prediction.get("confidence", 60), 1),
                        "direction": "up" if change_pct > 0 else "down" if change_pct < 0 else "neutral"
                    }
                except Exception as e:
                    results[coin.upper()][tf] = {"error": str(e)}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "coins": coin_list,
            "timeframes": timeframe_list,
            "predictions": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
