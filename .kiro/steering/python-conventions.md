---
inclusion: always
---

# Python & Django Conventions

## Naming

- Variables/Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`
- Models: Singular nouns (`Student`, not `Students`)
- URLs: lowercase-with-hyphens (`/student-grades/`)

## Code Formatting

- Black: line length 100
- isort: profile black, line length 100
- flake8: max line length 120
- Run `pre-commit run --all-files` before commits

## Import Order

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party Django
from django.db import models
from django.contrib.auth.models import User

# 3. Third-party other
from rest_framework import serializers

# 4. Local app
from grading.models import Student
from grading.services.semester_manager import SemesterManager
```

## Documentation

- Use type hints for parameters and return values
- Document public functions with docstrings
- Include Args, Returns, Raises sections

```python
def calculate_grade(submission: Submission, rubric: dict) -> float:
    """Calculate grade for submission.
    
    Args:
        submission: Student submission to grade
        rubric: Grading criteria
        
    Returns:
        Grade as float (0-100)
        
    Raises:
        ValueError: If rubric invalid
    """
```

## Django Patterns

- Business logic in `services/`, not views
- Always filter by `tenant` in queries
- Never edit existing migrations
- Use Django logger, not print()
- Access settings via `django.conf.settings`

## Error Handling

- Use custom exceptions from `grading/exceptions.py`
- Catch specific exceptions, not bare `except:`
- Log errors with context before re-raising
- Return user-friendly error messages
