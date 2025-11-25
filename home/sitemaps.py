from django.contrib.sitemaps import Sitemap
from django.utils.text import slugify
from .models import Story, Category, Tag


class StorySitemap(Sitemap):
    """Sitemap for blog posts/stories"""
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        return Story.objects.filter(approval_status="approved")
    
    def lastmod(self, obj):
        return obj.publication_date
    
    def location(self, obj):
        from django.urls import reverse
        return reverse('blog', kwargs={'uuid': obj.uuid})


class CategorySitemap(Sitemap):
    """Sitemap for categories"""
    changefreq = "monthly"
    priority = 0.6
    
    def items(self):
        return Category.objects.all()
    
    def location(self, obj):
        from django.urls import reverse
        return reverse('filter-search-results-slug', kwargs={'slug': slugify(obj.name)})


class StaticSitemap(Sitemap):
    """Sitemap for static pages"""
    changefreq = "monthly"
    priority = 0.5
    
    def items(self):
        return ['home', 'our_story', 'contact']
    
    def location(self, item):
        from django.urls import reverse
        try:
            return reverse(item)
        except:
            return '/'

