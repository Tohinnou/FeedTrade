import asyncio
from sqlalchemy import select
from src.infrastructure.database import async_session
from src.infrastructure.database.models import ArticleModel, SentimentModel

async def main():
  async with async_session() as session:
    stmt = select(ArticleModel).limit(10)
    result = await session.execute(stmt)
    articles  =  result.scalars().all()
    
    
    for article in articles:
      sentiment_stmt = select(SentimentModel).where(
        SentimentModel.article_id == article.id
      )
      
      sent_result = await session.execute(sentiment_stmt)
      sentiment = sent_result.scalars().first()
      
      doc = f"""
      Title: {article.title}
Summary: {article.summary[:200]}
Source: {article.source}
Sentiment: {sentiment.sentiment if sentiment else 'N/A'}
Pair: {sentiment.pair if sentiment else 'N/A'}
Reason: {sentiment.reason if sentiment else 'N/A'}
"""
      print(doc)
      print("---")
      
asyncio.run(main())