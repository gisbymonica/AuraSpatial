# AuraSpatial: Agentic Digital Twin for Stadium Operations

Welcome to **AuraSpatial**—a Geospatial Digital Twin powered by Google Cloud and Gemini 1.5 Flash. This project serves as a real-time command center designed to monitor physical crowd movement, cluster anomalies, and resolve spatial bottlenecks via AI-driven operational reasoning.

## Chosen Vertical
**Sports & Entertainment (Crowd & Safety Operations)**
Managing foot traffic at large events like concerts or sporting events traditionally relies on reactive monitoring via CCTV. AuraSpatial acts proactively by combining real-time spatial clustering with Agentic reasoning, effectively assigning a dedicated AI "Incident Commander" to assess bottlenecks and dynamically propose actionable rerouting directly to ground staff.

---

## Approach and Logic
The AuraSpatial architecture operates on a **Sense - Think - Act** framework:

1. **Sense (Ingestion Layer)**: Trajectories are ingested into BigQuery. BigQuery serves as the Geospatial Brain, actively recalculating densities using standard GIS formulas (leveraging `ST_CLUSTERDBSCAN` to find hotspots).
2. **Think (Agent layer)**: We utilize a **Metadata-based RAG architecture**. Rather than running thousands of physical coordinates through a heavy LLM prompt, we synthesize the parsed anomaly clusters and Gate Occupancy counts from BigQuery into a unified JSON format. This tiny payload gives Gemini complete operational context instantly.
3. **Act (Dashboard Layer)**: A lightweight Flask and `deck.gl` frontend creates the Cyberpunk control room. It visualizes the hotspots via neon scatterplots while piping the Gemini instructions seamlessly to the operator panel.

---

## How the Solution Works
1. **Automated PoC Ingestion**: For this Proof of Concept (PoC), you do not need to manually run simulation scripts! When a user visits the dashboard URL, the backend seamlessly pulses `mock_ingestion.py` behind the scenes. This guarantees fresh demo data is always visualized by seamlessly spawning 50 AI-represented fans and migrating their geometries towards defined target Gates (pulled dynamically from `gates.json`). 
2. **Spatial Analytics**: `spatial_analytics.py` maintains automatic BigQuery Views. By leveraging native `TIMESTAMP` filters, the map automatically destroys "ghost" anomalies by cleanly wiping historical records older than 15 minutes to guarantee pure real-time tactical mapping.
3. **Agent Brain**: `agent.py` wraps the Google GenAI SDK. Once a threshold is triggered, the AI reviews the inputs and issues strict text actions in an `[INPUT] -> [REASONING] -> [ACTION]` structure.
4. **Flask Relay**: `app.py` acts as the control tower. It protects your API keys by masking the Gemini endpoints, seamlessly manages the heartbeat of the background simulation bots to bypass Cloud API overload limits, and orchestrates the web dashboard.

---

## Production vs. Prototype Data Ingestion 
* **Current Prototype**: The script uses `client.load_table_from_json()` pushing batches to BQ because the Free Tier (Sandbox) aggressively blocks direct Google Streaming API logic. 
* **Production Build**: In a live stadium deployment, ticket turnstiles and CCTV computer-vision systems would transmit data directly through **Google Cloud Pub/Sub**. A **Dataflow** job would instantly pipe those coordinate updates via BigQuery Streaming API, bypassing manual batched scripts to provide absolutely zero latency tracking.

---

## Assumptions Made
* **API Rate Limits**: Attempted use of the `gemini-2.5-flash` model rapidly exhausted aggressive Free Tier limits (capped at 20 request/day globally limits). So, it is important to be mindful of the number of requests to the app.
* **Cost Saving Storage**: No database caching layer (like Redis) is implemented here. It polls BigQuery sequentially due to the simplicity of the architecture constraints.
* **Stateless Agents**: Simulated Fan trajectories do not avoid physical walls/boundaries around the stadium mock context.

---

## Guide for Local Deployment
To run this Digital Twin directly on your local laptop:

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   $env:GEMINI_API_KEY="your_api_key_here"  # Command for PowerShell
   ```
2. **Ensure Authentication Context**:
   Verify your service account specifically `<SERVICE_ACCOUNT_KEY>.json` handles the target dataset locally.
3. **Deploy Dashboard**:
   In your terminal, simply spin up the web proxy:
   ```bash
   python app.py
   ```
4. **Visualizing the Stadium**:
   Navigate to `http://localhost:8080` in Chrome/Edge! 
   *Because of our automated ingestion architecture, the Dashboard natively pushes dummy batches of AI Crowd Movement out into the stadium the exact millisecond you boot the URL! You will see the teal spatial clusters load into the physical limits instantly!*

---

## Guide for Cloud Run Deployment (High Level)
Because the codebase is equipped with `Dockerfile` and utilizes Application Default Credentials, migrating to Google Cloud Run is exceptionally native.

1. Submit your build to Google Cloud Artifact Registry using `gcloud builds...`
2. Deploy the container as a serverless instance using `gcloud run deploy...`
3. Expose the URL directly to authorized operational staff.

*For full step-by-step deployment instructions, please view `cloud_run_deployment.md`!*
