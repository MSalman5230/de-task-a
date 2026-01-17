# Credit Risk Modeling - Data Engineering Task

A data engineering pipeline for predicting customer credit risk (90-day default prediction) using transaction data.



## Quick Start

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment as per your OS/IDE:

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or install manually:
   ```bash
   pip install fastapi uvicorn scikit-learn joblib pydantic seaborn pandas
   ```

### Running the Pipeline

1. **Check data quality:**
   Open `Data_Quality_Check.ipynb` in Jupyter Notebook.
   This notebook checks the data quality of the provided datasets (transactions and labels), including:
   - Missing values (nulls)
   - Duplicate records
   - Outliers
   - Data type issues
   - Referential integrity issues

2. **Prepare the data (THE DATA PIPELINE):**
   ```bash
   python data_prep/prepare_data.py
   ```
   This generates `artifacts/training_set.csv` with engineered features.

3. **Explore the data:**
   Open `Exploratory_Data_Analysis.ipynb` in Jupyter Notebook.

4. **Run the ML Inference API:**
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

**Note:** The `api/app.py` template provided in the zip file was already working. The only modification made was adding `async` to the endpoint functions for improved performance. and wrote github action to create docker image when changes push to main branch.

**Important:** The model expects data in the format specified in the PDF (not the engineered features created in the data preparation pipeline). The model was not retrained with the engineered features because:
- There's no point creating a model with only 11 rows of data
- The PDF/question did not mention training a model

### API Endpoints


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

# Questions Answers as per PDF

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

#### Production Deployment Solution

Given the lightweight nature of the `model.joblib` artifact and the current FastAPI implementation (which uses async endpoints) changes i made compared to the template provided, the service can easily handle 1000 predictions/hour on Azure Container Apps with minimal resource allocation.

#### Performance Characteristics

Based on testing, the endpoint processing time is **3-4ms per prediction** (excluding network latency). This is well within the <100ms latency requirement, leaving ample headroom for network overhead and Azure infrastructure latency.

#### Recommended Deployment: Azure Container Apps

**Configuration:**
- **Plan**: Pay-as-you-go
- **Resources**: 1 vCPU + 1 GiB memory
- **Server**: Uvicorn (instead of Gunicorn) to minimize idle CPU and RAM usage, reducing costs during low-traffic periods

This configuration is sufficient for handling 1000 requests/hour, with significant capacity headroom for traffic spikes.

#### Cost Analysis

**Worst-case scenario (always active for 30 days):**

Assume a 30-day month (2,592,000 seconds).

**Cost calculation (without free grant):**
- vCPU: 2,592,000 × $0.000024 = **$62.208**
- Memory: 2,592,000 × $0.000003 = **$7.776**
- **Total ≈ $69.984 / month** (approximately £56/month at current exchange rates)

**Conclusion:** The deployment cost is **well under the £500/month budget**, providing significant cost headroom for scaling or additional Azure services (e.g., Application Insights, Log Analytics, or increased traffic).

**High Availability & Redundancy:** Since we are well under budget, we can add multiple replicas (e.g., 2-3 instances) for redundancy and high availability. This ensures:
- **Zero-downtime deployments**: Rolling updates can be performed without service interruption
- **Fault tolerance**: If one replica fails, others continue serving traffic
- **Load distribution**: Traffic is automatically distributed across replicas
- **Cost impact**: Even with 2-3 replicas, the total cost remains well within the £500/month budget (~£112-£168/month for 2-3 replicas)

**Note:** Using Uvicorn instead of Gunicorn further reduces idle costs, as Gunicorn has higher idle CPU usage and RAM consumption. For 1000 requests/hour, Uvicorn provides sufficient performance while maintaining lower operational costs during idle periods.


## **Q4. How would you deploy the FastAPI service and make the model artifact available?**

Here I will explain how I envision this full stack will be deployed while keeping in mind scalability, cost, and the Azure platform.

#### 1. Data Preparation (Azure Databricks Spark)

