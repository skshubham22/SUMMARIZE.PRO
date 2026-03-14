from django.shortcuts import render, redirect
from .models import Summary
from .utils import get_page_summary, get_search_summary
import re

def index(request):
    result = None
    error = None
    
    # Handle History Retrieval
    history_id = request.GET.get('history_id')
    if history_id:
        try:
            item = Summary.objects.get(id=history_id)
            result = {
                'success': True,
                'original_url': item.url,
                'title': item.wiki_title or "Re-opened Report",
                'summary_data': {
                    'overview': item.overview,
                    'insights': item.insights,
                },
                'metrics': {
                    'keywords': item.keywords,
                    'reading_time': item.reading_time,
                    'category': item.category,
                    'word_count': item.word_count,
                },
                'full_text': item.full_text,
                'image_url': item.image_url,
                'wiki_data': item.wiki_json or {'title': item.wiki_title, 'summary': item.overview, 'url': item.url}
            }
        except Summary.DoesNotExist:
            error = "Selected history item not found."

    if request.method == 'POST':
        query = request.POST.get('url', '').strip()
        if query:
            # Detect if it's a URL or search keywords
            url_pattern = re.compile(r'^(http|https)://|^www\.', re.IGNORECASE)
            
            try:
                if url_pattern.match(query):
                    if query.startswith('www.'):
                        query = 'http://' + query
                    data = get_page_summary(query)
                else:
                    data = get_search_summary(query)
                
                if data['success']:
                    # Save to DB with all metrics
                    Summary.objects.create(
                        url=data['original_url'],
                        wiki_title=data['title'],
                        overview=data['summary_data']['overview'],
                        insights=data['summary_data']['insights'],
                        keywords=data['metrics']['keywords'],
                        reading_time=data['metrics']['reading_time'],
                        category=data['metrics']['category'],
                        word_count=data['metrics']['word_count'],
                        full_text=data['full_text'],
                        image_url=data['image_url'],
                        wiki_json=data.get('wiki_data', {})
                    )
                    result = data
                else:
                    error = data['error']
                    
            except Exception as e:
                error = f"Internal Error: {str(e)}"

    recent_summaries = Summary.objects.all().order_by('-created_at')[:6]
    return render(request, 'core/index.html', {
        'result': result, 
        'error': error,
        'recent_summaries': recent_summaries
    })
