import os
import json
import time
from google import genai
from google.genai import types
from spatial_analytics import get_spatial_context

def invoke_incident_commander():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("======== CONFIGURATION ERROR ========")
        print("GEMINI_API_KEY environment variable is not set.")
        print("Please set your Gemini API key in your console to run Phase 3:")
        print('$env:GEMINI_API_KEY="your-api-key"')
        print("=====================================")
        return {"error": "GEMINI_API_KEY not set"}
        
    client = genai.Client(api_key=api_key)
    
    print("Fetching live spatial context from BigQuery Brain...")
    raw_context = get_spatial_context()
    if raw_context == "{}" or not raw_context:
        print("Error fetching spatial context from BigQuery.")
        return {"error": "Failed to fetch context from BigQuery"}
        
    context_data = json.loads(raw_context)
    
    # Strip heavy geometry arrays to drastically save Gemini API Tokens
    agent_context = {
        "gates": context_data.get("gates", []),
        "hotspot_clusters": [
            {"cluster_id": c["cluster_id"], "fan_count": c["fan_count"]} 
            for c in context_data.get("hotspot_clusters", [])
        ]
    }
    
    system_instruction = """
    You are the 'Operations Incident Commander' for AuraSpatial. Your job is to monitor real-time flow capacities at large-scale sporting venues.
    Your objective is to review the Metadata-based RAG context of the stadium, analyze High-Density Spikes or Gate Bottlenecks, and propose spatial resolutions.
    
    You will receive current Gate Occupancies and Spatial Cluster Hotspots in JSON format.
    
    CRITICAL INSTRUCTION: You must strictly format your response using exactly these three headers:
    [INPUT]
    (Brief summary of the raw JSON layout you observe. E.g., which gates have capacity, how many hotspots exist.)
    
    [REASONING]
    (Explain your thought process. Which gate or cluster is overloaded? Where can pressure be released? What is the logical deduction for safety?)
    
    [ACTION]
    (Clear, actionable outcome for the ground-staff. E.g., 'Deploy 3 personnel to Gate A to redirect flow. Open emergency route to Gate B.')
    """
    
    # Sending dense, compact JSON
    prompt = f"""
    Current Spatial Context:
    {json.dumps(agent_context)}
    
    Please analyze this real-time context and respond according to your format.
    """
    
    print("Agent Reasoning started via Gemini Flash...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )
            return {
                "spatial": context_data,
                "agent_reasoning": response.text
            }
        except Exception as e:
            err_str = str(e)
            print(f"Attempt {attempt+1} - Error invoking Gemini model: {err_str}")
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                fallback_ui = "[WARNING] API Quota Exhausted (429). Please wait for the daily reset or adjust polling limits."
                return {"spatial": context_data, "agent_reasoning": fallback_ui}
            elif attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying
            else:
                # Provide a graceful degradation payload for the UI instead of a hard crash
                fallback_ui = "[WARNING] The Gemini model is currently experiencing high demand (503). Retrying next cycle..."
                return {"spatial": context_data, "agent_reasoning": fallback_ui}

if __name__ == "__main__":  # pragma: no cover
    result = invoke_incident_commander()
    print("\n" + "="*50)
    print("AGENT DECISION SUMMARY")
    print("="*50)
    if not result.get("error"):
        print(result.get("agent_reasoning", "No resoning generated."))
    else:
        print("Error:", result.get("error"))

