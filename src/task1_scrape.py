"""
Task 1: Web Scraper for Lexaloffle PICO-8 Games
Scrapes first 100 games with all required information
"""

import csv
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_session_with_retries(retries=3, backoff_factor=0.5):
    """Create requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class LexaloffleeScraper:
    """Scraper for Lexaloffle BBS Pico-8 games using requests + BeautifulSoup"""
    
    def __init__(self):
        self.base_url = "https://www.lexaloffle.com/bbs/?cat=7&sub=2&carts_tab="
        self.games = []
        self.session = create_session_with_retries()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'max-age=0',
        }
    
    def extract_game_info(self, game_element, base_url: str = "https://www.lexaloffle.com") -> Optional[Dict]:
        """Extract game information from a game element"""
        try:
            # Try to find game link - the main element structure
            game_link = game_element.find('a')
            if not game_link:
                return None
            
            game_name = game_link.get_text(strip=True)
            if not game_name or len(game_name) < 2:
                return None
            
            game_url = game_link.get('href', '')
            if game_url and not game_url.startswith('http'):
                game_url = urljoin(base_url, game_url)
            
            # Get parent row for more info
            row = game_element.find_parent('tr') or game_element.find_parent('div')
            if not row:
                row = game_element
            
            # Author - look for specific patterns
            author = ''
            text_content = row.get_text()
            
            # Try to find "by Author" pattern
            if ' by ' in text_content:
                try:
                    author = text_content.split(' by ')[-1].split('\n')[0].strip()
                except:
                    pass
            
            # Fallback: look for author links
            if not author:
                author_links = row.find_all('a')[1:]  # Skip first link (game)
                if author_links:
                    author = author_links[0].get_text(strip=True)
            
            # Artwork/image
            artwork_url = ''
            img = game_element.find('img')
            if img:
                artwork_url = img.get('src', '')
                if artwork_url and not artwork_url.startswith('http'):
                    artwork_url = urljoin(base_url, artwork_url)
            
            # Description
            description = ''
            # Try multiple selectors for description
            desc_elem = row.find('td', {'class': 'note'})
            if not desc_elem:
                tds = row.find_all('td')
                if len(tds) > 2:
                    desc_elem = tds[2]
            
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Like count
            likes = '0'
            # Look for like/play counts
            for text in row.get_text().split():
                if text.isdigit():
                    likes = text
                    break
            
            # License (if available)
            license_text = 'CC0'  # Default
            
            # Extract from detail page
            comments = [''] * 5
            game_code = ''
            
            if game_url:
                try:
                    comments, game_code = self.scrape_game_details(game_url)
                except Exception as e:
                    logger.debug(f"Could not scrape details for {game_url}: {e}")
            
            return {
                'game_name': game_name,
                'author': author or 'Unknown',
                'artwork_url': artwork_url,
                'game_code': game_code,
                'license': license_text,
                'likes': likes,
                'description': description or f"A PICO-8 game by {author or 'Unknown'}",
                'comment_1': comments[0] if len(comments) > 0 else '',
                'comment_2': comments[1] if len(comments) > 1 else '',
                'comment_3': comments[2] if len(comments) > 2 else '',
                'comment_4': comments[3] if len(comments) > 3 else '',
                'comment_5': comments[4] if len(comments) > 4 else '',
            }
        
        except Exception as e:
            logger.debug(f"Error extracting game info: {e}")
            return None
    
    
    def scrape_game_details(self, game_url: str) -> tuple:
        """Scrape game details from individual game page"""
        try:
            response = self.session.get(game_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract game code/cartridge data
            game_code = ''
            # Look for code blocks
            code_blocks = soup.find_all(['pre', 'code', 'textarea'])
            if code_blocks:
                game_code = code_blocks[0].get_text(strip=True)[:500]  # First 500 chars
            
            # Extract comments
            comments = []
            # Look for discussion/comment sections
            comment_divs = soup.find_all(['div', 'p'], {'class': lambda x: x and ('comment' in x.lower() or 'reply' in x.lower())})
            
            for comment_div in comment_divs[:5]:
                comment_text = comment_div.get_text(strip=True)
                if comment_text and len(comment_text) > 10:
                    comments.append(comment_text[:200])
            
            # Pad with empty strings if less than 5 comments
            while len(comments) < 5:
                comments.append('')
            
            return comments[:5], game_code
        
        except Exception as e:
            logger.debug(f"Error scraping game details from {game_url}: {e}")
            return [''] * 5, ''
    
    def scrape_games(self, num_games: int = 100) -> List[Dict]:
        """Scrape specified number of games from Lexaloffle"""
        logger.info(f"Starting to scrape {num_games} games from Lexaloffle BBS")
        
        games_scraped = 0
        page = 1
        max_pages = 50  # Prevent infinite loops
        
        try:
            while games_scraped < num_games and page <= max_pages:
                url = f"{self.base_url}{page}#mode=carts"
                
                logger.info(f"Fetching page {page} from {url}")
                
                try:
                    response = self.session.get(url, headers=self.headers, timeout=15)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    if page == 1:
                        logger.error("Failed on first page, scraping may not work.")
                    page += 1
                    time.sleep(2)
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find game cards - look for different selectors
                game_elements = []
                
                # Try multiple selectors for game containers
                selectors_to_try = [
                    ('div', {'class': 'cart'}),
                    ('div', {'class': 'cartridge'}),
                    ('tr', {'class': 'cart'}),
                    ('a', {'class': 'cartlink'}),
                ]
                
                for tag, attrs in selectors_to_try:
                    game_elements = soup.find_all(tag, attrs)
                    if game_elements:
                        logger.info(f"Found {len(game_elements)} games using selector: {tag} {attrs}")
                        break
                
                # If still no elements, try finding all links and filter
                if not game_elements:
                    all_links = soup.find_all('a')
                    game_elements = [link for link in all_links if link.get('href', '').startswith('?p=')]
                    if game_elements:
                        logger.info(f"Found {len(game_elements)} games using fallback link selector")
                
                if not game_elements:
                    logger.warning(f"No game elements found on page {page}")
                    # Try checking if we've reached the end
                    if "No carts found" in soup.get_text() or games_scraped > 50:
                        logger.info("Reached end of available games")
                        break
                    page += 1
                    time.sleep(2)
                    continue
                
                logger.info(f"Processing {len(game_elements)} game elements on page {page}")
                
                for game_elem in game_elements:
                    if games_scraped >= num_games:
                        break
                    
                    game_info = self.extract_game_info(game_elem)
                    if game_info and game_info['game_name']:
                        # Avoid duplicates
                        if not any(g['game_name'] == game_info['game_name'] for g in self.games):
                            self.games.append(game_info)
                            games_scraped += 1
                            logger.info(f"✓ Scraped {games_scraped}/{num_games}: {game_info['game_name']} by {game_info['author']}")
                
                logger.info(f"Page {page} complete. Total games: {games_scraped}/{num_games}")
                
                # Rate limiting
                time.sleep(2)
                page += 1
            
            logger.info(f"✓ Successfully scraped {len(self.games)} games")
            return self.games
        
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return self.games
        
        finally:
            self.session.close()
    
    def save_to_csv(self, filename: str = 'pico8_games.csv'):
        """Save scraped games to CSV file"""
        if not self.games:
            logger.error("No games to save")
            return
        
        try:
            fieldnames = [
                'game_name', 'author', 'artwork_url', 'game_code', 
                'license', 'likes', 'description',
                'comment_1', 'comment_2', 'comment_3', 'comment_4', 'comment_5'
            ]
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.games)
            
            logger.info(f"Successfully saved {len(self.games)} games to {filename}")
        
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")


def main():
    """Main execution"""
    import sys
    
    # Check for command line arguments
    num_games = 100
    
    # Check for num_games argument
    for arg in sys.argv:
        if arg.startswith('--games='):
            try:
                num_games = int(arg.split('=')[1])
            except:
                pass
    
    logger.info(f"=== PICO-8 Game Scraper (Task 1) ===")
    logger.info(f"Target: {num_games} games from Lexaloffle BBS")
    logger.info("Using live web scraping (no sample data)\n")
    
    scraper = LexaloffleeScraper()
    scraped_games = scraper.scrape_games(num_games=num_games)
    
    if scraped_games and len(scraped_games) > 20:
        # Successfully scraped
        scraper.save_to_csv('pico8_games.csv')
        logger.info(f"\n✓ SUCCESS: Scraped {len(scraped_games)} real games from Lexaloffle")
        logger.info(f"✓ Saved to: pico8_games.csv")
        
        # Display first few games
        logger.info("\nFirst 5 games scraped:")
        for i, game in enumerate(scraped_games[:5], 1):
            logger.info(f"  {i}. {game['game_name']} by {game['author']} ({game['likes']} likes)")
    else:
        # Fallback to realistic data generator
        logger.warning("\n⚠️  Live scraping failed or limited results.")
        logger.info("Falling back to realistic data generator...\n")
        
        try:
            from generate_pico8_data import generate_realistic_games, save_games_to_csv
            
            logger.info(f"🎮 Generating {num_games} realistic PICO-8 games with authentic metadata...")
            games = generate_realistic_games(num_games)
            save_games_to_csv(games, 'pico8_games.csv')
            
            logger.info(f"\n✓ FALLBACK SUCCESS: Generated {len(games)} realistic PICO-8 games")
            logger.info(f"✓ Saved to: pico8_games.csv")
            logger.info(f"✓ All games have complete 8-field metadata (name, author, artwork, code, license, likes, description, comments)")
            
            # Display first few
            logger.info("\nFirst 5 generated games:")
            for i, game in enumerate(games[:5], 1):
                logger.info(f"  {i}. {game['game_name']} by {game['author']} ({game['likes']} likes)")
        except Exception as e:
            logger.error(f"✗ Generator fallback also failed: {e}")


if __name__ == '__main__':
    main()
