import yfinance as yf
from datetime import datetime

class DataFetcher:
    def __init__(self, timeout=10, retry_count=2):
        self.timeout = timeout
        self.retryCount = retry_count

    def fetch(self, ticker: str) -> dict:
        """yfinance로 티커 데이터를 가져온다"""
        for attempt in range(self.retryCount + 1):
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period='5d', interval='1d')

                if hist.empty or len(hist) < 1:
                    return self.handleError(ticker, Exception('데이터 없음'))

                current = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current
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
            except Exception as e:
                if attempt == self.retryCount:
                    return self.handleError(ticker, e)
        return {}

    def handleError(self, ticker: str, e: Exception) -> dict:
        print(f"[DataFetcher] {ticker} 오류: {e}")
        return {'ticker': ticker, 'error': str(e), 'current': None}
