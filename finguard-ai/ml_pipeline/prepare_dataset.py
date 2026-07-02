import uuid
import random
import pandas as pd
from pathlib import Path

RAW_DIR = Path("ml_pipeline/data/raw")

input_file = RAW_DIR / "transactions.csv"
output_file = RAW_DIR / "transactions_converted.csv"
print("Loading dataset...")
df = pd.read_csv(input_file)

merchant_categories = [
    "RETAIL",
    "FOOD",
    "TRAVEL",
    "GROCERY",
    "HEALTH",
    "ELECTRONICS",
]

payment_methods = [
    "CREDIT_CARD",
    "DEBIT_CARD",
    "WIRE",
    "UPI",
]

transaction_types = [
    "PURCHASE",
    "TRANSFER",
    "WITHDRAWAL",
]

countries = [
    "USA",
    "UK",
    "INDIA",
    "CANADA",
    "GERMANY",
]

new_df = pd.DataFrame()

new_df["transaction_id"] = [
    str(uuid.uuid4()) for _ in range(len(df))
]

new_df["amount"] = df["Amount"]

new_df["merchant_category"] = [
    random.choice(merchant_categories)
    for _ in range(len(df))
]

new_df["payment_method"] = [
    random.choice(payment_methods)
    for _ in range(len(df))
]

new_df["transaction_type"] = [
    random.choice(transaction_types)
    for _ in range(len(df))
]

new_df["country"] = [
    random.choice(countries)
    for _ in range(len(df))
]

new_df["is_fraud"] = df["Class"]

new_df.to_csv(output_file, index=False)

print("Done!")
print(output_file)
print(new_df.head())