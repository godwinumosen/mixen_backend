from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction


# ============================
# COIN SYSTEM (Atomic + Logged)
# ============================

@transaction.atomic
def spend_coins(user, amount, description=""):
    from .models import CoinTransaction  # import inside function to avoid circular import
    profile = user.profile

    if profile.coins < amount:
        return False

    profile.coins -= amount
    profile.save()

    CoinTransaction.objects.create(
        user=user,
        transaction_type="SPEND",
        coins=-amount,
        description=description
    )

    return True


@transaction.atomic
def add_coins(user, amount, description=""):
    from .models import CoinTransaction  # import inside function to avoid circular import
    profile = user.profile
    profile.coins += amount
    profile.save()

    CoinTransaction.objects.create(
        user=user,
        transaction_type="EARN",
        coins=amount,
        description=description
    )

    return True


# ============================
# EMAIL SYSTEM
# ============================

def send_pending_email(to_email, username):
    send_mail(
        subject="Your account is under review",
        message=(
            f"Hi {username},\n\n"
            "Thank you for submitting your profile.\n\n"
            "Your account is now pending admin approval. "
            "You will receive another email once approved."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,  # Better for debugging
    )


def send_approved_email(to_email, username):
    send_mail(
        subject="Your account is approved 🎉",
        message=(
            f"Hi {username},\n\n"
            "Congratulations!\n\n"
            "Your account has been approved. "
            "You can now log in and start using the app."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )


def send_rejected_email(to_email, username, reasons_list):
    reasons_text = "\n- ".join(reasons_list)
    send_mail(
        subject="Your account has been rejected",
        message=(
            f"Hi {username},\n\n"
            "Unfortunately, your account was rejected for the following reason(s):\n\n"
            f"- {reasons_text}\n\n"
            "Please fix the issues and resubmit your profile."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )

    