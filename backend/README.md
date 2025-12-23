# Record Linker Backend

A FastAPI-based backend for matching external data sources to Wikidata entities.

## Setup

1. Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Create `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/recordlinker
SECRET_KEY=your-secret-key-here
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest
pytest --cov=app  # with coverage
```
