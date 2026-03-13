# core/models.py
from django.db import models

class Summary(models.Model):
    url = models.URLField(max_length=500)
    wiki_title = models.CharField(max_length=200, blank=True, null=True)
    
    # Core Content
    overview = models.TextField(blank=True, null=True)
    insights = models.TextField(blank=True, null=True)
    
    # Metrics
    keywords = models.JSONField(default=list)
    reading_time = models.IntegerField(default=0)
    category = models.CharField(max_length=100, default="General")
    word_count = models.IntegerField(default=0)
    
    # Full Text (Optional, for re-summarization or deep view)
    full_text = models.TextField(blank=True, null=True)
    
    # Media
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    
    # Exhaustive Wiki Data
    wiki_json = models.JSONField(default=dict, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.wiki_title or self.url}"
