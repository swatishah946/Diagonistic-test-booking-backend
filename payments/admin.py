from django.contrib import admin

from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("event_id", "booking", "status", "processed_at")
    list_filter = ("status",)
    search_fields = ("event_id", "booking__id")
    readonly_fields = ("processed_at",)
