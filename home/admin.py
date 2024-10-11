from django.contrib import admin
from .models import (Story, Author, Category,
                     SubCategory, Tag, ContentBlock, Response,
                     Saved, StoryView)


class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ('story', 'content_type', 'order')
    search_fields = ('story__title', 'text_content', 'content_type')
    list_filter = ('content_type', 'story__title')


class StoryViewAdmin(admin.ModelAdmin):
    # Display the story title and count of views
    list_display = ('story', 'view_count', 'viewed_by')

    # Method to return the total number of views for each story
    def view_count(self, obj):
        return StoryView.objects.filter(story=obj.story).count()
    view_count.short_description = 'Total Views'

    # Method to return a list of usernames who viewed the story
    def viewed_by(self, obj):
        viewers = StoryView.objects.filter(story=obj.story).values_list('user__username', flat=True)
        return ", ".join(viewers)
    viewed_by.short_description = 'Viewed By'


admin.site.register(Story)
admin.site.register(Author)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Tag)
admin.site.register(ContentBlock, ContentBlockAdmin)
admin.site.register(Response)
admin.site.register(Saved)
admin.site.register(StoryView, StoryViewAdmin)
