#!/usr/bin/env python3
"""
Extract DOIs from markdown file and check against Mendeley library
"""

import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, cast
from urllib.parse import quote as url_quote


def extract_dois_from_markdown(md_file: str) -> list:
    """Extract all DOIs from markdown file"""
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern to match DOIs in markdown links and plain text
    # Matches: [10.xxxx/yyyy](https://doi.org/10.xxxx/yyyy) or just 10.xxxx/yyyy
    doi_patterns = [
        r"https?://doi\.org/(10\.\d{4,}/[^\)]+)",  # DOI in full URL
        r"\[(10\.\d{4,}/[^\]]+)\]\(",  # DOI in markdown link text
        r"DOI:\s*\[?(10\.\d{4,}/[^\]\)>\s]+)",  # DOI: prefix with optional bracket
    ]

    dois = set()
    for pattern in doi_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            # Clean up the DOI - strip trailing punctuation
            doi = match.strip().rstrip(").,;:")
            dois.add(doi)

    return sorted(list(dois))


def run_mendeley_check(dois: list) -> Optional[dict]:
    """Run the Mendeley check script and return results"""
    # Create temporary files safely
    temp_file = None
    output_file = None

    try:
        # Create temp file for DOIs using tempfile module
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tf:
            tf.write("\n".join(dois))
            temp_file = Path(tf.name)

        # Create temp file for output
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as of:
            output_file = Path(of.name)

        # Get absolute path to check script
        script_path = Path(__file__).resolve().parent / "check_mendeley_dois_v2.py"

        # Run the check script
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--file",
                str(temp_file),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Check for errors
        if result.returncode != 0:
            print("Mendeley check script failed.", file=sys.stderr)
            return None

        # Read results
        if not output_file.exists():
            print("No results file generated", file=sys.stderr)
            return None

        with open(output_file, "r", encoding="utf-8") as f:
            return cast(dict, json.load(f))

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error processing Mendeley check: {e}", file=sys.stderr)
        return None

    finally:
        # Clean up temp files
        if temp_file and temp_file.exists():
            temp_file.unlink()
        if output_file and output_file.exists():
            output_file.unlink()


