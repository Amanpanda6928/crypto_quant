# =========================
# api/import_data.py - Excel Import Endpoint
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
from typing import Dict, List, Optional
from datetime import datetime

router = APIRouter()

# Global storage for Excel data (replaces SQL database)
_excel_data_store = {
    "predictions": {},  # {coin: {timeframe: [predictions]}}
    "last_upload": None,
    "filename": None
}

# Valid timeframes
TIMEFRAMES = ["30m", "1h", "4h", "1d"]

def get_excel_data():
    """Get the current Excel data store"""
    return _excel_data_store

def clear_excel_data():
    """Clear all Excel data"""
    global _excel_data_store
    _excel_data_store = {
        "predictions": {},
        "last_upload": None,
        "filename": None
    }

def parse_excel_file(file_content: bytes) -> Dict:
    """Parse uploaded Excel file and store data"""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        
        # Validate required columns
        required_cols = ["Coin", "Timeframe", "Current_Price", "Predicted_Price", 
                        "Change_Percent", "Signal", "Confidence_Percent"]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {', '.join(missing_cols)}")
        
        # Clear existing data
        clear_excel_data()
        
        # Process and store data
        for _, row in df.iterrows():
            coin = str(row["Coin"]).upper()
            timeframe = str(row["Timeframe"]).lower()
            
            # Skip invalid timeframes
            if timeframe not in TIMEFRAMES:
                continue
            
            # Filter confidence >= 60%
            confidence = float(row.get("Confidence_Percent", 0))
            if confidence < 60:
                continue
            
            prediction = {
                "coin": coin,
                "timeframe": timeframe,
                "current_price": float(row.get("Current_Price", 0)),
                "predicted_price": float(row.get("Predicted_Price", 0)),
                "change_percent": float(row.get("Change_Percent", 0)),
                "signal": str(row.get("Signal", "HOLD")).upper(),
                "confidence": confidence,
                "direction": "up" if float(row.get("Change_Percent", 0)) > 0 else "down" if float(row.get("Change_Percent", 0)) < 0 else "neutral",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store by coin and timeframe
            if coin not in _excel_data_store["predictions"]:
                _excel_data_store["predictions"][coin] = {}
            
            if timeframe not in _excel_data_store["predictions"][coin]:
                _excel_data_store["predictions"][coin][timeframe] = []
            
            _excel_data_store["predictions"][coin][timeframe].append(prediction)
        
        _excel_data_store["last_upload"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "coins_imported": len(_excel_data_store["predictions"]),
            "total_predictions": sum(
                len(tf_data) 
                for coin_data in _excel_data_store["predictions"].values() 
                for tf_data in coin_data.values()
            ),
            "timeframes": TIMEFRAMES
        }
        
    except Exception as e:
        raise ValueError(f"Failed to parse Excel: {str(e)}")

@router.post("/upload")
async def upload_excel_file(file: UploadFile = File(...)):
    """
    Upload Excel file with prediction data
    
    Required columns:
    - Coin (e.g., BTC, ETH)
    - Timeframe (30m, 1h, 4h, 1d)
    - Current_Price
    - Predicted_Price
    - Change_Percent
    - Signal (BUY, SELL, HOLD)
    - Confidence_Percent (>= 60 will be stored)
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="File must be Excel (.xlsx, .xls) or CSV")
        
        content = await file.read()
        
        # Handle CSV
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode()))
            # Convert to Excel format in memory
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            content = excel_buffer.getvalue()
        
        result = parse_excel_file(content)
        _excel_data_store["filename"] = file.filename
        
        return JSONResponse(content={
            "success": True,
            "message": f"Successfully imported {file.filename}",
            "data": result
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data")
async def get_imported_data(coin: Optional[str] = None, timeframe: Optional[str] = None):
    """Get imported Excel data (filtered by coin and/or timeframe)"""
    try:
        data = _excel_data_store["predictions"]
        
        if coin:
            coin = coin.upper()
            data = {k: v for k, v in data.items() if k == coin}
        
        if timeframe:
            timeframe = timeframe.lower()
            data = {
                k: {tf: preds for tf, preds in v.items() if tf == timeframe}
                for k, v in data.items()
            }
        
        # Flatten for response
        flattened = []
        for coin_data in data.values():
            for tf_data in coin_data.values():
                flattened.extend(tf_data)
        
        return {
            "success": True,
            "count": len(flattened),
            "filename": _excel_data_store["filename"],
            "last_upload": _excel_data_store["last_upload"],
            "predictions": flattened
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_import_status():
    """Get status of Excel import"""
    total_predictions = sum(
        len(tf_data) 
        for coin_data in _excel_data_store["predictions"].values() 
        for tf_data in coin_data.values()
    )
    
    return {
        "has_data": total_predictions > 0,
        "filename": _excel_data_store["filename"],
        "last_upload": _excel_data_store["last_upload"],
        "coins_count": len(_excel_data_store["predictions"]),
        "predictions_count": total_predictions,
        "timeframes": TIMEFRAMES
    }

@router.delete("/clear")
async def clear_imported_data():
    """Clear all imported Excel data"""
    clear_excel_data()
    return {"success": True, "message": "All imported data cleared"}

@router.get("/template")
async def download_template():
    """Download sample Excel template"""
    try:
        # Create sample data
        sample_data = []
        coins = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE", 
                "DOT", "LINK", "MATIC", "LTC", "BCH", "UNI", "ATOM", "XLM", "ICP"]
        
        for coin in coins:
            base_price = 50000 if coin == "BTC" else 3000 if coin == "ETH" else 100
            for tf in TIMEFRAMES:
                # Generate sample predictions >= 60% confidence
                change = 2.5  # 2.5% up
                pred_price = base_price * (1 + change/100)
                
                sample_data.append({
                    "Coin": coin,
                    "Timeframe": tf,
                    "Current_Price": round(base_price, 2),
                    "Predicted_Price": round(pred_price, 2),
                    "Change_Percent": round(change, 2),
                    "Signal": "BUY",
                    "Confidence_Percent": 75.0,
                    "Direction": "up"
                })
                
                # Add some SELL signals
                change = -1.8
                pred_price = base_price * (1 + change/100)
                sample_data.append({
                    "Coin": coin,
                    "Timeframe": tf,
                    "Current_Price": round(base_price, 2),
                    "Predicted_Price": round(pred_price, 2),
                    "Change_Percent": round(change, 2),
                    "Signal": "SELL",
                    "Confidence_Percent": 65.0,
                    "Direction": "down"
                })
        
        df = pd.DataFrame(sample_data)
        
        # Create Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Predictions', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                "Field": ["Coin", "Timeframe", "Current_Price", "Predicted_Price", 
                         "Change_Percent", "Signal", "Confidence_Percent", "Direction"],
                "Description": [
                    "Cryptocurrency symbol (BTC, ETH, etc.)",
                    "Time period (30m, 1h, 4h, 1d)",
                    "Current market price",
                    "AI predicted future price",
                    "Percentage change predicted",
                    "Trading signal (BUY, SELL, HOLD)",
                    "Confidence level (only >= 60% shown)",
                    "Price direction (up, down, neutral)"
                ],
                "Required": ["Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "No"]
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=prediction_template.xlsx"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
