import re
import sys
import base64
import os
from github import Github, RateLimitExceededException, UnknownObjectException
import pandas as pd
from pathlib import Path
import time # For potential rate limit handling

def fetch_github_readme(repo_url, gh_instance, max_chars=1000):
    """
    Fetches and decodes README content from a GitHub URL using a pre-initialized Github instance.

    Args:
        repo_url (str): The full URL to the GitHub repository.
        gh_instance (Github): An initialized PyGithub Github instance.
        max_chars (int): Maximum characters to return from the README.

    Returns:
        str: The processed README content or an empty string if an error occurs.
    """
    repo_path = "" # Initialize for better error messages
    try:
        # Clean URL and extract owner/repo
        clean_url = repo_url.removesuffix('.git')
        parts = clean_url.rstrip('/').split('/')
        if len(parts) < 2:
             raise ValueError("Invalid GitHub URL format")
        owner, repo_name = parts[-2], parts[-1]
        repo_path = f"{owner}/{repo_name}"

        # Optional: Check rate limit before making the call
        # try:
        #     rate_limit = gh_instance.get_rate_limit()
        #     # print(f"Rate Limit Core Remaining: {rate_limit.core.remaining}") # Debug
        #     if rate_limit.core.remaining < 10: # Be conservative
        #         reset_time = rate_limit.core.reset
        #         sleep_time = max(0, (reset_time - datetime.datetime.now(datetime.timezone.utc)).total_seconds()) + 5 # Add buffer
        #         print(f"Approaching GitHub API rate limit. Sleeping for {sleep_time:.0f} seconds...", file=sys.stderr)
        #         time.sleep(sleep_time)
        # except Exception as rl_e:
        #      print(f"Warning: Could not check rate limit - {rl_e}", file=sys.stderr)

        print(f"  Fetching README for {repo_path}...", file=sys.stderr)
        repo = gh_instance.get_repo(repo_path)
        readme = repo.get_readme()
        readme_content = base64.b64decode(readme.content).decode('utf-8') # Explicitly decode as UTF-8
        print(f"  Successfully fetched README for {repo_path}", file=sys.stderr)
        # Return the specified number of characters
        return readme_content.strip()[:max_chars]

    except UnknownObjectException:
        print(f"  Error: Repository or README not found for {repo_url} (path: {repo_path})", file=sys.stderr)
        return "ERROR_NOT_FOUND" # Indicate specific error
    except RateLimitExceededException:
        print(f"  Error: GitHub API rate limit exceeded while fetching README for {repo_url}. Try again later.", file=sys.stderr)
        # Consider re-raising or handling more gracefully if running long jobs
        return "ERROR_RATE_LIMIT"
    except Exception as e:
        print(f"  Error fetching README for {repo_url} (path: {repo_path}): {type(e).__name__} - {e}", file=sys.stderr)
        return "ERROR_FETCHING" # General fetch error

