import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

class InquireTopStocks:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://finance.naver.com/',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    # ETF/ETN/스팩/리츠 제외 키워드
    EXCLUDE_KEYWORDS = [
        'ETF','ETN','KODEX','TIGER','KINDEX','KOSEF','ARIRANG','HANARO',
        'FOCUS','TIMEFOLIO','SOL','ACE','KB스타','히어로즈','PLUS',
        '레버리지','인버스','선물','스팩','SPAC','리츠','REIT',
        '2X','3X','-1X','-2X','TR','합성','액티브','밸런스드',
        'KIWOOM','하나','미래에셋','삼성','NH','신한','한국투자',
    ]

    def _isExcluded(self, name: str) -> bool:
        """ETF/ETN/스팩 등 제외 여부 판단"""
        for kw in self.EXCLUDE_KEYWORDS:
            if kw.lower() in name.lower():
                return True
        # 종목명이 영어+숫자만이면 ETF 계열일 가능성 높음
        if re.match(r'^[A-Z0-9\s\-]+$', name.strip()):
            return True
        return False

    def getTopVolume(self, n: int = 15) -> list:
        """거래대금 상위 종목 - KOSPI + KOSDAQ 합산 후 상위 n개"""
        results = []
        for sosok in ['0', '1']:  # 0=KOSPI, 1=KOSDAQ
            url = f'https://finance.naver.com/sise/sise_quant.naver?sosok={sosok}'
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=12)
                r.encoding = 'euc-kr'
                soup = BeautifulSoup(r.text, 'html.parser')
                items = self._parseVolumeTable(soup)
                results.extend(items)
            except Exception as e:
                print(f'[TopStocks] 거래대금 sosok={sosok} 오류: {e}')

        # ETF 제외 후 거래대금 내림차순 정렬
        filtered = [x for x in results if not self._isExcluded(x['name'])]
        filtered.sort(key=lambda x: x.get('_vol_raw', 0), reverse=True)
        return filtered[:n]

    def getTopGainers(self, n: int = 15) -> list:
        """상승률 상위 종목"""
        results = []
        for sosok in ['0', '1']:
            url = f'https://finance.naver.com/sise/sise_rise.naver?sosok={sosok}'
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=12)
                r.encoding = 'euc-kr'
                soup = BeautifulSoup(r.text, 'html.parser')
                items = self._parseRiseTable(soup)
                results.extend(items)
            except Exception as e:
                print(f'[TopStocks] 상승률 sosok={sosok} 오류: {e}')

        # ETF 제외 후 상승률 내림차순 정렬
        filtered = [x for x in results if not self._isExcluded(x['name'])]
        filtered.sort(key=lambda x: x.get('_pct_raw', 0), reverse=True)
        return filtered[:n]

    def _parseVolumeTable(self, soup) -> list:
        """거래대금 페이지 파싱"""
        results = []
        table = soup.select_one('table.type_2')
        if not table:
            return []

        for row in table.select('tr'):
            cols = row.select('td')
            if len(cols) < 8:
                continue

            name_tag = cols[1].select_one('a')
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            price = cols[2].get_text(strip=True)
            change_pct_raw = cols[5].get_text(strip=True)  # 등락률
            vol_raw_str = cols[7].get_text(strip=True).replace(',', '')  # 거래대금

            if not name or not price:
                continue

            # 거래대금 숫자 변환
            try:
                vol_raw = int(vol_raw_str) if vol_raw_str.isdigit() else 0
            except:
                vol_raw = 0

            # 등락률 부호
            direction = 'flat'
            pct_raw = 0.0
            try:
                num = float(change_pct_raw.replace('+','').replace('%','').replace(',',''))
                pct_raw = num
                if change_pct_raw.startswith('+') or num > 0:
                    direction = 'up'
                elif num < 0:
                    direction = 'down'
            except:
                pass

            # 등락률 표시
            sign = '+' if direction == 'up' else ''
            change_pct_display = f'{sign}{change_pct_raw}%' if '%' not in change_pct_raw else f'{sign}{change_pct_raw}'

            # 거래대금 표시 (억 단위)
            if vol_raw >= 100000000:
                vol_display = f'{vol_raw // 100000000:,}억'
            elif vol_raw >= 10000:
                vol_display = f'{vol_raw // 10000:,}만'
            else:
                vol_display = f'{vol_raw:,}'

            results.append({
                'name': name,
                'price': price,
                'change_pct': change_pct_display,
                'volume': vol_display,
                'direction': direction,
                '_vol_raw': vol_raw,
                '_pct_raw': pct_raw,
            })

        return results

    def _parseRiseTable(self, soup) -> list:
        """상승률 페이지 파싱"""
        results = []
        table = soup.select_one('table.type_2')
        if not table:
            return []

        for row in table.select('tr'):
            cols = row.select('td')
            if len(cols) < 8:
                continue

            name_tag = cols[1].select_one('a')
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            price = cols[2].get_text(strip=True)
            change_pct_raw = cols[3].get_text(strip=True)  # 상승률 페이지는 3번째 컬럼
            vol_raw_str = cols[7].get_text(strip=True).replace(',', '')

            if not name or not price:
                continue

            try:
                vol_raw = int(vol_raw_str) if vol_raw_str.isdigit() else 0
            except:
                vol_raw = 0

            direction = 'up'  # 상승률 페이지는 모두 상승
            pct_raw = 0.0
            try:
                pct_raw = float(change_pct_raw.replace('+','').replace('%','').replace(',',''))
            except:
                pass

            sign = '+' if pct_raw >= 0 else ''
            change_pct_display = f'{sign}{pct_raw:.2f}%'

            if vol_raw >= 100000000:
                vol_display = f'{vol_raw // 100000000:,}억'
            elif vol_raw >= 10000:
                vol_display = f'{vol_raw // 10000:,}만'
            else:
                vol_display = f'{vol_raw:,}'

            results.append({
                'name': name,
                'price': price,
                'change_pct': change_pct_display,
                'volume': vol_display,
                'direction': direction,
                '_vol_raw': vol_raw,
                '_pct_raw': pct_raw,
            })

        return results

    def getFormattedData(self) -> dict:
        return {
            'top_volume': self.getTopVolume(15),
            'top_gainers': self.getTopGainers(15),
            'updated': datetime.now().strftime('%H:%M'),
        }
