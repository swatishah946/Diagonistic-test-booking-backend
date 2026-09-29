from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "test", "centre", "amount", "status", "appointment_time", "created_at")
    list_filter = ("status", "centre")
    search_fields = ("user__email", "test__name")
    readonly_fields = ("id", "amount", "created_at", "updated_at")
