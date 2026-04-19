import pytest
from app import app
import app as app_module
from unittest.mock import MagicMock

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_index_route(client, mocker):
    mocker.patch("app.render_template", return_value="mock_html")
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "mock_html"

def test_stadium_state_success(client, mocker):
    mocker.patch("app.invoke_incident_commander", return_value={"agent_reasoning": "mock_data"})
    mocker.patch("app.threading.Thread")
    mocker.patch("app.time.time", return_value=1000)
    
    app_module.LAST_API_STATE = None
    app_module.LAST_INGESTION_TIME = 0
    
    response = client.get("/api/stadium_state")
    assert response.status_code == 200
    assert response.json == {"agent_reasoning": "mock_data"}

def test_stadium_state_error(client, mocker):
    mocker.patch("app.invoke_incident_commander", return_value=None)
    
    app_module.LAST_API_STATE = None
    app_module.LAST_INGESTION_TIME = 0
    
    response = client.get("/api/stadium_state")
    assert response.status_code == 500

def test_stadium_state_caching(client, mocker):
    app_module.LAST_API_STATE = {"cached": "data"}
    app_module.LAST_API_UPDATE = 1000
    
    mocker.patch("app.time.time", return_value=1010)
    
    response = client.get("/api/stadium_state")
    assert response.status_code == 200
    assert response.json == {"cached": "data"}

def test_stadium_state_run_ingestion_mock_called(client, mocker):
    mocker.patch("app.invoke_incident_commander", return_value={"agent_reasoning": "mock_data"})
    mock_thread = mocker.patch("app.threading.Thread")
    mocker.patch("app.time.time", return_value=2000)

    
    app_module.LAST_API_STATE = None
    app_module.LAST_INGESTION_TIME = 0
    
    response = client.get("/api/stadium_state")
    assert response.status_code == 200
    # Thread called twice: one for mock_ingestion, one for upload_incident_log since "error" not in state
    assert mock_thread.call_count == 2
