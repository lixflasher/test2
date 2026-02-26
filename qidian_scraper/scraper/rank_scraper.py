import time
import random
import json
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions
from utils.logger import logger
from utils.config import CONF

class RankScraper:
    def __init__(self, start_url=None):
        self.url = start_url or CONF.scraper.get('default_url')
        self.max_books = CONF.scraper.get('max_books', 500)
        self.cache_file = Path("data/rank_cache.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup browser
        co = ChromiumOptions()
        co.headless(False)  # Set to True if you want headless
        co.set_argument('--no-sandbox')
        self.page = ChromiumPage(co)

    def scrape(self):
        books = self._load_cache()
        if len(books) >= self.max_books:
            logger.info(f"Loaded {len(books)} books from cache. Skipping rank scrape.")
            return books[:self.max_books]

        logger.info(f"Starting rank scrape from: {self.url}")
        self.page.get(self.url)
        
        page_num = 1
        while len(books) < self.max_books:
            logger.info(f"Scraping rank page {page_num}...")
            
            # Wait for list to load
            self.page.wait.ele('.book-img-text', timeout=10)
            
            # Extract books on current page
            items = self.page.eles('.book-img-text ul li')
            if not items:
                logger.warning("No book items found on page.")
                break

            for item in items:
                if len(books) >= self.max_books:
                    break
                
                try:
                    book_info = self._parse_item(item)
                    if book_info:
                        # Check for duplicates
                        if not any(b['book_id'] == book_info['book_id'] for b in books):
                            books.append(book_info)
                except Exception as e:
                    logger.error(f"Error parsing item: {e}")

            self._save_cache(books)
            logger.info(f"Collected {len(books)} books so far.")

            if len(books) >= self.max_books:
                break

            # Next page
            next_btn = self.page.ele('css:.pagination li a[class*="lbf-pagination-next"]')
            if next_btn and 'lbf-pagination-disabled' not in next_btn.attr('class'):
                delay = random.uniform(
                    CONF.scraper.get('page_delay_min', 2),
                    CONF.scraper.get('page_delay_max', 5)
                )
                logger.info(f"Waiting {delay:.2f}s before next page...")
                time.sleep(delay)
                next_btn.click()
                page_num += 1
            else:
                logger.info("No more pages.")
                break
        
        self.page.quit()
        return books[:self.max_books]

    def _parse_item(self, item):
        try:
            h2 = item.ele('h2')
            a_tag = h2.ele('a')
            title = a_tag.text
            book_url = a_tag.attr('href')
            # Extract ID from URL (e.g., //book.qidian.com/info/1038473829/)
            book_id = book_url.strip('/').split('/')[-1]
            
            author_ele = item.ele('.author a.name')
            author = author_ele.text if author_ele else "Unknown"
            
            intro_ele = item.ele('.intro')
            intro = intro_ele.text if intro_ele else ""
            
            # Tags usually in .author class or separate tags div
            tags = []
            tag_eles = item.eles('.author a.go-sub-type')
            for t in tag_eles:
                tags.append(t.text)
                
            return {
                "book_id": book_id,
                "title": title,
                "author": author,
                "rank_intro": intro,
                "tags": tags,
                "rank_url": book_url
            }
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_cache(self, data):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
