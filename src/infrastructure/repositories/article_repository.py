from datetime import datetime
from typing import Optional
import html

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.article import Article
from src.domain.models.sentiment import Sentiment
from src.domain.interfaces.article_repository import ArticleRepository
from src.infrastructure.database.models import ArticleModel, SentimentModel


class SQLAlchemyArticleRepository(ArticleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_article(self, article: Article) -> Article:
        model = ArticleModel(
            id=article.id if article.id else None,
            title=article.title,
            summary=article.summary,
            source=article.source,
            published=article.published,
            url=self.normalize_url(article.url),
        )
        if model.id is None:
            self.session.add(model)
            await self.session.flush()
            article = Article(
                id=model.id,
                title=model.title,
                summary=model.summary,
                source=model.source,
                published=model.published,
                url=model.url,
            )
        else:
            await self.session.merge(model)
        await self.session.commit()
        return article

    async def save_sentiment(self, sentiment: Sentiment) -> Sentiment:
        model = SentimentModel(
            article_id=sentiment.article_id,
            pair=sentiment.pair,
            sentiment=sentiment.sentiment,
            reason=sentiment.reason,
            raw_response=sentiment.raw_response,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.commit()
        return sentiment

    async def get_article_by_url(self, url: str) -> Optional[Article]:
        normalized = self.normalize_url(url)
        
        if not normalized:
            return None
        
        stmt = select(ArticleModel).where(ArticleModel.url == normalized)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return Article(
                id=model.id,
                title=model.title,
                summary=model.summary,
                source=model.source,
                published=model.published,
                url=model.url,
            )
        return None

    async def get_sentiments_since(self, since: datetime) -> list[Sentiment]:
        stmt = (
            select(SentimentModel)
            .where(SentimentModel.created_at >= since)
            .order_by(SentimentModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [
            Sentiment(
                article_id=m.article_id,
                pair=m.pair,
                sentiment=m.sentiment,
                reason=m.reason,
                raw_response=m.raw_response,
            )
            for m in models
        ]
    
    
    async def get_article_by_title_source(self, title: str, source: str) -> Optional[Article]:
        stmt = select(ArticleModel).where(
           ArticleModel.title == title,
           ArticleModel.source == source
        )
       
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return Article(
                id=model.id,
                title=model.title,
                summary=model.summary,
                source=model.source,
                published=model.published,
                url=model.url,
            )
        return None
       
    @staticmethod
    def normalize_url(url: str) -> str:
        if not url:
            return ""
        
        #strip whitespace
        url = url.strip()
        #Decode HTML entities
        url = html.unescape(url)
        #Remove trailing slashes
        url = url.rstrip('/')
        return url