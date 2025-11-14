from rest_framework import serializers
from .models import Course, Category, CourseModule, Lesson, CourseMaterial, Enrollment, CourseProgress
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime

class CategorySerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'course_count']

    def get_course_count(self, obj):
        return obj.courses.filter(status='published').count()
    

class CourseSerializer(serializers.ModelSerializer):
    """Main Course Serializer that handles all course operations"""
    
    # Basic fields
    instructor_name = serializers.CharField(source='instructor.username', read_only=True)
    instructor_full_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    
    # Computed fields
    student_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()
    is_available = serializers.ReadOnlyField()
    is_enrolled = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    # Timestamp fields
    created_at_natural = serializers.SerializerMethodField()
    discount_expiry_natural = serializers.SerializerMethodField()
    
    # Related fields (for detailed views)
    modules = serializers.SerializerMethodField()  # Will be populated in detailed views
    
    class Meta:
        model = Course
        fields = [
            # Basic identification
            'id', 'title', 'subtitle', 'slug', 'description',
            
            # Media
            'image', 'image_url',
            
            # Pricing
            'price', 'current_price', 'is_paid', 'has_discount', 
            'discount_price', 'discount_expiry', 'discount_expiry_natural',
            'currency',
            
            # Instructor & Students
            'instructor', 'instructor_name', 'instructor_full_name',
            'students', 'student_count', 'enrollment_count',
            
            # Course metadata
            'category', 'category_name', 'duration', 'created_at', 'created_at_natural',
            
            # Advanced course info
            'status', 'language', 'level', 'learning_objectives', 
            'prerequisites', 'target_audience', 'welcome_message',
            'completion_message', 'certificate_available', 'featured',
            'max_students',
            
            # Access control
            'is_public', 'allow_enrollment', 'is_available',
            
            # User-specific fields
            'is_enrolled', 'progress', 'rating',
            
            # Related data (for detailed views)
            'modules'
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'instructor', 'students',
            'current_price', 'is_available', 'student_count', 'enrollment_count'
        ]
        extra_kwargs = {
            'learning_objectives': {'write_only': False},
            'prerequisites': {'write_only': False},
            'target_audience': {'write_only': False},
        }

    def get_instructor_full_name(self, obj):
        """Get instructor's full name"""
        if obj.instructor.first_name and obj.instructor.last_name:
            return f"{obj.instructor.first_name} {obj.instructor.last_name}"
        return obj.instructor.username

    def get_student_count(self, obj):
        """Get count of enrolled students"""
        return obj.students.count()

    def get_enrollment_count(self, obj):
        """Get count of active enrollments"""
        return Enrollment.objects.filter(course=obj, payment_status__in=['paid', 'completed', 'free']).count()

    def get_current_price(self, obj):
        """Get current price considering active discounts"""
        return obj.current_price

    def get_is_enrolled(self, obj):
        """Check if current user is enrolled in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.students.filter(id=request.user.id).exists()
        return False

    def get_progress(self, obj):
        """Get user's progress in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and self.get_is_enrolled(obj):
            total_lessons = Lesson.objects.filter(module__course=obj).count()
            if total_lessons == 0:
                return 0
            
            completed_lessons = CourseProgress.objects.filter(
                enrollment__user=request.user,
                enrollment__course=obj,
                completed=True
            ).count()
            
            return int((completed_lessons / total_lessons) * 100)
        return 0

    def get_rating(self, obj):
        """Calculate course rating (placeholder - implement rating system later)"""
        # TODO: Implement proper rating system
        return 4.5  # Placeholder

    def get_image_url(self, obj):
        """Get absolute image URL"""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_created_at_natural(self, obj):
        """Get human-readable created_at timestamp"""
        return naturaltime(obj.created_at)

    def get_discount_expiry_natural(self, obj):
        """Get human-readable discount expiry timestamp"""
        if obj.discount_expiry:
            return naturaltime(obj.discount_expiry)
        return None

    def get_modules(self, obj):
        """Get course modules (only in detailed views)"""
        # This will only be populated when explicitly requested
        # to avoid N+1 queries in list views
        if hasattr(obj, 'prefetched_modules'):
            from .serializers import CourseModuleSerializer
            return CourseModuleSerializer(
                obj.prefetched_modules, 
                many=True, 
                context=self.context
            ).data
        return None

    def validate_learning_objectives(self, value):
        """Validate learning objectives field"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Learning objectives must be a list.")
        # Remove empty strings and validate each objective
        cleaned_objectives = [obj.strip() for obj in value if obj.strip()]
        if len(cleaned_objectives) == 0:
            raise serializers.ValidationError("At least one learning objective is required.")
        return cleaned_objectives

    def validate_prerequisites(self, value):
        """Validate prerequisites field"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Prerequisites must be a list.")
        # Remove empty strings
        return [pre.strip() for pre in value if pre.strip()]

    def validate_target_audience(self, value):
        """Validate target audience field"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Target audience must be a list.")
        # Remove empty strings
        return [aud.strip() for aud in value if aud.strip()]

    def validate_price(self, value):
        """Validate price field"""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_discount_price(self, value):
        """Validate discount price"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Discount price cannot be negative.")
        return value

    def validate_max_students(self, value):
        """Validate max students"""
        if value < 0:
            raise serializers.ValidationError("Maximum students cannot be negative.")
        return value

    def validate(self, data):
        """Cross-field validation"""
        # Validate discount fields
        has_discount = data.get('has_discount', self.instance.has_discount if self.instance else False)
        discount_price = data.get('discount_price', self.instance.discount_price if self.instance else None)
        price = data.get('price', self.instance.price if self.instance else None)

        if has_discount:
            if not discount_price:
                raise serializers.ValidationError({
                    "discount_price": "Discount price is required when discount is enabled."
                })
            if discount_price >= price:
                raise serializers.ValidationError({
                    "discount_price": "Discount price must be less than regular price."
                })

        # Validate that free courses don't have prices
        is_paid = data.get('is_paid', self.instance.is_paid if self.instance else False)
        if not is_paid and price and price > 0:
            raise serializers.ValidationError({
                "price": "Free courses must have price set to 0."
            })

        # Validate discount expiry
        discount_expiry = data.get('discount_expiry')
        if discount_expiry and discount_expiry < timezone.now():
            raise serializers.ValidationError({
                "discount_expiry": "Discount expiry cannot be in the past."
            })

        return data

    def create(self, validated_data):
        """Create a new course with the current user as instructor"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['instructor'] = request.user
        
        # Ensure is_paid is set correctly based on price
        price = validated_data.get('price', 0)
        validated_data['is_paid'] = price > 0
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update course instance"""
        # Update is_paid based on price if price is being updated
        if 'price' in validated_data:
            price = validated_data['price']
            validated_data['is_paid'] = price > 0
        
        return super().update(instance, validated_data)


class CourseMaterialSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = CourseMaterial
        fields = ['id', 'title', 'file', 'file_url', 'file_size', 'description', 'uploaded_at']
        read_only_fields = ['uploaded_at']

    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return None

class LessonSerializer(serializers.ModelSerializer):
    materials = CourseMaterialSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'video_url', 'content', 'duration', 'materials', 'is_completed', 'is_published', 'is_preview', 'thumbnail', 'video_file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make title not required for partial updates (PATCH)
        if self.partial:
            self.fields['title'].required = False
            self.fields['content'].required = False

    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if user has completed this lesson
            progress = CourseProgress.objects.filter(
                enrollment__user=request.user,
                enrollment__course=obj.module.course,
                lesson=obj,
                completed=True
            ).first()
            return progress is not None
        return False

class CourseModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = ['id', 'title', 'order', 'description', 'lessons', 'progress', 'is_published']

    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Calculate progress for this module
            total_lessons = obj.lessons.count()
            if total_lessons == 0:
                return 0
            
            completed_lessons = CourseProgress.objects.filter(
                enrollment__user=request.user,
                enrollment__course=obj.course,
                lesson__module=obj,
                completed=True
            ).count()
            
            return int((completed_lessons / total_lessons) * 100)
        return 0

class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course listings (minimal data)"""
    instructor_name = serializers.CharField(source='instructor.username')
    category_name = serializers.CharField(source='category.name', allow_null=True)
    student_count = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'subtitle', 'slug', 'image', 'instructor_name',
            'price', 'current_price', 'has_discount', 'discount_price',
            'category_name', 'level', 'duration', 'student_count', 'rating',
            'status', 'featured', 'created_at'
        ]

    def get_student_count(self, obj):
        return obj.students.count()

    def get_rating(self, obj):
        # Placeholder for rating system - implement later
        return 4.5

    def get_current_price(self, obj):
        return obj.current_price

class CourseDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed course view"""
    instructor = serializers.ReadOnlyField(source='instructor.username')
    instructor_full_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    modules = CourseModuleSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', allow_null=True)
    current_price = serializers.SerializerMethodField()
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'subtitle', 'slug', 'description', 'price', 'current_price',
            'is_paid', 'has_discount', 'discount_price', 'discount_expiry',
            'instructor', 'instructor_full_name', 'students', 'enrollment_count',
            'created_at', 'duration', 'category', 'category_name', 'image', 'modules',
            'is_enrolled', 'progress', 'status', 'language', 'level',
            'learning_objectives', 'prerequisites', 'target_audience',
            'welcome_message', 'completion_message', 'certificate_available',
            'featured', 'max_students', 'currency', 'is_public', 'allow_enrollment',
            'is_available', 'is_published', 'modules', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at', 'instructor']

    def get_image(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.students.filter(id=request.user.id).exists()
        return False

    def get_enrollment_count(self, obj):
        return obj.students.count()

    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and self.get_is_enrolled(obj):
            total_lessons = Lesson.objects.filter(module__course=obj).count()
            if total_lessons == 0:
                return 0
            
            completed_lessons = CourseProgress.objects.filter(
                enrollment__user=request.user,
                enrollment__course=obj,
                completed=True
            ).count()
            
            return int((completed_lessons / total_lessons) * 100)
        return 0

    def get_instructor_full_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}".strip() or obj.instructor.username

    def get_current_price(self, obj):
        return obj.current_price

