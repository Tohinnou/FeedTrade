from sentence_transformers import SentenceTransformer
from test_rag_data import main as fetch_docs

model = SentenceTransformer('all-minilm-l6-v2')

doc = "Title:Japanese yen weakens a day after reports of currency intervention, dollar rises | Sentiment: BULLISH | Pair: EUR/USD"
embedding = model.encode(doc)
print(f"Embedding shape: {embedding.shape}")