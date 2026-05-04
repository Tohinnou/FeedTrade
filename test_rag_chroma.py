import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
  name="forex_articles",
  metadata={'hnsw:space': "cosine"}
)

model = SentenceTransformer('all-MiniLM-L6-v2')

doc1 = "Title: EUR/USD bullish | Sentiment: BULLISH | Pair: EUR/USD | Reason: dollar weakens"
doc2 = "Title: GBP/JPY bearish | Sentiment: BEARISH | Pair: GBP/JPY | Reason: BoE hawkish"

emb1 = model.encode(doc1).tolist()
emb2 = model.encode(doc2).tolist()

collection.add(
    ids=["1", "2"],
    embeddings=[emb1, emb2],
    documents=[doc1, doc2],
    metadatas=[{"pair": "EUR/USD"}, {"pair": "GBP/JPY"}]
)

query = "Which currency pair is strong?"
query_emb = model.encode(query).tolist()
results = collection.query(
    query_embeddings=[query_emb],
    n_results=2
)
print(results)