from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_preview', 'notification_type', 'sent', 'read', 'created_at')
    list_filter = ('notification_type', 'sent', 'read')
    search_fields = ('message', 'user__email')

    def message_preview(self, obj):
        return obj.message[:80] + '...' if len(obj.message) > 80 else obj.message
    message_preview.short_description = 'Message'
