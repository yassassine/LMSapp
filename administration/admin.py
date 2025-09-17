from django.contrib import admin
from .models import (
    ContentCategory, Course, Lesson, 
    Resource, Activity, ContentAnalytics
)

# Register your models here.

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['title', 'order', 'created_at']
    readonly_fields = ['created_at']

class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 1
    fields = ['title', 'resource_type', 'created_at']
    readonly_fields = ['created_at']

class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 1
    fields = ['title', 'activity_type', 'max_score', 'due_date']
    readonly_fields = ['created_at']

@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'creator', 'status', 'level', 'created_at')
    list_filter = ('status', 'level', 'category', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'creator')
        }),
        ('Contenu', {
            'fields': ('description', 'short_description', 'featured_image')
        }),
        ('Métadonnées', {
            'fields': ('status', 'level', 'duration')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course__category', 'course')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ResourceInline, ActivityInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'slug', 'order')
        }),
        ('Contenu', {
            'fields': ('content', 'video_url')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'resource_type', 'created_at')
    list_filter = ('resource_type', 'lesson__course__category')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('lesson', 'title', 'resource_type')
        }),
        ('Contenu', {
            'fields': ('file', 'external_link', 'description')
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'activity_type', 'max_score', 'due_date', 'created_at')
    list_filter = ('activity_type', 'lesson__course__category')
    search_fields = ('title', 'instructions')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('lesson', 'title', 'activity_type')
        }),
        ('Détails', {
            'fields': ('instructions', 'max_score', 'due_date')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ContentAnalytics)
class ContentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'views', 'downloads', 'completions')
    list_filter = ('course__category', 'date')
    readonly_fields = ('date',)
    date_hierarchy = 'date'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False