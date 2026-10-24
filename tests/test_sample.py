from fastapi.testclient import TestClient
from pathlib import Path
#from sample_manager.main import app
from io import BytesIO
import wave
import pytest

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

def make_wav_bytes() -> bytes:
    buffer = BytesIO()

    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 8000)

    return buffer.getvalue()

def test_get_samples_returns_empty_list(client: TestClient) -> None:
    response = client.get("/samples")

    assert response.status_code == 200
    assert response.json() == []

def test_create_sample(client: TestClient) -> None:
    payload = sample_payload()

    response = client.post("/samples", json=payload)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        **payload,
        "duration_seconds": None,
        "file_size_bytes": None,
        "audio_format": None
    }

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

    audio_content = make_wav_bytes()
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
                audio_content,
                "audio/wav"
            )
        }
    )

    assert response.status_code == 201, response.json()
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

    audio_content = make_wav_bytes()

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

def test_delete_sample_removes_audio_file(
    client: TestClient,
    tmp_path,
    monkeypatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        tmp_path
    )
    audio_content = make_wav_bytes()
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

    sample = upload_response.json()
    sample_id = sample["id"]
    audio_path = Path(sample["file_path"])

    assert audio_path.exists()

    delete_response = client.delete(
        f"/samples/{sample_id}"
    )

    assert delete_response.status_code == 204
    assert not audio_path.exists()

    get_response = client.get(
        f"/samples/{sample_id}"
    )

    assert get_response.status_code == 404

def test_delete_sample_with_missing_file(
    client: TestClient,
    tmp_path,
    monkeypatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        tmp_path
    )

    response = client.post(
        "/samples",
        json={
            "name": "Missing Audio",
            "file_path": str(tmp_path / "missing.wav"),
            "bpm": 90,
            "musical_key": None,
            "category": "drums"
        }
    )

    sample_id = response.json()["id"]

    delete_response = client.delete(
        f"/samples/{sample_id}"
    )

    assert delete_response.status_code == 204

def test_delete_sample_not_removing_ext_file(
    client: TestClient,
    tmp_path,
    monkeypatch
) -> None:
    upload_directory = tmp_path / "uploads"
    upload_directory.mkdir()

    external_file = tmp_path / "external.wav"
    external_file.write_bytes(b"external audio")

    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        upload_directory
    )

    response = client.post(
        "/samples",
        json={
            "name": "External Audio",
            "file_path": str(external_file),
            "bpm": 90,
            "musical_key": None,
            "category": "drums"
        }
    )

    sample_id = response.json()["id"]

    delete_response = client.delete(
        f"/samples/{sample_id}"
    )

    assert delete_response.status_code == 204
    assert external_file.exists()

def test_upload_extracts_audio_metadata(
    client: TestClient,
    tmp_path,
    monkeypatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        tmp_path
    )

    audio_content = make_wav_bytes()

    response = client.post(
        "/samples/upload",
        data={
            "name": "One Second Sample",
            "category": "pad",
            "bpm": "83" 
        },
        files={
            "file": (
                "sample.wav",
                audio_content,
                "audio/wav"
            )
        }
    )

    assert response.status_code == 201

    sample = response.json()

    assert sample["duration_seconds"] == pytest.approx(1.0, abs=0.01)
    assert sample["file_size_bytes"] == len(audio_content)
    assert sample["audio_format"] == "wav"

def test_rejects_invalid_audio_content(
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
            "name": "Fake Audio",
            "category": "unknown"
        },
        files={
            "file": (
                "fake.wav",
                b"this is not a wav file",
                "audio/wav"
            )
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid audio file"
    }

    assert list(tmp_path.iterdir()) == []

def test_paginate_samples(client: TestClient) -> None:
    for index in range(3):
        payload = sample_payload()
        payload["name"] = f"Sample {index + 1}"
        payload["file_path"] = f"data/sample-{index + 1}.wav"

        response = client.post("/samples", json=payload)

        assert response.status_code == 201

    response = client.get("/samples", params={
        "offset":1,
        "limit": 1
    })

    assert response.status_code == 200

    samples = response.json()

    assert len(samples) == 1
    assert samples[0]["name"] == "Sample 2"

def test_pagination_returns_empty_list(
    client: TestClient
) -> None:
    client.post("/samples", json=sample_payload())

    response = client.get(
        "/samples",
        params={
            "offset": 100,
            "limit": 10
        }
    )

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("offset", -1),
        ("limit", 0),
        ("limit", 101)
    ]
)
def test_rejects_invalid_pagination_parameters(
    client: TestClient,
    parameter: str,
    value: int
) -> None:
    response = client.get(
        "/samples",
        params={
            parameter: value
        })

    assert response.status_code == 422

def test_combines_filter_and_pagination(
    client: TestClient
) -> None:
    for index in range(3):
        payload = sample_payload()
        payload["name"] = f"Pad {index + 1}"
        payload["file_path"] = f"data/pad-{index + 1}.wav"

        client.post("/samples", json=payload)

    drum = sample_payload()
    drum["name"] = "Drum Loop"
    drum["file_path"] = "data/drum-loop.wav"
    drum["category"] = "drums"

    client.post("/samples", json=payload)

    response = client.get(
        "/samples",
        params={
            "category": "pad",
            "offset": 1,
            "limit": 1
        }
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Pad 2"

def test_rejects_oversized_audio(
    client,
    tmp_path,
    monkeypatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.routes.UPLOAD_DIR",
        tmp_path
    )

    monkeypatch.setattr(
        "sample_manager.config.settings.max_audio_size_bytes",
        10 
    )

    response = client.post(
        "/samples/upload",
        data={
            "name": "Large file",
            "category": "test"
        },
        files={
            "file": (
                "large.wav",
                make_wav_bytes(),
                "audio/wav"
            )
        }
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "Audio file is too large"
    }
    assert list(tmp_path.iterdir()) == []

def test_rejects_dangerous_filename(
    client,
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
            "name": "Unsafe file",
            "category": "test"
        },
        files={
            "file": (
                "../unsafe.wav",
                make_wav_bytes(),
                "audio/wav"
            )
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid filename"
    }

def test_rejects_mismatched_audio_format(
    client,
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
            "name": "Wrong extension",
            "category": "test"
        },
        files={
            "file": (
                "audiio.mp3",
                make_wav_bytes(),
                "audio/mpeg"
            )
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Audio content does not match its extension"
        )
    }

    assert list(tmp_path.iterdir()) == []

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
