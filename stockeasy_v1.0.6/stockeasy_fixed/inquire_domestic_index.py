from datetime import datetime, time
import pytz

class InquireDomesticIndex:
    TICKERS = {
        'KOSPI':    '^KS11',
        'KOSDAQ':   '^KQ11',
        'KOSPI200': '^KS200',
    }

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.lastUpdated = None

    def fetch(self) -> list:
        results = []
        for name, ticker in self.TICKERS.items():
            raw = self.fetcher.fetch(ticker)
            raw['name'] = name
            results.append(raw)
        self.lastUpdated = datetime.now()
        return results

    def getFormattedData(self) -> dict:
        items = self.fetch()
        formatted = []
        for item in items:
            if item.get('error') or item.get('current') is None:
                formatted.append({'name': item.get('name', ''), 'error': True})
                continue
            change = item.get('change', 0)
            formatted.append({
                'name': item['name'],
                'current': f"{item['current']:,.2f}",
                'change': f"{'+' if change >= 0 else ''}{change:,.2f}",
                'change_pct': f"{'+' if change >= 0 else ''}{item['change_pct']:.2f}%",
                'direction': 'up' if change > 0 else ('down' if change < 0 else 'flat'),
                'timestamp': item.get('timestamp', '--:--'),
            })
        return {
            'items': formatted,
            'market_open': self.isMarketOpen(),
            'updated': datetime.now().strftime('%H:%M'),
        }

    def isMarketOpen(self) -> bool:
        tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(tz)
        t = now.time()
        weekday = now.weekday()
        if weekday >= 5:
            return False
        return time(9, 0) <= t <= time(15, 30)
