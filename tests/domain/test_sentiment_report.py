from src.domain.models.analysis import AnalysisResult
from src.domain.models.sentiment import Sentiment
from src.domain.services.sentiment_service import SentimentReport


def make_sentiment(pair: str = "EUR/USD", sentiment: str = "BULLISH") -> Sentiment:
    return Sentiment(article_id=1, pair=pair, sentiment=sentiment, reason="ok")


def make_analysis_result(sentiments: list[Sentiment]):
    return AnalysisResult(
        sentiments=sentiments,
        total_fetched=len(sentiments),
        total_analyzed=len(sentiments),
        time_seconds=1.0,
    )


class TestMajority:
    def test_return_bullish_when_majority(self):
        assert SentimentReport._majority(["BULLISH", "BEARISH", "BULLISH"]) == "BULLISH"

    def test_returns_bearish_when_majority(self):
        assert SentimentReport._majority(["BEARISH", "NEUTRAL", "BEARISH"]) == "BEARISH"

    def test_returns_unknown_when_empty(self):
        assert SentimentReport._majority([]) == "UNKNOWN"

    def test_returns_first_inserted_on_tie(self):
        assert SentimentReport._majority(["BULLISH", "BEARISH"]) == "BULLISH"


class TestSummary:
    def test_returns_bullish_majority(self):
        sentiments = [
            make_sentiment("EUR/USD", "BULLISH"),
            make_sentiment("EUR/USD", "BEARISH"),
            make_sentiment("EUR/USD", "BULLISH"),
        ]

        result = make_analysis_result(sentiments)
        report = SentimentReport(result)

        assert report.summary()["EUR/USD"] == "BULLISH (3 articles)"

    def test_uses_singular_form_when_one_article(self):
        sentiments = [make_sentiment("EUR/USD", "BULLISH")]
        result = make_analysis_result(sentiments)
        report = SentimentReport(result)
        assert report.summary()["EUR/USD"] == "BULLISH (1 article)"

    def test_filters_invalid_sentiments(self):
        sentiments = [
            make_sentiment("EUR/USD", "BULLISH"),
            make_sentiment("EUR/USD", "BULLISH"),
            make_sentiment("UNKNOWN", "BULLISH"),  # invalide : pair interdite
            make_sentiment("EUR/USD", "PARSE_ERR"),  # invalide : sentiment hors enum
        ]
        result = make_analysis_result(sentiments)
        report = SentimentReport(result)

        summary = report.summary()
        assert summary == {"EUR/USD": "BULLISH (2 articles)"}
        assert "UNKNOWN" not in summary

    def test_groups_sentiments_by_pair(self):
        sentiments = [
            make_sentiment("EUR/USD", "BULLISH"),
            make_sentiment("EUR/USD", "BULLISH"),
            make_sentiment("GBP/USD", "BEARISH"),
        ]
        result = make_analysis_result(sentiments)
        report = SentimentReport(result)

        assert report.summary() == {
            "EUR/USD": "BULLISH (2 articles)",
            "GBP/USD": "BEARISH (1 article)",
        }

    def test_returns_empty_when_no_sentiments(self):
        """sentiments=[] → summary() == {}"""
        result = make_analysis_result([])
        report = SentimentReport(result)
        assert report.summary() == {}


class TestDetailedBreakdown:
    def test_returns_majority_and_counts_per_pair(self):
        sentiments = [
            make_sentiment("EUR/USD", "BULLISH"),
            make_sentiment("EUR/USD", "BULLISH"),
            make_sentiment("EUR/USD", "BEARISH"),
            make_sentiment("GBP/USD", "NEUTRAL"),
        ]
        result = make_analysis_result(sentiments)
        report = SentimentReport(result)

        assert report.detailed_breakdown() == {
            "EUR/USD": {
                "sentiment": "BULLISH",
                "counts": {"BULLISH": 2, "BEARISH": 1, "NEUTRAL": 0},
            },
            "GBP/USD": {
                "sentiment": "NEUTRAL",
                "counts": {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 1},
            },
        }


class TestPairSentiment:
    def test_returns_string_when_pair_exists(self):
        sentiments = [make_sentiment("EUR/USD", "BULLISH")]
        report = SentimentReport(make_analysis_result(sentiments))
        assert report.pair_sentiment("EUR/USD") == "BULLISH (1 article)"

    def test_returns_none_when_pair_absent(self):
        sentiments = [make_sentiment("EUR/USD", "BULLISH")]
        report = SentimentReport(make_analysis_result(sentiments))
        assert report.pair_sentiment("USD/JPY") is None
