"""
Main Execution Script - FIXED (Multi-Asset Pipeline)
"""

import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # ensure parent directory includes crypto_quant package root

try:
    from .data.build_dataset import build_dataset, DatasetBuilder
    from .model.predict import get_current_prediction
    from .backtest.run_backtest import run_simple_backtest, WalkForwardBacktest
except ImportError:
    from crypto_quant.backend.data.build_dataset import build_dataset, DatasetBuilder
    from crypto_quant.backend.model.predict import get_current_prediction
    from crypto_quant.backend.backtest.run_backtest import run_simple_backtest, WalkForwardBacktest


# =====================================================
# FULL PIPELINE
# =====================================================

def run_full_pipeline(candles: int = 1000):

    print("=" * 60)
    print("CRYPTO QUANT SYSTEM (MULTI-ASSET)")
    print("=" * 60)

    # =========================
    # STEP 1: DATASET
    # =========================
    print("\n📊 STEP 1: Building Dataset...")

    builder = DatasetBuilder()
    # Use all default coins (30) unless custom symbols are passed in DatasetBuilder.
    df = builder.build_multi_asset(limit=candles)

    print(f"Dataset shape: {df.shape}")
    print(f"Coins processed: {df['symbol'].nunique()}")

    # =========================
    # STEP 2: TRAIN
    # =========================
    print("\n🤖 STEP 2: Training Models...")

    try:
        from .model.train import train_model  # Import here to avoid slow startup
    except ImportError:
        from crypto_quant.backend.model.train import train_model
    trainer = train_model(limit=candles)

    # =========================
    # STEP 3: PREDICT
    # =========================
    print("\n🔮 STEP 3: Prediction (BTC)...")

    try:
        preds = get_current_prediction("BTCUSDT")
        print(preds.to_string(index=False))
    except Exception as e:
        print(f"Prediction error: {e}")

    # =========================
    # STEP 4: BACKTEST
    # =========================
    print("\n📈 STEP 4: Backtesting...")

    try:
        results = run_simple_backtest()
    except Exception:
        print("Fallback to walk-forward...")
        wf = WalkForwardBacktest()
        results = wf.run()

    print("\n✅ DONE")

    return df, trainer, results


# =====================================================
# DASHBOARD
# =====================================================

def run_dashboard():
    import subprocess
    dashboard_path = os.path.join(os.path.dirname(__file__), "app.py")
    subprocess.run(["streamlit", "run", dashboard_path])


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "train", "predict", "backtest", "dashboard", "live"], default="full")
    parser.add_argument("--candles", type=int, default=2500)

    args = parser.parse_args()

    if args.mode == "full":
        run_full_pipeline(args.candles)

    elif args.mode == "train":
        try:
            from .model.train import train_model  # Import here
        except ImportError:
            from crypto_quant.backend.model.train import train_model
        train_model(limit=args.candles)

    elif args.mode == "predict":
        try:
            from .model.predict import get_all_predictions
        except ImportError:
            from crypto_quant.backend.model.predict import get_all_predictions
        all_preds = get_all_predictions()

        # format as table
        for symbol, preds in all_preds.items():
            print(f"\n=== {symbol} ===")
            for horizon, (prob,) in preds.items():
                confidence = abs(prob - 0.5) * 2
                print(f"{horizon:>4} | Prob_Up: {prob:.4f} | Conf: {confidence:.4f}")

    elif args.mode == "backtest":
        run_simple_backtest()

    elif args.mode == "dashboard":
        run_dashboard()

    elif args.mode == "live":
        try:
            from .live.live_system import LiveSystem
        except ImportError:
            from crypto_quant.backend.live.live_system import LiveSystem
        import time

        system = LiveSystem()

        while True:
            try:
                system.run_cycle()
                time.sleep(300)
            except Exception as e:
                print("Error:", e)