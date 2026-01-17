# Credit Risk Modeling - Data Engineering Task

A data engineering pipeline for predicting customer credit risk (90-day default prediction) using transaction data.

## Installation

Install required dependencies:
```bash
pip install fastapi uvicorn scikit-learn joblib pydantic
```

> **Note:** For Linux/Unix production deployments, also install `gunicorn`:
> ```bash
> pip install gunicorn
> ```

## Quick Start

1. **Prepare the data:**
   ```bash
   python data_prep/prepare_data.py
   ```
   This generates `artifacts/training_set.csv` with engineered features.

2. **Explore the data:**
   Open `Exploratory_Data_Analysis.ipynb` in Jupyter Notebook or JupyterLab.

3. **Run the ML Inference API:**
   ```bash
   uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
   ```
   The API will be available at `http://localhost:8000`

## Documentation

- **[Feature Documentation](feature_documentation.md)** - Detailed explanation of all engineered features, their rationale, and credit risk interpretation
- **[Data Preparation Script](data_prep/prepare_data.py)** - Implementation of feature engineering pipeline
- **[Null Data Handling Strategy](null_data_handling_strategy.md)** - Strategy for handling missing values in labels and transactions datasets


## Features

The pipeline engineers 11 features from transaction data:
- **Volume/Amount**: Transaction count, total debit/credit, average amount, debit-to-credit ratio
- **Temporal**: Days since last credit, income stability ratio
- **Behavioral Flags**: Consistent salary, risky spending, rent/mortgage, subscriptions

See [feature_documentation.md](feature_documentation.md) for complete details.

## ML Inference API

The FastAPI service provides a REST API for making credit risk predictions.

- `api/app.py` - Local filesystem (development) (in production will change as it will load model from blob storage)

### API Endpoints

- **GET `/health`** - Health check endpoint
  ```bash
  curl http://localhost:8000/health
  ```

- **POST `/predict`** - Predict credit risk probability
  ```bash
  curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{
      "txn_count": 10.0,
      "total_debit": 5000.0,
      "total_credit": 3000.0,
      "avg_amount": 500.0,
      "kw_rent": 1,
      "kw_netflix": 0,
      "kw_tesco": 1,
      "kw_payroll": 1,
      "kw_bonus": 0
    }'
  ```

**Response:**
```json
{
  "probability": 0.75,
  "prediction": 1
}
```

# Part 3: Documentation and Questions Answers as per task


## **Q1. What part of the exercise did you find most challenging, and why?**

The most significant challenge was working with limited data—only 11 rows of transaction data spanning just 3 days of transaction timestamps. This constraint required making careful assumptions about data patterns and customer behavior, making it difficult to identify robust patterns suitable for production pipelines.

The sparse transaction history limited the ability to extract meaningful temporal patterns, seasonal trends, and behavioral signals. Particularly challenging was the description field—with more diverse and detailed transaction descriptions, we could extract richer insights into spending behavior (merchant categories, payment types, transaction purposes) that would significantly enhance credit risk prediction. The limited sample size meant that feature engineering decisions had to balance between capturing meaningful signals.

## **Q2. What tradeoffs did you make? (e.g., speed vs. accuracy, simplicity vs. completeness)**

The tradeoffs varied by feature based on their importance for the 90-day default prediction task:

- **Flag Consistent Salary**: Prioritized **accuracy and completeness**. Since consistent income is critical for predicting default within 90 days, the feature requires salary transactions in at least 90% of months where the customer has transaction records. This rigorous threshold ensures we capture true income stability rather than occasional salary payments.

- **Flag Risky Spend**: Prioritized **speed and simplicity**. A single occurrence of gambling, betting, or crypto-related transactions flags a customer as risky. While a consistency-based approach (similar to salary) would be more accurate, the logical deduction is that even one instance of risky spending behavior indicates elevated risk—someone who gambles once is already showing signs of financial risk-taking behavior. This simpler approach balances detection speed with practical risk assessment.

## **Q3. Assume this needs to run in production with these constraints:**
- Cloud provider: Azure
- Budget: £500/month
- Latency requirement: <100ms per prediction
- Expected traffic: 1000 predictions/hour initially

### Production Deployment Solution

Given the lightweight nature of the `model.joblib` artifact and the current FastAPI implementation (which uses async endpoints) changes i made compared to the template provided, the service can easily handle 1000 predictions/hour on Azure Container Apps with minimal resource allocation.

### Performance Characteristics

Based on testing, the endpoint processing time is **3-4ms per prediction** (excluding network latency). This is well within the <100ms latency requirement, leaving ample headroom for network overhead and Azure infrastructure latency.

### Recommended Deployment: Azure Container Apps

**Configuration:**
- **Plan**: Pay-as-you-go
- **Resources**: 1 vCPU + 1 GiB memory
- **Server**: Uvicorn (instead of Gunicorn) to minimize idle CPU and RAM usage, reducing costs during low-traffic periods

This configuration is sufficient for handling 1000 requests/hour, with significant capacity headroom for traffic spikes.

### Cost Analysis

**Worst-case scenario (always active for 30 days):**

Assume a 30-day month (2,592,000 seconds).

**Billable seconds after free grant:**
- vCPU: 2,592,000 − 180,000 = 2,412,000 vCPU-s
- Memory: 2,592,000 − 360,000 = 2,232,000 GiB-s

