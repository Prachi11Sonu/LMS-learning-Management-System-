from django import forms
from .models import Lesson

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'content', 'video_url', 'order', 'duration_minutes', 'is_free_preview']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
        }
    
    def clean_order(self):
        order = self.cleaned_data.get('order')
        if order < 1:
            raise forms.ValidationError('Order must be at least 1')
        return order
    
    def clean_duration_minutes(self):
        duration = self.cleaned_data.get('duration_minutes')
        if duration < 0:
            raise forms.ValidationError('Duration cannot be negative')
        return duration