# Null Data Handling Strategy

## Labels Dataset (`labels.csv`)

### Columns: `customer_id`, `defaulted_within_90d`

**Strategy: DROP records with any null values**

**Reason:**
- Both columns are critical for analysis
- `customer_id`: Required to link to transactions - without it, the record is unusable
- `defaulted_within_90d`: This is the target variable - missing values cannot be used for modeling or analysis

---

## Transactions Dataset (`transactions.csv`)

### 1. `transaction_id` and `customer_id` - **DROP**

**Strategy: DROP records with null values**

**Reason:**
- `transaction_id`: Required for unique identification and deduplication
- `customer_id`: Required to link transactions to customer labels - without it, transaction cannot be analyzed

---

### 2. `txn_timestamp` - **CALCULATE OR DROP**

**Strategy: Calculate based on adjacent transactions if transaction_ids are sequential, else DROP**

**Options:**

**Option A: Calculate from Sequential Transaction IDs**
- If transaction_ids are sequential (e.g., T00001, T00002, T00003), calculate timestamp based on adjacent transactions for the same customer
- Use average time difference between customer's transactions
- **Assumption**: Transaction IDs are sequential and processed in order

**Option B: Use Customer's Median Transaction Time**
- Calculate median timestamp from customer's other transactions
- Use median time of day if multiple transactions exist
- **Assumption**: Customer has transaction patterns

**Option C: Use Overall Dataset Median**
- If customer has no other transactions, use overall median timestamp
- **Risk**: Less accurate, but preserves record

**If transaction_ids are NOT sequential or no adjacent transactions exist: DROP**

---

### 3. `txn_type` - **CALCULATE OR INFER**

**Strategy: Infer from amount sign or description**

**Options:**

**Option A: Infer from Amount Sign**
- If `amount > 0`: Set `txn_type = 'credit'`
- If `amount < 0`: Set `txn_type = 'debit'`
- **Assumption**: Positive amounts are credits, negative are debits

**Option B: Infer from Description**
- Use keyword matching on description field
- Credit keywords: "PAYROLL", "PAYMENT", "DEPOSIT", "CREDIT", "BONUS"
- Debit keywords: "RENT", "PURCHASE", "DEBIT", "FEE", "WITHDRAWAL"
- **Assumption**: Descriptions contain transaction type information

---

### 4. `description` - **IMPUTE OR KEEP NULL**

**Strategy: Impute with generic value or keep null**

**Options:**

**Option A: Impute with Generic Description**
- Replace null with: `"{txn_type} TRANSACTION"` (e.g., "CREDIT TRANSACTION")
- Or: `"UNKNOWN TRANSACTION"`
- Preserves record but loses specific information

**Option B: Keep Null as Is**
- Leave description as null
- Use null as a category itself
- Flag records with missing descriptions for analysis
- **Assumption**: Missing descriptions might indicate specific transaction types

---

## Summary

| Column | Dataset | Strategy |
|--------|---------|----------|
| `customer_id` | labels.csv | **DROP** |
| `defaulted_within_90d` | labels.csv | **DROP** |
| `transaction_id` | transactions.csv | **DROP** |
| `customer_id` | transactions.csv | **DROP** |
| `txn_timestamp` | transactions.csv | **CALCULATE** (Options A-C) or **DROP** |
| `txn_type` | transactions.csv | **INFER** (Options A-B) |
| `description` | transactions.csv | **IMPUTE** (Option A) or **KEEP NULL** (Option B) |
| `amount` | transactions.csv | *Not specified - assume DROP if null* |
