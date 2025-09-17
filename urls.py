"""
URL configuration for LMSapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from LMSapp.accounts import views as accounts_views
from LMSapp.administration import views as admin_views
from LMSapp.communication import views as comm_views
from LMSapp.core import views as core_views
from LMSapp.dashboard import views as dash_views
from LMSapp.enrollment import views as enroll_views
from LMSapp.lms import views as lms_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('LMSapp.accounts.urls')),

    # --- Accounts ---
    path("", accounts_views.index, name="index"),
    path("register/", accounts_views.register, name="register"),

    # --- Core Pages ---
    path("home/", core_views.home, name="home"),
    path("about/", core_views.about, name="about"),
    path("schedule/", core_views.schedule, name="schedule"),
    path("activities/", core_views.activities, name="activities"),

    # --- Administration ---
    path("admin/users/", admin_views.user_management, name="user_management"),
    path("admin/content/manager/", admin_views.content_management, name="content_manager"),
    path("admin/course/<int:course_id>/", admin_views.course_detail, name="course_detail"),
    path("admin/course/create/", admin_views.create_course, name="create_course"),
    path("admin/course/<int:course_id>/edit/", admin_views.edit_course, name="edit_course"),
    path("admin/course/<int:course_id>/delete/", admin_views.delete_course, name="delete_course"),
    path("admin/course/<int:course_id>/status/", admin_views.change_course_status, name="change_course_status"),
    path("admin/lesson/<int:lesson_id>/", admin_views.lesson_detail, name="lesson_detail"),
    path("admin/content/analytics/", admin_views.content_analytics, name="content_analytics"),
    path("admin/enrollment/", admin_views.enrollment_admin, name="enrollment_admin"),
    path("admin/enrollment/<int:enrollment_id>/status/", admin_views.update_enrollment_status, name="update_enrollment_status"),
    path("admin/reports/", admin_views.ReportsView.as_view(), name="reports"),
    path("admin/reports/data/", admin_views.ReportsDataView.as_view(), name="reports_data"),

    # --- Communication ---
    path("inbox/", comm_views.inbox, name="inbox"),
    path("message/<int:message_id>/toggle/", comm_views.toggle_message_important, name="toggle_message_import"),
    path("compose/", comm_views.compose_message, name="compose_message"),
    path("notifications/", comm_views.notifications_view, name="notifications"),
    path("announcements/", comm_views.announcements_view, name="announcements"),

    # --- Dashboards ---
    path("dashboard/parent/", dash_views.parent_dashboard, name="parent_dashboard"),
    path("dashboard/teacher/", dash_views.teacher_dashboard, name="teacher_dashboard"),
    path("dashboard/child/", dash_views.child_dashboard, name="child_dashboard"),

    # --- Enrollment ---
    path("enrollment/", enroll_views.enrollment_view, name="enrollment"),
    path("enrollment/status/", enroll_views.enrollment_status, name="enrollment_status"),
    path("enrollment/<int:enrollment_id>/", enroll_views.enrollment_detail, name="enrolment_detail"),
    path("children/", enroll_views.child_management, name="child_management"),
    path("children/<int:child_id>/", enroll_views.child_detail, name="child_detail"),
    path("children/<int:child_id>/update/", enroll_views.update_child, name="update_child"),
    path("children/<int:child_id>/deactivate/", enroll_views.deactivate_child, name="deactivate_child"),
    path("children/<int:child_id>/activate/", enroll_views.activate_child, name="activate_child"),
    path("classes/", enroll_views.class_groups, name="class_groups"),

    # --- LMS ---
    path("courses/", lms_views.course_list, name="course_list"),
    path("courses/<int:pk>/", lms_views.CourseDetailView.as_view(), name="course_detail"),
    path("assignments/", lms_views.AssignmentListView.as_view(), name="assignment_list"),
    path("assignments/<int:pk>/submit/", lms_views.AssignmentSubmitView.as_view(), name="assignment_submit"),
    path("activities/", lms_views.InteractiveActivitiesView.as_view(), name="interactive_activities"),
    path("progress/", lms_views.ProgressTrackingView.as_view(), name="progress_tracking"),
]
