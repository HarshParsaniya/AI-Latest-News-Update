"""Free RSS sources for AI news. One feed failing must not fail the run."""

from typing import TypedDict


class Source(TypedDict):
    name: str
    url: str


SOURCES: list[Source] = [
    {
        "name": "Google News AI",
        "url": (
            "https://news.google.com/rss/search?q=artificial+intelligence+when:1d"
            "&hl=en-US&gl=US&ceid=US:en"
        ),
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
    },
    {
        "name": "Google DeepMind",
        "url": "https://deepmind.google/blog/rss.xml",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "name": "arXiv cs.AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
    },
]
