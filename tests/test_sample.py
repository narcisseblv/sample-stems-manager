from fastapi.testclient import TestClient
from sample_manager.main import app
from sample_manager.routes import samples

client = TestClient(app)

def setup_function() -> None:
    samples.clear()

def test_get_samples_returns_empty_list() -> None:
    response = client.get("/samples")

    assert response.status_code == 200
    assert response.json() == []

def test_create_sample() -> None:
    payload = {
        "name": "Vaporwave Pad",
        "file_path": "data/vaporwave-pad.wav",
        "bpm": 120,
        "musical_key": "F# minor",
        "category": "pad"
    }

    response = client.post("/samples", json=payload)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        **payload
    }

def test_get_existing_sample() -> None:
    payload = {
        "name": "Boom Bap Drums",
        "file_path": "data/boom-bap-drums.wav",
        "bpm": 92,
        "musical_key": None,
        "category": "drums"
    }

    created_sample = client.post("/samples", json=payload).json()
    sample_id = created_sample["id"]

    response = client.get(f"/samples/{sample_id}")

    assert response.status_code == 200
    assert response.json() == created_sample

def test_get_missing_sample() -> None:
    response = client.get("/samples/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Sample not found"}

def test_rejects_invalid_bpm() -> None:
    payload = {
        "name": "Invalid Sample",
        "file_path": "data/invalid.wav",
        "bpm": 500,
        "musical_key": "C major",
        "category": "melody"
    }

    response = client.post("/samples", json=payload)
    assert response.status_code == 422
    