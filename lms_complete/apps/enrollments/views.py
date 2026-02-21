from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.core.paginator import Paginator
from .models import Enrollment
from apps.courses.models import Course


from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from apps.courses.models import Course
from .models import Enrollment


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, status='published')

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('courses:course_detail', slug=course.slug)

    try:
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course
        )

        # ==============================
        # ✅ EMAIL TO STUDENT
        # ==============================
        student_subject = f"You have enrolled in {course.title} 🎉"
        student_message = f"""
Hi {request.user.get_full_name()},

Congratulations! 🎉

You have successfully enrolled in the course:

Course Title: {course.title}
Instructor: {course.instructor.get_full_name()}
Category: {course.category.name if hasattr(course, 'category') else 'N/A'}

Start learning and enjoy your journey!

Best Regards,
Portal Team
"""

        send_mail(
            student_subject,
            student_message,
            settings.EMAIL_HOST_USER,
            [request.user.email],
            fail_silently=False,
        )

        # ==============================
        # ✅ EMAIL TO INSTRUCTOR
        # ==============================
        instructor_subject = f"New Student Enrolled in {course.title} 🚀"
        instructor_message = f"""
Hi {course.instructor.get_full_name()},

A new student has enrolled in your course!

Student Name: {request.user.get_full_name()}
Student Email: {request.user.email}
Course: {course.title}

Keep inspiring and teaching! 🚀

Best Regards,
Portal Team
"""

        send_mail(
            instructor_subject,
            instructor_message,
            settings.EMAIL_HOST_USER,
            [course.instructor.email],
            fail_silently=False,
        )

        messages.success(request, f'Successfully enrolled in {course.title}!')

    except IntegrityError:
        messages.error(request, 'An error occurred during enrollment.')

    return redirect('courses:course_detail', slug=course.slug)




@login_required
def my_enrollments(request):
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course').order_by('-enrolled_at')
    
    paginator = Paginator(enrollments, 6)
    page = request.GET.get('page')
    enrollments = paginator.get_page(page)
    
    return render(request, 'enrollments/my_enrollments.html', {
        'enrollments': enrollments
    })


@login_required
def update_progress(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    
    if request.method == 'POST':
        enrollment.update_progress()
        messages.success(request, 'Progress updated!')
    
    return redirect('enrollments:my_enrollments')