from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Course, Category, Lesson, LessonFile, LessonFolder, FolderFile, CourseReview, InstructorReview, ReviewHelpful
from .forms import LessonForm
from .review_forms import CourseReviewForm, InstructorReviewForm
from apps.enrollments.models import Enrollment
from apps.accounts.models import User
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings

class InstructorRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to instructors only"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_instructor


class CourseListView(ListView):
    """List all published courses with filtering"""
    model = Course
    template_name = 'courses/courses_list.html'
    context_object_name = 'courses'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = Course.objects.filter(status='published').select_related('instructor', 'category')
        
        # Search functionality
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )
        
        # Filter by category
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by level
        level = self.request.GET.get('level', '')
        if level:
            queryset = queryset.filter(level=level)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(course_count=Count('courses'))
        context['levels'] = Course.LEVEL_CHOICES
        return context


class CourseDetailView(DetailView):
    """Display course details"""
    model = Course
    template_name = 'courses/courses_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Check if user is enrolled
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                course=course
            ).exists()

            if context['is_enrolled'] and self.request.user.is_student:
                from .models import InstructorReview
                context['has_reviewed_instructor'] = InstructorReview.objects.filter(
                    instructor=course.instructor,
                    student=self.request.user,
                    course=course
                ).exists()
            else:
                context['has_reviewed_instructor'] = True
        

        
        # Get lessons with file counts
        lessons = course.lessons.all().order_by('order')
        for lesson in lessons:
            lesson.files_count = LessonFile.objects.filter(lesson=lesson).count()
        
        context['lessons'] = lessons
        context['total_duration'] = sum(lesson.duration_minutes for lesson in lessons)
        
        return context


# class CourseCreateView(LoginRequiredMixin, InstructorRequiredMixin, CreateView):
#     """Create a new course"""
#     model = Course
#     template_name = 'courses/courses_form.html'
#     fields = ['title', 'description', 'short_description', 'category', 'level', 
#               'thumbnail', 'price', 'is_free', 'status']
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['categories'] = Category.objects.all()
#         return context
    
#     def form_valid(self, form):
#         form.instance.instructor = self.request.user
#         messages.success(self.request, 'Course created successfully!')
#         return super().form_valid(form)
    
#     def get_success_url(self):
#         # FIXED: Changed from 'courses_detail' to 'course_detail' to match urls.py
#         return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})

