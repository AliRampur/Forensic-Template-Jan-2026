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
    
    # Inventory URLs
    path('inventory/metrics/', views.inventory_metrics_view, name='inventory_metrics'),
    path('inventory/units/', views.InventoryUnitListView.as_view(), name='inventory_unit_list'),
    path('inventory/units/<int:pk>/', views.inventory_unit_detail_view, name='inventory_unit_detail'),
    path('inventory/commissions/', views.CommissionListView.as_view(), name='commission_list'),
    
    # Document URLs
    path('documents/', views.document_inventory_view, name='document_inventory'),
]