**Why Databricks Spark?** With millions of transaction rows, we need distributed computing to process data efficiently. Databricks provides managed Spark clusters with auto-scaling capabilities. We will write a similar notebook to `prepare_data.py` for Databricks using PySpark.

**Training Dataset Export:**
- **Format: Delta Lake** (recommended over CSV)
  - **ACID transactions**: Ensures data consistency during concurrent writes
  - **Time travel**: Enables versioning and rollback capabilities
  - **Schema evolution**: Handles schema changes without breaking pipelines
  - **Performance**: Columnar storage with automatic indexing and caching
  - **Partitioning**: Efficient querying on large datasets
- **Versioning Strategy**: `training_set/v1.0/`, `training_set/v1.1/`, etc.
  - Each version includes metadata: feature schema, data quality metrics, creation timestamp

#### 2. Model Training (Databricks or Azure ML)
**Use Databricks or Azure ML**
**Training Pipeline:**
- Loads versioned training dataset from Delta Lake
- Trains model (e.g., XGBoost, Random Forest) with hyperparameter tuning
- Validates model performance and generates metrics
- Exports trained model artifact (`.joblib` or `.pkl` format)

#### 3. Model Artifact Storage (Azure Blob Storage)

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
- **Integration**: Works seamlessly with Azure services (Azure Container Apps, Azure Functions, VMs)

#### 4. FastAPI Service Deployment

**Container-based Deployment on Azure Container Apps:**

The FastAPI service is deployed as a containerized application on Azure Container Apps for production workloads. The deployment process is automated through CI/CD:

- **Docker Image Build**: Docker images are automatically built and pushed to GitHub Container Registry (GHCR) via GitHub Actions workflow on every push to the main branch. The workflow is configured in `.github/workflows/docker-build.yml`.

- **Container Configuration**: The Dockerfile configures the application to run with Uvicorn, optimized for production loads. For the initial 1000 predictions/hour requirement, a single Uvicorn instance is sufficient and more cost-effective. For high-traffic scenarios, we can scale horizontally by adding more replicas and optionally switch to Gunicorn with multiple Uvicorn workers for increased throughput per container.

- **Model Loading**: The FastAPI service loads models from blob storage (Azure Blob Storage) at startup. The model path can be specified via container environment variables (e.g., `MODEL_PATH=azure-blob://ml-models-prod/credit-risk/v1.0/model.joblib`), which can be easily changed without rebuilding the container. Alternatively, a POST endpoint can be implemented to dynamically load a specific model version:

  ```bash
  POST /load-model
  Content-Type: application/json
  
  {
    "model_path": "azure-blob://ml-models-prod/credit-risk/v1.1/model.joblib"
  }
  ```
  
  This allows for runtime model updates without container restarts, enabling A/B testing and gradual rollouts.

- **Azure Container Apps Deployment**: The containerized application is deployed to Azure Container Apps, which provides auto-scaling capabilities, load balancing, and high availability for the inference service. Container Apps manages the container lifecycle and ensures the service remains available under varying traffic loads. The pay-as-you-go pricing model ensures cost efficiency, charging only for active compute time.

#### Key Advantages of This Architecture

1. **Scalability**: Databricks Spark handles millions of rows; Azure Blob Storage scales to any model size
2. **Versioning**: Both training data (Delta Lake) and models (Azure Blob Storage) are versioned for reproducibility
3. **Separation of Concerns**: Data prep, training, and inference are decoupled
4. **Cost Efficiency**: Pay only for compute and storage used
5. **Reliability**: Azure Blob Storage provides high durability and availability
6. **Flexibility**: Easy to update models without redeploying the API service

#### Model Updates & Rollback

- **Update**: New model versions are uploaded to blob storage with versioned paths. The service can be configured to load a specific model version by updating the model path configuration and restarting the Container Apps service.

- **Rollback**: In case of model performance degradation, the service can be quickly rolled back to a previous model version by updating the model path configuration to point to the previous version and restarting the Container Apps service.

