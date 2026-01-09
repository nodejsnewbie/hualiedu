---
inclusion: always
---

# Django Patterns & Best Practices

## Models

### Multi-Tenant (CRITICAL)
- All tenant-scoped models MUST have `tenant` ForeignKey
- **ALWAYS** filter by tenant: `Model.objects.filter(tenant=request.tenant)`
- Middleware sets `request.tenant` and `request.user_profile`
- Never skip tenant filtering

### Conventions
- Use `db_table` in Meta (e.g., `grading_student`)
- Singular names (`Student`, not `Students`)
- Add `created_at`, `updated_at` timestamps
- Use `help_text` on fields
- Define `__str__()` method

### Fields
- `blank=True` for optional, `null=True` only for DB NULL
- Defaults: `default=""` (CharField), `default=0` (numbers)
- Choices as class constants
- `unique_together` or `UniqueConstraint` for composite keys

### Methods
- Business logic: `is_current_semester()`, `can_sync()`
- Path calculation: `get_full_path()`, `get_repo_dir_name()`
- Status checks return boolean
- `@classmethod` for factory methods: `get_value()`, `set_value()`

## Services Layer

- Business logic in `services/`, NOT views
- One service per domain (e.g., `SemesterManager`)
- Stateless or minimal state
- Use dependency injection

### Responsibilities
- Complex business logic
- Multi-model operations/transactions
- External API integrations
- Data transformation/validation

```python
class SemesterManager:
    def __init__(self):
        self.detector = CurrentSemesterDetector()
    
    @handle_semester_exceptions(default_return=None)
    def auto_update_current_semester(self, current_date=None):
        # Business logic
        pass
```

## Views

- Keep thin - delegate to services
- Use decorators: `@login_required`, `@require_http_methods`, `@require_staff_user`
- Separate GET/POST logic clearly

### Validation Pattern
```python
def validate_file_path(file_path, base_dir=None, request=None, repo_id=None):
    """Returns: (is_valid, full_path, error_message)"""
    return True, full_path, None
```

### Responses
- Use helpers: `create_error_response()`, `create_success_response()`
- Support JSON and HTML based on request type
- Check `request.headers.get("X-Requested-With") == "XMLHttpRequest"` for AJAX

### Error Handling
- Validate early, return early
- Log with context before returning
- Use correct HTTP codes (400, 403, 404, 500)
- User-friendly messages

## Admin

- Override `list_display`, `list_filter`, `search_fields`
- Use `readonly_fields` for computed fields
- Custom actions with `format_html()` for buttons
- Add custom URLs with `get_urls()`

### Forms
- ModelForm subclasses for complex validation
- Customize with `widgets`
- Custom Media class for CSS/JS
- `clean()` for cross-field validation

```python
def custom_action(self, obj):
    return format_html(
        '<a class="button" href="{}">Action</a>',
        reverse('admin:app_model_action', args=[obj.pk])
    )
custom_action.short_description = "Action Label"
```

## Middleware

- Sets `request.tenant` and `request.user_profile`
- Auto-creates default tenant/profile for new users
- Helpers: `get_user_tenant()`, `get_user_profile()`
- Decorators: `@require_tenant_admin`, `@require_superuser`

## Database

### Transactions
- `@transaction.atomic` for multi-model operations
- `with transaction.atomic():` for critical updates

### Query Optimization
- `select_related()` for ForeignKey
- `prefetch_related()` for reverse FK and M2M
- Filter at DB level, not Python
- `exists()` instead of `count() > 0`

### Config Pattern
```python
@classmethod
def get_value(cls, key, default=None):
    try:
        return cls.objects.get(key=key).value
    except cls.DoesNotExist:
        return default

@classmethod
def set_value(cls, key, value, description=""):
    config, created = cls.objects.get_or_create(
        key=key, defaults={"value": value, "description": description}
    )
    if not created:
        config.value = value
        config.save()
    return config
```

## Logging

- Module level: `logger = logging.getLogger(__name__)`
- Include context in messages
- Log before raising exceptions
- Levels: DEBUG (diagnostic), INFO (expected), WARNING (unexpected but handled), ERROR (failed)

## File Operations

- Use `os.path.join()` for paths
- Use `os.path.expanduser()` for `~`
- Validate paths within allowed directories (security)

```python
# Security check
if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
    return False, None, "无权访问该文件"

# Existence check
if not os.path.exists(full_path):
    return False, None, "文件不存在"
if not os.access(full_path, os.R_OK):
    return False, None, "无权限读取文件"
```

## Exceptions

- Define in `exceptions.py`
- Use decorators for consistent handling
- Provide context in messages
- Log before re-raising

```python
@handle_semester_exceptions(default_return=None)
def risky_operation(self):
    pass
```

## Testing

- App tests: `<app>/tests/test_*.py`
- Integration: `tests/test_*.py`
- Manual: `scripts/manual_test_*.py`
- Use `TestCase` from `grading/tests/base.py`
- Clean up in `tearDown()`

## URLs

- Lowercase with hyphens: `/student-grades/`
- Name all URLs: `name='grading_repository_clone'`
- Use namespaces: `app_name = 'grading'`
- Reference with `reverse()`: `reverse('admin:grading_repository_clone', args=[pk])`

## Forms

- `clean()` for cross-field validation
- `clean_<fieldname>()` for single field
- Raise `ValidationError` with user-friendly messages
- Customize widgets in Meta.widgets

## Templates

- App: `<app>/templates/<app>/`
- Global: `templates/`
- Admin overrides: `templates/admin/<app>/<model>/`
- Inheritance: `{% extends 'base.html' %}`
- Reference static: `{% static 'grading/css/custom.css' %}`

## Performance

- `select_related()` and `prefetch_related()` for queries
- Index frequently queried fields
- Cache expensive operations
- Profile queries in development
