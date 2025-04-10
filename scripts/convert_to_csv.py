import re
import sys
import base64
import os
from github import Github
import pandas as pd

def parse_files(input_files, output_file):
    output_lines = ["Category,URL,readme"]
    hierarchy = []
    data = []

    header_pattern = re.compile(r"^(#{2,5})\s+(.*)")
    plugin_pattern = re.compile(r"- \[.*\]\((https://github\.com/[^\)]+)\)")

    for file in input_files:
        hierarchy.clear()
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                header_match = header_pattern.match(line)
                plugin_match = plugin_pattern.match(line)

                if header_match:
                    level = len(header_match.group(1)) - 2  # ## = 0
                    title = header_match.group(2).strip()

                    if len(hierarchy) > level:
                        hierarchy = hierarchy[:level]
                    hierarchy.append(title)

                elif plugin_match and hierarchy:
                    github_url = plugin_match.group(1)
                    combined_category = " / ".join(hierarchy)
                    readme_text = fetch_github_readme(github_url)
                    data.append({"URL": github_url, "category": combined_category, "readme": readme_text})
                    df = pd.DataFrame(data)
                    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"Output: '{output_file}'")

def fetch_github_readme(repo_url, max_chars=1000):
    gh = Github(os.getenv("GITHUB_TOKEN"))
    try:
        parts = repo_url.rstrip('/').split('/')
        owner, repo_name = parts[-2], parts[-1]

        repo = gh.get_repo(f"{owner}/{repo_name}")
        readme = repo.get_readme()
        readme_content = base64.b64decode(readme.content).decode()

        return readme_content.strip()[:max_chars]
    except Exception as e:
        print(f"Error fetching README for {repo_url}: {e}")
        return ""

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("python convert_to_csv.py output_file input_file1 [input_file2 ...]")
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    parse_files(input_files, output_file)

