import argparse
import asyncio
import json
from pathlib import Path
from scraper.rank_scraper import RankScraper
from scraper.book_scraper import BookScraper
from analyzer.search import SearchEngine
from analyzer.llm_judge import LLMJudge
from utils.logger import logger
from utils.config import CONF

async def process_book(book, search_engine, llm_judge, semaphore):
    async with semaphore:
        logger.info(f"Analyzing: {book['title']}")
        
        # 1. Search
        search_results = await search_engine.search(book['title'])
        
        # 2. LLM Judge
        result = await llm_judge.judge(book, search_results)
        
        if result:
            return {
                "rank": book.get('rank', 0), # Rank might need to be added during scraping
                "title": book['title'],
                "author": book['author'],
                "is_multi_heroine": result.get('is_multi_heroine'),
                "confidence": result.get('confidence'),
                "reason": result.get('reason')
            }
        return None

async def main_async(books):
    search_engine = SearchEngine()
    llm_judge = LLMJudge()
    
    # Limit concurrency for LLM/Search to avoid rate limits
    semaphore = asyncio.Semaphore(5)
    
    tasks = [process_book(book, search_engine, llm_judge, semaphore) for book in books]
    results = await asyncio.gather(*tasks)
    
    return [r for r in results if r is not None]

def main():
    parser = argparse.ArgumentParser(description="Qidian Multi-Heroine Scraper")
    parser.add_argument("--url", help="Override rank URL")
    args = parser.parse_args()

    # 1. Scrape Rank
    rank_scraper = RankScraper(start_url=args.url)
    basic_books = rank_scraper.scrape()
    logger.info(f"Rank scraping complete. Got {len(basic_books)} books.")

    # 2. Scrape Details
    book_scraper = BookScraper()
    detailed_books = book_scraper.scrape_details(basic_books)
    logger.info("Detail scraping complete.")

    # 3. Analyze (Async)
    logger.info("Starting analysis...")
    results = asyncio.run(main_async(detailed_books))
    
    # 4. Filter and Save
    final_results = [r for r in results if r['is_multi_heroine'] is True]
    final_results.sort(key=lambda x: x['confidence'] or 0, reverse=True)
    
    output_file = Path("data/results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Analysis complete. Found {len(final_results)} potential multi-heroine books.")
    logger.info(f"Results saved to {output_file}")
    
    # Print to terminal
    print("\n" + "="*50)
    print("Top Multi-Heroine Candidates:")
    print("="*50)
    for book in final_results[:20]:
        print(f"[{book['confidence']}%] {book['title']} - {book['author']}")
        print(f"Reason: {book['reason']}")
        print("-" * 30)

if __name__ == "__main__":
    main()
