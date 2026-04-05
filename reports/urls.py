from django.urls import path
from .views import DashboardStatsView, BirthdayListView

urlpatterns = [
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('birthdays/', BirthdayListView.as_view(), name='birthday-list'),
]
