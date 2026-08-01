"""
TradeOracle AI
indices_engine.py

Purpose:
Fetch and manage live Indian indices data.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import csv


@dataclass
class IndexData:
    symbol: str
    name: str
    last_price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    previous_close: float = 0.0
    volume: int = 0
    timestamp: Optional[datetime] = None


class IndicesEngine:

    def __init__(self):
        self.indices = {
            "NIFTY": IndexData("NIFTY", "NIFTY 50"),
            "BANKNIFTY": IndexData("BANKNIFTY", "BANK NIFTY"),
            "FINNIFTY": IndexData("FINNIFTY", "FINNIFTY"),
            "SENSEX": IndexData("SENSEX", "SENSEX"),
            "MIDCAP": IndexData("MIDCAP", "NIFTY MIDCAP SELECT"),
            "BANKEX": IndexData("BANKEX", "BANKEX"),
            "INDIAVIX": IndexData("INDIAVIX", "INDIA VIX"),
        }

        self.data_folder = Path("data")

        self.indices_csv = None
        self.fno_csv = None

        self.load_latest_csv_files()

        self.load_indices_csv()
        self.load_fno_csv()
        
    def get_all_indices(self) -> Dict[str, IndexData]:
        return self.indices

    def get_index(self, symbol: str) -> Optional[IndexData]:
        return self.indices.get(symbol)

    def update_index(self, symbol: str, data: dict):
        if symbol not in self.indices:
            return

        item = self.indices[symbol]

        item.last_price = data.get("last_price", item.last_price)
        item.change = data.get("change", item.change)
        item.change_percent = data.get("change_percent", item.change_percent)
        item.open_price = data.get("open_price", item.open_price)
        item.high_price = data.get("high_price", item.high_price)
        item.low_price = data.get("low_price", item.low_price)
        item.previous_close = data.get("previous_close", item.previous_close)
        item.volume = data.get("volume", item.volume)
        item.timestamp = datetime.now()

    def get_symbols(self) -> List[str]:
        return list(self.indices.keys())

    def load_latest_csv_files(self):

        self.indices_csv = self.find_latest_file("MW-All-Indices*.csv")
        self.fno_csv = self.find_latest_file("MW-SECURITIES*.csv")
        
        if self.indices_csv is None:
            print("MW-All-Indices CSV not found")

        if self.fno_csv is None:
            print("MW-SECURITIES CSV not found")

    def find_latest_file(self, pattern):

        files = list(self.data_folder.glob(pattern))

        if not files:
            return None

        return max(files, key=lambda f: f.stat().st_mtime)

    def load_indices_csv(self):

        if self.indices_csv is None:
            print("Indices CSV file not found.")
            return

        try:

            with open(
                self.indices_csv,
                mode="r",
                newline="",
                encoding="utf-8"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    symbol = (row.get("Symbol") or "").strip()

                    if symbol not in self.indices:
                        continue

                    self.update_index(symbol, {
                        "last_price": float(row.get("Last") or 0),
                        "change": float(row.get("Change") or 0),
                        "change_percent": float(row.get("%Change") or 0),
                        "open_price": float(row.get("Open") or 0),
                        "high_price": float(row.get("High") or 0),
                        "low_price": float(row.get("Low") or 0),
                        "previous_close": float(row.get("Prev Close") or 0),
                        "volume": int(float(row.get("Volume") or 0))
                    })

            print(f"Loaded Indices CSV: {self.indices_csv.name}")

        except FileNotFoundError:
            print("Indices CSV file not found.")

        except PermissionError:
            print("Permission denied while reading Indices CSV.")

        except ValueError as error:
            print(f"Invalid numeric value in Indices CSV: {error}")

        except Exception as error:
            print(f"Indices CSV Load Error: {error}")

    def load_fno_csv(self):

        self.fno_symbols = []

        if self.fno_csv is None:
            return

        try:
            with open(
                self.fno_csv,
                newline="",
                encoding="utf-8"
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    symbol = row.get("SYMBOL")

                    if symbol:
                        self.fno_symbols.append(symbol.strip())

        except Exception as error:

            print(f"F&O CSV Load Error: {error}")

    def is_fno_symbol(self, symbol: str) -> bool:
        return symbol in self.fno_symbols
