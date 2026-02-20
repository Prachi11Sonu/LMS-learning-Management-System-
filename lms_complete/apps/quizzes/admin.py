from django.contrib import admin
from .models import Quiz, Question, QuizAttempt


class QuestionInline(admin.TabularInline):
    """Inline admin for questions within quiz"""
    model = Question
    extra = 1
    fields = ['order', 'text', 'points', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for Quiz model"""
    list_display = ['title', 'lesson', 'total_questions', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'lesson__title', 'lesson__course__title']
    inlines = [QuestionInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson', 'title', 'description')
        }),
        ('Quiz Settings', {
            'fields': ('time_limit', 'passing_score', 'max_attempts', 
                      'shuffle_questions', 'show_answers', 'is_published')
        }),
    )
    
    def total_questions(self, obj):
        """Display total questions count"""
        return obj.questions.count()
    total_questions.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for Question model (MCQ only)"""
    list_display = ['id', 'quiz', 'text_preview', 'points', 'correct_answer', 'order']
    list_filter = ['quiz', 'correct_answer']
    search_fields = ['text', 'quiz__title']
    list_editable = ['order', 'points']
    
    fieldsets = (
        ('Question Details', {
            'fields': ('quiz', 'text', 'points', 'order')
        }),
        ('Options (MCQ)', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d')
        }),
        ('Correct Answer', {
            'fields': ('correct_answer', 'explanation')
        }),
    )
    
    def text_preview(self, obj):
        """Show truncated question text"""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    """Admin configuration for QuizAttempt model"""
    list_display = ['student', 'quiz', 'attempt_number', 'percentage', 'passed', 'status', 'started_at']
    list_filter = ['status', 'passed', 'started_at']
    search_fields = ['student__email', 'student__first_name', 'student__last_name', 'quiz__title']
    readonly_fields = ['started_at', 'completed_at', 'time_taken']
    
    fieldsets = (
        ('Student & Quiz', {
            'fields': ('student', 'quiz', 'attempt_number')
        }),
        ('Results', {
            'fields': ('status', 'score', 'percentage', 'passed')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'time_taken')
        }),
        ('Answers (JSON)', {
            'fields': ('answers',),
            'classes': ('collapse',),
        }),
    )