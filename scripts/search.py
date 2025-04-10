import os
import sys
import base64
import json
import chromadb
from openai import OpenAI
from github import Github

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
github_client = Github(os.getenv("GITHUB_TOKEN"))

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("nvim_plugins")

def get_embedding(text):
    resp = openai_client.embeddings.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding

def fetch_github_readme(repo_url):
    parts = repo_url.rstrip('/').split('/')
    owner, repo_name = parts[-2], parts[-1]

    repo = github_client.get_repo(f"{owner}/{repo_name}")
    readme = repo.get_readme()
    readme_content = base64.b64decode(readme.content).decode().strip()

    if not readme_content:
        readme_content = "No description provided."

    return readme_content

def main():
    if len(sys.argv) != 2:
        print("Usage: python search.py <GitHub_URL>")
        sys.exit(1)

    github_url = sys.argv[1]

    new_plugin_readme = fetch_github_readme(github_url)

    new_embedding = get_embedding(new_plugin_readme)

    results = collection.query(
        query_embeddings=[new_embedding],
        n_results=10
    )

    output = {
        "input_url": github_url,
        "results": results["metadatas"]
    }

    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()

