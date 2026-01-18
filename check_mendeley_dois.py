#!/usr/bin/env python3
"""
Mendeley Library DOI Checker

This script checks a list of DOIs against your Mendeley library to identify
which papers you already have saved.

Usage:
    python check_mendeley_dois.py --dois "10.1038/nature12345,10.1126/science.abc123"
    python check_mendeley_dois.py --file dois.txt
    python check_mendeley_dois.py --interactive

Requirements:
    - Mendeley API credentials (see mendeley_setup_guide.md)
    - Python packages: mendeley, python-dotenv
"""

import os
import json
import argparse
from typing import List, Dict, Set, Tuple
from pathlib import Path
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from mendeley import Mendeley

# Load environment variables
load_dotenv()

# Configuration
CLIENT_ID = os.getenv('MENDELEY_CLIENT_ID')
CLIENT_SECRET = os.getenv('MENDELEY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8080'
TOKEN_FILE = 'mendeley_token.json'


class AuthHandler(BaseHTTPRequestHandler):
    """Simple HTTP server to capture OAuth callback"""
    
    auth_code = None
    
    def do_GET(self):
        """Handle the OAuth redirect"""
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            AuthHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


def authenticate_mendeley() -> Mendeley:
    """
    Authenticate with Mendeley API using OAuth 2.0
    
    Returns:
        Authenticated Mendeley session
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "Mendeley credentials not found. "
            "Please set MENDELEY_CLIENT_ID and MENDELEY_CLIENT_SECRET in .env file. "
            "See mendeley_setup_guide.md for instructions."
        )
    
    mendeley = Mendeley(
        CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI
    )
    
    # Try to load saved token
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            
            # Create session from saved token
            auth = mendeley.start_authorization_code_flow()
            session = auth.authenticate_with_refresh_token(token_data['refresh_token'])
            
            print("✓ Authenticated using saved token")
            return session
        except Exception as e:
            print(f"⚠ Saved token invalid, re-authenticating: {e}")
            os.remove(TOKEN_FILE)
    
    # Perform new OAuth flow
    print("\n=== Mendeley Authentication ===")
    print("Opening browser for authentication...")
    
    auth = mendeley.start_authorization_code_flow()
    login_url = auth.get_login_url()
    
    # Open browser
    webbrowser.open(login_url)
    
    # Start local server to capture callback
    server = HTTPServer(('localhost', 8080), AuthHandler)
    print(f"\nWaiting for authentication callback at {REDIRECT_URI}")
    print("Please complete the login in your browser...")
    
    # Wait for callback
    while AuthHandler.auth_code is None:
        server.handle_request()
    
    # Complete authentication
    auth_response = f"{REDIRECT_URI}?code={AuthHandler.auth_code}"
    session = auth.authenticate(auth_response)
    
    # Save token for future use
    token_data = {
        'access_token': session.token['access_token'],
        'refresh_token': session.token['refresh_token'],
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)
    
    print("✓ Authentication successful! Token saved for future use.\n")
    
    return session


def fetch_library_dois(session) -> Dict[str, Dict]:
    """
    Fetch all documents from Mendeley library and extract DOIs
    
    Args:
        session: Authenticated Mendeley session
    
    Returns:
        Dictionary mapping DOI (lowercase) to document info
    """
    print("Fetching documents from your Mendeley library...")
    
    library_docs = {}
    total_docs = 0
    
    # Iterate through all documents using the SDK's pagination
    for doc in session.documents.iter():
        total_docs += 1
        
        # Check if document has identifiers
        if hasattr(doc, 'identifiers') and doc.identifiers:
            doi = doc.identifiers.get('doi', '').strip()
            
            if doi:
                # Store with lowercase DOI as key for case-insensitive matching
                library_docs[doi.lower()] = {
                    'doi': doi,  # Original case
                    'title': getattr(doc, 'title', 'Untitled'),
                    'year': getattr(doc, 'year', None),
                    'authors': getattr(doc, 'authors', []),
                    'id': doc.id
                }
    
    print(f"✓ Found {total_docs} total documents in library")
    print(f"✓ {len(library_docs)} documents have DOIs\n")
    
    return library_docs


def check_dois(dois_to_check: List[str], library_docs: Dict[str, Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Check which DOIs are in the library
    
    Args:
        dois_to_check: List of DOIs to check
        library_docs: Dictionary of library documents with DOIs
    
    Returns:
        Tuple of (found_docs, missing_dois)
    """
    found_docs = []
    missing_dois = []
    
    for doi in dois_to_check:
        doi_clean = doi.strip().lower()
        
        if doi_clean in library_docs:
            found_docs.append(library_docs[doi_clean])
        else:
            missing_dois.append(doi.strip())
    
    return found_docs, missing_dois


def print_results(dois_checked: List[str], found_docs: List[Dict], missing_dois: List[str]):
    """Print formatted results"""
    
    print(f"\n{'='*70}")
    print(f"RESULTS: Checked {len(dois_checked)} DOIs against your Mendeley library")
    print(f"{'='*70}\n")
    
    if found_docs:
        print(f"✓ ALREADY IN LIBRARY ({len(found_docs)}):\n")
        for doc in found_docs:
            authors = ""
            if doc.get('authors'):
                author_names = [f"{a.get('last_name', '')}" for a in doc['authors'][:2]]
                authors = f" - {', '.join(filter(None, author_names))}"
                if len(doc['authors']) > 2:
                    authors += " et al."
            
            year = f" ({doc['year']})" if doc.get('year') else ""
            print(f"  • {doc['doi']}")
            print(f"    {doc['title']}{authors}{year}")
            print()
    
    if missing_dois:
        print(f"\n✗ NOT IN LIBRARY ({len(missing_dois)}):\n")
        for doi in missing_dois:
            print(f"  • {doi}")
    
    print(f"\n{'='*70}\n")


def save_results(dois_checked: List[str], found_docs: List[Dict], missing_dois: List[str], output_file: str):
    """Save results to JSON file"""
    
    results = {
        'summary': {
            'total_checked': len(dois_checked),
            'found_in_library': len(found_docs),
            'not_in_library': len(missing_dois)
        },
        'in_library': [
            {
                'doi': doc['doi'],
                'title': doc['title'],
                'year': doc.get('year'),
                'mendeley_id': doc['id']
            }
            for doc in found_docs
        ],
        'not_in_library': missing_dois
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Check DOIs against your Mendeley library',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check specific DOIs
  python check_mendeley_dois.py --dois "10.1038/nature12345,10.1126/science.abc123"
  
  # Check DOIs from a file (one per line)
  python check_mendeley_dois.py --file dois.txt
  
  # Interactive mode
  python check_mendeley_dois.py --interactive
  
  # Save results to JSON
  python check_mendeley_dois.py --file dois.txt --output results.json
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dois', type=str, help='Comma-separated list of DOIs')
    group.add_argument('--file', type=str, help='File containing DOIs (one per line)')
    group.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    parser.add_argument('--output', type=str, help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Collect DOIs to check
    dois_to_check = []
    
    if args.dois:
        dois_to_check = [d.strip() for d in args.dois.split(',')]
    elif args.file:
        with open(args.file, 'r') as f:
            dois_to_check = [line.strip() for line in f if line.strip()]
    elif args.interactive:
        print("Enter DOIs (one per line, empty line to finish):")
        while True:
            doi = input("> ").strip()
            if not doi:
                break
            dois_to_check.append(doi)
    
    if not dois_to_check:
        print("No DOIs provided!")
        return
    
    print(f"\nPreparing to check {len(dois_to_check)} DOI(s)...\n")
    
    # Authenticate
    try:
        session = authenticate_mendeley()
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Fetch library
    try:
        library_docs = fetch_library_dois(session)
    except Exception as e:
        print(f"❌ Failed to fetch library: {e}")
        return
    
    # Check DOIs
    found_docs, missing_dois = check_dois(dois_to_check, library_docs)
    
    # Print results
    print_results(dois_to_check, found_docs, missing_dois)
    
    # Save results if requested
    if args.output:
        save_results(dois_to_check, found_docs, missing_dois, args.output)


if __name__ == '__main__':
    main()
