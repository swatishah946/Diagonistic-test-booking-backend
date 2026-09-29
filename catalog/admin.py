from django.contrib import admin

from .models import DiagnosticCentre, DiagnosticTest


class DiagnosticTestInline(admin.TabularInline):
    model = DiagnosticTest
    extra = 1


@admin.register(DiagnosticCentre)
class DiagnosticCentreAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "created_at")
    search_fields = ("name", "location")
    inlines = [DiagnosticTestInline]


@admin.register(DiagnosticTest)
class DiagnosticTestAdmin(admin.ModelAdmin):
    list_display = ("name", "centre", "price", "created_at")
    list_filter = ("centre",)
    search_fields = ("name",)
