from flask import Flask, render_template, jsonify
from data_fetcher import DataFetcher
from news_collector import NewsCollector
from inquire_domestic_index import InquireDomesticIndex
from inquire_us_futures import InquireUSFuturesIndex
from inquire_commodity import InquireCommodityPrice
from inquire_news import InquireRealtimeNews

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/domestic')
def api_domestic():
    try:
        inquirer = InquireDomesticIndex(DataFetcher())
        return jsonify(inquirer.getFormattedData())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usfutures')
def api_usfutures():
    try:
        inquirer = InquireUSFuturesIndex(DataFetcher())
        return jsonify(inquirer.getFormattedData())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/commodity')
def api_commodity():
    try:
        inquirer = InquireCommodityPrice(DataFetcher())
        return jsonify(inquirer.getFormattedData())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news')
def api_news():
    try:
        inquirer = InquireRealtimeNews(NewsCollector())
        return jsonify(inquirer.getSortedArticles())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
