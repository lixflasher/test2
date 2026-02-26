import time
import random
import json
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions
from utils.logger import logger
from utils.config import CONF

class BookScraper:
    def __init__(self):
        self.cache_file = Path("data/details_cache.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        co = ChromiumOptions()
        co.headless(False)
        co.set_argument('--no-sandbox')
        self.page = ChromiumPage(co)

    def scrape_details(self, books):
        detailed_books = self._load_cache()
        processed_ids = {b['book_id'] for b in detailed_books}
        
        books_to_process = [b for b in books if b['book_id'] not in processed_ids]
        logger.info(f"Found {len(books_to_process)} books to scrape details for.")

        for i, book in enumerate(books_to_process):
            logger.info(f"[{i+1}/{len(books_to_process)}] Scraping details for: {book['title']}")
            
            try:
                details = self._get_single_book(book['book_id'])
                if details:
                    # Merge details into book object
                    full_book = {**book, **details}
                    detailed_books.append(full_book)
                    self._save_cache(detailed_books)
                
                delay = random.uniform(
                    CONF.scraper.get('detail_delay_min', 3),
                    CONF.scraper.get('detail_delay_max', 8)
                )
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Failed to scrape {book['title']}: {e}")
                continue

        self.page.quit()
        return detailed_books

    def _get_single_book(self, book_id):
        url = f"https://book.qidian.com/info/{book_id}/"
        self.page.get(url)
        
        # Wait for content
        if not self.page.wait.ele('.book-info', timeout=10):
            logger.warning(f"Timeout waiting for book info: {book_id}")
            return None

        # Full Synopsis
        synopsis_ele = self.page.ele('.book-intro p')
        synopsis = synopsis_ele.text.strip() if synopsis_ele else ""

        # Tags (often in .tag-wrap)
        tags = []
        tag_eles = self.page.eles('.tag-wrap .tags')
        for t in tag_eles:
            tags.append(t.text)

        # Free Chapters (First 3)
        free_chapters_summary = ""
        try:
            # Click 'Catalog' tab if exists, or find chapter links
            # Qidian often has a "Catalog" (目录) button
            catalog_btn = self.page.ele('#j_catalogBtn')
            if catalog_btn:
                catalog_btn.click()
                self.page.wait.ele('.volume-wrap', timeout=5)
            
            # Get first few chapters
            chapter_links = self.page.eles('.volume-wrap .cf li a')[:3]
            chapter_texts = []
            
            # We need to visit these links. 
            # To avoid losing context, we can open new tabs or just use the current one and go back.
            # Using new tab is safer.
            current_tab = self.page.tab_id
            
            for link in chapter_links:
                chap_url = link.attr('href')
                if not chap_url.startswith('http'):
                    chap_url = 'https:' + chap_url
                
                new_tab = self.page.new_tab(chap_url)
                if new_tab.wait.ele('.read-content', timeout=5):
                    content = new_tab.ele('.read-content').text[:500] # First 500 chars
                    chapter_texts.append(content)
                new_tab.close()
            
            free_chapters_summary = "\n---\n".join(chapter_texts)

        except Exception as e:
            logger.warning(f"Could not fetch chapters for {book_id}: {e}")

        return {
            "full_synopsis": synopsis,
            "all_tags": tags,
            "free_chapters_summary": free_chapters_summary
        }

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
