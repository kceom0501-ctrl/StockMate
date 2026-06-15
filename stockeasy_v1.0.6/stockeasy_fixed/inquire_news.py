from datetime import datetime

class InquireRealtimeNews:
    def __init__(self, collector):
        self.collector = collector
        self.articles = []
        self.lastFetched = None

    def collect(self) -> list:
        all_articles = []
        for url in self.collector.RSS_FEEDS:
            entries = self.collector.fetch(url)
            parsed = self.collector.parse(entries)
            all_articles.extend(parsed)
        self.articles = all_articles
        self.lastFetched = datetime.now()
        return all_articles

    def getSortedArticles(self) -> list:
        articles = self.collect()
        # 중복 제거 (제목 기준)
        seen = set()
        unique = []
        for a in articles:
            if a['title'] not in seen:
                seen.add(a['title'])
                unique.append(a)
        # 발행 시각 내림차순 정렬
        unique.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return unique[:20]  # 최신 20건

    def getLatestNews(self, n: int = 10) -> list:
        return self.getSortedArticles()[:n]
