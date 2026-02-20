from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.courses.models import Lesson
from django.utils import timezone

User = get_user_model()


class Quiz(models.Model):
    """Quiz model for lessons - MCQ only"""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Quiz settings
    time_limit = models.PositiveIntegerField(default=0, help_text="Time limit in minutes (0 = no limit)")
    passing_score = models.PositiveIntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_attempts = models.PositiveIntegerField(default=0, help_text="0 = unlimited attempts")
    shuffle_questions = models.BooleanField(default=False)
    show_answers = models.BooleanField(default=True, help_text="Show correct answers after submission")
    
    # Status
    is_published = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Quizzes"
    
    def __str__(self):
        return f"{self.lesson.course.title} - {self.lesson.title} - {self.title}"
    
    def total_questions(self):
        return self.questions.count()
    
    def total_points(self):
        return self.questions.aggregate(models.Sum('points'))['points__sum'] or 0


class Question(models.Model):
    """MCQ Questions only"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    
    # Options for MCQ
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)
    
    # Correct answer (A, B, C, or D)
    CORRECT_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    correct_answer = models.CharField(max_length=1, choices=CORRECT_CHOICES)
    
    # Explanation for students
    explanation = models.TextField(blank=True, help_text="Explanation of correct answer")
    
    # Order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}: {self.text[:50]}"
    
    def get_options(self):
        """Return options as a list"""
        options = []
        if self.option_a:
            options.append(('A', self.option_a))
        if self.option_b:
            options.append(('B', self.option_b))
        if self.option_c:
            options.append(('C', self.option_c))
        if self.option_d:
            options.append(('D', self.option_d))
        return options
    
    def check_answer(self, answer):
        """Check if answer is correct"""
        return str(answer).upper() == self.correct_answer


class QuizAttempt(models.Model):
    """Student attempts at quizzes"""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    
    # Attempt details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.FloatField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    
    # Answers storage (JSON format: {"1": "A", "2": "B", etc.})
    answers = models.JSONField(default=dict)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    time_taken = models.PositiveIntegerField(default=0, help_text="Time taken in seconds")
    
    # Attempt number
    attempt_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['-started_at']
        unique_together = ['student', 'quiz', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.quiz.title} - Attempt {self.attempt_number} - {self.percentage}%"
    
    def calculate_score(self):
        """Calculate quiz score"""
        total_points = 0
        earned_points = 0
        
        for question in self.quiz.questions.all():
            total_points += question.points
            answer = self.answers.get(str(question.id))
            
            if answer and question.check_answer(answer):
                earned_points += question.points
        
        if total_points > 0:
            self.score = earned_points
            self.percentage = (earned_points / total_points) * 100
            self.passed = self.percentage >= self.quiz.passing_score
        
        self.status = 'completed'
        self.save()
    
    def get_time_remaining(self):
        """Get remaining time in seconds"""
        if not self.quiz.time_limit or self.status != 'in_progress':
            return None
        
        elapsed = (timezone.now() - self.started_at).total_seconds()
        remaining = (self.quiz.time_limit * 60) - elapsed
        
        if remaining <= 0:
            self.status = 'completed'
            self.save()
            return 0
        
        return int(remaining)