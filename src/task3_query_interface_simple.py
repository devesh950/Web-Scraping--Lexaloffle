"""
Task 3: PICO-8 RAG Database Query Interface
Interactive CLI for querying the RAG database and generating code
"""

import os
import csv
import logging
import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class SimplePico8QueryInterface:
    """Simple query interface using CSV data directly (fallback mode)"""
    
    def __init__(self, csv_file: str = 'pico8_games.csv'):
        self.csv_file = csv_file
        self.games = []
        self.load_csv()
    
    def load_csv(self):
        """Load games from CSV"""
        try:
            try:
                df = pd.read_csv(self.csv_file, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(self.csv_file, encoding='latin-1')
            
            self.games = df.to_dict('records')
            logger.info(f"Loaded {len(self.games)} games from CSV")
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            self.games = []
    
    def search_games(self, query_term: str, limit: int = 5) -> list:
        """Search games by keyword in name, description, or author"""
        query_lower = query_term.lower()
        results = []
        
        for game in self.games:
            # Search across multiple fields
            name = str(game.get('game_name', '')).lower()
            desc = str(game.get('description', '')).lower()
            author = str(game.get('author', '')).lower()
            code = str(game.get('game_code', '')).lower()
            
            if (query_lower in name or 
                query_lower in desc or 
                query_lower in author or
                query_lower in code):
                results.append(game)
        
        return results[:limit]
    
    def get_popular_games(self, limit: int = 5) -> list:
        """Return most liked games"""
        sorted_games = sorted(
            self.games, 
            key=lambda x: int(x.get('likes', 0) or 0), 
            reverse=True
        )
        return sorted_games[:limit]
    
    def search_by_author(self, author: str, limit: int = 5) -> list:
        """Search games by author"""
        results = [g for g in self.games if author.lower() in g.get('author', '').lower()]
        return results[:limit]
    
    def format_game(self, game: dict) -> str:
        """Format a game record for display"""
        output = f"""
Game: {game.get('game_name', 'Unknown')}
Author: {game.get('author', 'Unknown')}
Likes: {game.get('likes', 0)}
License: {game.get('license', 'Not specified')}
Description: {game.get('description', 'N/A')}
        """
        return output.strip()
    
    def interactive_session(self):
        """Start interactive query session"""
        print("\n" + "="*70)
        print("PICO-8 RAG Database - Interactive Query Session")
        print("="*70)
        print("\nAvailable Commands:")
        print("  1. search <term>          - Search games by keyword")
        print("  2. author <name>          - Find games by author")
        print("  3. popular                - Get most liked games")
        print("  4. list                   - List all games")
        print("  5. help                   - Show this menu")
        print("  6. exit                   - Exit session")
        print("="*70 + "\n")
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                if command == 'search':
                    if not arg:
                        print("Usage: search <term>")
                        continue
                    logger.info(f"Searching for '{arg}' games...")
                    results = self.search_games(arg)
                    print(f"\nGames matching '{arg}':")
                    if results:
                        for game in results:
                            print(self.format_game(game))
                    else:
                        print("No games found.")
                
                elif command == 'author':
                    if not arg:
                        print("Usage: author <name>")
                        continue
                    logger.info(f"Finding games by author '{arg}'...")
                    results = self.search_by_author(arg)
                    print(f"\nGames by {arg}:")
                    if results:
                        for game in results:
                            print(self.format_game(game))
                    else:
                        print("No games found.")
                
                elif command == 'popular':
                    logger.info("Getting popular games...")
                    results = self.get_popular_games(10)
                    print("\nMost liked games:")
                    for i, game in enumerate(results, 1):
                        print(f"\n{i}. {game.get('game_name')} by {game.get('author')} ({game.get('likes')} likes)")
                
                elif command == 'list':
                    logger.info(f"Listing all {len(self.games)} games...")
                    print(f"\nAll {len(self.games)} games in database:")
                    for i, game in enumerate(self.games, 1):
                        print(f"{i}. {game.get('game_name')} by {game.get('author')} ({game.get('likes')} likes)")
                
                elif command == 'help':
                    print("\nAvailable Commands:")
                    print("  1. search <term>          - Search games by keyword")
                    print("  2. author <name>          - Find games by author")
                    print("  3. popular                - Get most liked games")
                    print("  4. list                   - List all games")
                    print("  5. help                   - Show this menu")
                    print("  6. exit                   - Exit session")
                
                elif command == 'exit':
                    print("Thank you for using PICO-8 Query Interface. Goodbye!")
                    break
                
                else:
                    print("Unknown command. Type 'help' for available commands.")
                
                print()  # Blank line for readability
                
            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"Error: {e}")


def main():
    """Main entry point"""
    print("Initializing PICO-8 Query Interface...")
    
    interface = SimplePico8QueryInterface()
    
    if not interface.games:
        print("Error: Could not load games from CSV file.")
        return
    
    print(f"Successfully loaded {len(interface.games)} games!")
    print("Starting interactive session...\n")
    
    interface.interactive_session()


if __name__ == "__main__":
    main()
