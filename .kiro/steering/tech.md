---
inclusion: always
---

# Technology Stack & Commands

## Core Stack

- **Python**: 3.13 (managed by uv)
- **Django**: 4.2.20
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Package Manager**: uv (fast Python package installer)

## Python Environment (CRITICAL)

**ALL Python commands MUST use uv**

```bash
# Correct command format
uv run python manage.py <command>

# NEVER use bare python commands
python manage.py <command>  # ❌ WRONG
conda run -n py313 python manage.py <command>  # ❌ OLD (deprecated)
```

## Key Dependencies

- **django-jazzmin** 3.0.1 - Enhanced admin UI
- **volcengine** 1.0.206 - AI grading SDK
- **GitPython** 3.1.45 - Git operations
- **python-docx** 1.2.0, **openpyxl** 3.1.5, **pandas** 2.3.3 - Document processing

## Code Quality Tools

- **black** (line length: 100)
- **isort** (profile: black, line length: 100)
- **flake8** (max line length: 120)
- **pre-commit** - Run before commits

## Essential Commands

### Environment Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (including dev dependencies)
uv sync --all-extras

# Or use Makefile
make install
```

### Django Operations
```bash
# Server
uv run python manage.py runserver

# Database
uv run python manage.py makemigrations
uv run python manage.py migrate

# Testing
uv run python manage.py test                           # All tests
uv run python manage.py test grading                   # App tests
uv run python manage.py test grading.tests.test_models # Specific test

# Code quality
uv run black . --line-length=100
uv run isort . --profile=black --line-length=100
uv run flake8 . --max-line-length=120

# Or use Makefile (recommended)
make test
make runserver
make migrate
make format
```

### Custom Management Commands
```bash
uv run python manage.py scan_courses          # Scan course directories
uv run python manage.py import_homeworks      # Import homework data
uv run python manage.py semester_management   # Manage semesters
uv run python manage.py create_templates      # Create semester templates
uv run python manage.py update_course_types   # Update course types
uv run python manage.py clear_cache           # Clear cache
```

## Configuration

### Environment Variables (.env)
- `SECRET_KEY` - Django secret (NEVER commit)
- `DEBUG` - True/False
- `ALLOWED_HOSTS` - Comma-separated
- `LOG_LEVEL` - INFO, DEBUG, ERROR
- `MAX_UPLOAD_SIZE` - Bytes
- Volcengine API keys for AI grading

### File Locations
- Static: `static/` (dev), `staticfiles/` (prod)
- Media: `media/` (assignments, grades, ssh_keys)
- Logs: `logs/app.log`
- Database: `db.sqlite3` (dev)
