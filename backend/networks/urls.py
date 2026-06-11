from django.urls import path
from .views import (
    NetworkListCreateView, 
    NetworkDetailView,
    NetworkConnectContainerView,
    NetworkDisconnectContainerView,
    NetworkPruneView
)

urlpatterns = [
    path('hosts/<uuid:host_id>/networks/', NetworkListCreateView.as_view(), name='network-list-create'),
    path('hosts/<uuid:host_id>/networks/prune/', NetworkPruneView.as_view(), name='network-prune'),
    path('hosts/<uuid:host_id>/networks/<uuid:id>/', NetworkDetailView.as_view(), name='network-detail'),
    path('hosts/<uuid:host_id>/networks/<uuid:id>/connect/', NetworkConnectContainerView.as_view(), name='network-connect'),
    path('hosts/<uuid:host_id>/networks/<uuid:id>/disconnect/', NetworkDisconnectContainerView.as_view(), name='network-disconnect'),
]