**Cost calculation:**
- vCPU: 2,412,000 × $0.000024 = **$57.888**
- Memory: 2,232,000 × $0.000003 = **$6.696**
- **Total ≈ $64.584 / month** (approximately £51/month at current exchange rates)

**Conclusion:** The deployment cost is **well under the £500/month budget**, providing significant cost headroom for scaling or additional Azure services (e.g., Application Insights, Log Analytics, or increased traffic).

**High Availability & Redundancy:** Since we are well under budget, we can add multiple replicas (e.g., 2-3 instances) for redundancy and high availability. This ensures:
- **Zero-downtime deployments**: Rolling updates can be performed without service interruption
- **Fault tolerance**: If one replica fails, others continue serving traffic
- **Load distribution**: Traffic is automatically distributed across replicas
- **Cost impact**: Even with 2-3 replicas, the total cost remains well within the £500/month budget (~£102-£153/month for 2-3 replicas)

**Note:** Using Uvicorn instead of Gunicorn further reduces idle costs, as Gunicorn has higher idle CPU usage and RAM consumption. For 1000 requests/hour, Uvicorn provides sufficient performance while maintaining lower operational costs during idle periods.

**Q4. How would you deploy the FastAPI service and make the model artifact available?**
## Production Deployment Architecture
For production at scale (millions of transaction rows), we deploy using a distributed, cloud-native architecture:

### 1. Data Preparation (Databricks Spark)

**Why Databricks Spark?** With millions of transaction rows, we need distributed computing to process data efficiently. Databricks provides managed Spark clusters with auto-scaling capabilities.

```python
# Databricks notebook: data_prep/prepare_data_spark.py
# Runs the feature engineering pipeline on Spark DataFrame
# Handles millions of rows with distributed processing
```

**Training Dataset Export:**
- **Format: Delta Lake** (recommended over CSV)
  - **ACID transactions**: Ensures data consistency during concurrent writes
  - **Time travel**: Enables versioning and rollback capabilities
  - **Schema evolution**: Handles schema changes without breaking pipelines
  - **Performance**: Columnar storage with automatic indexing and caching
  - **Partitioning**: Efficient querying on large datasets
- **Versioning Strategy**: `training_set/v1.0/`, `training_set/v1.1/`, etc.
  - Each version includes metadata: feature schema, data quality metrics, creation timestamp

### 2. Model Training (Databricks or Azure ML)

**Training Pipeline:**
- Loads versioned training dataset from Delta Lake
- Trains model (e.g., XGBoost, Random Forest) with hyperparameter tuning
- Validates model performance and generates metrics
- Exports trained model artifact (`.joblib` or `.pkl` format)

### 3. Model Artifact Storage (Azure Blob Storage)

**Blob Storage Structure with Versioning:**
```
azure-blob://ml-models-prod/
├── credit-risk/
│   ├── v1.0/
│   │   ├── model.joblib
│   │   ├── metadata.json (model version, training date, metrics)
│   │   └── feature_schema.json
│   ├── v1.1/
│   │   └── ...
│   └── latest/ -> v1.1/ (reference to latest version)
```

**Benefits:**
- **Scalability**: Azure Blob Storage handles any model size with high availability
- **Versioning**: Blob versioning enables model rollback and A/B testing
- **Cost-effective**: Pay only for storage and requests
- **Security**: Managed identities and access policies for secure access control
- **Integration**: Works seamlessly with Azure services (ECS, Azure Functions, VMs)

### 4. FastAPI Service Deployment

**Container-based Deployment on Azure ECS:**

The FastAPI service is deployed as a containerized application on Azure ECS for production workloads. The deployment process is automated through CI/CD:

- **Docker Image Build**: Docker images are automatically built and pushed to GitHub Container Registry (GHCR) via GitHub Actions workflow on every push to the main branch. The workflow is configured in `.github/workflows/docker-build.yml`.

- **Container Configuration**: The Dockerfile configures the application to run with gunicorn using uvicorn workers, optimized for high-traffic production loads. The service runs with 4 worker processes to handle concurrent requests efficiently.

- **Model Loading**: The FastAPI service loads models from blob storage (Azure Blob Storage) at startup, with fallback to local filesystem for local development. The service supports managed identity authentication for secure access to blob storage resources.

- **Azure ECS Deployment**: The containerized application is deployed to Azure ECS, which provides auto-scaling capabilities, load balancing, and high availability for the inference service. ECS manages the container lifecycle and ensures the service remains available under varying traffic loads.

### Key Advantages of This Architecture

1. **Scalability**: Databricks Spark handles millions of rows; Azure Blob Storage scales to any model size
2. **Versioning**: Both training data (Delta Lake) and models (Azure Blob Storage) are versioned for reproducibility
3. **Separation of Concerns**: Data prep, training, and inference are decoupled
4. **Cost Efficiency**: Pay only for compute and storage used
5. **Reliability**: Azure Blob Storage provides high durability and availability
6. **Flexibility**: Easy to update models without redeploying the API service

### Model Updates & Rollback

- **Update**: New model versions are uploaded to blob storage with versioned paths. The service can be configured to load a specific model version by updating the model path configuration and restarting the ECS service.

- **Rollback**: In case of model performance degradation, the service can be quickly rolled back to a previous model version by updating the model path configuration to point to the previous version and restarting the service.

- **A/B Testing**: Multiple ECS service instances can be deployed with different model versions, allowing traffic to be routed between different model versions for performance comparison and gradual rollout strategies.
