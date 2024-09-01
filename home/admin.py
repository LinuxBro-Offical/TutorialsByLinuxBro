from django.contrib import admin
from .models import (Story, Author, Category,
                     SubCategory, Tag, ContentBlock, Response)
# Register your models here.

admin.site.register(Story)
admin.site.register(Author)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Tag)
admin.site.register(ContentBlock)
admin.site.register(Response)
