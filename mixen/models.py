from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import PermissionDenied

# Import ONLY from utils (no duplicate definitions here)
from .utils import send_pending_email, send_approved_email, send_rejected_email


# ---------------------------
# VERIFICATION STATUS CHOICES
# ---------------------------
class VerificationStatus(models.TextChoices):
    DRAFT = "DRAFT"        # User still filling profile
    PENDING = "PENDING"   # Waiting for admin review
    APPROVED = "APPROVED" # Approved → full access
    REJECTED = "REJECTED" # Rejected → fix & resubmit


# ---------------------------
# CUSTOM USER MODEL
# ---------------------------
class User(AbstractUser):
    """
    You can later extend this with phone number, etc.
    """
    pass


# ---------------------------
# PROFILE MODEL
# ---------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Verification system
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.DRAFT
    )
    rejection_reason = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Profile info
    bio = models.TextField(blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=100, blank=True)
    height = models.IntegerField(null=True, blank=True)
    drink = models.BooleanField(default=False)
    smoke = models.BooleanField(default=False)
    looking_for = models.CharField(max_length=100, blank=True)

    # ------------------------
    # COINS SYSTEM
    # ------------------------
    coins = models.IntegerField(default=30)  # Every new user gets 30 free coins

    def __str__(self):
        return self.user.username


# ---------------------------
# PROFILE IMAGES (FIREBASE URLS)
# ---------------------------
class ProfileImage(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField()  # Firebase Storage URL
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.profile.user.username}"


# ---------------------------
# VERIFICATION VIDEO
# ---------------------------
class VerificationVideo(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    video_url = models.URLField()  # Firebase video URL
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video for {self.profile.user.username}"


# ---------------------------
# LIKE SYSTEM
# ---------------------------
class Like(models.Model):
    from_user = models.ForeignKey(User, related_name="likes_sent", on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name="likes_received", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate likes
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user} liked {self.to_user}"


# ---------------------------
# MATCH SYSTEM
# ---------------------------
class Match(models.Model):
    user1 = models.ForeignKey(User, related_name="matches1", on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name="matches2", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate matches
        unique_together = ("user1", "user2")

    def __str__(self):
        return f"Match: {self.user1} & {self.user2}"


# ---------------------------
# CHAT MESSAGE MODEL
# ---------------------------
class Message(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender}"


# ---------------------------
# SUBMIT PROFILE FOR REVIEW
# ---------------------------
def submit_for_review(profile):
    images_count = profile.images.count()
    has_video = hasattr(profile, "verificationvideo")

    # Must upload at least 4 images
    if images_count < 4:
        return {"error": "You must upload at least 4 verification images"}

    # Must upload 1 video
    if not has_video:
        return {"error": "You must upload a verification video"}

    # Mark profile as pending
    profile.status = VerificationStatus.PENDING
    profile.submitted_at = timezone.now()
    profile.save()

    # Send pending email
    send_pending_email(profile.user.email)

    return {"success": "Profile submitted for review"}


# ---------------------------
# APPROVE PROFILE (ADMIN)
# ---------------------------
def approve_profile(profile):
    profile.status = VerificationStatus.APPROVED
    profile.reviewed_at = timezone.now()
    profile.rejection_reason = ""
    profile.save()

    # Send approval email
    send_approved_email(profile.user.email)


# ---------------------------
# REJECTION REASONS
# ---------------------------
REJECTION_REASONS = [
    "Blurry or unclear images",
    "Face not clearly visible",
    "Video does not match photos",
    "Fake or stolen images",
    "Incomplete profile information",
    "Multiple people in images",
]


class RejectionReason(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.profile.user.username} - {self.reason}"


# ---------------------------
# REJECT PROFILE (ADMIN)
# ---------------------------
def reject_profile(profile, reasons_list):
    profile.status = VerificationStatus.REJECTED
    profile.reviewed_at = timezone.now()

    # Save reasons as one string
    profile.rejection_reason = ", ".join(reasons_list)
    profile.save()

    # Send rejection email
    send_rejected_email(profile.user.email, reasons_list)


# ---------------------------
# ONLY ALLOW APPROVED USERS
# ---------------------------
def only_approved(user):
    if user.profile.status != VerificationStatus.APPROVED:
        raise PermissionDenied("Account not approved yet")


# ---------------------------
# AUTO CREATE PROFILE ON REGISTER
# ---------------------------
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Automatically create Profile when a new User is created.
    Gives user 30 free coins by default.
    """
    if created:
        Profile.objects.create(user=instance)
