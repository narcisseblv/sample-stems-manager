from fastapi.testclient import TestClient
#from sample_manager.main import app

# client = TestClient(app)
"""
def setup_function() -> None:
    samples.clear()
"""
def sample_payload() -> dict[str, object]:
    return {
        "name": "Vaporwave Pad",
        "file_path": "data/vaporwave-pad.wav",
        "bpm": 83,
        "musical_key": "F# minor",
        "category": "pad"
    }

def test_get_samples_returns_empty_list(client: TestClient) -> None:
    response = client.get("/samples")

    assert response.status_code == 200
    assert response.json() == []

def test_create_sample(client: TestClient) -> None:
    payload = sample_payload()

    response = client.post("/samples", json=payload)

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Vaporwave Pad"
    assert response.json()["bpm"] == 83
   
def test_get_existing_sample(client: TestClient) -> None:
    created_sample = client.post("/samples", json=sample_payload()).json()
    sample_id = created_sample["id"]

    response = client.get(f"/samples/{sample_id}")

    assert response.status_code == 200
    assert response.json() == created_sample

def test_get_missing_sample(client: TestClient) -> None:
    response = client.get("/samples/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Sample not found"}

def test_rejects_invalid_bpm(client: TestClient) -> None:
    payload = sample_payload()
    payload["bpm"] = 500

    response = client.post("/samples", json=payload)
    assert response.status_code == 422

def test_update_sample(client: TestClient) -> None:
    created_sample = client.post("/samples", json=sample_payload()).json()
    sample_id = created_sample["id"]
    response = client.patch(
        f"/samples/{sample_id}",
        json={"bpm":90}
    )
    assert response.status_code == 200
    assert response.json()["bpm"] == 90
    assert response.json()["name"] == "Vaporwave Pad"

def test_delete_sample(client: TestClient) -> None:
    created_sample = client.post("/samples", json=sample_payload()).json()

    sample_id = created_sample["id"]
    delete_response = client.delete(f"/samples/{sample_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/samples/{sample_id}")

    assert get_response.status_code == 404

"""
def test_update_missing_sample() -> None:
    response = client.patch("/samples/999", json={"bpm": 100})
    assert response.status_code == 404
    assert response.json() == {"detail": "Sample not found"}

def test_delete_missing_sample() -> None:
    response = client.delete("/samples/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Sample not found"}
"""
