from django.shortcuts import render

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Course
from .serializers import CourseSerializer
from registration_app.permissions import IsInstructor
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from registration_app.permissions import IsInstructor



class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsInstructor]

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)  # Set the instructor as the logged-in user

class CourseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

class CourseEnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != "student":
            return Response({"error": "Only students can enroll"}, status=403)
        
        # Enrollment logic here
        return Response({"message": "Enrolled successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    return Response({"message": "Welcome to the student dashboard"})

# bbudo token b3698f1a0c2b428cf71b45a7a7f02a0dd28541ad



