"""
Data Exploration and Quality Assessment Script

This script loads and explores the labels and transactions CSV files,
documenting any data quality issues found including:
- Missing values (nulls)
- Duplicate records
- Outliers
- Data type issues
- Referential integrity issues

Assumptions:
1. Transaction amounts are in the same currency (no currency column present)
2. Timestamps are in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
3. Transaction types should be either 'credit' or 'debit'
4. Default labels should be binary (0 or 1)
5. Customer IDs should be consistent across both files
6. Transaction IDs should be unique
7. Amounts for credits should be positive, debits should be negative
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# LOAD DATA
# ============================================================================

print("=" * 80)
print("LOADING DATA")
print("=" * 80)

# Load labels CSV
print("\nLoading labels.csv...")
labels_df = pd.read_csv("data/labels.csv")
print(f"Labels shape: {labels_df.shape}")

# Load transactions CSV
print("\nLoading transactions.csv...")
transactions_df = pd.read_csv("data/transactions.csv")
print(f"Transactions shape: {transactions_df.shape}")

# ============================================================================
# BASIC DATA EXPLORATION
# ============================================================================

print("\n" + "=" * 80)
print("BASIC DATA EXPLORATION")
print("=" * 80)

# Labels exploration
print("\n--- LABELS DATA ---")
print("\nFirst 3 rows:")
print(labels_df.head(3))
print("\nData types:")
print(labels_df.dtypes)
print("\nColumn names:")
print(labels_df.columns.tolist())
print("\nBasic statistics:")
print(labels_df.describe(include="all"))

# Transactions exploration
print("\n--- TRANSACTIONS DATA ---")
print("\nFirst 3 rows:")
print(transactions_df.head(3))
print("\nData types:")
print(transactions_df.dtypes)
print("\nColumn names:")
print(transactions_df.columns.tolist())
print("\nBasic statistics:")
print(transactions_df.describe(include="all"))

# ============================================================================
# DATA QUALITY CHECKS
# ============================================================================

print("\n" + "=" * 80)
print("DATA QUALITY ASSESSMENT")
print("=" * 80)

data_quality_issues = []

# ----------------------------------------------------------------------------
# 1. MISSING VALUES (NULLS)
# ----------------------------------------------------------------------------

print("\n--- 1. MISSING VALUES CHECK ---")

# Check labels for nulls
labels_nulls = labels_df.isnull().sum()
if labels_nulls.sum() > 0:
    print("\n❌ NULLS FOUND IN LABELS:")
    print(labels_nulls[labels_nulls > 0])
    data_quality_issues.append({"file": "labels.csv", "issue": "Missing values", "details": labels_nulls[labels_nulls > 0].to_dict()})
else:
    print("\n✅ No missing values in labels.csv")

# Check transactions for nulls
transactions_nulls = transactions_df.isnull().sum()
if transactions_nulls.sum() > 0:
    print("\n❌ NULLS FOUND IN TRANSACTIONS:")
    print(transactions_nulls[transactions_nulls > 0])
    data_quality_issues.append({"file": "transactions.csv", "issue": "Missing values", "details": transactions_nulls[transactions_nulls > 0].to_dict()})
else:
    print("\n✅ No missing values in transactions.csv")

# ----------------------------------------------------------------------------
# 2. DUPLICATE RECORDS
# ----------------------------------------------------------------------------

print("\n--- 2. DUPLICATE RECORDS CHECK ---")

# Check for duplicate rows in labels
labels_duplicates = labels_df.duplicated().sum()
if labels_duplicates > 0:
    print(f"\n❌ Found {labels_duplicates} duplicate rows in labels.csv")
    data_quality_issues.append({"file": "labels.csv", "issue": "Duplicate rows", "count": labels_duplicates})
else:
    print("\n✅ No duplicate rows in labels.csv")

# Check for duplicate customer_ids in labels (should be unique)
labels_dup_customers = labels_df["customer_id"].duplicated().sum()
if labels_dup_customers > 0:
    print(f"\n❌ Found {labels_dup_customers} duplicate customer_ids in labels.csv")
    print("Duplicate customer_ids:")
    print(labels_df[labels_df["customer_id"].duplicated(keep=False)])
    data_quality_issues.append({"file": "labels.csv", "issue": "Duplicate customer_ids", "count": labels_dup_customers})
else:
    print("\n✅ All customer_ids are unique in labels.csv")

# Check for duplicate rows in transactions
transactions_duplicates = transactions_df.duplicated().sum()
if transactions_duplicates > 0:
    print(f"\n❌ Found {transactions_duplicates} duplicate rows in transactions.csv")
    data_quality_issues.append({"file": "transactions.csv", "issue": "Duplicate rows", "count": transactions_duplicates})
else:
    print("\n✅ No duplicate rows in transactions.csv")

# Check for duplicate transaction_ids (should be unique)
transactions_dup_ids = transactions_df["transaction_id"].duplicated().sum()
if transactions_dup_ids > 0:
    print(f"\n❌ Found {transactions_dup_ids} duplicate transaction_ids in transactions.csv")
    print("Duplicate transaction_ids:")
    print(transactions_df[transactions_df["transaction_id"].duplicated(keep=False)])
    data_quality_issues.append({"file": "transactions.csv", "issue": "Duplicate transaction_ids", "count": transactions_dup_ids})
else:
    print("\n✅ All transaction_ids are unique in transactions.csv")

# ----------------------------------------------------------------------------
# 3. DATA TYPE VALIDATION
# ----------------------------------------------------------------------------

print("\n--- 3. DATA TYPE VALIDATION ---")

# Convert txn_timestamp to datetime for validation
try:
    transactions_df["txn_timestamp"] = pd.to_datetime(transactions_df["txn_timestamp"])
    print("\n✅ Transaction timestamps are valid datetime format")
except Exception as e:
    print(f"\n❌ ERROR converting timestamps: {e}")
    data_quality_issues.append({"file": "transactions.csv", "issue": "Invalid timestamp format", "details": str(e)})

# Check defaulted_within_90d values (should be 0 or 1)
invalid_defaults = labels_df[~labels_df["defaulted_within_90d"].isin([0, 1])]
if len(invalid_defaults) > 0:
    print(f"\n❌ Found {len(invalid_defaults)} invalid defaulted_within_90d values (should be 0 or 1):")
    print(invalid_defaults)
    data_quality_issues.append({"file": "labels.csv", "issue": "Invalid defaulted_within_90d values", "count": len(invalid_defaults)})
else:
    print("\n✅ All defaulted_within_90d values are valid (0 or 1)")

# Check transaction types (should be 'credit' or 'debit')
invalid_txn_types = transactions_df[~transactions_df["txn_type"].isin(["credit", "debit"])]
if len(invalid_txn_types) > 0:
    print(f"\n❌ Found {len(invalid_txn_types)} invalid transaction types:")
    print(invalid_txn_types)
    data_quality_issues.append({"file": "transactions.csv", "issue": "Invalid transaction types", "count": len(invalid_txn_types)})
else:
    print("\n✅ All transaction types are valid ('credit' or 'debit')")

# Check amount data type
if not pd.api.types.is_numeric_dtype(transactions_df["amount"]):
    print("\n❌ Amount column is not numeric")
    data_quality_issues.append({"file": "transactions.csv", "issue": "Amount column not numeric"})
else:
    print("\n✅ Amount column is numeric")

# ----------------------------------------------------------------------------
# 4. OUTLIER DETECTION
# ----------------------------------------------------------------------------

print("\n--- 4. OUTLIER DETECTION ---")

# Outlier detection for transaction amounts using IQR method
# Assumption: Using IQR method with 1.5x multiplier (standard approach)
Q1 = transactions_df["amount"].quantile(0.25)
Q3 = transactions_df["amount"].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = transactions_df[(transactions_df["amount"] < lower_bound) | (transactions_df["amount"] > upper_bound)]

if len(outliers) > 0:
    print(f"\n⚠️  Found {len(outliers)} potential outliers in transaction amounts (IQR method):")
    print(f"Lower bound: {lower_bound:.2f}, Upper bound: {upper_bound:.2f}")
    print(outliers[["transaction_id", "customer_id", "amount", "txn_type", "description"]])
    data_quality_issues.append({"file": "transactions.csv", "issue": "Potential outliers in amounts", "count": len(outliers), "method": "IQR (1.5x multiplier)"})
else:
    print("\n✅ No outliers detected in transaction amounts (IQR method)")

# Check for extremely large or small amounts
# Assumption: Amounts should be reasonable (e.g., between -1,000,000 and 1,000,000)
# This is a business rule assumption
EXTREME_THRESHOLD = 1000000
extreme_amounts = transactions_df[abs(transactions_df["amount"]) > EXTREME_THRESHOLD]
if len(extreme_amounts) > 0:
    print(f"\n⚠️  Found {len(extreme_amounts)} transactions with extremely large amounts (> {EXTREME_THRESHOLD:,}):")
    print(extreme_amounts[["transaction_id", "customer_id", "amount", "txn_type", "description"]])
    data_quality_issues.append({"file": "transactions.csv", "issue": "Extremely large amounts", "count": len(extreme_amounts), "threshold": EXTREME_THRESHOLD})

# Check for zero amounts
zero_amounts = transactions_df[transactions_df["amount"] == 0]
if len(zero_amounts) > 0:
    print(f"\n⚠️  Found {len(zero_amounts)} transactions with zero amount:")
    print(zero_amounts[["transaction_id", "customer_id", "amount", "txn_type", "description"]])
    data_quality_issues.append({"file": "transactions.csv", "issue": "Zero amount transactions", "count": len(zero_amounts)})

# Check timestamp outliers (future dates or very old dates)
# Assumption: Transactions should be between 2000-01-01 and current date + 1 year
if "txn_timestamp" in transactions_df.columns and pd.api.types.is_datetime64_any_dtype(transactions_df["txn_timestamp"]):
    min_reasonable_date = pd.Timestamp("2000-01-01")
    max_reasonable_date = pd.Timestamp.now() + pd.Timedelta(days=365)

    future_dates = transactions_df[transactions_df["txn_timestamp"] > max_reasonable_date]
    old_dates = transactions_df[transactions_df["txn_timestamp"] < min_reasonable_date]

    if len(future_dates) > 0:
        print(f"\n⚠️  Found {len(future_dates)} transactions with future dates:")
        print(future_dates[["transaction_id", "customer_id", "txn_timestamp", "amount"]])
        data_quality_issues.append({"file": "transactions.csv", "issue": "Future date transactions", "count": len(future_dates)})

    if len(old_dates) > 0:
        print(f"\n⚠️  Found {len(old_dates)} transactions with very old dates (< 2000-01-01):")
        print(old_dates[["transaction_id", "customer_id", "txn_timestamp", "amount"]])
        data_quality_issues.append({"file": "transactions.csv", "issue": "Very old date transactions", "count": len(old_dates)})

# ----------------------------------------------------------------------------
# 5. BUSINESS LOGIC VALIDATION
# ----------------------------------------------------------------------------

print("\n--- 5. BUSINESS LOGIC VALIDATION ---")

# Check if credit transactions have positive amounts and debit transactions have negative amounts
# Assumption: Credits should be positive, debits should be negative
credit_negative = transactions_df[(transactions_df["txn_type"] == "credit") & (transactions_df["amount"] < 0)]
debit_positive = transactions_df[(transactions_df["txn_type"] == "debit") & (transactions_df["amount"] > 0)]

if len(credit_negative) > 0:
    print(f"\n⚠️  Found {len(credit_negative)} credit transactions with negative amounts:")
    print(credit_negative[["transaction_id", "customer_id", "amount", "txn_type"]])
    data_quality_issues.append({"file": "transactions.csv", "issue": "Credit transactions with negative amounts", "count": len(credit_negative)})

if len(debit_positive) > 0:
    print(f"\n⚠️  Found {len(debit_positive)} debit transactions with positive amounts:")
    print(debit_positive[["transaction_id", "customer_id", "amount", "txn_type"]])
    data_quality_issues.append({"file": "transactions.csv", "issue": "Debit transactions with positive amounts", "count": len(debit_positive)})

if len(credit_negative) == 0 and len(debit_positive) == 0:
    print("\n✅ Transaction types and amounts are consistent (credits positive, debits negative)")

# ----------------------------------------------------------------------------
# 6. REFERENTIAL INTEGRITY
# ----------------------------------------------------------------------------

print("\n--- 6. REFERENTIAL INTEGRITY CHECK ---")

# Check if all customer_ids in transactions exist in labels
unique_labels_customers = set(labels_df["customer_id"].unique())
unique_transactions_customers = set(transactions_df["customer_id"].unique())

missing_in_labels = unique_transactions_customers - unique_labels_customers
if len(missing_in_labels) > 0:
    print(f"\n❌ Found {len(missing_in_labels)} customer_ids in transactions that don't exist in labels:")
    print(list(missing_in_labels))
    data_quality_issues.append(
        {"file": "transactions.csv", "issue": "Customer IDs missing in labels", "count": len(missing_in_labels), "customer_ids": list(missing_in_labels)}
    )
else:
    print("\n✅ All customer_ids in transactions exist in labels")

# Check if all customer_ids in labels have transactions
missing_in_transactions = unique_labels_customers - unique_transactions_customers
if len(missing_in_transactions) > 0:
    print(f"\n⚠️  Found {len(missing_in_transactions)} customer_ids in labels with no transactions:")
    print(list(missing_in_transactions))
    data_quality_issues.append(
        {"file": "labels.csv", "issue": "Customer IDs with no transactions", "count": len(missing_in_transactions), "customer_ids": list(missing_in_transactions)}
    )
else:
    print("\n✅ All customer_ids in labels have at least one transaction")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

print("\n--- LABELS SUMMARY ---")
print(f"Total customers: {len(labels_df)}")
print(f"Customers with default (1): {labels_df['defaulted_within_90d'].sum()}")
print(f"Customers without default (0): {(labels_df['defaulted_within_90d'] == 0).sum()}")
print(f"Default rate: {labels_df['defaulted_within_90d'].mean():.2%}")

print("\n--- TRANSACTIONS SUMMARY ---")
print(f"Total transactions: {len(transactions_df)}")
print(f"Credit transactions: {(transactions_df['txn_type'] == 'credit').sum()}")
print(f"Debit transactions: {(transactions_df['txn_type'] == 'debit').sum()}")
print(f"Total credit amount: {transactions_df[transactions_df['txn_type'] == 'credit']['amount'].sum():,.2f}")
print(f"Total debit amount: {transactions_df[transactions_df['txn_type'] == 'debit']['amount'].sum():,.2f}")
print(f"Net amount: {transactions_df['amount'].sum():,.2f}")

if "txn_timestamp" in transactions_df.columns and pd.api.types.is_datetime64_any_dtype(transactions_df["txn_timestamp"]):
    print(f"\nDate range:")
    print(f"  Earliest transaction: {transactions_df['txn_timestamp'].min()}")
    print(f"  Latest transaction: {transactions_df['txn_timestamp'].max()}")
    print(f"  Date span: {(transactions_df['txn_timestamp'].max() - transactions_df['txn_timestamp'].min()).days} days")

print(f"\nAmount statistics:")
print(f"  Min amount: {transactions_df['amount'].min():,.2f}")
print(f"  Max amount: {transactions_df['amount'].max():,.2f}")
print(f"  Mean amount: {transactions_df['amount'].mean():,.2f}")
print(f"  Median amount: {transactions_df['amount'].median():,.2f}")
print(f"  Std deviation: {transactions_df['amount'].std():,.2f}")

# Transactions per customer
transactions_per_customer = transactions_df.groupby("customer_id").size()
print(f"\nTransactions per customer:")
print(f"  Min: {transactions_per_customer.min()}")
print(f"  Max: {transactions_per_customer.max()}")
print(f"  Mean: {transactions_per_customer.mean():.2f}")
print(f"  Median: {transactions_per_customer.median():.2f}")

# ============================================================================
# DATA QUALITY ISSUES SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("DATA QUALITY ISSUES SUMMARY")
print("=" * 80)

if len(data_quality_issues) == 0:
    print("\n✅ No data quality issues found!")
else:
    print(f"\n⚠️  Found {len(data_quality_issues)} data quality issue(s):\n")
    for i, issue in enumerate(data_quality_issues, 1):
        print(f"{i}. File: {issue['file']}")
        print(f"   Issue: {issue['issue']}")
        if "count" in issue:
            print(f"   Count: {issue['count']}")
        if "details" in issue:
            print(f"   Details: {issue['details']}")
        if "customer_ids" in issue:
            print(f"   Customer IDs: {issue['customer_ids']}")
        print()

print("\n" + "=" * 80)
print("EXPLORATION COMPLETE")
print("=" * 80)
