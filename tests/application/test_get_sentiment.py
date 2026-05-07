from unittest.mock import AsyncMock, MagicMock

from src.application.get_sentiment import GetSentiment
from src.domain.interfaces.llm_client import LLMClient
from src.domain.interfaces.rss_fetcher import RSSFetcher
from src.domain.models.article import Article
from src.domain.models.sentiment import Sentiment

async def test_execute_filters_invalid_sentiments():
    #Data article
    article1 = Article(id=1, title="Title 1", summary="Summary 1", source="src1")
    article2 = Article(id=2, title="Title 2", summary="Summary 2", source="src2")
    article3 = Article(id=3, title="Title 3", summary="Summary 3", source="src3")
    article4 = Article(id=4, title="Title 4", summary="Summary 4", source="src4")
    
    #Data sentiment
    s1 = Sentiment(article_id=1, pair="EUR/USD", sentiment="BULLISH", reason="ok")
    s2 = Sentiment(article_id=2, pair="JPY/USD", sentiment="BEARISH", reason="ok")
    s3 = Sentiment(article_id=3, pair="AUD/USD", sentiment="BULLISH", reason="ok")
    s4 = Sentiment(article_id=4, pair="UNKNOWN", sentiment="BEARISH", reason="fail")
    
    fetcher = MagicMock(spec=RSSFetcher)
    fetcher.fetch_all.return_value = [article1, article2, article3, article4]
    
    llm=AsyncMock(spec=LLMClient)
    llm.analyze_sentiment.side_effect = [s1, s2, s3, s4]
    
    use_case = GetSentiment(fetcher, llm, repo=None)
    
    result = await use_case.execute()
    
    assert result.total_fetched == 4
    assert result.total_analyzed == 3
    assert len(result.sentiments) == 4
    
    fetcher.fetch_all.assert_called_once()
    assert llm.analyze_sentiment.call_count == 4

  