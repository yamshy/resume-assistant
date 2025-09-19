# Database Migrations

Migrations are managed with Alembic. Generate new revisions with:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```
