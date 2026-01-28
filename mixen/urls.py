# misen_server/urls.py
from django.urls import path
from .views import (
    RegisterView,
    JWTLoginView,
    UploadProfileImagesView,
    UploadVerificationVideoView,
    SubmitProfileForReviewView,
    ProfileStatusView,
    SwipeUsersView,
    LikeUserView,
    MatchesListView,
    ViewLikesView,
    SendMessageView,
)

urlpatterns = [
    # ---------------- User Auth ----------------
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", JWTLoginView.as_view(), name="jwt-login"),

    # ---------------- Upload Media ----------------
    path("upload-images/", UploadProfileImagesView.as_view(), name="upload-images"),
    path("upload-video/", UploadVerificationVideoView.as_view(), name="upload-video"),

    # ---------------- Profile Verification ----------------
    path("submit-review/", SubmitProfileForReviewView.as_view(), name="submit-review"),
    path("status/", ProfileStatusView.as_view(), name="profile-status"),

    # ---------------- Dating System ----------------
    path("swipe/", SwipeUsersView.as_view(), name="swipe-users"),
    path("like/", LikeUserView.as_view(), name="like-user"),
    path("matches/", MatchesListView.as_view(), name="matches-list"),

    # ---------------- Coins Features ----------------
    path("view-likes/", ViewLikesView.as_view(), name="view-likes"),
    path("send-message/", SendMessageView.as_view(), name="send-message"),
]
