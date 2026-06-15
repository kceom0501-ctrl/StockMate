import feedparser
from datetime import datetime, timezone, timedelta
import time as time_module

KST = timezone(timedelta(hours=9))

class NewsCollector:
    RSS_FEEDS = [
        # 연합뉴스 경제
        'https://www.yonhapnewstv.co.kr/browse/feed/',
        # 네이버 금융 뉴스 RSS (실시간 시황)
        'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258',
        # 한국경제
        'https://www.hankyung.com/feed/economy',
        # 매일경제
        'https://www.mk.co.kr/rss/30000001/',
    ]

    def __init__(self, timeout=8, retry_count=1):
        self.timeout = timeout
        self.retryCount = retry_count

    def fetch(self, url: str) -> list:
        for attempt in range(self.retryCount + 1):
            try:
                feed = feedparser.parse(url)
                return feed.entries if feed.entries else []
            except Exception as e:
                if attempt == self.retryCount:
                    return self.handleError(url, e)
        return []

    def parse(self, entries: list) -> list:
        articles = []
        for entry in entries:
            try:
                title = entry.get('title', '').strip()
                link = entry.get('link', '#')

                # 발행 시각 파싱 (UTC → KST 변환)
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc).astimezone(KST)
                    pub_str = pub_dt.strftime('%H:%M')
                    pub_ts = pub_dt.timestamp()
                else:
                    pub_str = '--:--'
                    pub_ts = 0

                if title:
                    articles.append({
                        'title': title,
                        'link': link,
                        'published': pub_str,
                        'timestamp': pub_ts,
                    })
            except Exception:
                continue
        return articles

    def handleError(self, url: str, e: Exception) -> list:
        print(f"[NewsCollector] {url} 오류: {e}")
        return []
