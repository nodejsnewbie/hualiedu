#!/usr/bin/env python
"""
Database Structure Verification Script

This script verifies that all database migrations have been applied correctly
and that the database structure matches the expected schema for the homework
grading system.

Usage:
    conda run -n py313 python scripts/verify_database_structure.py
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Django setup
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hualiEdu.settings")
django.setup()

from django.db import connection


def verify_table_exists(cursor, table_name):
    """Verify that a table exists in the database."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    result = cursor.fetchone()
    return result is not None


def verify_column_exists(cursor, table_name, column_name):
    """Verify that a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    return column_name in column_names


def verify_index_exists(cursor, index_name):
    """Verify that an index exists in the database."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,)
    )
    result = cursor.fetchone()
    return result is not None


def main():
    """Main verification function."""
    print("=" * 80)
    print("Database Structure Verification")
    print("=" * 80)

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    all_passed = True

    # Verify core tables exist
    print("\n1. Verifying Core Tables...")
    required_tables = [
        "grading_course",
        "grading_class",
        "grading_repository",
        "grading_homework",
        "grading_submission",
        "grading_grade_type_config",
        "grading_comment_template",
    ]

    for table in required_tables:
        exists = verify_table_exists(cursor, table)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
        if not exists:
            all_passed = False

    # Verify Course model fields
    print("\n2. Verifying Course Model Fields...")
    course_fields = [
        ("teacher_id", "Teacher foreign key"),
        ("course_type", "Course type field"),
        ("description", "Description field"),
        ("tenant_id", "Tenant foreign key"),
    ]

    for field, description in course_fields:
        exists = verify_column_exists(cursor, "grading_course", field)
        status = "✓" if exists else "✗"
        print(f"  {status} {field} - {description}")
        if not exists:
            all_passed = False

    # Verify Class model
    print("\n3. Verifying Class Model...")
    class_fields = [
        ("name", "Class name"),
        ("student_count", "Student count"),
        ("course_id", "Course foreign key"),
        ("tenant_id", "Tenant foreign key"),
    ]

    for field, description in class_fields:
        exists = verify_column_exists(cursor, "grading_class", field)
        status = "✓" if exists else "✗"
        print(f"  {status} {field} - {description}")
        if not exists:
            all_passed = False

    # Verify Repository model fields
    print("\n4. Verifying Repository Model Fields...")
    repo_fields = [
        ("repo_type", "Repository type (git/filesystem)"),
        ("git_url", "Git URL"),
        ("git_branch", "Git branch"),
        ("git_username", "Git username"),
        ("git_password", "Git password"),
        ("filesystem_path", "Filesystem path"),
        ("allocated_space_mb", "Allocated space"),
        ("class_obj_id", "Class foreign key"),
    ]

    for field, description in repo_fields:
        exists = verify_column_exists(cursor, "grading_repository", field)
        status = "✓" if exists else "✗"
        print(f"  {status} {field} - {description}")
        if not exists:
            all_passed = False

    # Verify Homework model fields
    print("\n5. Verifying Homework Model Fields...")
    homework_fields = [
        ("homework_type", "Homework type (normal/lab_report)"),
        ("class_obj_id", "Class foreign key"),
        ("folder_name", "Folder name"),
    ]

    for field, description in homework_fields:
        exists = verify_column_exists(cursor, "grading_homework", field)
        status = "✓" if exists else "✗"
        print(f"  {status} {field} - {description}")
        if not exists:
            all_passed = False

    # Verify Submission model fields
    print("\n6. Verifying Submission Model Fields...")
    submission_fields = [
        ("homework_id", "Homework foreign key"),
        ("student_id", "Student foreign key"),
        ("version", "Version number"),
        ("file_size", "File size"),
    ]

    for field, description in submission_fields:
        exists = verify_column_exists(cursor, "grading_submission", field)
        status = "✓" if exists else "✗"
        print(f"  {status} {field} - {description}")
        if not exists:
            all_passed = False

    # Verify GradeTypeConfig model fields
    print("\n7. Verifying GradeTypeConfig Model Fields...")
    grade_config_fields = [
        ("grade_type", "Grade type (letter/text/percentage)"),
        ("class_obj_id", "Class foreign key"),
    ]

    for field, description in grade_config_fields:
        exists = verify_column_exists(cursor, "grading_grade_type_config", field)
        status = "✓" if exists else "✗"
        print(f"  {status} {field} - {description}")
        if not exists:
            all_passed = False

    # Verify CommentTemplate model
    print("\n8. Verifying CommentTemplate Model...")
    comment_fields = [
        ("template_type", "Template type (personal/system)"),
        ("comment_text", "Comment text"),
        ("usage_count", "Usage count"),
        ("teacher_id", "Teacher foreign key"),
        ("tenant_id", "Tenant foreign key"),
    ]

    for field, description in comment_fields:
        exists = verify_column_exists(cursor, "grading_comment_template", field)
        status = "✓" if exists else "✗"
        print(f"  {status} {field} - {description}")
        if not exists:
            all_passed = False

    # Verify indexes
    print("\n9. Verifying Indexes...")
    required_indexes = [
        ("grading_sub_homewor_27ae80_idx", "Submission homework/student index"),
        ("grading_com_teacher_725d54_idx", "Comment template teacher index"),
        ("grading_com_tenant__6d6cbf_idx", "Comment template tenant index"),
    ]

    for index, description in required_indexes:
        exists = verify_index_exists(cursor, index)
        status = "✓" if exists else "✗"
        print(f"  {status} {index} - {description}")
        if not exists:
            all_passed = False

    conn.close()

    # Final result
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ All database structure verifications PASSED")
        print("=" * 80)
        return 0
    else:
        print("✗ Some database structure verifications FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