class CourseCreateView(LoginRequiredMixin, InstructorRequiredMixin, CreateView):
    """Create a new course"""
    model = Course
    template_name = 'courses/courses_form.html'
    fields = ['title', 'description', 'short_description', 'category', 'level', 
              'thumbnail', 'price', 'is_free', 'status']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        response = super().form_valid(form)

        # ✅ Send email to instructor
        subject = "Course Created Successfully 🎉"
        message = f"""
Hi {self.request.user.get_full_name()},

Your course "{self.object.title}" has been created successfully.

You can now manage and publish it from your dashboard.

Thank you for teaching with us!
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.request.user.email],
            fail_silently=False,
        )

        messages.success(self.request, 'Course created successfully! Email notification sent.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})
    

class CourseUpdateView(LoginRequiredMixin, InstructorRequiredMixin, UpdateView):
    """Update an existing course"""
    model = Course
    template_name = 'courses/courses_form.html'
    fields = ['title', 'description', 'short_description', 'category', 'level', 
              'thumbnail', 'price', 'is_free', 'status']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context
    
    def get_queryset(self):
        # Instructors can only edit their own courses
        return Course.objects.filter(instructor=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Course updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        # FIXED: Changed from 'courses_detail' to 'course_detail' to match urls.py
        return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})

class CourseDeleteView(LoginRequiredMixin, InstructorRequiredMixin, DeleteView):
    """Delete a course (instructor only)"""
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course_list')
    
    def get_queryset(self):
        # Instructors can only delete their own courses
        return Course.objects.filter(instructor=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, f'Course "{course.title}" has been deleted successfully.')
        return super().delete(request, *args, **kwargs)
    

@login_required
def lesson_detail(request, course_slug, lesson_id):
    """Display lesson content with access control"""
    lesson = get_object_or_404(Lesson, course__slug=course_slug, id=lesson_id)
    course = lesson.course
    
    # Check access permissions
    can_access = False
    is_enrolled = False
    
    # Case 1: Lesson is free preview - anyone can access
    if lesson.is_free_preview:
        can_access = True
    
    # Case 2: User is authenticated
    elif request.user.is_authenticated:
        # Check enrollment - DO THIS FIRST
        is_enrolled = Enrollment.objects.filter(
            student=request.user,
            course=course
        ).exists()
        
        print(f"DEBUG - User: {request.user.email}")
        print(f"DEBUG - Course: {course.title}")
        print(f"DEBUG - Is enrolled: {is_enrolled}")
        
        # Case 2a: User is the instructor of this course
        if request.user.is_instructor and course.instructor == request.user:
            can_access = True
        
        # Case 2b: User is admin
        elif request.user.is_admin_user:
            can_access = True
        
        # Case 2c: User is a student enrolled in the course
        elif is_enrolled:
            can_access = True
    
    if not can_access:
        messages.error(request, 'Please enroll in this course to access this lesson.')
        return redirect('courses:course_detail', slug=course_slug)
    
    # Get all lessons for the sidebar
    all_lessons = list(course.lessons.all().order_by('order'))
    
    # Find current lesson index
    current_index = None
    for i, l in enumerate(all_lessons):
        if l.id == lesson.id:
            current_index = i
            break
    
    # Get next and previous lessons
    next_lesson = all_lessons[current_index + 1] if current_index is not None and current_index < len(all_lessons) - 1 else None
    prev_lesson = all_lessons[current_index - 1] if current_index is not None and current_index > 0 else None
    
    # Check which lessons are accessible for the sidebar
    accessible_lessons = []
    for l in all_lessons:
        l_accessible = (
            l.is_free_preview or 
            (request.user.is_authenticated and (
                (request.user.is_instructor and course.instructor == request.user) or
                request.user.is_admin_user or
                Enrollment.objects.filter(student=request.user, course=course).exists()
            ))
        )
        accessible_lessons.append({
            'lesson': l,
            'accessible': l_accessible
        })
    
    # Get file count for the resources button
    files_count = LessonFile.objects.filter(lesson=lesson).count()
    
    # IMPORTANT: Force refresh the enrollment check
    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).exists()
    
    print(f"FINAL DEBUG - Is enrolled: {is_enrolled}")
    
    context = {
        'lesson': lesson,
        'course': course,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
        'all_lessons': all_lessons,
        'accessible_lessons': accessible_lessons,
        'current_index': current_index + 1 if current_index is not None else 1,
        'files_count': files_count,
        'is_enrolled': is_enrolled,  # Make sure this is passed
    }
    
    return render(request, 'courses/lesson_detail.html', context)


@login_required
def manage_lessons(request, course_id):
    """Manage lessons for a course (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to manage lessons for this course.')
        # FIXED: Changed from 'courses_detail' to 'course_detail'
        return redirect('courses:course_detail', slug=course.slug)
    
    lessons = course.lessons.all().order_by('order')
    
    return render(request, 'courses/manage_lessons.html', {
        'course': course,
        'lessons': lessons
    })


@login_required
def lesson_create(request, course_id):
    """Create a new lesson (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to add lessons to this course.')
        # FIXED: Changed from 'courses_detail' to 'course_detail'
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, 'Lesson created successfully!')
            return redirect('courses:manage_lessons', course_id=course.id)
    else:
        form = LessonForm()
    
    return render(request, 'courses/lesson_form.html', {
        'form': form,
        'course': course
    })


@login_required
def lesson_edit(request, course_id, lesson_id):
    """Edit an existing lesson (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to edit this lesson.')
        # FIXED: Changed from 'courses_detail' to 'course_detail'
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lesson updated successfully!')
            return redirect('courses:manage_lessons', course_id=course.id)
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'courses/lesson_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson
    })


@login_required
def lesson_delete(request, course_id, lesson_id):
    """Delete a lesson (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to delete this lesson.')
        # FIXED: Changed from 'courses_detail' to 'course_detail'
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lesson deleted successfully!')
        return redirect('courses:manage_lessons', course_id=course.id)
    
    return render(request, 'courses/lesson_confirm_delete.html', {
        'lesson': lesson
    })


@login_required
def course_students(request, course_id):
    """View all students enrolled in a course (instructor only)"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to view this page.')
        # FIXED: Changed from 'courses_detail' to 'course_detail'
        return redirect('courses:course_detail', slug=course.slug)
    
    enrollments = Enrollment.objects.filter(course=course).select_related('student').order_by('-enrolled_at')
    
    # Pagination
    paginator = Paginator(enrollments, 20)
    page = request.GET.get('page')
    enrollments = paginator.get_page(page)
    
    # Statistics
    total_students = enrollments.paginator.count
    completed_count = enrollments.paginator.object_list.filter(status='completed').count()
    in_progress_count = enrollments.paginator.object_list.filter(status='in_progress').count()
    
    return render(request, 'courses/course_students.html', {
        'course': course,
        'enrollments': enrollments,
        'total_students': total_students,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
    })


