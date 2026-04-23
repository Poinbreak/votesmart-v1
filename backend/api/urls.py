"""
VoteSmart TN — API URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('moral-match/', views.moral_match, name='moral-match'),
    path('reality-predict/<int:constituency_id>/', views.reality_predict, name='reality-predict'),
    path('constituencies/', views.constituency_list, name='constituency-list'),
    path('candidates/<int:constituency_id>/', views.candidates_for_constituency, name='candidates'),
]
