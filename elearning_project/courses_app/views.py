from django.shortcuts import render
from rest_framework import generics
from .models import Course, Category
from .serializers import CourseSerializer, CategorySerializer
from registration_app.permissions import IsInstructor, IsAdminUser 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from registration_app.permissions import IsInstructor
from rest_framework.permissions import AllowAny 
from rest_framework import status

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny] #allow anyone to view the categories

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
    permission_classes = [AllowAny] #allow anyone to view the course list

    def perform_create(self, serializer):
        # Only authenticated users can create courses
        if self.request.user.is_authenticated:
            serializer.save(instructor=self.request.user)
        else:
            raise serializers.ValidationError("You must be logged in to create a course.")

class CourseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]



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

class CheckCourseAccessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the course is free
        if not course.is_paid:
            return Response({"has_access": True, "message": "This is a free course."})
        # Check if the user is authenticated and has paid/enrolled
        if request.user.is_authenticated and request.user in course.students.all():
            return Response({"has_access": True, "message": "You have access to this course."})
        else:
            return Response({"has_access": False, "message": "You need to pay to access this course."})


class CourseSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('query', '')
        courses = Course.objects.filter(title__icontains=query)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


