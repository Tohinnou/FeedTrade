from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base


class ArticleModel(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    source = Column(String(200), nullable=False)
    published = Column(DateTime, nullable=True)
    url = Column(String(500), nullable=True)

    sentiments = relationship("SentimentModel", back_populates="article")


class SentimentModel(Base):
    __tablename__ = "sentiments"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    pair = Column(String(20), nullable=False)
    sentiment = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("ArticleModel", back_populates="sentiments")
