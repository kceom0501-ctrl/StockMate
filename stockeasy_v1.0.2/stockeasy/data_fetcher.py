import requests
from datetime import datetime

class DataFetcher:
    def __init__(self, timeout=15, retry_count=2):
        self.timeout = timeout
        self.retryCount = retry_count
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json,text/html,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/',
        })

    def _getCrumb(self) -> str | None:
        """Yahoo Finance crumb 획득"""
        try:
            r = self.session.get(
                'https://query2.finance.yahoo.com/v1/test/getcrumb',
                timeout=self.timeout
            )
            if r.status_code == 200 and r.text:
                return r.text.strip()
        except Exception:
            pass
        return None

    def fetch(self, ticker: str) -> dict:
        for attempt in range(self.retryCount + 1):
            try:
                result = self._fetchV8(ticker)
                if result and 'error' not in result:
                    return result
            except Exception as e:
                if attempt == self.retryCount:
                    return self.handleError(ticker, e)
        return self.handleError(ticker, Exception('재시도 초과'))

    def _fetchV8(self, ticker: str) -> dict:
        url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}'
        params = {
            'interval': '1d',
            'range': '5d',
            'includePrePost': 'false',
        }
        # crumb 시도
        crumb = self._getCrumb()
        if crumb:
            params['crumb'] = crumb

        r = self.session.get(url, params=params, timeout=self.timeout)

        if r.status_code != 200:
            raise Exception(f'HTTP {r.status_code}')

        data = r.json()
        result = data.get('chart', {}).get('result', [])
        if not result:
            raise Exception('데이터 없음')

        meta = result[0].get('meta', {})
        quotes = result[0].get('indicators', {}).get('quote', [{}])[0]
        closes = quotes.get('close', [])

        # None 제거
        closes = [c for c in closes if c is not None]
        if len(closes) < 1:
            raise Exception('종가 없음')

        current = float(closes[-1])
        prev = float(closes[-2]) if len(closes) >= 2 else current
        change = current - prev
        change_pct = (change / prev * 100) if prev != 0 else 0.0

        return {
            'ticker': ticker,
            'current': current,
            'prev': prev,
            'change': change,
            'change_pct': change_pct,
            'timestamp': datetime.now().strftime('%H:%M'),
        }

    def handleError(self, ticker: str, e: Exception) -> dict:
        print(f'[DataFetcher] {ticker} 오류: {e}')
        return {'ticker': ticker, 'error': str(e), 'current': None}
