from django.urls import path
from . import views

app_name = 'enrollments'

urlpatterns = [
    path('', views.my_enrollments, name='my_enrollments'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('update-progress/<int:enrollment_id>/', views.update_progress, name='update_progress'),
]