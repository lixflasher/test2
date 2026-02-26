import httpx
from bs4 import BeautifulSoup
from utils.logger import logger
from utils.config import CONF

class SearchEngine:
    def __init__(self):
        self.enabled = CONF.search.get('enabled', False)
        self.max_results = CONF.search.get('max_results', 5)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

    async def search(self, query):
        if not self.enabled:
            return ""
        
        search_query = f"{query} 多女主 OR 后宫"
        url = "https://www.bing.com/search"
        params = {"q": search_query}
        
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
                resp = await client.get(url, params=params, timeout=10.0)
                
            if resp.status_code != 200:
                logger.warning(f"Search failed with status {resp.status_code}")
                return ""

            return self._parse_bing(resp.text)
            
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")
            return ""

    def _parse_bing(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Bing standard results usually in 'li.b_algo'
        items = soup.select('li.b_algo')
        
        for item in items[:self.max_results]:
            title_tag = item.select_one('h2 a')
            snippet_tag = item.select_one('.b_caption p') or item.select_one('.b_algoSlug')
            
            if title_tag:
                title = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                results.append(f"标题: {title}\n摘要: {snippet}")
        
        return "\n\n".join(results)
