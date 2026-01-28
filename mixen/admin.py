from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.core.mail import send_mail
from .models import User, Profile, ProfileImage, VerificationVideo, Like, Match, RejectionReason

# -------------------------
# Admin Actions
# -------------------------
def approve_profiles(modeladmin, request, queryset):
    for profile in queryset:
        profile.status = "APPROVED"
        profile.reviewed_at = timezone.now()
        profile.rejection_reason = ""
        profile.save()

        send_mail(
            "Your account is approved!",
            "Congratulations! Your account has been approved. You can now access the app.",
            "no-reply@yourapp.com",
            [profile.user.email],
            fail_silently=False,
        )
approve_profiles.short_description = "Approve selected profiles"


def reject_profiles(modeladmin, request, queryset):
    default_reason = "Incomplete profile information"
    for profile in queryset:
        profile.status = "REJECTED"
        profile.reviewed_at = timezone.now()
        profile.rejection_reason = default_reason
        profile.save()

        RejectionReason.objects.create(profile=profile, reason=default_reason)

        send_mail(
            "Your account is rejected",
            f"Sorry, your account has been rejected. Reason: {default_reason}",
            "no-reply@yourapp.com",
            [profile.user.email],
            fail_silently=False,
        )
reject_profiles.short_description = "Reject selected profiles"

# -------------------------
# Profile Admin
# -------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "submitted_at", "reviewed_at", "rejection_reason")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email")
    fields = (
        "user",
        "status",
        "rejection_reason",
        "height",
        "drink",
        "smoke",
        "looking_for",
        "submitted_at",
        "reviewed_at",
    )
    readonly_fields = ("submitted_at", "reviewed_at")
    actions = [approve_profiles, reject_profiles]

# -------------------------
# User Admin
# -------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")

# -------------------------
# Other Models
# -------------------------
@admin.register(ProfileImage)
class ProfileImageAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "uploaded_at")

@admin.register(VerificationVideo)
class VerificationVideoAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "uploaded_at")

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "created_at")

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("user1", "user2", "created_at")

@admin.register(RejectionReason)
class RejectionReasonAdmin(admin.ModelAdmin):
    list_display = ("profile", "reason")
