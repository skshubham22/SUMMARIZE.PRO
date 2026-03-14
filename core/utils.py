import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import os
from readability import Document
from urllib.parse import urlparse, parse_qs
import re
from collections import Counter
from typing import List, Optional, Any

# Set NLTK data path to local folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nltk_data_path = os.path.join(BASE_DIR, 'nltk_data')
if nltk_data_path not in nltk.data.path:
    nltk.data.path.append(nltk_data_path)

class PageMock:
    """
    Mock object that mimics the 'wikipedia' library page object.
    Provides explicit attributes for type-checking and cleaner internal access.
    """
    def __init__(self, title: str = "", summary: str = "", content: str = "", url: str = "", images: Optional[List[str]] = None):
        self.title: str = title
        self.summary: str = summary
        self.content: str = content
        self.url: str = url
        self.sections: List[Any] = []
        self.images: List[str] = images or []

class WikiSearcher:
    """
    A robust Wikipedia searcher using direct API calls with proper User-Agent identifying.
    Replaces the standard 'wikipedia' library for better reliability and control.
    """
    API_URL = "https://en.wikipedia.org/w/api.php"
    HEADERS = {
        'User-Agent': 'SummarizePro/2.0 (Intelligence Extraction Engine; contact@summarize.pro)'
    }

    @classmethod
    def search(cls, query: str, limit: int = 5) -> List[str]:
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srinfo": "suggestion",
                "format": "json"
            }
            res = requests.get(cls.API_URL, params=params, headers=cls.HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                search_query = data.get('query', {})
                items = search_query.get('search', [])
                
                # If no direct results, try opensearch for typo correction
                if not items:
                    params_os = {
                        "action": "opensearch",
                        "search": query,
                        "limit": 1,
                        "namespace": 0,
                        "format": "json"
                    }
                    res_os = requests.get(cls.API_URL, params=params_os, headers=cls.HEADERS, timeout=10)
                    if res_os.status_code == 200:
                        data_os = res_os.json()
                        # opensearch result format: [query, [titles], [descriptions], [urls]]
                        if len(data_os) > 1 and data_os[1]:
                            return [str(data_os[1][0])]
                    
                    # Try suggestion if opensearch failed
                    if 'searchinfo' in search_query:
                        suggestion = search_query['searchinfo'].get('suggestion')
                        if suggestion:
                            return cls.search(suggestion, limit)
                
                return [str(item.get('title', '')) for item in items]
            return []
        except Exception:
            return []

    @classmethod
    def get_page(cls, title: str) -> Optional[PageMock]:
        try:
            params = {
                "action": "query",
                "prop": "extracts|pageimages|info",
                "exintro": True,
                "explaintext": True,
                "titles": title,
                "format": "json",
                "pithumbsize": 800,
                "inprop": "url"
            }
            res = requests.get(cls.API_URL, params=params, headers=cls.HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                pages = data.get('query', {}).get('pages', {})
                for pid in pages:
                    p = pages[pid]
                    if pid == "-1": return None # Page not found
                    
                    # Instantiate our top-level PageMock
                    images: List[str] = []
                    if 'thumbnail' in p:
                        images.append(str(p['thumbnail'].get('source', '')))
                        
                    page = PageMock(
                        title=str(p.get('title', title)),
                        summary=str(p.get('extract', '')),
                        content=str(p.get('extract', '')), # For intro-based summarization
                        url=str(p.get('fullurl', f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")),
                        images=images
                    )
                    
                    return page
            return None
        except Exception:
            return None

def preprocess_query(query):
    """
    Refines conversational or question-based queries into core search terms.
    Handles complex subjects like 'Who is the CEO of Apple' or 'Capital of France'.
    """
    if not query:
        return ""
    
    # 1. Basic Cleaning
    q = query.strip().strip('?!.').lower()
    
    # 2. Pattern Matching for common question starters
    question_patterns = [
        r"^who (is|was|are|were|am)\s+",
        r"^what (is|was|are|were)\s+",
        r"^where (is|was|are|were)\s+",
        r"^how (does|do|did|is|are)\s+",
        r"^tell me (about|everything about|more about)\s+",
        r"^search for\s+",
        r"^find (info|information) on\s+",
        r"^define\s+",
        r"^(can you )?summarize\s+",
        r"^give me (the|a) brief on\s+",
        r"^who (is|was) the (ceo|founder|creator) of\s+",
        r"^what is the (capital|population|currency) of\s+",
        r"^where is\s+",
        r"^how (high|tall|big) is\s+",
        r"^height of\s+",
        r"^capital of\s+",
        r"^population of\s+",
        r"^color of\s+",
        r"^meaning of\s+",
        r"^history of\s+"
    ]
    
    # Apply patterns and extract the core subject
    for pattern in question_patterns:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            # We want to keep some context if it's a "Capital of" or "CEO of" type question
            # But strip "Who is" etc.
            # If the pattern is like "Capital of", we keep it for Wiki to handle better
            if "of" in pattern or "is" in pattern:
                 # Check if the match is just the prefix "Who is "
                 # For "Capital of France", pattern "^capital of\s+" matches "capital of "
                 # We return "Capital of France" because it's a good search term
                 # If pattern is "^who is\s+", we return the rest.
                 pass
            
            # Simple strip for most
            q = q[match.end():].strip()
            
            # Re-add key context if stripped but useful
            if "ceo of" in pattern.lower(): q = f"CEO of {q}"
            if "capital of" in pattern.lower(): q = f"Capital of {q}"
            if "color of" in pattern.lower(): q = f"Color of {q}"
            if "meaning of" in pattern.lower(): q = f"Meaning of {q}"
            break
            
    # 3. Refine: Remove ending fluff like "please", "now", "immediately"
    q = re.sub(r"\s+(please|now|immediately|exactly|briefly|work|mean|happen|info|information)$", "", q)
    
    return q.title() if len(q) > 0 else query

def smart_wiki_search(query):
    """
    Search Wikipedia with automatic spelling correction and disambiguation handling.
    Uses robust WikiSearcher for reliability with a smart scoring system.
    """
    # Preprocess natural language queries
    query = query.strip()
    refined_query = preprocess_query(query)
    query_clean = query.lower()
    refined_clean = refined_query.lower()
    
    # 1. Direct Page Fetch (Best for exact titles)
    page = WikiSearcher.get_page(refined_query)
    if page:
        # High confidence if title matches refined query exactly
        if page.title.lower() == refined_clean:
            return page
        # Good confidence if refined query is a major part of title or intro
        if refined_clean in page.title.lower() or refined_clean in str(page.summary.lower())[:200]:
            return page

    # 2. Results-based Search with Scoring
    results: Any = WikiSearcher.search(refined_query, limit=8)
    if not results:
         # Try one last time with original query if refined one returned nothing
         results = WikiSearcher.search(query, limit=5)
    
    scored_pages: Any = []
    
    for title in results[:6]:
        p: Optional[PageMock] = WikiSearcher.get_page(title)
        if not p: continue
        
        score: int = 0
        p_title_low: str = p.title.lower()
        p_summary_low: str = p.summary.lower()
        
        # Exact match (Massive boost)
        if p_title_low == refined_clean: score += 100
        
        # Partial title match
        if refined_clean in p_title_low: score += 50
        
        # Word overlap check
        refined_words = set(re.findall(r'\w+', refined_clean))
        p_title_words = set(re.findall(r'\w+', p_title_low))
        overlap = refined_words.intersection(p_title_words)
        score += len(overlap) * 15
        
        # Subject extraction check for "of" queries
        if str(" of ") in str(refined_clean):
            subject: str = str(refined_clean).split(" of ")[-1].strip()
            if subject in p_title_low:
                # If the title IS exactly the subject (e.g. "Rainbow" for "Color of Rainbow")
                if p_title_low == subject: score += 80
                else: score += 30
            elif subject in str(p_summary_low)[:300]:
                score += 10
        
        # Penalty for disambiguation or list pages unless exact match
        if any(w in p_title_low for w in ["disambiguation", "list of", "color-coded"]):
            if p_title_low != refined_clean:
                score -= 40
        
        scored_pages.append((p, score))
    
    # Sort by score and pick the best
    if scored_pages:
        scored_pages.sort(key=lambda x: x[1], reverse=True)
        best_match = scored_pages[0]
        best_page: PageMock = best_match[0]
        best_score: int = best_match[1]
        
        # Validation threshold
        if best_score > 20: 
            return best_page

    return None

def get_content_summary(text_only, title, original_url, is_blocked=False, wiki_data=None, image_url=None):
    """
    Core logic to summarize text content and return a structured report.
    """
    try:
        # Professional Stop Words for extraction
        STOP_WORDS = {"the", "and", "a", "an", "in", "on", "at", "for", "with", "is", "are", "was", "were", "to", "of", "it", "this", "that", "from", "by", "as"}
        
        # Use Wiki image if direct one isn't found
        if not image_url and wiki_data and 'image' in wiki_data:
            image_url = wiki_data['image']

        # Detect bot blocks etc if not already flagged
        lowered_text = text_only.lower()
        if not is_blocked:
            is_blocked = any(phrase in lowered_text for phrase in [
                "robot check", "captcha", "security check", "access denied", 
                "please enable js", "not redirected", "click here", "redirecting"
            ])

        # Catch-all for very short content
        summary_data = None
        if len(text_only) < 100:
            if is_blocked:
                text_only = "Warning: Access restricted. Synthesis from local archives."
            summary_data = {
                "overview": "Concise Intelligence Brief.",
                "insights": f"• {text_only}"
            }
        
        # 4. Custom Smart Summarizer
        sentences = sent_tokenize(text_only)
        total_s = len(sentences)
        
        if not summary_data:
            if total_s <= 3:
                summary_data = {
                    "overview": "Rapid Information Extract.",
                    "insights": "\n".join([f"• {s.strip()}" for s in sentences])
                }
            else:
                # Overview is a punchy lead intro
                overview_text = sentences[0].strip()
                if len(overview_text) > 130:
                    overview_text = overview_text[:127] + "..."
                
                # Scoring for Insights
                words_in_text = word_tokenize(text_only.lower())
                freq_table = Counter([w for w in words_in_text if w.isalpha() and w not in STOP_WORDS])
                
                sentence_scores = {}
                title_words = set(word_tokenize(title.lower())) if title else set()
                
                professional_boost = {"significantly", "impact", "strategy", "key", "objective", "analysis", "growth", "major", "critical", "development", "innovation"}

                for sent in sentences[1:50]: 
                    score = 0
                    sent_words = word_tokenize(sent.lower())
                    if len(sent_words) < 10 or len(sent_words) > 60: continue
                    
                    for word in sent_words:
                        if word in freq_table: score += min(freq_table[word], 5)
                        if word in title_words: score += 15
                        if word in professional_boost: score += 20
                    
                    if any(char.isdigit() for char in sent): score += 20
                    sentence_scores[sent] = score / (len(sent_words) ** 0.5)

                sorted_sentences: Any = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
                top_insights = [str(s).strip() for s, score in sorted_sentences[:2]]
                
                if not top_insights:
                    top_insights = [s.strip() for s in sentences[1:3]]

                summary_data = {
                    "overview": overview_text,
                    "insights": "\n".join([f"• {s}" for s in top_insights])
                }

        # Metrics
        words = text_only.split()
        word_count = len(words)
        reading_time = max(1, word_count // 200)
        clean_words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in words if w.lower() not in STOP_WORDS and len(w) > 3]
        keywords = [word for word, count in Counter(clean_words).most_common(7)]

        category = "General"
        if "wikipedia" in original_url.lower(): category = "Encyclopedic"
        elif any(w in lowered_text for w in ["research", "study"]): category = "Educational"
        
        # Blocked site handling
        if is_blocked and wiki_data:
            summary_data = {
                "overview": "Access restricted; intelligence synthesized from community archives.",
                "insights": f"• {wiki_data['summary'][:350]}..."
            }

        return {
            "success": True,
            "original_url": original_url,
            "title": title or "Intelligence Report",
            "summary_data": summary_data,
            "full_text": text_only,
            "wiki_data": wiki_data,
            "image_url": image_url,
            "is_blocked": is_blocked,
            "metrics": { "reading_time": reading_time, "keywords": keywords, "category": category, "word_count": word_count }
        }
    except Exception as e:
        return {"success": False, "error": f"Summarization Error: {str(e)}"}

        return {
            "success": True,
            "original_url": original_url,
            "title": title or "Source Intelligence Report",
            "summary_data": summary_data,
            "full_text": text_only,
            "wiki_data": wiki_data,
            "image_url": image_url,
            "is_blocked": is_blocked,
            "metrics": {
                "reading_time": reading_time,
                "keywords": keywords,
                "category": category,
                "word_count": word_count
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Summarization Error: {str(e)}"}

def get_page_summary(url):
    try:
        # 1. Fetch HTML
        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 2. Extract Title and Clean HTML
        doc = Document(response.text)
        clean_html = doc.summary()
        title = doc.title()
        
        image_url = None
        soup = BeautifulSoup(response.text, 'html.parser')
        og_image = soup.find("meta", property="og:image")
        if og_image: image_url = og_image.get("content")
        
        summary_soup = BeautifulSoup(clean_html, 'html.parser')
        text_only = summary_soup.get_text(separator=' ', strip=True)
        
        if len(text_only) < 300:
            full_soup = BeautifulSoup(response.text, 'html.parser')
            for script_or_style in full_soup(["script", "style", "nav", "footer", "header"]):
                script_or_style.decompose()
            text_only = full_soup.get_text(separator=' ', strip=True)

        lowered_text = text_only.lower()
        is_blocked = any(phrase in lowered_text for phrase in [
            "robot check", "captcha", "security check", "access denied", 
            "please enable js", "not redirected", "click here", "redirecting"
        ])

        wiki_data = None
        if is_blocked:
            search_query = title.split(' - ')[0].split(' | ')[0] if title else ""
            page = smart_wiki_search(search_query)
            if page:
                wiki_data = {
                    "title": page.title,
                    "summary": page.summary,
                    "url": page.url,
                    "image": page.images[0] if page.images else None
                }

        return get_content_summary(text_only, title, url, is_blocked, wiki_data, image_url)
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_search_summary(query):
    """
    Search Wikipedia for a query and summarize the results.
    """
    try:
        refined_query = preprocess_query(query)
        page = smart_wiki_search(refined_query)
        if not page:
            return {"success": False, "error": f"No definitive Wikipedia entry found for '{refined_query}'. Try a more specific term."}
        
        wiki_data = {
            "title": page.title,
            "summary": page.summary,
            "url": page.url,
            "image": page.images[0] if page.images else None
        }
        
        return get_content_summary(page.summary, page.title, page.url, is_blocked=False, wiki_data=wiki_data, image_url=wiki_data['image'])
        
    except Exception as e:
        return {"success": False, "error": f"Search Error: {str(e)}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

