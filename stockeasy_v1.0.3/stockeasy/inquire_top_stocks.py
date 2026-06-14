import requests
from bs4 import BeautifulSoup
from datetime import datetime

class InquireTopStocks:
    """네이버 금융에서 거래대금/상승률 상위 종목 크롤링"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://finance.naver.com/',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    def getTopVolume(self, n: int = 15) -> list:
        """거래대금 상위 종목"""
        try:
            url = 'https://finance.naver.com/sise/sise_quant.naver'
            r = requests.get(url, headers=self.HEADERS, timeout=10)
            r.encoding = 'euc-kr'
            soup = BeautifulSoup(r.text, 'html.parser')
            return self._parseTable(soup, n)
        except Exception as e:
            print(f'[TopStocks] 거래대금 오류: {e}')
            return []

    def getTopGainers(self, n: int = 15) -> list:
        """상승률 상위 종목"""
        try:
            url = 'https://finance.naver.com/sise/sise_rise.naver'
            r = requests.get(url, headers=self.HEADERS, timeout=10)
            r.encoding = 'euc-kr'
            soup = BeautifulSoup(r.text, 'html.parser')
            return self._parseTable(soup, n)
        except Exception as e:
            print(f'[TopStocks] 상승률 오류: {e}')
            return []

    def _parseTable(self, soup, n: int) -> list:
        results = []
        table = soup.select_one('table.type_2')
        if not table:
            return []
        rows = table.select('tr')
        for row in rows:
            cols = row.select('td')
            if len(cols) < 7:
                continue
            name = cols[1].get_text(strip=True)
            price = cols[2].get_text(strip=True)
            change_pct = cols[5].get_text(strip=True)
            volume = cols[6].get_text(strip=True) if len(cols) > 6 else '-'

            if not name or name == '종목명':
                continue

            # 등락률 부호로 방향 판단
            direction = 'flat'
            if change_pct.startswith('+'):
                direction = 'up'
            elif change_pct.startswith('-'):
                direction = 'down'

            results.append({
                'name': name,
                'price': price,
                'change_pct': change_pct,
                'volume': volume,
                'direction': direction,
            })
            if len(results) >= n:
                break
        return results

    def getFormattedData(self) -> dict:
        return {
            'top_volume': self.getTopVolume(15),
            'top_gainers': self.getTopGainers(15),
            'updated': datetime.now().strftime('%H:%M'),
        }
