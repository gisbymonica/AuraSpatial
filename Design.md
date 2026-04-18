# Design.md: AuraSpatial
## Agentic Digital Twin for Stadium Operations

### 1. Executive Summary
**AuraSpatial** is a real-time spatial twin and decision-support system designed for large-scale sporting venues. By integrating high-velocity spatial data processing with Agentic AI, the system predicts crowd bottlenecks, automates emergency routing, and optimizes staff deployment through a "Geospatial Brain."

### 2. Challenge Vertical
* **Vertical:** Stadium Infrastructure & Crowd Safety.
* **Persona:** Operations Incident Commander (The "Controller").
* **Core Innovation:** Spatial-Aware RAG (Retrieval-Augmented Generation) utilizing Vectorized Trajectories rather than just text.

### 3. System Architecture: The "Sense-Think-Act" Loop

#### A. The Data Plane (Sense)
* **Ingestion:** IoT sensors (CCTV, Wi-Fi pings, BLE beacons) streamed via **Google Cloud Pub/Sub**.
* **Spatial Processing:** **Dataflow** integrated with **Apache Sedona** for real-time spatial joins and trajectory clustering.
* **Storage:** **BigQuery Geospatial** for historical pattern analysis and high-velocity streaming.

#### B. The Reasoning Engine (Think)
* **Spatial RAG:** A custom vector database (Vertex AI Vector Search) storing "Spatial Contexts"�historical egress patterns, gate capacities, and security protocols.
* **Agentic Logic (Gemini 2.5 Flash):** The agent monitors the stream. If a density spike is detected, the agent:
    1. Queries Spatial RAG for "Pressure Release" gates.
    2. Simulates rerouting impacts.
    3. Evaluates staff proximity.

#### C. The Execution Layer (Act)
* **Command Center:** A 3D dashboard built with **Deck.gl** and **CARTO Maps - Command Center Cyan Theme**.
* **API Outbound:** Automated triggers to digital signage via **Cloud Functions** to update directional arrows.
* **Staff Dispatch:** **AppSheet** integration for real-time ground-staff instructions.

### 4. Logical Decision Flow
The system operates on the fundamental flow-density relationship:
$$q = \rho \cdot v$$
*Where $q$ is flow, $\rho$ is density, and $v$ is velocity.*

**The Agent's Decision Matrix:**
* **IF** $\rho > \text{Threshold}$ AND $v < \text{Critical Velocity}$:
    * **Action:** Identify "Spatial Sink" (unoccupied area).
    * **Action:** Generate "Egress Pivot" for ground staff.
    * **Action:** Update LED Wayfinding.

### 5. Google Services Integration
| Service | Implementation Detail |
| :--- | :--- |
| **Vertex AI** | Gemini 2.5 Flash for reasoning; Vector Search for Spatial RAG. |
| **CARTO** | Maps for high-fidelity venue visualization. |
| **BigQuery** | Analyzing "Hotspot" history to predict issues. |
| **Cloud Run** | Hosting Agentic microservices for low-latency responses. |
