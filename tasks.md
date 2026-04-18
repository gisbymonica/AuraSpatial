# AuraSpatial Implementation Roadmap

Below is the execution tracking for the AuraSpatial Geospatial Twin prototype. This document has been updated to reflect the full Hackathon implementation journey, highlighting what was fully achieved, what was intentionally scoped out, and specific workflow optimizations executed during the build process.

## Phase 1: Data Ingestion (The "Sense" Layer) 
- [x] Create a Python script (`mock_ingestion.py`) to generate random initial coordinates for fans around the stadium.
- [x] Integrate python script to push to BigQuery table via Batch load jobs.
- [x] Handle Google Cloud Free-Tier quota constraints natively (Bypassed blocked Streaming API by transitioning to Batch uploads).
- [x] Configure central configuration extraction: Gate definitions moved out of hardcoded logic into dynamic `gates.json` to allow scalable testing.

## Phase 2: Spatial Analytics (The "Brain" Foundation) 
- [x] Implement BigQuery spatial clustering using `ST_CLUSTERDBSCAN`.
- [x] Create a robust querying wrapper inside `spatial_analytics.py` ensuring pure JSON extraction for Gemini.
- [x] Implement **Ghost Fan purging**: Added temporal filtering (`WHERE timestamp > TIMESTAMP_SUB(...)`) extending across all BigQuery Views. This destroyed old historical hotspots, heavily restricting runaway Token usage and reducing JSON payload noise.
- [x] Dynamically construct BigQuery SQL generation from `gates.json` mapping. 

## Phase 3: Agentic Reasoning (The "Think" Layer)
- [x] Develop **Gemini 1.5 Flash** System Prompt for the Incident Commander.
- [x] Integrate **Metadata-based RAG**: Send JSON-defined spatial anomalies to the language model.
- [x] Implement API Quota Retry strategies: Mitigated the `429 RESOURCE_EXHAUSTED` limitation of the 2.5-flash payload by gracefully trapping 503/429 limits inside a local recovery loop, reverting safely to 1.5-flash quotas.
- [ ] Create a "Simulation" function where the agent formally validates its own rerouting recommendation back to Vertex AI. *(Omitted for Hackathon scope constraint)*

## Phase 4: Frontend & Visualization (The "Act" Layer)
- [x] Initialize **Deck.gl** with an ultra-fast base map via MapLibre & Carto (Cyberpunk Dark Matter theme).
- [x] Ensure Frontend receives coordinate data (`[lon, lat]`) straight from the API layer without client-side hardcoding.
- [x] Implement localized Flask backend natively architected for Google Cloud Run (included `Dockerfile` mapping and Application Default Credentials).
- [x] Map pure logic into UI via `ScatterplotLayer` for heatmaps. Avoided H3 Hexagon calculations to preserve browser memory and harness BigQuery's native Database aggregation directly.
- [x] **Dynamic Routing Integrations**: Built responsive neon **Deck.gl ArcLayers** dynamically routing all hotspot traffic metrics to the stadium's safest/lightest-load gate!
- [x] Integrate "Live Terminal Output" feeding Gemini's `[ACTION]` resolution directly into the sidebar panel.
- [ ] Build automated SMS integration or "AppSheet" bindings for Ground Staff deployment alerts. *(Omitted for Hackathon scope constraint)*

---

### Key Technical Optimizations During Development

1. **BigQuery Heavy Lifting over Client-Side Computation**:
   Instead of forcing the frontend to parse 1,000s of coordinates into WebGL Hexagons (which destroys frame rates on laptops), we routed data directly through `ST_CLUSTERDBSCAN` inside Google Cloud. This compresses thousands of coordinates into exactly `n` highly-relevant Hotspot clusters. The frontend now runs flawlessly using lightweight Scatterplots.

2. **Temporal Payload Reductions & Token Conservation**:
   A deep optimization was executing `TIMESTAMP_SUB` in SQL, instantly killing historic trajectories. This stopped the Gemini API from burning Context Tokens assessing irrelevant ghost fans from previous script tests.

3. **GCP Secure Authentication Flow**:
   Instead of exposing JSON service keys into typical Web applications, `app.py` acts as a pure backend API proxy, built with `google.auth.default()`. It provides a seamless transition from localized `python app.py` executions immediately onto **Google Cloud Run** using Application Default Credentials without a single code refactor.
