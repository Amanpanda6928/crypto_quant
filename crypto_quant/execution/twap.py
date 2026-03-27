import time
import random
from typing import Optional, Callable, Any, List, Dict
from dataclasses import dataclass
from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class TWAPResult:
    symbol: str
    side: OrderSide
    total_filled: float
    avg_price: float
    chunks_executed: int
    chunks_failed: int
    execution_time: float
    fill_details: List[Dict]


class TWAPExecutionError(Exception):
    pass


def execute_twap(
    symbol: str,
    side: OrderSide,
    total_quantity: float,
    num_chunks: int,
    delay_seconds: float,
    executor: Any,
    min_chunk_size: Optional[float] = None,
    max_slippage_pct: float = 0.002,
    max_retries: int = 3,
    timeout_seconds: Optional[float] = None
) -> TWAPResult:

    if total_quantity <= 0:
        raise ValueError("total_quantity must be positive")

    start_time = time.time()
    fill_details = []

    total_filled = 0.0
    total_value = 0.0
    chunks_executed = 0
    chunks_failed = 0

    chunk_size = total_quantity / num_chunks

    for i in range(num_chunks):

        # Timeout protection
        if timeout_seconds and (time.time() - start_time > timeout_seconds):
            break

        # Adaptive chunk sizing (remaining quantity)
        remaining = total_quantity - total_filled
        if remaining <= 0:
            break

        qty = min(chunk_size, remaining)

        if min_chunk_size and qty < min_chunk_size:
            continue

        success = False

        for attempt in range(max_retries):
            try:
                result = executor.safe_order(
                    symbol=symbol,
                    side=side.value,
                    quantity=qty
                )

                filled_qty = result.get("filled", 0)
                price = result.get("price", 0)

                # Slippage check
                ref_price = executor.get_market_price(symbol)

                if ref_price > 0:
                    slippage = abs(price - ref_price) / ref_price
                    if slippage > max_slippage_pct:
                        raise TWAPExecutionError("Slippage too high")

                fill_details.append({
                    "chunk": i + 1,
                    "filled": filled_qty,
                    "price": price,
                    "attempt": attempt + 1,
                    "status": "success",
                    "timestamp": time.time()
                })

                total_filled += filled_qty
                total_value += filled_qty * price
                chunks_executed += 1

                success = True
                break

            except Exception as e:
                if attempt == max_retries - 1:
                    fill_details.append({
                        "chunk": i + 1,
                        "error": str(e),
                        "status": "failed"
                    })
                    chunks_failed += 1

                time.sleep(1 + random.random())

        # Randomized delay (anti-predictability)
        if i < num_chunks - 1:
            jitter = random.uniform(-0.3, 0.3) * delay_seconds
            time.sleep(max(0, delay_seconds + jitter))

    execution_time = time.time() - start_time

    avg_price = total_value / total_filled if total_filled > 0 else 0

    return TWAPResult(
        symbol=symbol,
        side=side,
        total_filled=total_filled,
        avg_price=avg_price,
        chunks_executed=chunks_executed,
        chunks_failed=chunks_failed,
        execution_time=execution_time,
        fill_details=fill_details
    )