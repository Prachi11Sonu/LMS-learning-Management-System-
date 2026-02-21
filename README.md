EduFlow - Learning Management System

A comprehensive full-stack Learning Management System built with Django, featuring role-based access for students and instructors, course management, interactive quizzes, and real-time analytics.


Features


For Students 

Course Enrollment - Browse and enroll in courses
Interactive Learning - Access lessons with video content and resources
Quiz System - Take MCQ quizzes with automatic grading
Progress Tracking - Track course completion and quiz scores
Reviews & Ratings - Rate courses and instructors

For Instructors 

Course Creation - Create and manage courses with lessons
Content Management - Upload videos, PDFs, and resources
Quiz Builder - Create MCQ quizzes with multiple questions
Student Analytics - Track student progress and performance
Review Management - View and respond to student reviews
Performance Dashboard - Real-time analytics on course metrics

Technology Stack

Backend

Python 3.12 - Core programming language
Django 6.0 - Web framework
PostgreSQL - Database
Django ORM - Database abstraction

Frontend

HTML5/CSS3 - Structure and styling
JavaScript - Interactive elements
Tailwind CSS - Utility-first styling (custom implementation)

Additional Tools

Git - Version control
Pillow - Image processing
Django Debug Toolbar - Development debugging

Prerequisites

Python 3.12 or higher
PostgreSQL 15 or higher
pip (Python package manager)
Git

Installation

1. Clone the Repository

git clone https://github.com/kumarayush07ak/LMS-learning-Management-System-

2. Create Virtual Environment

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Database Setup

Create a PostgreSQL database:
CREATE DATABASE learning;

5. Run Migrations

python manage.py makemigrations accounts
python manage.py makemigrations courses
python manage.py makemigrations enrollments
python manage.py makemigrations quizzes
python manage.py migrate

6. Create Superuser

python manage.py createsuperuser

7. Run Development Server

python manage.py runserver
Visit http://127.0.0.1:8000 to access the application.

Key Modules

1. User Management (accounts)

Registration and authentication
Role-based access (Student/Instructor)
Profile management

2. Course Management (courses)

Course creation and editing
Lesson organization
File uploads (PDFs, images)
Progress tracking
Reviews and ratings

3. Enrollment System (enrollments)

Course enrollment
Progress tracking
Wishlist functionality

4. Quiz System (quizzes)

MCQ quiz creation
Automatic grading
Attempt tracking
Performance analytics

Usage Guide

For Students

Register as a student
Browse available courses
Enroll in courses
Access lessons and complete quizzes
Track progress in dashboard
Leave reviews for completed courses

For Instructors

Register as an instructor
Create new courses
Add lessons with content
Create quizzes for lessons
Monitor student progress
View analytics dashboard

Database Schema

Key Models:

User - Custom user model with roles
Course - Course information and metadata
Lesson - Course lessons and content
Enrollment - Student course enrollments
Quiz - Quiz details and settings
Question - MCQ questions
QuizAttempt - Student quiz attempts
CourseReview - Student course reviews

Security Features

Password hashing with Django's built-in system
CSRF protection
SQL injection prevention via ORM
XSS protection in templates
Role-based access control
Secure file upload validation

