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

        self.data_folder = Path("/storage/emulated/0/Download")

        self.indices_csv = None
        self.summary_csv = None
        self.fno_csv = None
        self.fno_symbols = []

        self.load_latest_csv_files()
        self.load_indices_csv()
        self.load_summary_csv()
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
        """
        Locate the latest Indices and F&O CSV files
        from the data folder.
        """

        self.indices_csv = self.find_latest_file("MW-All-Indices*.csv")
        self.fno_csv = self.find_latest_file("MW-SECURITIES*.csv")
        self.summary_csv = self.find_latest_file("INDEXSummary*.csv")

        if self.indices_csv:
            print(f"Loaded Indices CSV : {self.indices_csv.name}")
        else:
            print("Warning: MW-All-Indices CSV not found.")

        if self.fno_csv:
            print(f"Loaded F&O CSV : {self.fno_csv.name}")
        else:
            print("Warning: MW-SECURITIES CSV not found.")
            
        if self.summary_csv:
            print(f"Loaded Summary CSV : {self.summary_csv.name}")
        else:
            print("Warning: INDEXSummary CSV not found.")

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

            with open(self.indices_csv, mode="r", newline="", encoding="utf-8-sig") as file:

                reader = csv.DictReader(file)

                reader.fieldnames = [
                    h.replace('"', '').replace("\ufeff", "").strip()
                    for h in reader.fieldnames
                ]
                
                for row in reader:

                    index_name = (
                        row.get("INDEX")
                        or row.get("Index")
                        or row.get("INDEX NAME")
                        or row.get("Index Name")
                        or ""
                    ).strip()

                    index_map = {
                        "NIFTY 50": "NIFTY",
                        "NIFTY BANK": "BANKNIFTY",
                        "NIFTY FINANCIAL SERVICES": "FINNIFTY",
                        "NIFTY MIDCAP SELECT": "MIDCAP",
                        "INDIA VIX": "INDIAVIX",
                        "S&P BSE SENSEX": "SENSEX",
                        "S&P BSE BANKEX": "BANKEX",
                    }

                    symbol = index_map.get(index_name)

                    if symbol is None:
                        continue

                    self.update_index(
                        symbol,
                        {
                            "last_price": float((row.get("CURRENT") or "0").replace(",", "")),
                            "change": 0.0,
                            "change_percent": float((row.get("%CHNG") or "0").replace(",", "")),
                            "open_price": float((row.get("OPEN") or "0").replace(",", "")),
                            "high_price": float((row.get("HIGH") or "0").replace(",", "")),
                            "low_price": float((row.get("LOW") or "0").replace(",", "")),
                            "previous_close": float((row.get("PREV. CLOSE") or "0").replace(",", "")),
                            "volume": 0,
                        },
                    )

            print(f"Loaded Indices CSV: {self.indices_csv.name}")

        except FileNotFoundError:
            print("Indices CSV file not found.")

        except PermissionError:
            print("Permission denied while reading Indices CSV.")

        except ValueError as error:
            print(f"Invalid numeric value in Indices CSV: {error}")

        except Exception as error:
            print(f"Indices CSV Load Error: {error}")

    def load_summary_csv(self):

        if self.summary_csv is None:
            return

        try:
            with open(self.summary_csv, newline="", encoding="utf-8-sig") as file:

                reader = csv.DictReader(file)

                for row in reader:

                    index_id = (row.get("IndexID") or "").strip().upper()

                    if index_id not in ("SENSEX", "BANKEX"):
                        continue

                    previous_close = float((row.get("PreviousClose") or "0").replace(",", ""))
                    close_price = float((row.get("ClosePrice") or "0").replace(",", ""))

                    change = close_price - previous_close

                    if previous_close != 0:
                        change_percent = (change / previous_close) * 100
                    else:
                        change_percent = 0.0

                    self.update_index(
                        index_id,
                        {
                            "last_price": close_price,
                            "change": change,
                            "change_percent": change_percent,
                            "open_price": float((row.get("OpenPrice") or "0").replace(",", "")),
                            "high_price": float((row.get("HighPrice") or "0").replace(",", "")),
                            "low_price": float((row.get("LowPrice") or "0").replace(",", "")),
                            "previous_close": previous_close,
                        },
                    )

            print(f"Loaded Summary CSV: {self.summary_csv.name}")

        except Exception as error:
            print(f"Summary CSV Load Error: {error}")
            
    def load_fno_csv(self):

        self.fno_symbols = []

        if self.fno_csv is None:
            return

        try:
            with open(self.fno_csv, newline="", encoding="utf-8") as file:

                reader = csv.DictReader(file)

                for row in reader:
                    
                    symbol = row.get("SYMBOL")

                    if symbol:
                        self.fno_symbols.append(symbol.strip())

        except Exception as error:
            print(f"F&O CSV Load Error: {error}")
            

    def is_fno_symbol(self, symbol: str) -> bool:
        return symbol in self.fno_symbols
