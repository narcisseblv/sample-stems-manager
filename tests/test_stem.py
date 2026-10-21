from io import BytesIO
from pathlib import Path
import wave

import pytest
from fastapi.testclient import TestClient

def make_wav_bytes() -> bytes:
    buffer = BytesIO()

    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 8000)

    return buffer.getvalue()

def create_parent_sample(
    client: TestClient
) -> int:
    response = client.post(
        "/samples",
        json={
            "name": "Vaporwav Track",
            "file_path": "data/vaporwave-track.wav",
            "bpm": 95,
            "musical_key": "F# minor",
            "category": "Vaporwave"
        }
    )

    assert response.status_code == 201

    return response.json()["id"]

def upload_stem(
    client: TestClient,
    sample_id: int,
    *,
    name: str = "Lead Vocals",
    stem_type: str = "vocals"
):
    return client.post(
        f"/samples/{sample_id}/stems/upload",
        data={
            "name": name,
            "stem_type": stem_type
        },
        files={
            "file": (
                "stem.wav",
                make_wav_bytes(),
                "audio/wav"
            )
        }
    )

def test_upload_stem(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.stem_routes.STEM_UPLOAD_DIR",
        tmp_path
    )

    sample_id = create_parent_sample(client)
    response = upload_stem(client, sample_id)

    assert response.status_code == 201

    stem = response.json()

    assert stem["id"] == 1
    assert stem["name"] == "Lead Vocals"
    assert stem["stem_type"] == "vocals"
    assert stem["sample_id"] == sample_id

    stored_path = Path(stem["file_path"])

    assert stored_path.exists()
    assert stored_path.parent == tmp_path
    assert stored_path.suffix == ".wav"

def test_upload_stem_for_missing_sample(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.stem_routes.STEM_UPLOAD_DIR",
        tmp_path
    )

    response = upload_stem(
        client,
        sample_id=999
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Sample not found"
    }

    assert list(tmp_path.iterdir()) == []

def test_get_sample_stems(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.stem_routes.STEM_UPLOAD_DIR",
        tmp_path
    )

    sample_id = create_parent_sample(client)

    first_response = upload_stem(
        client,
        sample_id,
        name="Lead Vocals",
        stem_type="vocals"
    )

    second_response = upload_stem(
        client,
        sample_id,
        name="Bass Stem",
        stem_type="bass"
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        f"/samples/{sample_id}/stems"
    )

    assert response.status_code == 200

    stems = response.json()

    assert len(stems) == 2
    assert stems[0]["name"] == "Lead Vocals"
    assert stems[0]["stem_type"] == "vocals"
    assert stems[1]["name"] == "Bass Stem"
    assert stems[1]["stem_type"] == "bass"

    assert all(
        stem["sample_id"] == sample_id
        for stem in stems
    )

    stem_id = stems[0]["id"]
    stem_response = client.get(
        f"/stems/{stem_id}"
    )

    assert stem_response.status_code == 200
    assert stem_response.json() == stems[0]

def test_download_stem_audio(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.stem_routes.STEM_UPLOAD_DIR",
        tmp_path
    )

    sample_id = create_parent_sample(client)
    audio_content = make_wav_bytes()

    upload_response = client.post(
        f"/samples/{sample_id}/stems/upload",
        data={
            "name": "Drum Stem",
            "stem_type": "drums"
        },
        files={
            "file": (
                "drums.wav",
                audio_content,
                "audio_wav"
            )
        }
    )

    assert upload_response.status_code == 201

    stem_id = upload_response.json()["id"]
    response = client.get(
        f"/stems/{stem_id}/audio"
    )

    assert response.status_code == 200
    assert response.content == audio_content
    assert response.headers["content-type"] == "audio/wav"

def test_delete_stem_removes_audio_file(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sample_manager.stem_routes.STEM_UPLOAD_DIR",
        tmp_path
    )

    sample_id = create_parent_sample(client)
    upload_response = upload_stem(
        client,
        sample_id
    )

    assert upload_response.status_code == 201

    stem = upload_response.json()
    stem_id = stem["id"]
    stored_path = Path(stem["file_path"])

    assert stored_path.exists()

    delete_response = client.delete(
        f"/stems/{stem_id}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert not stored_path.exists()

    get_response = client.get(
        f"/stems/{stem_id}"
    )

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Stem not found"
    }

    def test_rejects_invalid_stem_audio(
        client: TestClient,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "sample_manager.stem_routes.STEM_UPLOAD_DIR",
            tmp_path
        )
        sample_id = create_parent_sample(client)
        response = client.post(
            f"/samples/{sample_id}/stems/upload",
            data={
                "name": "Fake Stem",
                "stem_type": "vocals"
            },
            files={
                "file": (
                    "fake.wav",
                    b"this is not a real wav file",
                    "audio/wav"
                )
            }
        )

def test_get_missing_stem(
    client: TestClient
) -> None:
    response = client.get("/stems/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Stem not found"
    }

def test_get_stems_for_missing_sample(
    client: TestClient
) -> None:
    response = client.get(
        "/samples/999/stems"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Sample not found"
    }

    def test_rejects_unsupported_stem_file(
        client: TestClient
    ) -> None:
        sample_id = create_parent_sample(client)
        response = client.post(
            f"/samples/{sample_id}/stems/upload",
            data={
                "name": "Document",
                "stem_type": "unknown"
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