- **A/B Testing**: Multiple Container Apps revisions can be deployed with different model versions, allowing traffic to be routed between different model versions for performance comparison and gradual rollout strategies.

## **Q5. If transaction volume jumped from thousands to millions per day, how would you rethink Part 1?**

Most of the solution for handling millions of transactions per day has already been addressed in **Q4, Section 1: Data Preparation (Azure Databricks Spark)**. Here, we expand on the approach for processing large-scale transaction data:

#### Scalable Data Processing Architecture

**Azure Databricks for Large-Scale Processing:**
- **Distributed Computing**: Databricks Spark enables parallel processing of millions of transaction rows across multiple nodes, dramatically reducing processing time compared to single-machine processing
- **Auto-scaling Clusters**: Databricks automatically scales compute resources up or down based on workload, ensuring cost efficiency while maintaining performance
- **PySpark Implementation**: We will write a similar notebook to `prepare_data.py` for Databricks using PySpark, translating the feature engineering logic to distributed Spark operations

**Automated Data Pipeline with Blob Storage Triggers:**
- **Event-Driven Processing**: When new label and transaction datasets land in Azure Blob Storage, blob storage triggers automatically initiate the Databricks job
- **Scheduled Processing**: For regular batch processing, we can configure scheduled Databricks jobs (e.g., daily, hourly) to process new data as it arrives
- **Incremental Processing**: The pipeline can be designed to process only new or changed data since the last run, reducing compute costs and processing time

**Delta Lake for Versioning and Data Management:**
- **ACID Transactions**: Delta Lake ensures data consistency during concurrent writes, critical when processing millions of transactions
- **Time Travel**: Enables querying historical versions of the data, useful for debugging and auditing
- **Schema Evolution**: Handles schema changes gracefully without breaking the pipeline
- **Partitioning**: Efficient partitioning strategies (e.g., by date, customer_id) enable fast queries and processing on large datasets
- **Versioning Strategy**: Each processed dataset version is stored in Delta Lake with metadata (processing timestamp, data quality metrics, feature schema), enabling full traceability

#### Key Improvements Over Single-Machine Processing

1. **Performance**: Distributed processing reduces feature engineering time from hours/days to minutes
2. **Scalability**: Can handle millions of transactions per day without performance degradation
3. **Reliability**: Automated triggers and scheduling ensure data is processed consistently
4. **Cost Efficiency**: Pay only for compute time used, with auto-scaling to minimize idle costs
5. **Data Quality**: Delta Lake's ACID properties ensure data integrity at scale

## **Q6. What metrics would you track in production and why? What could go wrong with this model in production?**

Since this question could refer to either the API server (inference service) or the data pipeline (training data preparation), I will focus on **both** aspects, as both are critical for production ML systems.

### API Server (FastAPI Inference Service) Metrics

**Key Metrics to Track:**
- **Request Latency (P50, P95, P99)**: Ensure <100ms SLA compliance; P95/P99 identify outliers
- **Throughput & Error Rate**: Monitor request rate and HTTP error rates (4xx, 5xx) for capacity planning and issue detection
- **Model Inference Time**: Track actual prediction time (excluding network overhead) to detect performance degradation
- **Availability & Container Health**: Monitor uptime (target: 99.9%+), container restarts, memory/CPU usage
- **Prediction Distribution**: Track probability distributions to detect model drift
- **Active Replicas**: Monitor for cost optimization

**Alerting Thresholds:** Latency P95 > 100ms, Error rate > 1%, Availability < 99.5%, Memory usage > 80%, Container restarts > 3 in 5 minutes

### Data Pipeline Metrics

**Input Data Quality (Critical for Transformation Success):**
- **Schema Validation**: Alert when labels.csv or transactions.csv don't match expected schema (columns, data types, required fields)
- **Data Completeness & Volume Anomalies**: Track missing value rates and alert on significant volume deviations (±50%)
- **Date Range Validation**: Verify transaction timestamps are within expected ranges

