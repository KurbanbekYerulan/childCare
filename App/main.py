#!/usr/bin/env python3
"""
Screenpipe-Gemini Integration
----------------------------
This application connects Screenpipe's OCR data with a local Gemini instance,
allowing you to query your screen content using natural language.
"""

import argparse
import sys
import os
from screenpipe_connector import ScreenpipeConnector
from llama_client import LlamaClient
from query_engine import QueryEngine
import config

def parse_arguments():
    parser = argparse.ArgumentParser(description='Screenpipe-Gemini Integration')
    parser.add_argument('--db-path', type=str, default=config.SCREENPIPE_DB_PATH,
                        help='Path to Screenpipe SQLite database')
    parser.add_argument('--api-key', type=str, default=os.environ.get("GOOGLE_API_KEY", ""),
                        help='Google Gemini API key')
    parser.add_argument('--time-window', type=int, default=config.DEFAULT_TIME_WINDOW,
                        help='Time window in seconds for retrieving OCR data')
    parser.add_argument('--query', type=str,
                        help='Query to run against screen content')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive mode')
    parser.add_argument('--analyze', action='store_true',
                        help='Automatically analyze current app')
    return parser.parse_args()

def interactive_mode(query_engine):
    """Run in interactive mode."""
    print("\nScreenpipe-Gemini Interactive Mode")
    print("Type 'exit' or 'quit' to exit")
    print("Type 'analyze' to analyze the current app")
    print("Or enter your query about recent screen content\n")
    
    while True:
        user_input = input("\nQuery: ")
        
        if user_input.lower() in ['exit', 'quit']:
            break
        elif user_input.lower() == 'analyze':
            print("\nAnalyzing current app...")
            result = query_engine.analyze_current_app()
            print("\nAnalysis Result:")
            print(result)
        elif user_input.strip():
            print("\nProcessing query...")
            result = query_engine.process_query(user_input)
            print("\nResponse:")
            print(result)

def main():
    args = parse_arguments()
    
    try:
        # Initialize components
        screenpipe = ScreenpipeConnector(args.db_path)
        
        # Check Screenpipe connection
        if not screenpipe.test_connection():
            print("Error: Cannot connect to Screenpipe database")
            return 1
        
        # Set API key from args if provided
        if args.api_key:
            os.environ["GOOGLE_API_KEY"] = args.api_key
        
        # Initialize Gemini client
        llama = LlamaClient()
        
        # Test Gemini connection
        gemini_connected = llama.test_connection()
        if not gemini_connected:
            print("Error: Cannot connect to Google Gemini API")
            print("Please set your API key with: export GOOGLE_API_KEY=your_key_here")
            print("Get a free API key at: https://makersuite.google.com/app/apikey")
            return 1
        
        query_engine = QueryEngine(screenpipe, llama, args.time_window)
        
        # Run in appropriate mode
        if args.analyze:
            result = query_engine.analyze_current_app()
            print(result)
        elif args.interactive:
            interactive_mode(query_engine)
        elif args.query:
            result = query_engine.process_query(args.query)
            print(result)
        else:
            # Default to analysis mode
            result = query_engine.analyze_current_app()
            print(result)
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 