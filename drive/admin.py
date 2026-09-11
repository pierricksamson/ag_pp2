from django.contrib import admin

from .models import DriveFile, StorageQuota


@admin.register(StorageQuota)
class StorageQuotaAdmin(admin.ModelAdmin):
    list_display = ("role", "max_mb")


@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "owner", "class_group", "size_bytes", "uploaded_at")
    list_filter = ("class_group",)
    search_fields = ("original_name", "owner__email", "owner__last_name")