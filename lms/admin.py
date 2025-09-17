from django.contrib import admin
from .models import Course, Module, Resource, InteractiveActivity, ChildProgress

# Register your models here.
# lms/admin.py

class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 1

class ActivityInline(admin.TabularInline):
    model = InteractiveActivity
    extra = 1

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    show_change_link = True
    inlines = [ResourceInline, ActivityInline]

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'level', 'start_date')
    list_filter = ('level', 'category', 'start_date')
    search_fields = ('title', 'teacher__username')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [ResourceInline, ActivityInline]

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'resource_type')
    list_filter = ('resource_type',)

@admin.register(InteractiveActivity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'activity_type', 'status')
    list_filter = ('activity_type', 'status')

@admin.register(ChildProgress)
class ChildProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'child', 'status', 'updated_at')
    #list_filter = ('course',)
