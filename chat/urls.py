from django.urls import path

from .views import (
    login_view, signup_view, logout_view,
    conversations_list, conversation_detail
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("logout/", logout_view, name="logout"),
    path("conversations/", conversations_list, name="conversations_list"),
    path("conversations/new/", conversation_detail, name="new_conversation"),
    path("conversations/<int:conv_id>/", conversation_detail, name="conversation_detail"),
]

