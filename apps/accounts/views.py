from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.middleware import csrf
from django.conf import settings

#this is the imported for the deleting the acc
from rest_framework.permissions import IsAuthenticated

from .serializers import RegisterSerializer, LoginSerializer, ProfileSerializer, DeleteAccountSerializer

#things imported for the profile watching
from rest_framework import generics, permissions
from .serializers import ProfileSerializer
from .models import Profile

#view for the register
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Optionally: send verification email here (later)
        return Response({"detail": "User registered successfully.", "id": user.id}, status=status.HTTP_201_CREATED)


#view for the login
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # create session
        auth_login(request, user)

        # ensure CSRF cookie is set for future authenticated requests (browsers)
        csrf_token = csrf.get_token(request)

        resp = Response({
            "detail": "Logged in successfully.",
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }, status=status.HTTP_200_OK)

        # Set CSRF cookie (Django already sets it for templates; this ensures API clients get it)
        resp.set_cookie(settings.CSRF_COOKIE_NAME, csrf_token, httponly=False, samesite="Lax")
        return resp



#view for the logout
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Properly log out the user:
        - call Django logout
        - flush the session (removes session data and invalidates cookie)
        - return response with strict no-cache headers
        - delete session cookie explicitly
        Note: the client should also clear localStorage/sessionStorage and any client-side caches.
        """
        # server-side session/session key invalidation
        try:
            request.session.flush()   # deletes the session data and the session cookie
        except Exception:
            pass

        auth_logout(request)

        resp = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)

        # Instruct browser & proxies not to cache any authenticated responses
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        resp["Pragma"] = "no-cache"
        resp["Expires"] = "0"

        # Delete sessionid cookie (common session cookie name)
        resp.delete_cookie("sessionid", path="/")
        # Also delete CSRF cookie
        resp.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")

        return resp

#hiiuhi
#view for the profile watching
class MyProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        # ensures profile exists via signal
        return self.request.user.profile
    

#view for the deleting the acc
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user

        # flush session, logout first
        try:
            request.session.flush()
        except Exception:
            pass
        auth_logout(request)

        # hard delete user (cascades to profile)
        user.delete()

        resp = Response({"detail": "Account deleted permanently."}, status=status.HTTP_200_OK)
        # instruct browsers not to cache and remove cookies
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        resp["Pragma"] = "no-cache"
        resp["Expires"] = "0"
        resp.delete_cookie("sessionid", path="/")
        from django.conf import settings
        resp.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")
        return resp
