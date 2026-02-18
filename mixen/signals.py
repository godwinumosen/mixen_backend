from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, VerificationStatus
from .utils import send_pending_email, send_approved_email, send_rejected_email

@receiver(post_save, sender=Profile)
def send_status_email(sender, instance, created, **kwargs):
    if created:
        return  # Don't send email on creation here

    # Detect status change
    old_status = instance.__class__.objects.get(id=instance.id).status
    new_status = instance.status

    if old_status != new_status:
        if new_status == VerificationStatus.PENDING:
            send_pending_email(instance.user.email)
        elif new_status == VerificationStatus.APPROVED:
            send_approved_email(instance.user.email)
        elif new_status == VerificationStatus.REJECTED:
            reasons = instance.rejection_reason.split(", ") if instance.rejection_reason else []
            send_rejected_email(instance.user.email, reasons)
