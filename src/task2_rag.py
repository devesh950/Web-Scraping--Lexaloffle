"""
Task 2: RAG Database for Pico-8 Game Information
Converts scraped dataset into queryable RAG database
"""

import os
import csv
import logging
from typing import List, Dict, Optional
import pandas as pd
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class Pico8RAGDatabase:
    """RAG Database for Pico-8 games and code generation"""
    
    def __init__(self, persist_dir: str = './pico8_db', csv_file: str = 'pico8_games.csv'):
        self.persist_dir = persist_dir
        self.csv_file = csv_file
        self.db = None
        self.retriever = None
        self.qa_chain = None
        self.embeddings = None
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)
    
    def load_csv_data(self) -> List[Document]:
        """Load game data from CSV and convert to documents"""
        logger.info(f"Loading data from {self.csv_file}")
        
        documents = []
        
        try:
            try:
                df = pd.read_csv(self.csv_file, encoding='utf-8')
            except UnicodeDecodeError:
                logger.warning("UTF-8 decoding failed, trying latin-1")
                df = pd.read_csv(self.csv_file, encoding='latin-1')
            
            for idx, row in df.iterrows():
                # Create a comprehensive document for each game
                content = f"""
Game: {row.get('game_name', 'Unknown')}
Author: {row.get('author', 'Unknown')}
Description: {row.get('description', 'No description')}
Likes: {row.get('likes', 0)}
License: {row.get('license', 'Not specified')}
Game Code: {row.get('game_code', 'N/A')}

Top Comments:
1. {row.get('comment_1', 'No comments')}
2. {row.get('comment_2', '')}
3. {row.get('comment_3', '')}
4. {row.get('comment_4', '')}
5. {row.get('comment_5', '')}

Artwork: {row.get('artwork_url', 'N/A')}
                """
                
                metadata = {
                    'game_name': row.get('game_name', 'Unknown'),
                    'author': row.get('author', 'Unknown'),
                    'likes': row.get('likes', 0),
                    'index': idx
                }
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} game documents from CSV")
            return documents
        
        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_file}")
            return []
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            return []
    
    def initialize_rag_database(self):
        """Initialize RAG database with embeddings and vector store"""
        logger.info("Initializing RAG database...")
        
        # Check for API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OpenAI API key not found. Using mock embeddings for demo.")
            # For local development, you can use other embeddings
            # from langchain.embeddings import HuggingFaceEmbeddings
            # self.embeddings = HuggingFaceEmbeddings()
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        
        # Load documents
        documents = self.load_csv_data()
        
        if not documents:
            logger.error("No documents to process")
            return False
        
        # Split documents if they're too large
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        
        split_documents = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(split_documents)} chunks")
        
        # Create vector store
        try:
            logger.info("Creating vector store with Chroma...")
            self.db = Chroma.from_documents(
                documents=split_documents,
                embedding=self.embeddings,
                persist_directory=self.persist_dir,
                collection_name="pico8_games"
            )
            logger.info("Vector store created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            return False
    
    def load_existing_database(self):
        """Load existing RAG database from disk"""
        logger.info("Loading existing RAG database...")
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        
        try:
            self.db = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="pico8_games"
            )
            logger.info("Successfully loaded existing database")
            return True
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return False
    
    def setup_qa_chain(self):
        """Setup QA chain for querying the RAG database"""
        if not self.db:
            logger.error("Database not initialized")
            return False
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # Create retriever
            self.retriever = self.db.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # Create LLM
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.2,
                api_key=api_key
            )
            
            # Create prompt template for Pico-8 code generation
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are an expert Pico-8 developer. 
                Use the provided game information and code examples to answer questions about Pico-8 games.
                If asked to generate code, provide Pico-8 Lua code snippets.
                Context from retrieved documents:
                {context}"""),
                ("human", "{question}")
            ])
            
            # Create a simple chain using RunnablePassthrough
            def format_docs(docs):
                return "\n\n".join([doc.page_content for doc in docs])
            
            # Create the chain without using RetrievalQA
            self.qa_chain = (
                {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
                | prompt_template
                | llm
            )
            
            logger.info("QA chain setup successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error setting up QA chain: {e}")
            return False
    
    def query(self, question: str) -> Dict:
        """Query the RAG database"""
        if not self.qa_chain:
            logger.error("QA chain not initialized")
            return {"error": "QA chain not initialized"}
        
        try:
            # The new chain structure returns an AIMessage directly
            result = self.qa_chain.invoke(question)
            
            # Extract content from the AIMessage
            if hasattr(result, 'content'):
                answer = result.content
            else:
                answer = str(result)
            
            return {
                "question": question,
                "answer": answer,
                "sources": []
            }
        except Exception as e:
            logger.error(f"Error querying database: {e}")
            return {"error": str(e)}
    
    def search_games(self, query: str, k: int = 5) -> List[Dict]:
        """Search for games by query"""
        if not self.db:
            logger.error("Database not initialized")
            return []
        
        try:
            results = self.db.similarity_search(query, k=k)
            
            games = []
            for doc in results:
                games.append({
                    "game": doc.metadata.get('game_name', 'Unknown'),
                    "author": doc.metadata.get('author', 'Unknown'),
                    "relevance": doc.metadata.get('likes', 0),
                    "content": doc.page_content[:500]  # First 500 chars
                })
            
            return games
        except Exception as e:
            logger.error(f"Error searching games: {e}")
            return []


def main():
    """Main execution for RAG database setup"""
    
    # Check if CSV file exists
    if not os.path.exists('pico8_games.csv'):
        logger.error("pico8_games.csv not found. Run task1_scrape.py first.")
        return
    
    # Initialize RAG database
    rag_db = Pico8RAGDatabase()
    
    # Initialize database (or load existing)
    db_initialized = rag_db.initialize_rag_database()
    if not db_initialized:
        logger.info("Attempting to load existing database...")
        db_initialized = rag_db.load_existing_database()
    
    if not db_initialized:
        logger.error("Failed to initialize or load database")
        return
    
    # Setup QA chain
    qa_setup = rag_db.setup_qa_chain()
    if not qa_setup:
        logger.error("Failed to setup QA chain")
        return
    
    # Example queries
    logger.info("\n" + "="*60)
    logger.info("RAG Database Ready for Queries")
    logger.info("="*60)
    
    # Test search
    search_results = rag_db.search_games("puzzle platformer", k=5)
    logger.info("\nSearch Results for 'puzzle platformer':")
    for game in search_results:
        logger.info(f"  - {game['game']} by {game['author']}")
    
    logger.info("\nRAG database initialized successfully!")
    logger.info("Use rag_db.query() or rag_db.search_games() for queries")


if __name__ == '__main__':
    main()
