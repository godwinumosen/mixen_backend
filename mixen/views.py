from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    User, Profile, ProfileImage, VerificationVideo,
    VerificationStatus, Like, Match, Message, submit_for_review
)

from .serializers import RegisterSerializer
from .utils import spend_coins


# ---------------------------
# 1️⃣ REGISTER
# ---------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Give 30 free coins automatically
            profile = user.profile
            profile.coins = 30
            profile.save()

            return Response(
                {"message": "Account created successfully. You have 30 free coins!", "user_id": user.id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# 2️⃣ NORMAL LOGIN
# ---------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        # Block unapproved users
        if user.profile.status != VerificationStatus.APPROVED:
            return Response(
                {"error": "Account not approved yet", "status": user.profile.status},
                status=403,
            )

        return Response({
            "message": "Login successful",
            "user_id": user.id,
            "username": user.username
        })


# ---------------------------
# 3️⃣ JWT LOGIN (FOR FLUTTER)
# ---------------------------
class JWTLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        if user.profile.status != VerificationStatus.APPROVED:
            return Response(
                {"error": "Account not approved yet", "status": user.profile.status},
                status=403,
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user_id": user.id,
            "username": user.username
        })


# ---------------------------
# 4️⃣ UPLOAD PROFILE IMAGE
# ---------------------------
class UploadProfileImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        image_url = request.data.get("image_url")

        if not image_url:
            return Response({"error": "image_url is required"}, status=400)

        ProfileImage.objects.create(profile=profile, image_url=image_url)
        return Response({"success": "Image uploaded"}, status=201)


# ---------------------------
# 5️⃣ UPLOAD VERIFICATION VIDEO
# ---------------------------
class UploadVerificationVideoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        video_url = request.data.get("video_url")

        if not video_url:
            return Response({"error": "video_url is required"}, status=400)

        if hasattr(profile, "verificationvideo"):
            return Response({"error": "Verification video already uploaded"}, status=400)

        VerificationVideo.objects.create(profile=profile, video_url=video_url)
        return Response({"success": "Video uploaded"}, status=201)


# ---------------------------
# 6️⃣ SUBMIT PROFILE FOR REVIEW
# ---------------------------
class SubmitProfileForReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        result = submit_for_review(profile)

        if "error" in result:
            return Response(result, status=400)

        return Response(result, status=200)


# ---------------------------
# 7️⃣ PROFILE STATUS
# ---------------------------
class ProfileStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        return Response({
            "status": profile.status,
            "rejection_reason": profile.rejection_reason,
            "coins": profile.coins
        })


# ---------------------------
# 8️⃣ SWIPE USERS
# ---------------------------
class SwipeUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_user = request.user

        users = User.objects.filter(profile__status=VerificationStatus.APPROVED).exclude(id=current_user.id)

        liked_ids = Like.objects.filter(from_user=current_user).values_list('to_user_id', flat=True)
        matched_ids1 = Match.objects.filter(user1=current_user).values_list('user2_id', flat=True)
        matched_ids2 = Match.objects.filter(user2=current_user).values_list('user1_id', flat=True)

        excluded_ids = list(liked_ids) + list(matched_ids1) + list(matched_ids2)

        users_to_swipe = users.exclude(id__in=excluded_ids)

        data = []
        for u in users_to_swipe:
            # Take the first profile image if exists
            profile_image = u.profile.images.first()
            image_url = profile_image.image_url if profile_image else None

            data.append({
                "id": u.id,
                "username": u.username,
                "age": u.profile.age,
                "bio": u.profile.bio,
                "profile_image": image_url
            })

        return Response(data)



# ---------------------------
# 9️⃣ LIKE A USER
# ---------------------------
class LikeUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from_user = request.user
        to_user_id = request.data.get("to_user_id")

        if not to_user_id:
            return Response({"error": "to_user_id is required"}, status=400)

        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if from_user == to_user:
            return Response({"error": "You cannot like yourself"}, status=400)

        if Like.objects.filter(from_user=from_user, to_user=to_user).exists():
            return Response({"error": "You already liked this user"}, status=400)

        Like.objects.create(from_user=from_user, to_user=to_user)

        # Check for match
        if Like.objects.filter(from_user=to_user, to_user=from_user).exists():
            Match.objects.create(user1=from_user, user2=to_user)
            return Response({"success": "It's a match! 🎉"}, status=201)

        return Response({"success": "User liked"}, status=201)


# ---------------------------
# 🔟 VIEW MATCHES
# ---------------------------
class MatchesListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        matches1 = Match.objects.filter(user1=user)
        matches2 = Match.objects.filter(user2=user)

        all_matches = []

        for m in matches1:
            all_matches.append({"id": m.user2.id, "username": m.user2.username})

        for m in matches2:
            all_matches.append({"id": m.user1.id, "username": m.user1.username})

        return Response(all_matches)


# ---------------------------
# 1️⃣1️⃣ SEND MESSAGE (COSTS 1 COIN)
# ---------------------------
class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to_user_id = request.data.get("to_user")
        text = request.data.get("text")
        sender = request.user

        if not to_user_id or not text:
            return Response({"error": "to_user and text required"}, status=400)

        try:
            receiver = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Deduct 1 coin
        if not spend_coins(sender, 1):
            return Response({"error": "Not enough coins. Please buy more."}, status=400)

        # Find match
        match = Match.objects.filter(
            (models.Q(user1=sender, user2=receiver)) |
            (models.Q(user1=receiver, user2=sender))
        ).first()

        if not match:
            return Response({"error": "You are not matched with this user"}, status=403)

        Message.objects.create(match=match, sender=sender, text=text)

        return Response({
            "success": "Message sent",
            "remaining_coins": sender.profile.coins
        })


# ---------------------------
# 1️⃣2️⃣ VIEW WHO LIKED YOU (COSTS 5 COINS)
# ---------------------------
class ViewLikesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        coin_cost = 5

        if not spend_coins(user, coin_cost):
            return Response({"error": "Not enough coins to view likes."}, status=400)

        likes = user.likes_received.all()

        data = [
            {
                "from_user": like.from_user.username,
                "created_at": like.created_at
            }
            for like in likes
        ]

        return Response({
            "likes": data,
            "remaining_coins": user.profile.coins
        })
