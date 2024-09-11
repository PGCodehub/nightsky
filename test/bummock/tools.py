# tools.py
import requests
import time
from typing import List, Dict, Any  # Ensure List is imported
from dotenv import load_dotenv
import os
from firecrawl.firecrawl import FirecrawlApp


load_dotenv()

def tavily_search(query: str, state) -> Dict[str, Any]:
    # Check cache
    if query in state.cache:
        return state, state.cache[query]
    
    # Check rate limit
    current_time = time.time()
    if state.last_search_time and current_time - state.last_search_time < 1:  # 1 second rate limit
        return state, {"error": "Rate limit exceeded"}
    
    if state.requests_remaining <= 0:
        return state, {"error": "API request limit reached"}
    
    url = "https://api.tavily.com/search"
    headers = {
        "content-type": "application/json"
    }
    data = {
        "api_key": os.getenv('TAVILY_SEARCH_API_KEY'),
        "query": query,
        "search_depth": state.search_depth
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        state.last_search_time = current_time
        state.requests_remaining -= 1
        
        if response.status_code == 200:
            result = response.json()
            state.cache[query] = result
            return state, result
        else:
            return state, {"error": f"API request failed with status code {response.status_code}: {response.text}"}
    except requests.RequestException as e:
        return state, {"error": f"Request failed: {str(e)}"}


def firecrawl_scrape(urls: List[str], state) -> Dict[str, Any]:
    results = []
    for url in urls:
        # Check cache
        if url in state.cache:
            results.append(state.cache[url])
            continue

        # Check rate limit
        current_time = time.time()
        if state.last_scrape_time and current_time - state.last_scrape_time < 1:
            logging.warning(f"Rate limit exceeded for URL: {url}")
            results.append({"status": "error", "message": "Rate limit exceeded", "url": url})
            continue
        
        if state.requests_remaining <= 0:
            logging.warning("API request limit reached")
            results.append({"status": "error", "message": "API request limit reached", "url": url})
            break  # Stop processing remaining URLs
        
        try:
            app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))
            scrape_result = app.scrape_url(url)
            
            state.last_scrape_time = current_time
            state.requests_remaining -= 1
            
            result = {
                "status": "success",
                "markdown": scrape_result['markdown'],
                "full_data": scrape_result,
                "url": url
            }
            state.cache[url] = result
            results.append(result)
            logging.info(f"Successfully scraped URL: {url}")
        except Exception as e:
            logging.error(f"Error scraping URL {url}: {str(e)}")
            results.append({"status": "error", "message": str(e), "url": url})

    return {
        "results": results,
        "state": state
    }