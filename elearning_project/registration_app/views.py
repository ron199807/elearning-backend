from django.shortcuts import render

from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

#login imports
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

# log out imports
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        try:
            user = User.objects.get(username=request.data["username"])
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=400)

        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": response.data})





class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = self.get_serializer().validate(request.data)["user"]  # Get the user object
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.id})



class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.auth:
            request.auth.delete()
            return Response({"message": "Logged out successfully"}, status=200)
        return Response({"error": "No active session found"}, status=400)
