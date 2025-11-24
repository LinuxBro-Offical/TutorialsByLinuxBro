from django.contrib import admin
from .models import (Story, Author, Category,
                     SubCategory, Tag, ContentBlock, Response,
                     Saved, StoryView, TeamMember, ContactInfo, ContactMessage,
                     AboutUsContent, FooterContent, AdSpace)


class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ('story', 'content_type', 'order', 'code_language', 'video_url_preview')
    search_fields = ('story__title', 'text_content', 'content_type', 'video_url')
    list_filter = ('content_type', 'code_language', 'story__title')
    fieldsets = (
        ('Basic Information', {
            'fields': ('story', 'content_type', 'order')
        }),
        ('Content', {
            'fields': ('text_content', 'image_content', 'video_url', 'code_language'),
            'description': 'For YouTube videos, enter either the video ID (e.g., "M06YHZ9YUdI") or full URL (e.g., "https://youtu.be/M06YHZ9YUdI"). For code blocks, select the programming language for syntax highlighting.'
        }),
    )
    
    def video_url_preview(self, obj):
        if obj.content_type == 'youtube' and obj.video_url:
            video_id = obj.get_youtube_video_id()
            if video_id:
                return f'YouTube: {video_id}'
            return obj.video_url
        return '-'
    video_url_preview.short_description = 'Video'


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


class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'approval_status', 'publication_date')
    list_filter = ('approval_status', 'category', 'publication_date')
    search_fields = ('title', 'subtitle', 'author__user__username')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'author', 'category', 'sub_category', 'tags', 'approval_status')
        }),
        ('Content', {
            'fields': ('cover_image', 'is_banner', 'banner_image')
        }),
        ('SEO Settings', {
            'fields': ('meta_description', 'meta_keywords'),
            'description': 'SEO optimization fields. Meta description should be 150-160 characters. Keywords should be comma-separated. If left blank, will use tags and category automatically.'
        }),
    )


admin.site.register(Story, StoryAdmin)
admin.site.register(Author)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Tag)
admin.site.register(ContentBlock, ContentBlockAdmin)
admin.site.register(Response)
admin.site.register(Saved)
admin.site.register(StoryView, StoryViewAdmin)
admin.site.register(TeamMember)
admin.site.register(ContactInfo)
admin.site.register(ContactMessage)
admin.site.register(AboutUsContent)
admin.site.register(FooterContent)


class AdSpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'ad_type', 'is_active', 'created_date')
    list_filter = ('position', 'ad_type', 'is_active')
    search_fields = ('name', 'ad_code')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'ad_type', 'is_active')
        }),
        ('Ad Code', {
            'fields': ('ad_code',),
            'description': 'Paste your AdSense code, Meta Ads code, or custom HTML/JavaScript here. For AdSense, paste the entire script tag. For Meta Ads, paste the pixel code or ad unit code.'
        }),
    )


admin.site.register(AdSpace, AdSpaceAdmin)