def generate_html_table(results: dict, output_html: str):
    """Generate HTML table with clickable DOI links"""

    in_library = results.get("in_library", [])
    not_in_library = results.get("not_in_library", [])

    total_checked = results["summary"]["total_checked"]
    found_count = results["summary"]["found_in_library"]
    missing_count = results["summary"]["not_in_library"]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mendeley DOI Check Results</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 40px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); }}
        h1 {{ text-align: center; color: #2c3e50; margin-bottom: 10px; font-size: 2.5em; font-weight: 700; }}
        .summary {{ text-align: center; margin-bottom: 40px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; }}
        .summary h2 {{ font-size: 1.3em; margin-bottom: 10px; }}
        .stats {{ display: flex; justify-content: center; gap: 40px; font-size: 1.1em; }}
        .stat-item {{ display: flex; flex-direction: column; align-items: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; }}
        .table-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px; }}
        .column {{ background: white; border-radius: 15px; padding: 25px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); }}
        .column h2 {{ color: white; padding: 15px 20px; border-radius: 10px; margin: -25px -25px 20px -25px; font-size: 1.4em; text-align: center; }}
        .in-library h2 {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .not-in-library h2 {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .doi-list {{ list-style: none; }}
        .doi-item {{ margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; transition: all 0.3s ease; border-left: 4px solid transparent; }}
        .in-library .doi-item {{ border-left-color: #38ef7d; }}
        .not-in-library .doi-item {{ border-left-color: #f45c43; }}
        .doi-item:hover {{ transform: translateX(5px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }}
        .doi-link {{ color: #667eea; text-decoration: none; font-weight: 600; font-size: 0.95em; word-break: break-all; display: block; margin-bottom: 8px; }}
        .doi-link:hover {{ color: #764ba2; text-decoration: underline; }}
        .doi-title {{ color: #2c3e50; font-size: 0.9em; margin-top: 5px; line-height: 1.4; }}
        .doi-meta {{ color: #7f8c8d; font-size: 0.85em; margin-top: 5px; }}
        .count-badge {{ display: inline-block; background: rgba(255, 255, 255, 0.3); padding: 5px 15px; border-radius: 20px; font-size: 0.9em; margin-left: 10px; }}
        .doi-checkbox {{ margin-right: 15px; transform: scale(1.5); cursor: pointer; }}
        .doi-item.checked {{ opacity: 0.6; background: #e9ecef; }}
        .doi-item.checked .doi-link {{ text-decoration: line-through; color: #95a5a6; }}
        .doi-flex {{ display: flex; align-items: start; }}
        .doi-content {{ flex: 1; }}
        @media (max-width: 968px) {{ .table-container {{ grid-template-columns: 1fr; }} }}
        .empty-message {{ text-align: center; color: #95a5a6; padding: 40px 20px; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Mendeley DOI Check Results</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{total_checked}</div>
                    <div>Total DOIs</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{found_count}</div>
                    <div>In Library</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{missing_count}</div>
                    <div>Not in Library</div>
                </div>
            </div>
        </div>
        
        <div class="table-container">
            <div class="column in-library">
                <h2>✓ Already in Library <span class="count-badge">{found_count}</span></h2>
                <ul class="doi-list">
"""

    # Add found DOIs
    if in_library:
        for doc in in_library:
            doi_escaped = html.escape(doc["doi"])
            title_escaped = html.escape(doc["title"])
            doi_url = f"https://doi.org/{url_quote(doc['doi'], safe='')}"
            year_str = f" ({html.escape(str(doc['year']))})" if doc.get("year") else ""
            html_content += f'''                    <li class="doi-item">
                        <a href="{doi_url}" class="doi-link" target="_blank">{doi_escaped}</a>
                        <div class="doi-title">{title_escaped}</div>
                        <div class="doi-meta">{year_str}</div>
                    </li>
'''
    else:
        html_content += '                    <li class="empty-message">No DOIs found in library</li>\n'

    html_content += f"""                </ul>
            </div>
            
            <div class="column not-in-library">
                <h2>✗ Not in Library <span class="count-badge">{missing_count}</span></h2>
                <ul class="doi-list">
"""

    # Add missing DOIs
    if not_in_library:
        for doi in not_in_library:
            doi_escaped = html.escape(doi)
            doi_url = f"https://doi.org/{url_quote(doi, safe='')}"
            doi_id = f"check_{url_quote(doi, safe='')}"  # Safe ID for checkbox
            html_content += f'''                    <li class="doi-item" data-doi="{doi_id}">
                        <div class="doi-flex">
                            <input type="checkbox" id="{doi_id}" class="doi-checkbox">
                            <div class="doi-content">
                                <a href="{doi_url}" class="doi-link" target="_blank">{doi_escaped}</a>
                            </div>
                        </div>
                    </li>
'''
    else:
        html_content += '                    <li class="empty-message">All DOIs are in your library! 🎉</li>\n'

    html_content += """                </ul>
            </div>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const checkboxes = document.querySelectorAll('.doi-checkbox');
            const storageKey = 'mendeley_seen_dois';
            
            // Load saved state
            const savedState = JSON.parse(localStorage.getItem(storageKey) || '{}');
            
            checkboxes.forEach(checkbox => {
                const doiId = checkbox.id;
                
                // Restore state
                if (savedState[doiId]) {
                    checkbox.checked = true;
                    checkbox.closest('.doi-item').classList.add('checked');
                }
                
                // Add change listener
                checkbox.addEventListener('change', function() {
                    // Update state object
                    if (this.checked) {
                        savedState[doiId] = true;
                        this.closest('.doi-item').classList.add('checked');
                    } else {
                        delete savedState[doiId];
                        this.closest('.doi-item').classList.remove('checked');
                    }
                    
                    // Save to local storage
                    localStorage.setItem(storageKey, JSON.stringify(savedState));
                });
            });
        });
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n✓ HTML table generated: {output_html}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_and_check_dois.py <markdown_file>")
        sys.exit(1)

    md_file = Path(sys.argv[1])

    # Validate file exists
    if not md_file.exists():
        print(f"Error: File not found: {md_file}")
        sys.exit(1)

    # Extract DOIs
    print(f"Extracting DOIs from {md_file}...")
    dois = extract_dois_from_markdown(str(md_file))
    print(f"✓ Found {len(dois)} DOIs\n")

    if not dois:
        print("No DOIs found in the file!")
        sys.exit(1)

    # Check against Mendeley
    print("Checking DOIs against Mendeley library...\n")
    results = run_mendeley_check(dois)

    if not results:
        print("Failed to get results from Mendeley check")
        sys.exit(1)

    # Generate HTML table in the same directory as the input file
    output_html = md_file.parent / "mendeley_dois_table.html"
    generate_html_table(results, str(output_html))

    print(f"\nDone! Open {output_html} in your browser to view the results.")


if __name__ == "__main__":
    main()
