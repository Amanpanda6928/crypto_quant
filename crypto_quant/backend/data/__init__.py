"""Data layer exports."""

# When run as a script, use absolute imports
if __name__ == "__main__":
    import sys
    import os
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    from crypto_quant.data.api import BinanceDataFetcher, fetch_current_data
    from crypto_quant.data.build_dataset import DatasetBuilder, build_dataset
else:
    from .api import BinanceDataFetcher, fetch_current_data
    from .build_dataset import DatasetBuilder, build_dataset

__all__ = ["BinanceDataFetcher", "fetch_current_data", "DatasetBuilder", "build_dataset"]


if __name__ == "__main__":
    print("Data module exports:")
    print(f"- BinanceDataFetcher: {BinanceDataFetcher}")
    print(f"- fetch_current_data: {fetch_current_data}")
    print(f"- DatasetBuilder: {DatasetBuilder}")
    print(f"- build_dataset: {build_dataset}")
    print("All imports successful!")