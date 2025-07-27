from django.urls import path

from . import views

urlpatterns = [
    
    # admin panel plans urls
    path('admin-panel/plans/add-edit/', views.Add_Edit_PlanView, name='add_edit_plan'),
    path('admin-panel/plans/delete/<int:pk>/', views.Delete_PlanView, name='delete-plan-instance'),

]