**Transformation Pipeline:**
- **Feature Engineering Success Rate**: Track successful vs. failed transformations
- **Keyword Detection & New Keywords**: Monitor existing keyword patterns and identify new transaction descriptions that could become feature flags
- **Null Value Handling**: Monitor records requiring imputation

**Pipeline Execution:**
- **Job Success Rate, Processing Time, Records Processed**: Track Databricks job completion, duration, and data completeness
- **Delta Lake Write Success**: Monitor successful writes

**Alerting:** Schema mismatch, Missing value rate > 20% for critical columns, Pipeline job failure

### What Could Go Wrong with This Model in Production?

**Data Quality Issues:**
- **Schema/Format Changes**: Unexpected changes to CSV schemas or transaction description formats break transformations and keyword detection
- **Missing Critical Data**: Absence of salary transactions or key behavioral indicators produces incomplete features
- **Label Data Quality**: Incorrect or delayed default flags result in unreliable model training

**Model Performance Degradation:**
- **Data Drift**: Customer behavior patterns change (new spending categories, payment methods), making historical features less predictive
- **Concept Drift**: Relationship between features and default risk changes due to economic/market conditions
- **Feature Distribution Shift**: Significant changes in input feature distributions cause unreliable predictions

**Infrastructure & Operational Issues:**
- **Model Loading Failures**: Network/authentication issues prevent loading models from blob storage
- **Resource Exhaustion**: High traffic causes memory/CPU exhaustion, leading to service degradation
- **Version Mismatches**: New model versions expect different features than the API provides

## **Q7. If you used AI tools such as ChatGPT, Claude, Copilot, or any other tools:**
**Where and how did you use them? (e.g., boilerplate code, debugging, syntax help)**
**How did they help or hinder your process?**

I used **Cursor** and **Google Gemini** throughout this project. Here's how I leveraged them:

### Documentation and Question Answers (README.md)

For writing the README and answering questions (Q1-Q6), I primarily used AI tools to help structure and refine my ideas. I would provide rough notes, bullet points, and key concepts, and the AI would help:
- Structure the content into coherent paragraphs
- Improve grammar and clarity
- Format technical details properly
- Expand on ideas while maintaining my original intent

An example of this workflow can be seen in `AI_TOOL_USAGES_EXAMPLE.txt` in the repository, where I provided rough notes about Q3 (production deployment constraints) with typos and incomplete thoughts, and the AI helped transform it into a well-structured, professional answer.

**How it helped:** Significantly accelerated documentation writing while ensuring clarity and professionalism. It allowed me to focus on the technical content and ideas rather than spending time on formatting and grammar.

**How it hindered:** Occasionally for this repo it tried to write code for azure deployment code which was not need so i had to delete them and keep reminding its not to write code.

### Code Development (data_prep/prepare_data.py)

For writing the feature engineering code in `data_prep/prepare_data.py`, I used a similar approach:
- I would describe the features I needed (e.g., "flag_risky_spend" and provide the keywords it should look for in the description)
- The AI would generate the Python syntax and implementation code
- I would review and refine the logic to ensure it matched my requirements

**How it helped:** 
- Rapid prototyping of feature engineering logic
- Syntax assistance for pandas operations and data transformations
- Code structure and best practices suggestions
- Reduced time spent on boilerplate code

**How it hindered:** 
For writing code in this repo, there was not much hindrance as it's simple. However, in my experience working with large repos, AI tends to make things overly complicated or sometimes does not write code that is easy to maintain, i.e., robust for adding features in the future, so I need to add that to the prompt or I sometimes write code manually.

### Overall Assessment

AI tools were instrumental in accelerating both documentation and code development. They served as a force multiplier, allowing me to focus on the high-level design and technical decisions while delegating syntax, formatting, and structure to the AI. The key was maintaining active oversight and iterative refinement to ensure the output matched my requirements and technical standards.

## NOTE: One thing you should know about me. I never commit code that I don't understand the logic for. That's my motto.
