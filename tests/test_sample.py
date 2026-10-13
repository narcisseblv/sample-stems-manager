from fastapi.testclient import TestClient
from pathlib import Path
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

def test_filter_samples_by_category(
    client: TestClient) -> None:
    first_sample = sample_payload()
    second_sample = {
        "name": "Boom Bap Drums",
        "file_path": "data/boom-bap-drums.wav",
        "bpm": 92,
        "muscial_key": None,
        "category": "drums"
    }

    client.post("/samples", json=first_sample)
    client.post("/samples", json=second_sample)

    response = client.get("/samples", params={"category": "drums"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Boom Bap Drums"

def test_filter_samples_by_name(client: TestClient) -> None:
    client.post("/samples", json=sample_payload())
    response =client.get("/samples", 
                         params={"name": "vapor"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Vaporwave Pad"

def test_filter_samples_by_bpm_range(
        client:TestClient
) -> None:
    first_sample = sample_payload()
    second_sample = {
        "name": "Fast Drum Loop",
        "file_path": "data/fast_drums.wav",
        "bpm": 140,
        "musical_key": None,
        "category": "drums"
    }

    client.post("/samples", json=first_sample)
    client.post("/samples", json=second_sample)

    response = client.get("/samples",
                          params={
                              "min_bpm": 80,
                              "max_bpm": 100
                          })

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["bpm"] == 83

def test_filter_samples_without_result(
        client:TestClient
) -> None:
    client.post("/samples", json=sample_payload())
    response = client.get("/samples",
                          params={"category": "vocals"})

    assert response.status_code == 200
    assert response.json() == []

def test_rejects_invalid_bpm_range(
        client: TestClient
) -> None:
    response = client.get("/samples",
                          params={
                              "min_bpm": 150,
                              "max_bpm": 80
                          }
)
    assert response.status_code == 400
    assert response.json() == {
        "detail": "min_bpm cannot be greater than max_bpm"
    }

def test_upload_audio_file(
    client: TestClient,
    tmp_path,
    monkeypatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        tmp_path
    )

    response = client.post(
        "/samples/upload",
        data={
            "name": "Test Kick",
            "category": "drums",
            "bpm": "92"
        },
        files={
            "file": (
                "kick.wav",
                b"fake audio cntent",
                "audio/wav"
            )
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Kick"
    assert response.json()["bpm"] == 92

    stored_path = Path(response.json()["file_path"])

    assert stored_path.exists()
    assert stored_path.suffix == ".wav"


def test_rejects_unsupported_file(
        client: TestClient
) -> None:
    response = client.post(
        "/samples/upload",
        data={
            "name": "Invalid File",
            "category": "unknown"
        },
        files={
            "file": (
                "document.txt",
                b"not audio",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only WAV and MP3 files are allowed"
    }

def test_download_audio_file(
    client: TestClient,
    tmp_path,
    monkeypatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        tmp_path
    )

    audio_content =b"fake audio content"

    upload_response = client.post(
        "/samples/upload",
        data={
            "name": "Test Kick",
            "category": "drums",
            "bpm": "92"
        },
        files={
            "file": (
                "kick.wav",
                audio_content,
                "audio/wav"
            )
        }
    )

    assert upload_response.status_code == 201

    sample_id = upload_response.json()["id"]

    response = client.get(
        f"/samples/{sample_id}/audio"
    )

    assert response.status_code == 200
    assert response.content == audio_content
    assert response.headers["content-type"] == "audio/wav"

def test_download_missing_sample(
    client: TestClient
) -> None:
    response = client.get("/samples/999/audio")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Sample not found"
    }

def test_download_missing_audio_file(
    client: TestClient,
    tmp_path,
    monkeypatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        tmp_path
    )

    create_response = client.post(
        "/samples",
        json={
            "name": "Missing Sample",
            "file_path": str(tmp_path / "missing.wav"),
            "bpm": 90,
            "musical_key": None,
            "category": "drums"
        }
    )
    
    sample_id = create_response.json()["id"]

    response = client.get(
        f"/samples/{sample_id}/audio"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Audio file not found"
    }

    
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
