from openai import OpenAI
import chromadb
import pandas as pd
import os
import sys

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("nvim_plugins")

def get_embedding(text):
    resp = client.embeddings.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding

def upsert_to_chroma(collection, id, document, embedding, metadata):
    existing = collection.get(ids=[id])
    if existing["ids"]:
        print(id, metadata)
        collection.update(
            ids=[id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata]
        )
    else:
        collection.add(
            ids=[id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata]
        )
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("python embedding.py input_file.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    df = pd.read_csv(input_file)
    df["readme"] = df["readme"].fillna("No description provided.")

    for _, row in df.iterrows():
        embedding = get_embedding(row["readme"])
        print(row["URL"])
        upsert_to_chroma(
            collection=collection,
            embedding=embedding,
            document=row["readme"],
            metadata={"url": row["URL"], "category": row["category"]},
            id=row["URL"]
        )

