from datetime import datetime

class InquireCommodityPrice:
    TICKERS = {
        '금':      {'ticker': 'GC=F', 'unit': '$/oz'},
        'WTI':    {'ticker': 'CL=F', 'unit': '$/bbl'},
        '브렌트유': {'ticker': 'BZ=F', 'unit': '$/bbl'},
    }

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.lastUpdated = None

    def fetch(self) -> list:
        results = []
        for name, meta in self.TICKERS.items():
            raw = self.fetcher.fetch(meta['ticker'])
            raw['name'] = name
            raw['unit'] = meta['unit']
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
                'unit': item.get('unit', ''),
                'current': f"{item['current']:,.2f}",
                'change': f"{'+' if change >= 0 else ''}{change:,.2f}",
                'change_pct': f"{'+' if change >= 0 else ''}{item['change_pct']:.2f}%",
                'direction': 'up' if change > 0 else ('down' if change < 0 else 'flat'),
                'timestamp': item.get('timestamp', '--:--'),
            })
        return {
            'items': formatted,
            'updated': datetime.now().strftime('%H:%M'),
        }
