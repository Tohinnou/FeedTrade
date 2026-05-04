import asyncio
import chromadb
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from src.infrastructure.database import async_session
from src.infrastructure.database.models import ArticleModel, SentimentModel
from dotenv import load_dotenv

import os
from groq import AsyncGroq

load_dotenv()

async def load_articles():
    async with async_session() as session:
        stmt = select(ArticleModel).limit(10)
        result = await session.execute(stmt)
        articles = result.scalars().all()
        
        docs = []
        for article in articles:
            # Chercher sentiment
            sent_stmt = select(SentimentModel).where(SentimentModel.article_id == article.id)
            sent_result = await session.execute(sent_stmt)
            sentiment = sent_result.scalars().first()
            
            # Creer document
            doc = f"""
Title: {article.title}
Summary: {article.summary[:150] if article.summary else ''}
Source: {article.source}
Sentiment: {sentiment.sentiment if sentiment else 'N/A'}
Pair: {sentiment.pair if sentiment else 'N/A'}
"""
            docs.append({
                "id": str(article.id),
                "doc": doc.strip(),
                "pair": sentiment.pair if sentiment else "N/A",
                "sentiment": sentiment.sentiment if sentiment else "N/A"
            })
        return docs
      
      

docs = asyncio.run(load_articles())

# Encoder tous les documents
model = SentenceTransformer('all-MiniLM-L6-v2')
ids = [d["id"] for d in docs]
documents = [d["doc"] for d in docs]
embeddings = model.encode(documents).tolist()
metadatas = [{"pair": d["pair"], "sentiment": d["sentiment"]} for d in docs]
# ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="forex_articles",
    metadata={"hnsw:space": "cosine"}
)

collection.delete(ids=ids)  # vider pour reessayer
collection.add(
    ids=ids,
    embeddings=embeddings,
    documents=documents,
    metadatas=metadatas
)

# Suite - tester le retrieval
query = "Which pairs are bullish?"
query_emb = model.encode(query).tolist()
results = collection.query(
    query_embeddings=[query_emb],
    n_results=3
)
print("\n=== RESULTS ===")

for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
    print(f"\n{i+1}. Distance: {dist:.4f}")
    print(doc)

context = "\n\n---\n\n".join(results["documents"][0])
rag_prompt = f"""Tu es un expert Forex. Utilise le contexte ci-dessous pour répondre à la question.
CONTEXTE:
{context}
QUESTION: {query}
REPONSE:"""


client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
async def ask():
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Tu es un expert Forex."},
            {"role": "user", "content": rag_prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )
    print("\n=== REPONSE LLM ===")
    print(response.choices[0].message.content)


asyncio.run(ask())