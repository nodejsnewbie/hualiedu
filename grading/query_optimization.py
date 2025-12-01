"""
Query optimization utilities for the grading application.

This module provides helper functions to optimize database queries
using select_related and prefetch_related.
"""

from django.db.models import QuerySet
from grading.models import (
    Repository,
    Submission,
    Course,
    Class,
    Homework,
    CommentTemplate,
    GradeTypeConfig,
    CourseSchedule,
)


def optimize_repository_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize Repository queryset with select_related.
    
    Args:
        queryset: Repository queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'owner',
        'tenant',
        'class_obj',
        'class_obj__course',
        'class_obj__course__teacher',
        'class_obj__course__semester'
    )


def optimize_submission_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize Submission queryset with select_related.
    
    Args:
        queryset: Submission queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'tenant',
        'homework',
        'homework__course',
        'homework__course__teacher',
        'homework__class_obj',
        'student',
        'repository',
        'repository__owner'
    )


def optimize_course_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize Course queryset with select_related.
    
    Args:
        queryset: Course queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'semester',
        'teacher',
        'tenant'
    )


def optimize_class_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize Class queryset with select_related.
    
    Args:
        queryset: Class queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'tenant',
        'course',
        'course__teacher',
        'course__semester'
    )


def optimize_homework_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize Homework queryset with select_related.
    
    Args:
        queryset: Homework queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'tenant',
        'course',
        'course__teacher',
        'course__semester',
        'class_obj'
    )


def optimize_comment_template_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize CommentTemplate queryset with select_related.
    
    Args:
        queryset: CommentTemplate queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'tenant',
        'teacher'
    )


def optimize_grade_type_config_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize GradeTypeConfig queryset with select_related.
    
    Args:
        queryset: GradeTypeConfig queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'tenant',
        'class_obj',
        'class_obj__course'
    )


def optimize_course_schedule_queryset(queryset: QuerySet) -> QuerySet:
    """
    Optimize CourseSchedule queryset with select_related and prefetch_related.
    
    Args:
        queryset: CourseSchedule queryset to optimize
        
    Returns:
        Optimized queryset with related objects prefetched
    """
    return queryset.select_related(
        'course',
        'course__teacher',
        'course__semester'
    ).prefetch_related(
        'week_schedules'
    )


# Convenience functions for common queries

def get_user_repositories_optimized(user, is_active=True):
    """
    Get user's repositories with optimized query.
    
    Args:
        user: User object
        is_active: Filter by active status (default: True)
        
    Returns:
        Optimized queryset of repositories
    """
    queryset = Repository.objects.filter(owner=user)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return optimize_repository_queryset(queryset)


def get_user_courses_optimized(user, semester=None, tenant=None):
    """
    Get user's courses with optimized query.
    
    Args:
        user: User object (teacher)
        semester: Optional semester filter
        tenant: Optional tenant filter
        
    Returns:
        Optimized queryset of courses
    """
    queryset = Course.objects.filter(teacher=user)
    if semester:
        queryset = queryset.filter(semester=semester)
    if tenant:
        queryset = queryset.filter(tenant=tenant)
    return optimize_course_queryset(queryset)


def get_homework_submissions_optimized(homework):
    """
    Get homework submissions with optimized query.
    
    Args:
        homework: Homework object
        
    Returns:
        Optimized queryset of submissions
    """
    queryset = Submission.objects.filter(homework=homework)
    return optimize_submission_queryset(queryset)


def get_course_classes_optimized(course):
    """
    Get course classes with optimized query.
    
    Args:
        course: Course object
        
    Returns:
        Optimized queryset of classes
    """
    queryset = Class.objects.filter(course=course)
    return optimize_class_queryset(queryset)


def get_teacher_comment_templates_optimized(teacher, template_type='personal', limit=5):
    """
    Get teacher's comment templates with optimized query.
    
    Args:
        teacher: User object (teacher)
        template_type: Template type ('personal' or 'system')
        limit: Maximum number of templates to return
        
    Returns:
        Optimized queryset of comment templates
    """
    queryset = CommentTemplate.objects.filter(
        teacher=teacher,
        template_type=template_type
    ).order_by('-usage_count', '-last_used_at')[:limit]
    
    return optimize_comment_template_queryset(queryset)


def get_tenant_comment_templates_optimized(tenant, template_type='system', limit=5):
    """
    Get tenant's comment templates with optimized query.
    
    Args:
        tenant: Tenant object
        template_type: Template type ('personal' or 'system')
        limit: Maximum number of templates to return
        
    Returns:
        Optimized queryset of comment templates
    """
    queryset = CommentTemplate.objects.filter(
        tenant=tenant,
        template_type=template_type,
        teacher__isnull=True  # System templates have no teacher
    ).order_by('-usage_count', '-last_used_at')[:limit]
    
    return optimize_comment_template_queryset(queryset)
