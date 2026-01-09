"""
Backfill migration to ensure grading_tenant.tenant_repo_dir exists.

The original AddField migration was faked in some environments, leaving the
column absent while the ORM still expects it, which triggers
OperationalError: no such column: grading_tenant.tenant_repo_dir.
"""

from django.db import migrations


def add_tenant_repo_dir_column(apps, schema_editor):
    table_name = "grading_tenant"
    column_name = "tenant_repo_dir"
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
        existing_columns = [col.name for col in description]

    if column_name in existing_columns:
        return

    column_sql = "VARCHAR(255) NOT NULL DEFAULT ''"
    quoted_table = schema_editor.quote_name(table_name)
    quoted_column = schema_editor.quote_name(column_name)

    schema_editor.execute(f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} {column_sql}")


class Migration(migrations.Migration):

    dependencies = [
        ("grading", "0021_add_defaults_to_submission"),
    ]

    operations = [
        migrations.RunPython(add_tenant_repo_dir_column, migrations.RunPython.noop),
    ]
