from django import forms
from .models import CourseReview, InstructorReview


class CourseReviewForm(forms.ModelForm):
    class Meta:
        model = CourseReview
        fields = ['rating', 'title', 'comment', 'would_recommend', 'difficulty_rating']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'type': 'range', 'min': '1', 'max': '5', 'step': '1',
                'class': 'rating-slider', 'style': 'width: 100%;'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Summarize your experience (optional)'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Share your thoughts about this course...'
            }),
            'difficulty_rating': forms.NumberInput(attrs={
                'type': 'range', 'min': '1', 'max': '5', 'step': '1',
                'class': 'difficulty-slider', 'style': 'width: 100%;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].label = "Your Rating"
        self.fields['would_recommend'].label = "Would you recommend this course to others?"
        self.fields['difficulty_rating'].label = "How difficult was this course?"


class InstructorReviewForm(forms.ModelForm):
    class Meta:
        model = InstructorReview
        fields = ['rating', 'clarity_rating', 'responsiveness_rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'type': 'range', 'min': '1', 'max': '5', 'step': '1',
                'class': 'rating-slider', 'style': 'width: 100%;'
            }),
            'clarity_rating': forms.NumberInput(attrs={
                'type': 'range', 'min': '1', 'max': '5', 'step': '1',
                'class': 'clarity-slider', 'style': 'width: 100%;'
            }),
            'responsiveness_rating': forms.NumberInput(attrs={
                'type': 'range', 'min': '1', 'max': '5', 'step': '1',
                'class': 'responsiveness-slider', 'style': 'width: 100%;'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Share your thoughts about the instructor...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].label = "Overall Instructor Rating"
        self.fields['clarity_rating'].label = "Teaching Clarity"
        self.fields['responsiveness_rating'].label = "Responsiveness to Questions"