@login_required
def lesson_files(request, lesson_id):
    """View and manage lesson files"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check access
    can_access = False
    if request.user.is_authenticated:
        # Instructors and admins can always access
        if (request.user.is_instructor and course.instructor == request.user) or request.user.is_admin_user:
            can_access = True
        # Students need to be enrolled
        else:
            can_access = Enrollment.objects.filter(
                student=request.user,
                course=course
            ).exists()
    
    if not can_access:
        messages.error(request, 'You do not have access to these resources.')
        # FIXED: Changed from 'courses_detail' to 'course_detail'
        return redirect('courses:course_detail', slug=course.slug)
    
    files = LessonFile.objects.filter(lesson=lesson).order_by('-created_at')
    folders = LessonFolder.objects.filter(lesson=lesson).prefetch_related('files').order_by('name')
    
    return render(request, 'courses/lesson_file.html', {
        'lesson': lesson,
        'course': course,
        'files': files,
        'folders': folders,
    })


@login_required
def upload_lesson_file(request, lesson_id):
    """Upload a file to a lesson (instructor only)"""
    if request.method == 'POST':
        try:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            course = lesson.course
            
            # Check permission
            if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
                messages.error(request, 'You do not have permission to upload files.')
                return redirect('courses:lesson_file', lesson_id=lesson.id)
            
            file = request.FILES.get('file')
            if file:
                # Check file size (limit to 100MB)
                if file.size > 100 * 1024 * 1024:  # 100MB in bytes
                    messages.error(request, 'File size too large. Maximum size is 100MB.')
                    return redirect('courses:lesson_file', lesson_id=lesson.id)
                
                # Check if file with same name already exists
                existing_file = LessonFile.objects.filter(lesson=lesson, title=file.name).first()
                if existing_file:
                    messages.warning(request, f'A file named "{file.name}" already exists. It will be replaced.')
                    existing_file.delete()
                
                # Determine file type from extension
                ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
                file_type_map = {
                    'pdf': 'pdf',
                    'doc': 'doc',
                    'docx': 'doc',
                    'ppt': 'ppt',
                    'pptx': 'ppt',
                    'zip': 'zip',
                    'rar': 'zip',
                    'txt': 'other',
                    'jpg': 'other',
                    'jpeg': 'other',
                    'png': 'other',
                    'gif': 'other',
                    'mp4': 'other',
                    'mp3': 'other',
                }
                file_type = file_type_map.get(ext, 'other')
                
                # Create the file record
                lesson_file = LessonFile.objects.create(
                    lesson=lesson,
                    title=file.name,
                    file=file,
                    file_type=file_type,
                    file_size=file.size
                )
                
                messages.success(request, f'File "{file.name}" uploaded successfully!')
            else:
                messages.error(request, 'No file selected.')
            
            return redirect('courses:lesson_file', lesson_id=lesson.id)
            
        except Exception as e:
            # Log the error for debugging
            print(f"Upload error: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error uploading file: {str(e)}')
            return redirect('courses:lesson_file', lesson_id=lesson.id)
    
    # If not POST, redirect to lesson detail
    return redirect('courses:lesson_detail', course_slug=lesson.course.slug, lesson_id=lesson.id)


@login_required
def create_folder(request, lesson_id):
    """Create a new folder in a lesson (instructor only)"""
    if request.method == 'POST':
        try:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            course = lesson.course
            
            # Check permission
            if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
                messages.error(request, 'You do not have permission to create folders.')
                return redirect('courses:lesson_file', lesson_id=lesson.id)
            
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            if name:
                # Check if folder with same name exists
                existing_folder = LessonFolder.objects.filter(lesson=lesson, name=name).first()
                if existing_folder:
                    messages.warning(request, f'A folder named "{name}" already exists.')
                else:
                    folder = LessonFolder.objects.create(
                        lesson=lesson,
                        name=name,
                        description=description
                    )
                    messages.success(request, f'Folder "{name}" created successfully!')
            else:
                messages.error(request, 'Folder name is required.')
            
            return redirect('courses:lesson_file', lesson_id=lesson.id)
            
        except Exception as e:
            print(f"Folder creation error: {str(e)}")
            messages.error(request, f'Error creating folder: {str(e)}')
            return redirect('courses:lesson_file', lesson_id=lesson.id)
    
    return redirect('courses:lesson_detail', course_slug=lesson.course.slug, lesson_id=lesson.id)


@login_required
def folder_detail(request, folder_id):
    """View folder contents"""
    folder = get_object_or_404(LessonFolder, id=folder_id)
    lesson = folder.lesson
    course = lesson.course
    
    # Check access
    can_access = False
    if request.user.is_authenticated:
        if (request.user.is_instructor and course.instructor == request.user) or request.user.is_admin_user:
            can_access = True
        else:
            can_access = Enrollment.objects.filter(
                student=request.user,
                course=course
            ).exists()
    
    if not can_access:
        messages.error(request, 'You do not have access to these resources.')
        # FIXED: Changed from 'courses_detail' to 'course_detail'
        return redirect('courses:course_detail', slug=course.slug)
    
    files = folder.files.all().order_by('-created_at')
    
    return render(request, 'courses/folder_detail.html', {
        'folder': folder,
        'lesson': lesson,
        'course': course,
        'files': files,
    })


@login_required
def upload_folder_file(request, folder_id):
    """Upload a file to a folder (instructor only)"""
    if request.method == 'POST':
        try:
            folder = get_object_or_404(LessonFolder, id=folder_id)
            course = folder.lesson.course
            
            # Check permission
            if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
                messages.error(request, 'You do not have permission to upload files.')
                return redirect('courses:folder_detail', folder_id=folder.id)
            
            file = request.FILES.get('file')
            if file:
                # Check file size
                if file.size > 100 * 1024 * 1024:
                    messages.error(request, 'File size too large. Maximum size is 100MB.')
                    return redirect('courses:folder_detail', folder_id=folder.id)
                
                # Check if file with same name exists
                existing_file = FolderFile.objects.filter(folder=folder, title=file.name).first()
                if existing_file:
                    messages.warning(request, f'A file named "{file.name}" already exists. It will be replaced.')
                    existing_file.delete()
                
                folder_file = FolderFile.objects.create(
                    folder=folder,
                    title=file.name,
                    file=file,
                    file_size=file.size
                )
                messages.success(request, f'File "{file.name}" uploaded successfully!')
            else:
                messages.error(request, 'No file selected.')
            
            return redirect('courses:folder_detail', folder_id=folder.id)
            
        except Exception as e:
            print(f"Folder upload error: {str(e)}")
            messages.error(request, f'Error uploading file: {str(e)}')
            return redirect('courses:folder_detail', folder_id=folder.id)
    
    return redirect('courses:lesson_file', lesson_id=folder.lesson.id)


@login_required
def delete_file(request, file_id):
    """Delete a file (instructor only)"""
    if request.method == 'POST':
        try:
            file = get_object_or_404(LessonFile, id=file_id)
            course = file.lesson.course
            
            if (request.user.is_instructor and course.instructor == request.user) or request.user.is_admin_user:
                file_name = file.title
                file.delete()
                return JsonResponse({'success': True, 'message': f'File "{file_name}" deleted successfully.'})
            else:
                return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@login_required
def delete_folder_file(request, file_id):
    """Delete a file from a folder (instructor only)"""
    if request.method == 'POST':
        try:
            file = get_object_or_404(FolderFile, id=file_id)
            course = file.folder.lesson.course
            
            if (request.user.is_instructor and course.instructor == request.user) or request.user.is_admin_user:
                file_name = file.title
                folder_id = file.folder.id
                file.delete()
                return JsonResponse({'success': True, 'message': f'File "{file_name}" deleted successfully.'})
            else:
                return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@login_required
def delete_folder(request, folder_id):
    """Delete a folder and all its contents (instructor only)"""
    if request.method == 'POST':
        try:
            folder = get_object_or_404(LessonFolder, id=folder_id)
            course = folder.lesson.course
            
            if (request.user.is_instructor and course.instructor == request.user) or request.user.is_admin_user:
                folder_name = folder.name
                lesson_id = folder.lesson.id
                folder.delete()
                return JsonResponse({'success': True, 'message': f'Folder "{folder_name}" deleted successfully.'})
            else:
                return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


def load_courses_demo(request):
    """Generator demonstration - lazy loading courses"""
    courses = Course.objects.filter(status='published').iterator()
    
    # Generator usage example
    def course_generator():
        for course in courses:
            yield {
                'id': course.id,
                'title': course.title,
                'instructor': course.instructor.get_full_name(),
            }
    
    return JsonResponse({
        'courses': list(course_generator()),
        'message': 'Courses loaded using generator (lazy loading)'
    })

@login_required
def add_course_review(request, course_id):
    """Add or edit a course review"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You must be enrolled in this course to leave a review.')
        return redirect('courses:course_detail', slug=course.slug)
    
    # Check if user already has a review
    existing_review = CourseReview.objects.filter(course=course, student=request.user).first()
    
    if request.method == 'POST':
        form = CourseReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.course = course
            review.student = request.user
            
            # Check if student has completed the course
            enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
            if enrollment and enrollment.status == 'completed':
                review.is_verified = True
            
            review.save()
            
            if existing_review:
                messages.success(request, 'Your review has been updated!')
            else:
                messages.success(request, 'Thank you for your review!')
            
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = CourseReviewForm(instance=existing_review)
    
    return render(request, 'courses/add_review.html', {
        'course': course,
        'form': form,
        'existing_review': existing_review,
        'review_type': 'course'
    })


