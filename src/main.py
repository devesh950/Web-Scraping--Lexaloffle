#!/usr/bin/env python
"""
Main Entry Point for Pico-8 Assessment Project
Orchestrates running all tasks in sequence or individually
"""

import sys
import os
import argparse
import logging
from config import validate_setup, PROJECT_ROOT, CSV_PATH, DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def run_task1():
    """Run Task 1: Web Scraper"""
    print_header("TASK 1: WEB SCRAPER - Lexaloffle Pico-8 Games")
    
    logger.info("Starting Task 1 - Web Scraping...")
    logger.info("This will scrape 100 games from Lexaloffle.com")
    logger.info("Estimated time: 10-15 minutes\n")
    
    try:
        from task1_scrape import LexaloffleeScraper
        
        scraper = LexaloffleeScraper()
        games = scraper.scrape_games(num_games=100)
        scraper.save_to_csv('pico8_games.csv')
        
        if os.path.exists('pico8_games.csv'):
            logger.info(f"✅ Task 1 Complete: Created pico8_games.csv with {len(games)} games")
            return True
        else:
            logger.error("❌ CSV file not created")
            return False
    
    except Exception as e:
        logger.error(f"❌ Task 1 Failed: {e}")
        return False


def run_task2():
    """Run Task 2: RAG Database Setup"""
    print_header("TASK 2: RAG DATABASE - Initialize Vector Database")
    
    # Check if CSV exists
    if not os.path.exists('pico8_games.csv'):
        logger.error("❌ pico8_games.csv not found!")
        logger.info("Please run Task 1 first: python main.py --task 1")
        return False
    
    logger.info("Starting Task 2 - RAG Database Setup...")
    logger.info("This will create embeddings and initialize the vector database")
    logger.info("Estimated time: 2-3 minutes\n")
    
    try:
        from task2_rag import Pico8RAGDatabase
        
        db = Pico8RAGDatabase()
        
        # Initialize database
        if db.initialize_rag_database():
            logger.info("✅ Database initialized successfully")
            
            # Setup QA chain
            if db.setup_qa_chain():
                logger.info("✅ QA chain configured")
                logger.info("✅ Task 2 Complete: RAG database ready for queries")
                return True
            else:
                logger.error("❌ Failed to setup QA chain")
                return False
        else:
            logger.error("❌ Failed to initialize database")
            return False
    
    except Exception as e:
        logger.error(f"❌ Task 2 Failed: {e}")
        if "OPENAI_API_KEY" in str(e):
            logger.info("\n⚠️  OpenAI API key not set!")
            logger.info("1. Create a .env file with: OPENAI_API_KEY=sk-xxxxx")
            logger.info("2. Get API key from: https://platform.openai.com/account/api-keys")
        return False


def run_task3():
    """Run Task 3: Interactive Query Interface"""
    print_header("TASK 3: QUERY INTERFACE - Interactive Session")
    
    # Check if RAG database exists
    if not os.path.exists(DB_PATH):
        logger.error("❌ RAG database not found!")
        logger.info("Please run Task 2 first: python main.py --task 2")
        return False
    
    logger.info("Starting Task 3 - Query Interface...")
    logger.info("Type 'help' for available commands\n")
    
    try:
        from task3_query_interface import Pico8RAGQueryInterface
        
        interface = Pico8RAGQueryInterface()
        if interface.initialized:
            interface.interactive_session()
            return True
        else:
            logger.error("❌ Failed to initialize query interface")
            logger.info("Make sure you have OPENAI_API_KEY set in .env")
            return False
    
    except Exception as e:
        logger.error(f"❌ Task 3 Failed: {e}")
        return False


def run_all_tasks():
    """Run all tasks in sequence"""
    print_header("RUNNING ALL TASKS IN SEQUENCE")
    
    results = {}
    
    # Task 1
    logger.info("Starting Task 1/3...")
    results['task1'] = run_task1()
    
    if not results['task1']:
        logger.error("❌ Task 1 failed, cannot proceed to Task 2")
        return results
    
    # Task 2
    logger.info("\nStarting Task 2/3...")
    results['task2'] = run_task2()
    
    if not results['task2']:
        logger.warning("⚠️  Task 2 encountered issues (check API key)")
    
    # Task 3
    if results['task2']:
        logger.info("\nStarting Task 3/3...")
        results['task3'] = run_task3()
    
    return results


def print_summary(results):
    """Print execution summary"""
    print_header("EXECUTION SUMMARY")
    
    tasks = {
        'task1': 'Web Scraper (CSV Export)',
        'task2': 'RAG Database Setup',
        'task3': 'Query Interface'
    }
    
    for task_id, task_name in tasks.items():
        if task_id in results:
            status = "✅ PASS" if results[task_id] else "❌ FAIL"
            print(f"{task_name}: {status}")


def show_menu():
    """Show interactive menu"""
    print_header("PICO-8 ASSESSMENT - MAIN MENU")
    
    print("Select task to run:")
    print("  1. Task 1 - Web Scraper")
    print("  2. Task 2 - RAG Database")
    print("  3. Task 3 - Query Interface")
    print("  4. Run All Tasks (1→2→3)")
    print("  5. Validate Setup")
    print("  6. Exit\n")
    
    choice = input("Enter choice (1-6): ").strip()
    
    if choice == '1':
        run_task1()
    elif choice == '2':
        run_task2()
    elif choice == '3':
        run_task3()
    elif choice == '4':
        results = run_all_tasks()
        print_summary(results)
    elif choice == '5':
        validate_setup()
    elif choice == '6':
        logger.info("Exiting...")
        sys.exit(0)
    else:
        logger.error("Invalid choice")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Pico-8 Machine Learning Assessment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Show interactive menu
  python main.py --task 1           # Run just Task 1
  python main.py --task 2           # Run just Task 2
  python main.py --task 3           # Run just Task 3
  python main.py --all              # Run all tasks in sequence
  python main.py --validate         # Validate setup

For more info, see README.md
        """
    )
    
    parser.add_argument('--task', type=int, choices=[1, 2, 3],
                       help='Run specific task')
    parser.add_argument('--all', action='store_true',
                       help='Run all tasks in sequence')
    parser.add_argument('--validate', action='store_true',
                       help='Validate project setup')
    
    args = parser.parse_args()
    
    # Validate setup first
    if not validate_setup():
        if args.task or args.all:
            sys.exit(1)
    
    # Execute based on arguments
    if args.validate:
        sys.exit(0)
    elif args.task == 1:
        run_task1()
    elif args.task == 2:
        run_task2()
    elif args.task == 3:
        run_task3()
    elif args.all:
        results = run_all_tasks()
        print_summary(results)
    else:
        # Show interactive menu
        try:
            while True:
                show_menu()
                again = input("\nRun another task? (y/n): ").strip().lower()
                if again != 'y':
                    break
        except KeyboardInterrupt:
            logger.info("\n\nExiting...")


if __name__ == '__main__':
    main()
