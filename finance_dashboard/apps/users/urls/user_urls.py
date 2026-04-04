from django.urls import path
from apps.users.views import UserListView, UserDetailView, ChangeUserRoleView

urlpatterns = [
    path("", UserListView.as_view(), name="user-list"),
    path("<uuid:user_id>/", UserDetailView.as_view(), name="user-detail"),
    path("<uuid:user_id>/role/", ChangeUserRoleView.as_view(), name="user-change-role"),
]
