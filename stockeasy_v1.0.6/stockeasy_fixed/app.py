from flask import Flask, render_template, jsonify
from data_fetcher import DataFetcher
from news_collector import NewsCollector
from inquire_domestic_index import InquireDomesticIndex
from inquire_us_futures import InquireUSFuturesIndex
from inquire_commodity import InquireCommodityPrice
from inquire_news import InquireRealtimeNews
from inquire_top_stocks import InquireTopStocks

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/all')
def api_all():
    try:
        fetcher = DataFetcher()
        collector = NewsCollector()
        return jsonify({
            'domestic': InquireDomesticIndex(fetcher).getFormattedData(),
            'usfutures': InquireUSFuturesIndex(fetcher).getFormattedData(),
            'commodity': InquireCommodityPrice(fetcher).getFormattedData(),
            'news': InquireRealtimeNews(collector).getSortedArticles(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domestic')
def api_domestic():
    try:
        return jsonify(InquireDomesticIndex(DataFetcher()).getFormattedData())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usfutures')
def api_usfutures():
    try:
        return jsonify(InquireUSFuturesIndex(DataFetcher()).getFormattedData())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/commodity')
def api_commodity():
    try:
        return jsonify(InquireCommodityPrice(DataFetcher()).getFormattedData())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news')
def api_news():
    try:
        return jsonify(InquireRealtimeNews(NewsCollector()).getSortedArticles())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/topstocks')
def api_topstocks():
    try:
        return jsonify(InquireTopStocks().getFormattedData())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart/<ticker>/<period>')
def api_chart(ticker, period):
    """차트 데이터 - Yahoo Finance v8"""
    try:
        fetcher = DataFetcher()
        data = fetcher.fetchChart(ticker, period)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
