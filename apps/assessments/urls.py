from django.urls import path
from .views import (
    AnalyzeAudioView, AnalyzeTextView,
    AssessmentListView, AssessmentDetailView, ReviewAssessmentView,
)

urlpatterns = [
    path('',                 AssessmentListView.as_view(),   name='assessment-list'),
    path('<int:pk>',         AssessmentDetailView.as_view(), name='assessment-detail'),
    path('analyze',          AnalyzeAudioView.as_view(),     name='analyze-audio'),
    path('analyze-text',     AnalyzeTextView.as_view(),      name='analyze-text'),
    path('<int:pk>/review',  ReviewAssessmentView.as_view(), name='review-assessment'),
]