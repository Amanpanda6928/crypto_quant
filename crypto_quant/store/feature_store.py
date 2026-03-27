"""
Production Feature Store (Quant-Grade)

Replaces pickle caching with:
- Parquet storage
- Atomic writes
- Metadata tracking
- Schema validation
- TTL-based cache control
"""

import pandas as pd
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class FeatureStoreError(Exception):
    pass


class FeatureStore:
    def __init__(self, cache_dir: str = "cache/features", ttl_days: int = 7):
        self.cache_dir = Path(cache_dir)
        self.meta_dir = self.cache_dir / "metadata"
        self.ttl_days = ttl_days

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # Key + Paths
    # =========================

    def _get_cache_key(self, symbol: str, start: str, end: str, features: List[str]) -> str:
        raw = f"{symbol}_{start}_{end}_{'_'.join(sorted(features))}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _get_data_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.parquet"

    def _get_meta_path(self, key: str) -> Path:
        return self.meta_dir / f"{key}.json"

    # =========================
    # Store
    # =========================

    def store_features(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        features: List[str],
        df: pd.DataFrame,
        metadata: Optional[Dict] = None
    ) -> str:

        if df is None or df.empty:
            raise ValueError("Empty DataFrame")

        key = self._get_cache_key(symbol, start_date, end_date, features)

        data_path = self._get_data_path(key)
        temp_path = data_path.with_suffix(".tmp")

        try:
            # Atomic write
            df.to_parquet(temp_path, engine="pyarrow", compression="snappy")
            temp_path.replace(data_path)

            meta = {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "features": features,
                "rows": len(df),
                "columns": list(df.columns),
                "created_at": datetime.utcnow().isoformat(),
                "ttl_days": self.ttl_days,
                "extra": metadata or {}
            }

            with open(self._get_meta_path(key), "w") as f:
                json.dump(meta, f, indent=2)

            return key

        except Exception as e:
            raise FeatureStoreError(f"Store failed: {e}")

    # =========================
    # Load
    # =========================

    def get_features(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        features: List[str]
    ) -> Optional[pd.DataFrame]:

        key = self._get_cache_key(symbol, start_date, end_date, features)

        data_path = self._get_data_path(key)
        meta_path = self._get_meta_path(key)

        if not data_path.exists() or not meta_path.exists():
            return None

        try:
            # Load metadata
            with open(meta_path, "r") as f:
                meta = json.load(f)

            # TTL check
            created = datetime.fromisoformat(meta["created_at"])
            if datetime.utcnow() - created > timedelta(days=self.ttl_days):
                return None

            df = pd.read_parquet(data_path, engine="pyarrow")

            # Schema validation
            if set(df.columns) != set(meta["columns"]):
                raise FeatureStoreError("Schema mismatch")

            return df

        except Exception:
            # Remove corrupted cache
            self._safe_delete(data_path)
            self._safe_delete(meta_path)
            return None

    # =========================
    # Utilities
    # =========================

    def _safe_delete(self, path: Path):
        try:
            if path.exists():
                path.unlink()
        except:
            pass

    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        removed = 0

        for file in self.cache_dir.glob("*.parquet"):
            if older_than_days:
                age = datetime.now() - datetime.fromtimestamp(file.stat().st_ctime)
                if age.days < older_than_days:
                    continue

            self._safe_delete(file)
            meta = self._get_meta_path(file.stem)
            self._safe_delete(meta)

            removed += 1

        return removed

    def list_cache(self) -> pd.DataFrame:
        rows = []

        for meta_file in self.meta_dir.glob("*.json"):
            try:
                with open(meta_file) as f:
                    meta = json.load(f)

                rows.append(meta)

            except:
                continue

        return pd.DataFrame(rows)

    def get_stats(self) -> Dict:
        df = self.list_cache()

        if df.empty:
            return {"files": 0, "symbols": []}

        return {
            "files": len(df),
            "symbols": df["symbol"].unique().tolist(),
            "total_rows": int(df["rows"].sum())
        }