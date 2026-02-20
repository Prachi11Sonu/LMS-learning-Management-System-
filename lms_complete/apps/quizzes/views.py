from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .models import Quiz, Question, QuizAttempt
from .forms import QuizForm, QuestionForm
from apps.courses.models import Lesson
from apps.enrollments.models import Enrollment


# Instructor Views
@login_required
def manage_quizzes(request, lesson_id):
    """Manage quizzes for a lesson (instructor only)"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to manage quizzes.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    quiz = Quiz.objects.filter(lesson=lesson).first()
    
    return render(request, 'quizzes/manage_quizzes.html', {
        'lesson': lesson,
        'course': course,
        'quiz': quiz
    })


@login_required
def create_quiz(request, lesson_id):
    """Create a new quiz (instructor only)"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to create quizzes.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    # Check if quiz already exists
    existing_quiz = Quiz.objects.filter(lesson=lesson).first()
    if existing_quiz:
        messages.warning(request, 'A quiz already exists for this lesson. You can edit it instead.')
        return redirect('quizzes:edit_quiz', quiz_id=existing_quiz.id)
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            messages.success(request, 'Quiz created successfully! Now add some questions.')
            return redirect('quizzes:manage_questions', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    return render(request, 'quizzes/quiz_form.html', {
        'form': form,
        'lesson': lesson,
        'course': course,
        'is_edit': False
    })


@login_required
def edit_quiz(request, quiz_id):
    """Edit an existing quiz (instructor only)"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    lesson = quiz.lesson
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to edit this quiz.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect('quizzes:manage_questions', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'quizzes/quiz_form.html', {
        'form': form,
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'is_edit': True
    })


@login_required
def delete_quiz(request, quiz_id):
    """Delete a quiz (instructor only)"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    lesson = quiz.lesson
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to delete this quiz.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully!')
        return redirect('quizzes:manage_quizzes', lesson_id=lesson.id)
    
    return render(request, 'quizzes/quiz_confirm_delete.html', {
        'quiz': quiz,
        'lesson': lesson,
        'course': course
    })


@login_required
def manage_questions(request, quiz_id):
    """Manage questions for a quiz (instructor only)"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    lesson = quiz.lesson
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to manage questions.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    # Get questions ordered by 'order' field
    questions = quiz.questions.all().order_by('order')
    
    # Debug print
    print(f"Quiz: {quiz.title} (ID: {quiz.id})")
    print(f"Questions count: {questions.count()}")
    for q in questions:
        print(f"  Question {q.order}: {q.text[:30]}...")
    
    return render(request, 'quizzes/manage_questions.html', {
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'questions': questions
    })


@login_required
def add_question(request, quiz_id):
    """Add a question to a quiz (instructor only)"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    lesson = quiz.lesson
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to add questions.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            # Set the order to be the next number
            question.order = quiz.questions.count() + 1
            question.save()
            messages.success(request, 'Question added successfully!')
            return redirect('quizzes:manage_questions', quiz_id=quiz.id)
        else:
            # If form is invalid, print errors
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = QuestionForm()
    
    return render(request, 'quizzes/question_form.html', {
        'form': form,
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'is_edit': False
    })


@login_required
def edit_question(request, question_id):
    """Edit a question (instructor only)"""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz
    lesson = quiz.lesson
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to edit this question.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('quizzes:manage_questions', quiz_id=quiz.id)
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'quizzes/question_form.html', {
        'form': form,
        'question': question,
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'is_edit': True
    })


@login_required
def delete_question(request, question_id):
    """Delete a question (instructor only)"""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz
    
    if request.method == 'POST':
        question.delete()
        
        # Reorder remaining questions
        for i, q in enumerate(quiz.questions.all().order_by('order')):
            q.order = i + 1
            q.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@login_required
