from django import forms
from .models import Quiz, Question


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'passing_score', 
                 'max_attempts', 'shuffle_questions', 'show_answers', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter quiz description'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Chapter 1 Quiz'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
            'max_attempts': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'points', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your question here'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'option_a': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option A'
            }),
            'option_b': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option B'
            }),
            'option_c': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option C (optional)'
            }),
            'option_d': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option D (optional)'
            }),
            'correct_answer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Explain why this answer is correct (optional)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        option_a = cleaned_data.get('option_a')
        option_b = cleaned_data.get('option_b')
        
        if not option_a or not option_b:
            raise forms.ValidationError('Options A and B are required.')
        
        return cleaned_data