import os
import socket
import chromadb
from google import genai
from google.genai import types

# 1. Force IPv4 so Indian ISP IPv6 routing doesn't stall requests
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    if host == "generativelanguage.googleapis.com":
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _ipv4_only

# 2. Initialize Gemini & Persistent ChromaDB
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("API key missing. Run: export GEMINI_API_KEY='your_key'")
    exit()

gemini_client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=30_000)
)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

try:
    chroma_client.delete_collection(name="cse_notes")
except Exception:
    pass
collection = chroma_client.get_or_create_collection(name="cse_notes")

# 3. Read & Chunk notes.txt by paragraph (single newline)
with open("notes.txt", "r", encoding="utf-8") as f:
    raw_text = f.read().strip()

chunks = [p.strip() for p in raw_text.split("\n") if p.strip()]
ids = [f"para_{i+1}" for i in range(len(chunks))]

collection.upsert(documents=chunks, ids=ids)
print(f"Indexed {len(chunks)} paragraphs into ./chroma_db.")

# 4. Interactive Retrieval + Generation Loop
while True:
    query = input("\nAsk a question about your notes (or 'exit'): ").strip()
    if query.lower() == "exit":
        break
    if not query:
        continue

    results = collection.query(query_texts=[query], n_results=min(3, len(chunks)))
    retrieved_ids = results["ids"][0]
    retrieved_chunks = results["documents"][0]
    context = "\n---\n".join(retrieved_chunks)

    print(f"[Retrieved: {', '.join(retrieved_ids)}]")

    prompt = f"""Answer the question using ONLY the context below. If the answer is not in the context, reply exactly: "Not found in notes."

Context:
{context}

Question: {query}
"""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        print(f"\nAnswer:\n{response.text}")
    except Exception as e:
        print(f"\nAPI Error: {e}")