def process_url_list_to_csv(url_list_filepath: Path, search_dir: Path, output_file: Path):
    """
    Processes a list of URLs: finds each URL in markdown files within a directory,
    extracts its category, fetches its GitHub README, and outputs a consolidated CSV.
    """
    # --- 1. Read URL List ---
    try:
        with open(url_list_filepath, "r", encoding="utf-8") as f:
            target_urls = sorted(list(set(line.strip() for line in f if line.strip()))) # Read, strip, unique, sort
        if not target_urls:
            print(f"Error: URL list file '{url_list_filepath}' is empty or contains no valid lines.", file=sys.stderr)
            return False
        print(f"Read {len(target_urls)} unique URLs from {url_list_filepath}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: URL list file not found: {url_list_filepath}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error reading URL list file {url_list_filepath}: {e}", file=sys.stderr)
        return False

    # --- Initialize GitHub Client ---
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        print("Error: GITHUB_TOKEN environment variable not set.", file=sys.stderr)
        return False
    try:
        gh = Github(gh_token)
        # Verify token is valid by making a simple call
        # _ = gh.get_user().login
        # print("GitHub token validated.", file=sys.stderr)
    except Exception as e:
        print(f"Error initializing GitHub client or validating token: {e}", file=sys.stderr)
        return False

    all_found_data = [] # Accumulate results for all URLs
    # Compile regex patterns once
    header_pattern = re.compile(r"^(#{2,5})\s+(.*)") # Headers ## to #####
    plugin_pattern = re.compile(r"- \[(?:.*?)\]\((https://github\.com/[^)]+)\)") # Markdown link like - [text](url)

    # --- Process each URL from the list ---
    for target_url in target_urls:
        print(f"\nProcessing URL: {target_url}", file=sys.stderr)
        found_category = "NOT_FOUND_IN_MARKDOWN" # Default category if not found
        url_found_in_md = False

        # --- 2. Search for the URL in Markdown files ---
        for filepath in search_dir.rglob('*.md'): # Recursive search
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    current_file_hierarchy = [] # Track hierarchy within the current file
                    for line_num, line in enumerate(f, 1):
                        line = line.rstrip()
                        header_match = header_pattern.match(line)
                        plugin_match = plugin_pattern.match(line)

                        # Update hierarchy based on headers
                        if header_match:
                            level = len(header_match.group(1)) - 2 # Level 0 for ##, 1 for ### etc.
                            title = header_match.group(2).strip()
                            # Trim hierarchy to the parent level
                            if len(current_file_hierarchy) > level:
                               current_file_hierarchy = current_file_hierarchy[:level]
                            # Append if at the correct level (handles first H2 correctly)
                            if len(current_file_hierarchy) == level:
                                current_file_hierarchy.append(title)
                            elif level == 0 and not current_file_hierarchy: # First H2 in file
                                current_file_hierarchy = [title]
                            # Note: This simple hierarchy tracking might be imperfect for complex/malformed MD

                        # Check if the line contains the target plugin URL
                        elif plugin_match and current_file_hierarchy: # Only consider plugins under some header
                            github_url = plugin_match.group(1)
                            if github_url == target_url:
                                print(f"  Found target URL in {filepath} at line {line_num}", file=sys.stderr)
                                found_category = " / ".join(current_file_hierarchy)
                                print(f"  Category determined: {found_category}", file=sys.stderr)
                                url_found_in_md = True
                                break # Stop searching lines in this file (found the URL)
            except Exception as e:
                print(f"  Warning: Error processing file {filepath}: {e}", file=sys.stderr)
                continue # Continue with the next file

            if url_found_in_md:
                break # Stop searching other files for this target_url

        # --- 3. Fetch README and append data ---
        if not url_found_in_md:
             print(f"  Warning: Target URL '{target_url}' not found in any markdown file in '{search_dir}'. Skipping README fetch for this URL.", file=sys.stderr)
             # Optionally add to output with "NOT_FOUND" category and empty readme:
             # all_found_data.append({"Category": found_category, "URL": target_url, "readme": ""})
             continue # Process next URL

        # Fetch README only if found in markdown and category determined
        readme_text = fetch_github_readme(target_url, gh) # Pass initialized gh instance
        all_found_data.append({
            "URL": target_url,
            "Category": found_category,
            "readme": readme_text # Will contain empty string or ERROR_* on fetch failure
        })
        # Optional: Add a small delay to avoid hitting secondary rate limits aggressively
        # time.sleep(0.5)


    # --- Output final CSV ---
    if all_found_data:
        print(f"\nProcessed {len(target_urls)} URLs. Found data for {len(all_found_data)}. Writing to CSV...", file=sys.stderr)
        # Create DataFrame using the accumulated data
        df = pd.DataFrame(all_found_data)
        try:
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            # Write DataFrame to CSV
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            # Final success message to stdout
            print(f"Output successfully written to: '{output_file}'")
            return True
        except Exception as e:
             # Report error to stderr
             print(f"Error writing CSV to {output_file}: {e}", file=sys.stderr)
             return False
    else:
        # Final status message to stdout
        print("No data found for the provided URLs or no URLs could be processed.")
        return False

# --- Main execution logic ---
if __name__ == "__main__":
    # Expect 4 arguments: script_name, output_csv, search_dir, url_list_file
    if len(sys.argv) != 4:
        print(f"Usage: python {Path(__file__).name} <output_csv_file> <search_directory> <url_list_file>", file=sys.stderr)
        print(f"  <output_csv_file>: Path for the resulting CSV file.", file=sys.stderr)
        print(f"  <search_directory>: Directory containing Markdown files to search within.", file=sys.stderr)
        print(f"  <url_list_file>: Path to a text file containing one GitHub URL per line.", file=sys.stderr)
        print(f"Example: python {Path(__file__).name} output.csv ./markdown_files urls.txt", file=sys.stderr)
        sys.exit(1) # Exit with error code for bad arguments

    # Assign arguments to variables using pathlib
    output_csv_path = Path(sys.argv[1])
    search_directory = Path(sys.argv[2])
    url_list_filepath = Path(sys.argv[3])

    # Validate input paths
    if not search_directory.is_dir():
        print(f"Error: Search directory not found or is not a directory: '{search_directory}'", file=sys.stderr)
        sys.exit(1)
    if not url_list_filepath.is_file():
        print(f"Error: URL list file not found: '{url_list_filepath}'", file=sys.stderr)
        sys.exit(1)

    # Call the main processing function
    success = process_url_list_to_csv(url_list_filepath, search_directory, output_csv_path)

    # Exit with status code 0 if successful (data written or no data found after processing),
    # Exit with 1 if there was an error during setup or writing.
    sys.exit(0 if success else 1)