@login_required
def add_instructor_review(request, course_id, instructor_id):
    """Add a review for an instructor"""
    course = get_object_or_404(Course, id=course_id)
    instructor = get_object_or_404(User, id=instructor_id, user_type='instructor')
    
    # Check if user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You must be enrolled in this course to review the instructor.')
        return redirect('courses:course_detail', slug=course.slug)
    
    # Check if user already reviewed this instructor for this course
    existing_review = InstructorReview.objects.filter(
        instructor=instructor, 
        student=request.user, 
        course=course
    ).first()
    
    if request.method == 'POST':
        form = InstructorReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.instructor = instructor
            review.student = request.user
            review.course = course
            review.save()
            
            # Update instructor's rating if you added the fields to User model
            if hasattr(instructor, 'update_instructor_rating'):
                instructor.update_instructor_rating()
            
            if existing_review:
                messages.success(request, 'Your instructor review has been updated!')
            else:
                messages.success(request, 'Thank you for reviewing the instructor!')
            
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = InstructorReviewForm(instance=existing_review)
    
    return render(request, 'courses/add_review.html', {
        'course': course,
        'instructor': instructor,
        'form': form,
        'existing_review': existing_review,
        'review_type': 'instructor'
    })


@login_required
def mark_review_helpful(request, review_id):
    """Mark a review as helpful"""
    if request.method == 'POST':
        review = get_object_or_404(CourseReview, id=review_id)
        
        # Check if user already marked this review as helpful
        existing = ReviewHelpful.objects.filter(review=review, user=request.user).first()
        
        if existing:
            existing.delete()
            helpful_count = review.helpful_votes.count()
            return JsonResponse({
                'success': True, 
                'action': 'removed',
                'count': helpful_count
            })
        else:
            ReviewHelpful.objects.create(review=review, user=request.user)
            helpful_count = review.helpful_votes.count()
            return JsonResponse({
                'success': True, 
                'action': 'added',
                'count': helpful_count
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def load_more_reviews(request, course_id):
    """Load more reviews via AJAX (pagination)"""
    course = get_object_or_404(Course, id=course_id)
    page = int(request.GET.get('page', 1))
    per_page = 5
    
    reviews = CourseReview.objects.filter(course=course).select_related('student').order_by('-created_at')
    
    start = (page - 1) * per_page
    end = start + per_page
    reviews_page = reviews[start:end]
    
    data = []
    for review in reviews_page:
        data.append({
            'id': review.id,
            'student_name': review.student.get_full_name(),
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'date': review.created_at.strftime('%B %d, %Y'),
            'helpful_count': review.helpful_votes.count(),
            'is_verified': review.is_verified,
        })
    
    return JsonResponse({
        'reviews': data,
        'has_more': end < reviews.count()
    })