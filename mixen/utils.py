from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction


# ----------------------------
# COIN SYSTEM
# ----------------------------

def spend_coins(user, amount):
    """
    Deduct coins from a user safely.
    Returns True if successful, False if not enough coins.
    """
    profile = user.profile

    if profile.coins < amount:
        return False

    profile.coins -= amount
    profile.save()
    return True


def add_coins(user, amount):
    """
    Add coins to a user (after subscription or purchase).
    """
    profile = user.profile
    profile.coins += amount
    profile.save()
    return profile.coins


# ----------------------------
# EMAIL SYSTEM
# ----------------------------

def send_pending_email(to_email):
    send_mail(
        subject="Your account is under review",
        message="Thank you for submitting your profile. Your account is now pending admin approval.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=True,
    )


def send_approved_email(to_email):
    send_mail(
        subject="Your account is approved 🎉",
        message="Congratulations! Your account has been approved. You can now access the app.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=True,
    )


def send_rejected_email(to_email, reasons_list):
    reasons_text = ", ".join(reasons_list)

    send_mail(
        subject="Your account has been rejected",
        message=f"Sorry, your account has been rejected for the following reason(s):\n\n{reasons_text}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=True,
    )
