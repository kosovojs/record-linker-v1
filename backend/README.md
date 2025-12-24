# Record Linker Backend

A FastAPI-based backend for matching external data sources to Wikidata entities.

## Development Environment

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and [go-task](https://taskfile.dev/) for automation.

**Important**: Always run development commands via `task` to ensure environment variables from `.env` are correctly loaded.

## Setup

1. Install `uv` and `task` if you haven't already.

2. Create virtual environment and install dependencies:
```bash
uv sync --all-extras
```

3. Create `.env` file (copy from `.env.example` if available, or create manually):
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/recordlinker
SECRET_KEY=your-secret-key-here
```

4. Run migrations:
```bash
task migrate
```

5. Start the server:
```bash
task run
```

## Available Tasks

Run `task --list` to see all available commands. Key commands include:

| Command | Description |
|---------|-------------|
| `task run` | Start the FastAPI server (reloads on change) |
| `task db:migrate` | Upgrade database to latest schema |
| `task db:heads` | Show current migration head(s) |
| `task db:current` | Show current migration status of the DB |
| `task db:history` | Show migration history |
| `task db:rollback` | Rollback the last migration |
| `task test` | Run all tests |
| `task lint` | Check code style with ruff |
| `task format` | Format code with ruff |

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
task test
```
