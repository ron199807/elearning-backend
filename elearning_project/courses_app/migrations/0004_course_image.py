# Generated by Django 5.1.5 on 2025-02-11 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses_app', '0003_category_course_duration_course_slug_course_students_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='course_images/'),
        ),
    ]
