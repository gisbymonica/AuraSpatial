import pytest
from unittest.mock import MagicMock
import agent

def test_invoke_no_api_key(mocker):
    mocker.patch("os.getenv", return_value=None)
    res = agent.invoke_incident_commander()
    assert res == {"error": "GEMINI_API_KEY not set"}

def test_invoke_no_context(mocker):
    mocker.patch("os.getenv", return_value="FAKE_KEY")
    mocker.patch("agent.get_spatial_context", return_value="{}")
    res = agent.invoke_incident_commander()
    assert res == {"error": "Failed to fetch context from BigQuery"}

def test_invoke_success(mocker):
    mocker.patch("os.getenv", return_value="FAKE_KEY")
    mocker.patch("agent.get_spatial_context", return_value='{"gates": [], "hotspot_clusters": [{"cluster_id":1, "fan_count":10}]}')
    
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked Reasoning"
    mock_client_instance.models.generate_content.return_value = mock_response
    
    mocker.patch("agent.genai.Client", return_value=mock_client_instance)
    
    res = agent.invoke_incident_commander()
    assert "spatial" in res
    assert res["agent_reasoning"] == "Mocked Reasoning"

def test_invoke_quota_exhausted(mocker):
    mocker.patch("os.getenv", return_value="FAKE_KEY")
    mocker.patch("agent.get_spatial_context", return_value='{"gates": []}')
    
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")
    mocker.patch("agent.genai.Client", return_value=mock_client_instance)
    
    res = agent.invoke_incident_commander()
    assert "[WARNING] API Quota Exhausted" in res["agent_reasoning"]

def test_invoke_retry_exhausted(mocker):
    mocker.patch("os.getenv", return_value="FAKE_KEY")
    mocker.patch("agent.get_spatial_context", return_value='{"gates": []}')
    mocker.patch("agent.time.sleep")
    
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.side_effect = Exception("503 Service Unavailable")
    mocker.patch("agent.genai.Client", return_value=mock_client_instance)
    
    res = agent.invoke_incident_commander()
    assert "[WARNING] The Gemini model is currently experiencing high demand" in res["agent_reasoning"]
    assert mock_client_instance.models.generate_content.call_count == 3
