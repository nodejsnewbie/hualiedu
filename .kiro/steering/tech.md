---
inclusion: always
---

# Technology Stack & Commands

## Core Stack

- **Python**: 3.13 (conda environment: py313)
- **Django**: 4.2.20
- **Database**: SQLite (dev), PostgreSQL (prod)

## Python Environment (CRITICAL)

**ALL Python commands MUST use conda py313 environment**

```bash
# Correct command format
conda run -n py313 python manage.py <command>

# NEVER use bare python commands
python manage.py <command>  # ❌ WRONG
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

### Django Operations
```bash
# Server
conda run -n py313 python manage.py runserver

# Database
conda run -n py313 python manage.py makemigrations
conda run -n py313 python manage.py migrate

# Testing
conda run -n py313 python manage.py test                           # All tests
conda run -n py313 python manage.py test grading                   # App tests
conda run -n py313 python manage.py test grading.tests.test_models # Specific test

# Code quality
conda run -n py313 black . --line-length=100
conda run -n py313 isort . --profile=black --line-length=100
conda run -n py313 flake8 . --max-line-length=120
```

### Custom Management Commands
```bash
conda run -n py313 python manage.py scan_courses          # Scan course directories
conda run -n py313 python manage.py import_homeworks      # Import homework data
conda run -n py313 python manage.py semester_management   # Manage semesters
conda run -n py313 python manage.py create_templates      # Create semester templates
conda run -n py313 python manage.py update_course_types   # Update course types
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
