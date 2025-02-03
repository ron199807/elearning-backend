from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Course, Category
from .serializers import CourseSerializer, CategorySerializer
from registration_app.permissions import IsInstructor, IsAdminUser 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from registration_app.permissions import IsInstructor

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return super().get_permissions()

class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsInstructor]

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)  # Set the instructor as the logged-in user

class CourseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsInstructor]



class CourseEnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != "student":
            return Response({"error": "Only students can enroll"}, status=403)
        
        try:
            course = Course.objects.get(course.title)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        # Add the student to the course's enrolled students
        course.students.add(request.user)
        return Response({"message": "Enrolled successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    return Response({"message": "Welcome to the student dashboard"})

# bbudo token b3698f1a0c2b428cf71b45a7a7f02a0dd28541ad



