import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

class InquireTopStocks:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://finance.naver.com/',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }

    EXCLUDE_KEYWORDS = [
        'ETF','ETN','KODEX','TIGER','KINDEX','KOSEF','ARIRANG','HANARO',
        'FOCUS','TIMEFOLIO','SOL','ACE','PLUS','히어로즈','KB스타',
        '레버리지','인버스','선물','스팩','SPAC','리츠','REIT',
        '2X','3X','-1X','-2X',' TR ','합성','액티브','밸런스드',
        'KIWOOM','하나 레버','미래에셋 레버','삼성 인버',
    ]

    def _isExcluded(self, name: str) -> bool:
        for kw in self.EXCLUDE_KEYWORDS:
            if kw.lower() in name.lower():
                return True
        if re.match(r'^[A-Z0-9\s\-]+$', name.strip()):
            return True
        return False

    def _toInt(self, s: str) -> int:
        try:
            return int(s.replace(',', '').strip())
        except:
            return 0

    def getTopVolume(self, n: int = 15) -> list:
        """거래대금 상위 - 컬럼: 순위/종목명/현재가/전일종가/거래대금"""
        results = []
        for sosok in ['0', '1']:
            url = f'https://finance.naver.com/sise/sise_quant.naver?sosok={sosok}'
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=12)
                r.encoding = 'euc-kr'
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.select_one('table.type_2')
                if not table:
                    continue
                for row in table.select('tr'):
                    cols = row.select('td')
                    if len(cols) < 10:
                        continue
                    name_tag = cols[1].select_one('a')
                    if not name_tag:
                        continue
                    name = name_tag.get_text(strip=True)
                    if not name:
                        continue
                    # 네이버 거래대금 페이지 컬럼 순서:
                    # 0:순위 1:종목명 2:현재가 3:전일비 4:등락률 5:액면가
                    # 6:시가총액 7:상장주식수 8:외국인비율 9:거래량 10:PER 11:ROE
                    # 거래대금은 sise_quant 에서 거래량(9번)으로 정렬됨
                    # 실제 거래대금 컬럼 확인 필요 - 일단 가능한 컬럼 다 뽑기
                    current  = cols[2].get_text(strip=True)
                    prev_day = cols[3].get_text(strip=True)  # 전일비(변동금액)
                    # 전일종가 = 현재가 - 전일비 (부호 처리)
                    prev_sign = row.select_one('td:nth-child(4) span')
                    vol_text = cols[9].get_text(strip=True) if len(cols) > 9 else '-'

                    cur_int = self._toInt(current)
                    prev_diff = self._toInt(prev_day)
                    # 전일 종가 계산
                    # 전일비가 양수면 오늘 오른 것 → 전일종가 = 현재가 - 전일비
                    # span class로 방향 판단
                    span = cols[3].select_one('span')
                    span_cls = span['class'][0] if span and span.get('class') else ''
                    if 'nv01' in span_cls or 'red' in span_cls:  # 상승
                        prev_close = cur_int - prev_diff
                    elif 'nv02' in span_cls or 'blue' in span_cls:  # 하락
                        prev_close = cur_int + prev_diff
                    else:
                        prev_close = cur_int

                    vol_int = self._toInt(vol_text)

                    if prev_close > 0:
                        prev_close_str = f'{prev_close:,}'
                    else:
                        prev_close_str = '-'

                    # 거래대금 표시 (억 단위, 거래량×현재가)
                    quant_int = vol_int * cur_int
                    if quant_int >= 100000000:
                        vol_display = f'{quant_int // 100000000:,}억'
                    elif quant_int >= 10000:
                        vol_display = f'{quant_int // 10000:,}만'
                    else:
                        vol_display = vol_text

                    results.append({
                        'name': name,
                        'price': current,
                        'prev_close': prev_close_str,
                        'volume': vol_display,
                        '_vol_raw': vol_int,
                        '_cur_int': cur_int,
                    })
            except Exception as e:
                print(f'[TopStocks] 거래대금 sosok={sosok} 오류: {e}')

        filtered = [x for x in results if not self._isExcluded(x['name'])]
        filtered.sort(key=lambda x: x['_vol_raw'] * x['_cur_int'], reverse=True)
        return [{k: v for k, v in item.items() if not k.startswith('_')} for item in filtered[:n]]

    def getTopGainers(self, n: int = 15) -> list:
        """상승률 상위 - 컬럼: 순위/종목명/현재가/전일종가/등락률"""
        results = []
        for sosok in ['0', '1']:
            url = f'https://finance.naver.com/sise/sise_rise.naver?sosok={sosok}'
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=12)
                r.encoding = 'euc-kr'
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.select_one('table.type_2')
                if not table:
                    continue
                for row in table.select('tr'):
                    cols = row.select('td')
                    if len(cols) < 6:
                        continue
                    name_tag = cols[1].select_one('a')
                    if not name_tag:
                        continue
                    name = name_tag.get_text(strip=True)
                    if not name:
                        continue
                    # 네이버 상승률 페이지 컬럼:
                    # 0:순위 1:종목명 2:현재가 3:등락률 4:전일종가 5:거래량...
                    current      = cols[2].get_text(strip=True)
                    change_pct   = cols[3].get_text(strip=True)
                    prev_close   = cols[4].get_text(strip=True)

                    pct_raw = 0.0
                    try:
                        pct_raw = float(change_pct.replace('+','').replace('%','').replace(',','').strip())
                    except:
                        pass

                    sign = '+' if pct_raw > 0 else ''
                    direction = 'up' if pct_raw > 0 else ('down' if pct_raw < 0 else 'flat')
                    pct_display = f'{sign}{pct_raw:.2f}%'

                    results.append({
                        'name': name,
                        'price': current,
                        'prev_close': prev_close,
                        'change_pct': pct_display,
                        'direction': direction,
                        '_pct_raw': pct_raw,
                    })
            except Exception as e:
                print(f'[TopStocks] 상승률 sosok={sosok} 오류: {e}')

        filtered = [x for x in results if not self._isExcluded(x['name'])]
        filtered.sort(key=lambda x: x['_pct_raw'], reverse=True)
        return [{k: v for k, v in item.items() if not k.startswith('_')} for item in filtered[:n]]

    def getFormattedData(self) -> dict:
        return {
            'top_volume': self.getTopVolume(15),
            'top_gainers': self.getTopGainers(15),
            'updated': datetime.now().strftime('%H:%M'),
        }
