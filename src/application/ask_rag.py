import os

import chromadb
from dotenv import load_dotenv
from groq import AsyncGroq
from sentence_transformers import SentenceTransformer

load_dotenv()


class AskRAG:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma.get_or_create_collection(
            name="forex_articles", metadata={"hnsw:space": "cosine"}
        )
        self.llm = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

    async def execute(self, question: str, top_k: int = 3) -> dict:
        query_emb = self.model.encode(question).tolist()
        results = self.collection.query(query_embeddings=[query_emb], n_results=top_k)

        context = "\n\n---\n\n".join(results["documents"][0])

        # Prompt
        prompt = f"""Tu es un expert Forex. Utilise le contexte ci-dessous pour répondre à la question.
  CONTEXTE:
    {context}
  QUESTION: {question}
  REPONSE:"""

        # LLM call
        response = await self.llm.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Tu es un expert Forex."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": results["documents"][0],
            "question": question,
        }
