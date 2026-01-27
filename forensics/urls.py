"""
URL Configuration for Forensics App
"""
from django.urls import path
from . import views

app_name = 'forensics'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api-docs/', views.api_docs_view, name='api_docs'),
    path('resume/', views.resume_view, name='resume'),
    path('sankey/', views.sankey_view, name='sankey'),
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('matches/', views.ReconciliationMatchListView.as_view(), name='match_list'),
]
