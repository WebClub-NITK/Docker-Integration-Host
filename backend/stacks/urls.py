from django.urls import path

from .views import StackListCreateView, StackDetailView, StackGraphView

urlpatterns = [
    path('', StackListCreateView.as_view(), name='stack-list-create'),
    path('<uuid:stack_id>/', StackDetailView.as_view(), name='stack-detail'),
    path('<uuid:stack_id>/graph/', StackGraphView.as_view(), name='stack-graph'),
]
