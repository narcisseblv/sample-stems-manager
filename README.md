# Sample & Stems Manager

Sample & Stems Manager is a FastAPI backend application for managing audio
samples and their associated stems.

The API allows users to upload audio files, extract metadata, search and filter
samples, download audio files, and manage stems linked to each sample.

## Features

- Create, retrieve, update, and delete samples
- Upload WAV and MP3 audio files
- Extract audio metadata automatically
- Download sample audio files
- Filter samples by name, category, musical key, and BPM
- Paginate sample results with `offset` and `limit`
- Upload and manage stems linked to a sample
- Download and delete stem audio files
- Validate audio extensions, formats, paths, and file sizes
- Store application data in SQLite
- Manage the database schema with Alembic migrations
- Configure the application with environment variables
- Test API endpoints with Pytest
- Explore the API through Swagger UI

## Project structure

```text
sample-stems-manager/
├── migrations/
│   ├── versions/
│   └── env.py
├── src/
│   └── sample_manager/
│       ├── __init__.py
│       ├── audio_files.py
│       ├── config.py
│       ├── database.py
│       ├── db_models.py
│       ├── main.py
│       ├── models.py
│       ├── routes.py
│       └── stem_routes.py
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_migrations.py
│   ├── test_sample.py
│   └── test_stem.py
├── uploads/
│   └── .gitkeep
├── .env.example
├── .gitignore
├── alembic.ini
├── pyproject.toml
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/sample-stems-manager.git
cd sample-stems-manager
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

On macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 4. Install the project and development dependencies

```bash
python -m pip install --editable ".[dev]"
```

## Environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Default configuration:

```env
DATABASE_URL=sqlite:///./samples.db
UPLOAD_DIR=uploads
```

Available variables:

| Variable | Description | Default value |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection URL | `sqlite:///./samples.db` |
| `UPLOAD_DIR` | Directory used to store uploaded audio files | `uploads` |
The real `.env` file is ignored by Git. Only `.env.example` should be committed.

## Environment variable

Copy the example environment file:

```bash
cp .env.example .env
```

Default configuration:

```env
DATABASE_URL=sqlite:///./samples.db
UPLOAD_DIR=uploads
```

Available variables:

| Variable | Description | Default value |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection URL | `sqlite:///./samples.db` |
| `UPLOAD_DIR` | Directory used to store uploaded audio files | `uploads` |

The real `.env` file is ignored by Git. Only `.env.example` should be committed.

## Database migrations

Create or update the database schema by running:

```bash
python -m alembic upgrade head
```

Display the migration history:

```bash
python -m alembic history
```

Display the current database revision:

```bash
python -m alembic current
```

Display the latest available revision:

```bash
python -m alembic heads
```

To generate a new migration after modifying the SQLAlchemy models:

```bash
python -m alembic revision --autogenerate -m "Describe the database change"
```

Then apply it:

```bash
python -m alembic upgrade head
```

## Running the application

Start the development server:

```bash
python -m uvicorn sample_manager.main:app --reload
```

The API is then available at:

```text
http://127.0.0.1:8000
```

Check the application health:

```bash
curl http://127.0.0.1:8000/health
```

## API documentation

Once the server is running, open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

The OpenAPI schema is available at:

```text
http://127.0.0.1:8000/openapi.json
```

## API examples

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Create a sample

```bash
curl -X POST http://127.0.0.1:8000/samples \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vaporwave Pad",
    "file_path": "data/vaporwave-pad.wav",
    "bpm": 90,
    "musical_key": "F# minor",
    "category": "pad"
  }'
```

### Upload an audio sample

```bash
curl -X POST http://127.0.0.1:8000/samples/upload \
  -F "name=Vaporwave Pad" \
  -F "category=pad" \
  -F "bpm=90" \
  -F "musical_key=F# minor" \
  -F "file=@/absolute/path/to/sample.wav"
```

### List samples

```bash
curl http://127.0.0.1:8000/samples
```

### Filter samples

```bash
curl "http://127.0.0.1:8000/samples?category=pad&min_bpm=80&max_bpm=100"
```

### Paginate samples

```bash
curl "http://127.0.0.1:8000/samples?offset=0&limit=10"
```

### Get one sample

```bash
curl http://127.0.0.1:8000/samples/1
```

### Update a sample

```bash
curl -X PATCH http://127.0.0.1:8000/samples/1 \
  -H "Content-Type: application/json" \
  -d '{
    "bpm": 95
  }'
```

### Download sample audio

```bash
curl http://127.0.0.1:8000/samples/1/audio \
  --output sample.wav
```

### Delete a sample

```bash
curl -X DELETE http://127.0.0.1:8000/samples/1
```

### Upload a stem

```bash
curl -X POST http://127.0.0.1:8000/samples/1/stems/upload \
  -F "name=Lead Vocals" \
  -F "stem_type=vocals" \
  -F "file=@/absolute/path/to/vocals.wav"
```

### List the stems of a sample

```bash
curl http://127.0.0.1:8000/samples/1/stems
```

### Get one stem

```bash
curl http://127.0.0.1:8000/stems/1
```

### Download stem audio

```bash
curl http://127.0.0.1:8000/stems/1/audio \
  --output stem.wav
```

### Delete a stem

```bash
curl -X DELETE http://127.0.0.1:8000/stems/1
```

## Tests

Run the complete test suite:

```bash
python -m pytest -v
```

Run only the sample endpoint tests:

```bash
python -m pytest tests/test_sample.py -v
```

Run only the stem endpoint tests:

```bash
python -m pytest tests/test_stem.py -v
```

Run the migration test:

```bash
python -m pytest tests/test_migrations.py -v
```
