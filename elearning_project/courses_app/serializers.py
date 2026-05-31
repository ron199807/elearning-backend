from rest_framework import serializers
from .models import Course, Category, CourseModule, Lesson, CourseMaterial, Enrollment, CourseProgress, Certificate, LessonVideo, LessonContentBlock
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
    

class LessonVideoSerializer(serializers.ModelSerializer):
    video_url_display = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonVideo
        fields = [
            'id', 'title', 'video_url', 'video_file', 'order', 'position',
            'thumbnail', 'thumbnail_url', 'duration', 'is_preview', 'video_url_display'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'video_url': {'required': False, 'allow_null': True},
            'title': {'required': False, 'allow_null': True},
            'duration': {'required': False},
            'thumbnail': {'required': False, 'allow_null': True},
            'is_preview': {'required': False},
            'position': {'required': False},
            'video_file': {'required': False},
            'order': {'required': False},  # Make order optional
        }
    
    def to_internal_value(self, data):
        """Convert incoming data to internal value"""
        # If data is not a dict, return empty
        if not isinstance(data, dict):
            return {}
        
        # Create a copy to avoid modifying original
        internal_data = {}
        
        # Define field mappings
        field_mappings = {
            'id': 'id',
            'title': 'title',
            'video_url': 'video_url',
            'video_file': 'video_file',
            'order': 'order',
            'position': 'position',
            'thumbnail': 'thumbnail',
            'duration': 'duration',
            'is_preview': 'is_preview',
        }
        
        # Map only fields that exist and have non-None values
        for internal_field, data_field in field_mappings.items():
            if data_field in data and data[data_field] is not None:
                # Skip empty strings for URL fields
                if data_field == 'video_url' and data[data_field] == '':
                    continue
                internal_data[internal_field] = data[data_field]
        
        return super().to_internal_value(internal_data)
    
    def get_video_url_display(self, obj):
        if obj.video_file and obj.video_file.url:
            return obj.video_file.url
        return obj.video_url
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
class LessonContentBlockSerializer(serializers.ModelSerializer):
    video_details = LessonVideoSerializer(source='video', read_only=True)
    
    class Meta:
        model = LessonContentBlock
        fields = [
            'id', 'block_type', 'content', 'video', 'video_details',
            'order', 'custom_css_class'
        ]
        read_only_fields = ['id']

class LessonSerializer(serializers.ModelSerializer):
    videos = LessonVideoSerializer(many=True, read_only=True)
    content_blocks = LessonContentBlockSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    total_duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'order', 'content', 'duration', 'total_duration',
            'materials', 'is_completed', 'is_published', 'is_preview', 
            'thumbnail', 'videos', 'content_blocks', 'module'
        ]
    
    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = CourseProgress.objects.filter(
                enrollment__user=request.user,
                enrollment__course=obj.module.course,
                lesson=obj,
                completed=True
            ).first()
            return progress is not None
        return False
    