class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for course creation with validation"""
    class Meta:
        model = Course
        fields = [
            'title', 'subtitle', 'description', 'price', 'is_paid',
            'duration', 'category', 'language', 'level', 'learning_objectives',
            'prerequisites', 'target_audience', 'welcome_message', 'completion_message',
            'certificate_available', 'featured', 'max_students', 'currency',
            'has_discount', 'discount_price', 'discount_expiry', 'is_public',
            'allow_enrollment', 'status'
        ]

    def validate_learning_objectives(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Learning objectives must be a list.")
        # Remove empty strings
        return [obj for obj in value if obj.strip()]

    def validate_prerequisites(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Prerequisites must be a list.")
        return [pre for pre in value if pre.strip()]

    def validate_target_audience(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Target audience must be a list.")
        return [aud for aud in value if aud.strip()]

    def validate(self, data):
        # Validate discount fields
        if data.get('has_discount') and not data.get('discount_price'):
            raise serializers.ValidationError({
                "discount_price": "Discount price is required when discount is enabled."
            })
        
        if data.get('has_discount') and data.get('discount_price') >= data.get('price', 0):
            raise serializers.ValidationError({
                "discount_price": "Discount price must be less than regular price."
            })
        
        # Validate max students
        if data.get('max_students', 0) < 0:
            raise serializers.ValidationError({
                "max_students": "Maximum students cannot be negative."
            })
        
        return data

    def create(self, validated_data):
        # Set the instructor from the request user
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)

class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'user', 'user_name', 'course', 'course_title', 'enrolled_at',
            'completed', 'completed_at', 'payment_status', 'payment_reference',
            'amount_paid', 'progress_percentage'
        ]
        read_only_fields = ['user', 'course', 'enrolled_at']

    def get_progress_percentage(self, obj):
        total_lessons = Lesson.objects.filter(module__course=obj.course).count()
        if total_lessons == 0:
            return 0
        
        completed_lessons = CourseProgress.objects.filter(
            enrollment=obj,
            completed=True
        ).count()
        
        return int((completed_lessons / total_lessons) * 100)

class CourseProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    module_title = serializers.CharField(source='lesson.module.title', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)

    class Meta:
        model = CourseProgress
        fields = [
            'id', 'lesson', 'lesson_title', 'module_title',
            'completed', 'completed_at', 'time_spent', 'last_accessed', 'course_title'
        ]
        read_only_fields = ['completed_at', 'time_spent', 'last_accessed']