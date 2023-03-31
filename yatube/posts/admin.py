from django.conf import settings
from django.contrib import admin

from .models import Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    list_editable = ("group",)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class GroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "slug", "description")
    search_fields = ("description",)
    list_filter = ("title",)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
