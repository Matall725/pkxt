from django.contrib import admin

from .models import ServicePlan, Student


class ServicePlanInline(admin.TabularInline):
    model = ServicePlan
    extra = 0
    fields = (
        "subject",
        "settlement_mode",
        "unit_price",
        "total_hours",
        "remaining_hours",
        "owed_hours",
        "effective_from",
        "expires_at",
        "is_active",
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "status", "service_type", "owner", "created_at")
    search_fields = ("name", "nickname", "phone", "parent_phone")
    list_filter = ("status", "service_type", "owner")
    inlines = [ServicePlanInline]


@admin.register(ServicePlan)
class ServicePlanAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "settlement_mode", "unit_price", "is_active", "effective_from")
    search_fields = ("student__name", "student__phone", "subject")
    list_filter = ("settlement_mode", "is_active")
