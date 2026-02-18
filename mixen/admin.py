from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import (
    User,
    Profile,
    ProfileImage,
    VerificationVideo,
    Like,
    Match,
    RejectionReason,
    approve_profile,
    reject_profile
)

# -------------------------
# Admin Actions
# -------------------------
def approve_profiles(modeladmin, request, queryset):
    """
    Approve selected profiles in admin and send automatic approval email.
    """
    for profile in queryset:
        approve_profile(profile)
approve_profiles.short_description = "Approve selected profiles"


def reject_profiles(modeladmin, request, queryset):
    """
    Reject selected profiles in admin and send automatic rejection email.
    """
    # Select default reason if nothing chosen
    default_reason = RejectionReason.objects.get_or_create(reason="Incomplete profile information")[0]
    for profile in queryset:
        reject_profile(profile, [default_reason])
reject_profiles.short_description = "Reject selected profiles"


# -------------------------
# Profile Admin
# -------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "submitted_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email")
    fields = (
        "user",
        "status",
        "rejection_reasons",  # changed to ManyToMany field
        "height",
        "drink",
        "coins",
        "smoke",
        "looking_for",
        "submitted_at",
        "reviewed_at",
    )
    readonly_fields = ("submitted_at", "reviewed_at")
    filter_horizontal = ("rejection_reasons",)  # makes multi-select in admin
    actions = [approve_profiles, reject_profiles]

    def save_model(self, request, obj, form, change):
        """
        Automatically send emails when admin changes profile status manually.
        """
        if change:
            old_obj = Profile.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                if obj.status == "APPROVED":
                    approve_profile(obj)
                    return
                elif obj.status == "REJECTED":
                    reasons = obj.rejection_reasons.all()
                    if not reasons:
                        default_reason = RejectionReason.objects.get_or_create(reason="Incomplete profile information")[0]
                        reasons = [default_reason]
                    reject_profile(obj, reasons)
                    return
        super().save_model(request, obj, form, change)


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
    list_display = ("reason",)
