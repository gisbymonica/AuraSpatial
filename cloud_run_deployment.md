# Guide to Google Cloud Run Deployment

Google Cloud Run is a fully managed compute environment that effortlessly scales your containerized apps. Following this guide will transition the AuraSpatial dashboard from local host to a robust, publicly accessible endpoint.

## Prerequisites
Before you begin, ensure you have:
1. **Google Cloud CLI (`gcloud`)** installed and authenticated (`gcloud auth login`).
2. An active GCP project linked to your billing account (Free Tier is totally acceptable).
3. The Project ID handy (e.g., `aurageo`).

---

## Step-by-Step Implementation

### Step 1: Configure Your Project Context
Open your terminal inside the AuraSpatial directory and target your project:
```bash
gcloud config set project aurageo
```

### Step 2: Build the Container Image
Google Cloud utilizes Artifact Registry to store your code images. First, ensure the API is enabled, then utilize Cloud Build to parse your local `Dockerfile`:
```bash
# Enable API (Only needs to happen once)
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Build and Push
gcloud builds submit --tag gcr.io/aurageo/auraspatial-dashboard
```
*Note: This command will package `requirements.txt`, `app.py`, and `agent.py` securely.*

### Step 3: Deploy the Service via Cloud Run
Command the container to instantiate on Cloud Run natively:
```bash
gcloud run deploy auraspatial-dashboard \
    --image gcr.io/aurageo/auraspatial-dashboard \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars GEMINI_API_KEY="your_api_key_here"
```

### Step 4: Verify Deployment Environment Auth
Cloud Run services run natively on Google Cloud's **Application Default Credentials (ADC)**. Since we programmed `app.py` and `spatial_analytics.py` to respect `google.auth.default()`, it will immediately attach to the default service account that Cloud Run runs under, granting it pristine access to your BigQuery schemas instantly!

---

## Potential Errors & Fixes Along the Way

### 1. `PermissionDenied` retrieving BigQuery Client
If your application successfully mounts but outputs: `Access Denied: Project aurageo...`
* **Why**: The default compute service account associated with the Cloud Run instance doesn't have BigQuery viewer privileges.
* **Fix**: Navigate to **IAM & Admin** in GCP. Find the `[Project-Number]-compute@developer.gserviceaccount.com` account and explicitly add the `BigQuery Data Viewer` and `BigQuery Job User` roles to it.

### 2. Service Returns `500 Server Error` on Page Load
* **Why**: The container might have tripped a strict Memory exception when processing heavy BigQuery loads natively.
* **Fix**: Upgrade the Memory Allocation dynamically:
  ```bash
  gcloud run services update auraspatial-dashboard --memory 1Gi
  ```

### 3. Port Allocation Conflicts
If your logs display a timeout or `Gunicorn missing port binding`:
* **Why**: Google Cloud Run injects `$PORT` as an environment variable (often 8080). Hardcoding port numbers into Flask will result in container rejection.
* **Fix**: Ensure your `app.py` always utilizes the environment binding provided. Do not change `int(os.environ.get("PORT", 8080))` inside `app.py` manually. Ensure `Dockerfile` utilizes `--bind :$PORT`.

### 4. Gunicorn Worker Timeout
While spinning up BigQuery instances and pinging Gemini simultaneously, the web request could exceed Gunicorn's default 30-second drop interval.
* **Why**: Flask requests that hang waiting on API dependencies (like GenAI resolving) occasionally trigger a timeout drop.
* **Fix**: As explicitly set in your `Dockerfile`, ensure your execution utilizes `--timeout 0` so the Gunicorn instance delegates response times strictly to Cloud Run (allowing up to 60+ seconds natively without killing the thread).
