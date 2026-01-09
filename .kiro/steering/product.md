---
inclusion: always
---

# Product Overview

Multi-tenant educational platform for assignment management, grading, and course administration.

## Core Features

- **AI-Powered Grading** - Volcengine Ark SDK
- **Multi-Tenant** - Isolated data per institution
- **Repository Management** - Git repos or local directories
- **Semester Management** - Auto-detection, status tracking
- **Batch Processing** - Bulk grading and documents
- **Course Scheduling** - Week-by-week schedules

## Domain Model

### Entities
- **Tenant** - Institution with isolated config/data
- **Repository** - Student submissions (Git URL + branch OR local path)
- **Submission** - Student work with grades and comments
- **Semester** - Academic term (auto-created from templates)
- **Course** - Class with schedules, homework, roster
- **Homework** - Assignment (normal or lab report)

### Relationships
- Tenant → UserProfile, Repository, Submission, GradeTypeConfig
- User → UserProfile, Repository, Course
- Semester → Course, SemesterTemplate
- Course → CourseSchedule, Homework
- Repository → Submission

## User Roles

- **Super Admin** - Global config, tenant management
- **Tenant Admin** - Institution administration
- **Teacher** - Course management, grading

## Business Rules

- **ALWAYS filter by tenant** - Data isolation critical
- Repositories: Git (URL + branch) OR local (file path)
- Semesters auto-create from templates by date
- Homework types affect grading workflow
