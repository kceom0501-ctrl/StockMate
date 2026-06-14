import requests
from datetime import datetime

class DataFetcher:
    def __init__(self, timeout=15, retry_count=2):
        self.timeout = timeout
        self.retryCount = retry_count
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/',
        })

    def _getCrumb(self):
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
                result = self._fetchV8(ticker, '5d', '1d')
                if result and 'error' not in result:
                    return result
            except Exception as e:
                if attempt == self.retryCount:
                    return self.handleError(ticker, e)
        return self.handleError(ticker, Exception('재시도 초과'))

    def fetchChart(self, ticker: str, period: str) -> dict:
        """차트용 데이터 - period: 1m,3m,5m,15m,30m,1d,1mo,1y"""
        period_map = {
            '1m':  ('1d',  '1m'),
            '3m':  ('1d',  '3m'),
            '5m':  ('5d',  '5m'),
            '15m': ('5d',  '15m'),
            '30m': ('1mo', '30m'),
            '1d':  ('1mo', '1d'),
            '1mo': ('1y',  '1wk'),
            '1y':  ('5y',  '1mo'),
        }
        range_, interval = period_map.get(period, ('1mo', '1d'))
        try:
            return self._fetchV8(ticker, range_, interval, chart=True)
        except Exception as e:
            return {'error': str(e)}

    def _fetchV8(self, ticker: str, range_: str, interval: str, chart: bool = False) -> dict:
        url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}'
        params = {
            'interval': interval,
            'range': range_,
            'includePrePost': 'false',
        }
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
        timestamps = result[0].get('timestamp', [])
        quotes = result[0].get('indicators', {}).get('quote', [{}])[0]
        closes = quotes.get('close', [])

        closes_clean = [c for c in closes if c is not None]

        if chart:
            # 차트용: timestamps + closes 반환
            pairs = []
            for ts, c in zip(timestamps, closes):
                if c is not None:
                    pairs.append({'t': ts * 1000, 'v': round(c, 2)})
            current = closes_clean[-1] if closes_clean else 0
            prev = closes_clean[0] if closes_clean else current
            change = current - prev
            change_pct = (change / prev * 100) if prev != 0 else 0.0
            return {
                'ticker': ticker,
                'name': meta.get('shortName', ticker),
                'current': round(current, 2),
                'change': round(change, 2),
                'change_pct': round(change_pct, 2),
                'points': pairs,
            }

        if len(closes_clean) < 1:
            raise Exception('종가 없음')

        current = float(closes_clean[-1])
        prev = float(closes_clean[-2]) if len(closes_clean) >= 2 else current
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
