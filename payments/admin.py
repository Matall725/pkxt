from django.contrib import admin

from .models import PaymentEntry, Receivable


class PaymentEntryInline(admin.TabularInline):
    model = PaymentEntry
    extra = 0
    fields = ("amount", "method", "received_at", "note", "created_by")


@admin.register(Receivable)
class ReceivableAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "amount_due", "amount_received", "status", "due_date")
    search_fields = ("title", "student__name", "student__phone")
    list_filter = ("status", "due_date")
    autocomplete_fields = ("student", "service_plan", "created_by")
    inlines = [PaymentEntryInline]


@admin.register(PaymentEntry)
class PaymentEntryAdmin(admin.ModelAdmin):
    list_display = ("receivable", "amount", "method", "received_at", "created_by")
    search_fields = ("receivable__student__name", "receivable__title")
    list_filter = ("method", "received_at")
    autocomplete_fields = ("receivable", "created_by")
