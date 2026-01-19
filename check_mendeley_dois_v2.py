#!/usr/bin/env python3
"""
Mendeley Library DOI Checker (Direct API Version)

This script checks a list of DOIs against your Mendeley library using
the Mendeley API directly (without the deprecated SDK).

Usage:
    python check_mendeley_dois_v2.py --dois "10.1038/nature12345,10.1126/science.abc123"
    python check_mendeley_dois_v2.py --file dois.txt
    python check_mendeley_dois_v2.py --interactive
"""

import os
import json
import argparse
from typing import List, Dict, Tuple
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
CLIENT_ID = os.getenv('MENDELEY_CLIENT_ID')
CLIENT_SECRET = os.getenv('MENDELEY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8080'
TOKEN_FILE = 'mendeley_token.json'

# API endpoints
AUTH_URL = 'https://api.mendeley.com/oauth/authorize'
TOKEN_URL = 'https://api.mendeley.com/oauth/token'
DOCUMENTS_URL = 'https://api.mendeley.com/documents'


def get_access_token() -> str:
    """
    Get access token using OAuth 2.0 Authorization Code Flow
    
    Returns:
        Access token string
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "Mendeley credentials not found. "
            "Please set MENDELEY_CLIENT_ID and MENDELEY_CLIENT_SECRET in .env file. "
            "See mendeley_setup_guide.md for instructions."
        )
    
    # Try to load saved token
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            
            # Try to refresh the token
            if 'refresh_token' in token_data:
                print("Attempting to refresh saved token...")
                response = requests.post(TOKEN_URL, data={
                    'grant_type': 'refresh_token',
                    'refresh_token': token_data['refresh_token'],
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI
                }, timeout=30)
                
                if response.status_code == 200:
                    new_token_data = response.json()
                    # Preserve refresh_token if not returned by API
                    if 'refresh_token' not in new_token_data:
                        new_token_data['refresh_token'] = token_data['refresh_token']
                    # Save new token with secure permissions
                    with open(TOKEN_FILE, 'w') as f:
                        json.dump(new_token_data, f)
                    if os.name != 'nt':  # Not Windows
                        os.chmod(TOKEN_FILE, 0o600)
                    print("✓ Token refreshed successfully\n")
                    return new_token_data['access_token']
                else:
                    print(f"⚠ Token refresh failed, re-authenticating...")
                    os.remove(TOKEN_FILE)
            else:
                # Old token format, try to use it
                if 'expires_at' not in token_data or token_data.get('expired', False):
                    print("⚠ Saved token expired, re-authenticating...")
                    os.remove(TOKEN_FILE)
                else:
                    print("✓ Using saved token")
                    return token_data['access_token']
        except Exception as e:
            print(f"⚠ Error with saved token: {e}, re-authenticating...")
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
    
    # Perform new OAuth flow
    print("\n=== Mendeley Authentication ===")
    
    # Build authorization URL
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'all'
    }
    login_url = f"{AUTH_URL}?{urlencode(auth_params)}"
    
    print("\n1. Open this URL in your browser:")
    print(f"\n   {login_url}\n")
    print("2. Log in to Mendeley and authorize the app")
    print("3. After authorization, you'll be redirected to a page that may not load")
    print("4. Copy the ENTIRE URL from your browser's address bar")
    print("   (it will look like: http://localhost:8080?code=XXXXX...)")
    print("\nPaste the redirect URL here and press Enter:")
    
    redirect_url = input("> ").strip()
    
    # Extract auth code from URL
    query = urlparse(redirect_url).query
    params = parse_qs(query)
    
    if 'code' not in params:
        raise ValueError("Could not find 'code' parameter in the URL. Please try again.")
    
    auth_code = params['code'][0]
    
    # Exchange code for token
    print("\nExchanging authorization code for access token...")
    token_response = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }, timeout=30)
    
    if token_response.status_code != 200:
        raise requests.exceptions.RequestException(f"Token exchange failed: {token_response.text}")
    
    token_data = token_response.json()
    
    # Save token for future use with secure permissions
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)
    if os.name != 'nt':  # Not Windows
        os.chmod(TOKEN_FILE, 0o600)
    
    print("✓ Authentication successful! Token saved for future use.\n")
    
    return token_data['access_token']


def fetch_library_dois(access_token: str) -> Dict[str, Dict]:
    """
    Fetch all documents from Mendeley library and extract DOIs
    
    Args:
        access_token: OAuth access token
    
    Returns:
        Dictionary mapping DOI (lowercase) to document info
    """
    print("Fetching documents from your Mendeley library...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.mendeley-document.1+json'
    }
    
    library_docs = {}
    total_docs = 0
    url = DOCUMENTS_URL
    
    # Paginate through all documents
    while url:
        response = requests.get(url, headers=headers, params={'limit': 100}, timeout=30)
        
        if response.status_code != 200:
            raise requests.exceptions.RequestException(f"Failed to fetch documents: {response.text}")
        
        documents = response.json()
        
        for doc in documents:
            total_docs += 1
            
            # Check if document has identifiers
            identifiers = doc.get('identifiers', {})
            doi = identifiers.get('doi', '').strip()
            
            if doi:
                # Store with lowercase DOI as key for case-insensitive matching
                library_docs[doi.lower()] = {
                    'doi': doi,  # Original case
                    'title': doc.get('title', 'Untitled'),
                    'year': doc.get('year'),
                    'authors': doc.get('authors', []),
                    'id': doc.get('id')
                }
        
        # Check for next page using response.links for robustness
        url = response.links.get('next', {}).get('url')
    
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
  python check_mendeley_dois_v2.py --dois "10.1038/nature12345,10.1126/science.abc123"
  
  # Check DOIs from a file (one per line)
  python check_mendeley_dois_v2.py --file dois.txt
  
  # Interactive mode
  python check_mendeley_dois_v2.py --interactive
  
  # Save results to JSON
  python check_mendeley_dois_v2.py --file dois.txt --output results.json
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
        access_token = get_access_token()
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Fetch library
    try:
        library_docs = fetch_library_dois(access_token)
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