class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating lessons with videos"""
    videos = LessonVideoSerializer(many=True, required=False)
    content_blocks = LessonContentBlockSerializer(many=True, required=False)
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'order', 'content', 'duration', 'is_published',
            'is_preview', 'thumbnail', 'videos', 'content_blocks'
        ]
        extra_kwargs = {
            'title': {'required': False},  # Make optional for updates
            'content': {'required': False, 'allow_null': True},
            'duration': {'required': False},
            'is_published': {'required': False},
            'is_preview': {'required': False},
            'thumbnail': {'required': False, 'allow_null': True},
        }
    
    def create(self, validated_data):
        """Create a new lesson with videos and content blocks"""
        videos_data = validated_data.pop('videos', [])
        content_blocks_data = validated_data.pop('content_blocks', [])
        
        # Get module from context
        module = self.context.get('module')
        
        if not module:
            raise serializers.ValidationError({"module": "Module is required"})
        
        # Create the lesson
        lesson = Lesson.objects.create(module=module, **validated_data)
        
        # Create videos
        for order, video_data in enumerate(videos_data):
            video_data.pop('id', None)  # Remove id if present
            LessonVideo.objects.create(lesson=lesson, order=order, **video_data)
        
        # Create content blocks
        for order, block_data in enumerate(content_blocks_data):
            block_data.pop('id', None)
            LessonContentBlock.objects.create(lesson=lesson, order=order, **block_data)
        
        return lesson
    
    def update(self, instance, validated_data):
        """Update an existing lesson with videos and content blocks"""
        videos_data = validated_data.pop('videos', None)
        content_blocks_data = validated_data.pop('content_blocks', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle videos - this allows adding, updating, and deleting
        if videos_data is not None:
            # Track IDs that should be kept
            kept_video_ids = []
            
            for video_data in videos_data:
                video_id = video_data.pop('id', None)
                
                if video_id:
                    # Update existing video
                    try:
                        existing_video = LessonVideo.objects.get(id=video_id, lesson=instance)
                        for attr, value in video_data.items():
                            setattr(existing_video, attr, value)
                        existing_video.save()
                        kept_video_ids.append(existing_video.id)
                    except LessonVideo.DoesNotExist:
                        # Create new if ID doesn't exist (shouldn't happen)
                        new_video = LessonVideo.objects.create(lesson=instance, **video_data)
                        kept_video_ids.append(new_video.id)
                else:
                    # Create new video
                    new_video = LessonVideo.objects.create(lesson=instance, **video_data)
                    kept_video_ids.append(new_video.id)
            
            # Delete videos that were not included in the update
            instance.videos.exclude(id__in=kept_video_ids).delete()
        
        # Handle content blocks similarly
        if content_blocks_data is not None:
            kept_block_ids = []
            
            for block_data in content_blocks_data:
                block_id = block_data.pop('id', None)
                
                if block_id:
                    try:
                        existing_block = LessonContentBlock.objects.get(id=block_id, lesson=instance)
                        for attr, value in block_data.items():
                            setattr(existing_block, attr, value)
                        existing_block.save()
                        kept_block_ids.append(existing_block.id)
                    except LessonContentBlock.DoesNotExist:
                        new_block = LessonContentBlock.objects.create(lesson=instance, **block_data)
                        kept_block_ids.append(new_block.id)
                else:
                    new_block = LessonContentBlock.objects.create(lesson=instance, **block_data)
                    kept_block_ids.append(new_block.id)
            
            # Delete blocks that were not included
            instance.content_blocks.exclude(id__in=kept_block_ids).delete()
        
        return instance

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


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for certificates"""
    verification_url = serializers.SerializerMethodField()
    course_slug = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    issued_date_formatted = serializers.SerializerMethodField()
    completion_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            'id',
            'certificate_id',
            'issued_at',
            'verification_token',
            'verification_url',
            'is_verified',
            
            # Certificate data
            'student_name',
            'student_email',
            'course_title',
            'course_duration',
            'instructor_name',
            'completion_date',
            'completion_date_formatted',
            'course_description',
            'grade',
            'final_score',
            'certificate_text',
            
            # Additional context
            'course_slug',
            'platform_name',
            'issued_date_formatted',
        ]
        read_only_fields = [
            'certificate_id', 'issued_at', 'verification_token',
            'verification_url', 'is_verified'
        ]
    
    def get_verification_url(self, obj):
        request = self.context.get('request')
        if request:
            return f"{request.scheme}://{request.get_host()}/api/certificates/verify/{obj.verification_token}/"
        return obj.verification_url
    
    def get_course_slug(self, obj):
        return obj.enrollment.course.slug
    
    def get_platform_name(self, obj):
        return "BTEE eLearning Platform"
    
    def get_issued_date_formatted(self, obj):
        return obj.issued_at.strftime('%B %d, %Y')
    
    def get_completion_date_formatted(self, obj):
        return obj.completion_date.strftime('%B %d, %Y')

class CertificateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating certificates"""
    class Meta:
        model = Certificate
        fields = [
            'grade',
            'final_score',
            'certificate_text',
        ]
        optional_fields = ['grade', 'final_score', 'certificate_text']