def take_quiz(request, lesson_id):
    """Take a quiz (student view)"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check if user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You must be enrolled in this course to take the quiz.')
        return redirect('courses:course_detail', slug=course.slug)
    
    # Check if quiz exists
    quiz = Quiz.objects.filter(lesson=lesson, is_published=True).first()
    if not quiz:
        messages.error(request, 'No quiz available for this lesson.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    # Check attempts
    attempts_count = QuizAttempt.objects.filter(student=request.user, quiz=quiz).count()
    if quiz.max_attempts > 0 and attempts_count >= quiz.max_attempts:
        messages.error(request, f'You have reached the maximum number of attempts ({quiz.max_attempts}).')
        # Redirect to attempts history page
        return redirect('quizzes:my_attempts')
    
    # Check for in-progress attempt
    current_attempt = QuizAttempt.objects.filter(
        student=request.user,
        quiz=quiz,
        status='in_progress'
    ).first()
    
    if request.method == 'POST':
        if current_attempt:
            # Submit answers
            answers = {}
            total_questions = quiz.questions.count()
            answered_count = 0
            
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    question_id = key.replace('question_', '')
                    answers[question_id] = value
                    answered_count += 1
            
            # Check if all questions are answered
            if answered_count < total_questions:
                messages.warning(request, f'You have answered {answered_count} out of {total_questions} questions. Please answer all questions.')
                return render(request, 'quizzes/take_quiz.html', {
                    'quiz': quiz,
                    'lesson': lesson,
                    'course': course,
                    'attempt': current_attempt,
                    'questions': quiz.questions.all().order_by('order'),
                    'time_remaining': current_attempt.get_time_remaining() if current_attempt else None
                })
            
            current_attempt.answers = answers
            current_attempt.completed_at = timezone.now()
            if current_attempt.started_at:
                current_attempt.time_taken = (current_attempt.completed_at - current_attempt.started_at).total_seconds()
            current_attempt.save()
            
            # Calculate score
            current_attempt.calculate_score()
            
            messages.success(request, f'Quiz submitted successfully! Your score: {current_attempt.percentage:.1f}%')
            # CORRECT REDIRECT - using attempt_id
            return redirect('quizzes:quiz_results', attempt_id=current_attempt.id)
    else:
        if not current_attempt:
            # Create new attempt
            current_attempt = QuizAttempt.objects.create(
                student=request.user,
                quiz=quiz,
                attempt_number=attempts_count + 1
            )
    
    # Get questions
    questions = quiz.questions.all().order_by('order')
    if quiz.shuffle_questions:
        import random
        questions = list(questions)
        random.shuffle(questions)
    
    return render(request, 'quizzes/take_quiz.html', {
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'attempt': current_attempt,
        'questions': questions,
        'time_remaining': current_attempt.get_time_remaining() if current_attempt else None
    })


@login_required
def quiz_results(request, attempt_id):
    """View quiz results"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    quiz = attempt.quiz
    lesson = quiz.lesson
    course = lesson.course
    
    questions = quiz.questions.all().order_by('order')
    
    # Prepare results for each question
    results = []
    for question in questions:
        user_answer = attempt.answers.get(str(question.id))
        is_correct = user_answer == question.correct_answer if user_answer else False
        
        results.append({
            'question': question,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'correct_answer': question.correct_answer,
            'points': question.points if is_correct else 0
        })
    
    return render(request, 'quizzes/quiz_results.html', {
        'attempt': attempt,
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'results': results
    })


@login_required
def my_quiz_attempts(request):
    """View all quiz attempts by the student"""
    attempts = QuizAttempt.objects.filter(student=request.user).select_related(
        'quiz', 'quiz__lesson', 'quiz__lesson__course'
    ).order_by('-started_at')
    
    paginator = Paginator(attempts, 10)
    page = request.GET.get('page')
    attempts = paginator.get_page(page)
    
    return render(request, 'quizzes/my_attempts.html', {
        'attempts': attempts
    })


# Instructor Statistics
@login_required
def quiz_statistics(request, quiz_id):
    """View quiz statistics (instructor only)"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    lesson = quiz.lesson
    course = lesson.course
    
    # Check permission
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
        messages.error(request, 'You do not have permission to view statistics.')
        return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    
    attempts = QuizAttempt.objects.filter(quiz=quiz, status='completed')
    total_attempts = attempts.count()
    
    # Statistics
    stats = {
        'total_attempts': total_attempts,
        'avg_score': attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0,
        'highest_score': attempts.aggregate(models.Max('percentage'))['percentage__max'] or 0,
        'lowest_score': attempts.aggregate(models.Min('percentage'))['percentage__min'] or 0,
        'pass_count': attempts.filter(passed=True).count(),
        'fail_count': attempts.filter(passed=False).count(),
    }
    
    # Question statistics
    question_stats = []
    for question in quiz.questions.all().order_by('order'):
        correct_count = 0
        total_responses = 0
        
        for attempt in attempts:
            answer = attempt.answers.get(str(question.id))
            if answer:
                total_responses += 1
                if answer == question.correct_answer:
                    correct_count += 1
        
        question_stats.append({
            'question': question,
            'correct_count': correct_count,
            'total_responses': total_responses,
            'percentage': (correct_count / total_responses * 100) if total_responses > 0 else 0
        })
    
    return render(request, 'quizzes/quiz_statistics.html', {
        'quiz': quiz,
        'lesson': lesson,
        'course': course,
        'stats': stats,
        'question_stats': question_stats
    })

@login_required
def reorder_questions(request, quiz_id):
    """Reorder questions via drag and drop"""
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, id=quiz_id)
        lesson = quiz.lesson
        course = lesson.course
        
        # Check permission
        if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_admin_user:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        import json
        data = json.loads(request.body)
        order = data.get('order', [])
        
        for index, question_id in enumerate(order):
            Question.objects.filter(id=question_id).update(order=index + 1)
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)