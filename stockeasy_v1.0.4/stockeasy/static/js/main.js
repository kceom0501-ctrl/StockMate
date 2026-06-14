/* ── StockEasy main.js ── */

let refreshTimer = null;
let chartInstance = null;
let currentTicker = null;
let currentPeriod = '1m';
let stocksData = { top_volume: [], top_gainers: [] };
let currentTab = 'volume';

// 티커 매핑 (카드명 → Yahoo ticker)
const TICKER_MAP = {
  'KOSPI': '^KS11', 'KOSDAQ': '^KQ11', 'KOSPI200': '^KS200',
  'S&P500': 'ES=F', '나스닥': 'NQ=F', '다우존스': 'YM=F',
  '금': 'GC=F', 'WTI': 'CL=F', '브렌트유': 'BZ=F',
};

document.addEventListener('DOMContentLoaded', () => {
  fetchAll();
  fetchTopStocks();
  setupAutoRefresh();
  document.getElementById('manualRefresh').addEventListener('click', () => { fetchAll(); fetchTopStocks(); });
  document.getElementById('intervalSelect').addEventListener('change', setupAutoRefresh);
  document.getElementById('modalClose').addEventListener('click', closeModal);
  document.getElementById('chartModal').addEventListener('click', (e) => { if (e.target === e.currentTarget) closeModal(); });
  document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentPeriod = btn.dataset.period;
      if (currentTicker) loadChart(currentTicker, currentPeriod);
    });
  });
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTab = btn.dataset.tab;
      renderStocksTable();
    });
  });
});

// ── 전체 데이터 fetch
async function fetchAll() {
  const btn = document.getElementById('manualRefresh');
  btn.classList.add('spinning');
  try {
    const res = await fetch('/api/all');
    const data = await res.json();
    renderDomestic(data.domestic);
    renderUSFutures(data.usfutures);
    renderCommodity(data.commodity);
    renderNews(data.news);
    renderTickerBar(data);
    updateTime();
  } catch (e) { console.error(e); }
  finally { btn.classList.remove('spinning'); }
}

// ── 종목 데이터 fetch
async function fetchTopStocks() {
  try {
    const res = await fetch('/api/topstocks');
    const data = await res.json();
    stocksData = data;
    document.getElementById('stocksUpdated').textContent = data.updated ? `${data.updated} 기준` : '';
    renderStocksTable();
  } catch (e) { console.error(e); }
}

function updateTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2,'0');
  const mm = String(now.getMinutes()).padStart(2,'0');
  document.getElementById('lastUpdated').textContent = `${hh}:${mm} 기준`;
}

function setupAutoRefresh() {
  clearInterval(refreshTimer);
  const val = parseInt(document.getElementById('intervalSelect').value);
  if (val > 0) refreshTimer = setInterval(() => { fetchAll(); }, val * 1000);
}

function arrow(d) { return d === 'up' ? '▲' : d === 'down' ? '▼' : ''; }

// ── 카드 클릭 → 차트 모달
function openChart(name, ticker) {
  currentTicker = ticker;
  currentPeriod = '1m';
  document.querySelectorAll('.period-btn').forEach(b => b.classList.toggle('active', b.dataset.period === '1m'));
  document.getElementById('modalTitle').textContent = name;
  document.getElementById('modalPrice').textContent = '';
  document.getElementById('chartModal').classList.add('open');
  loadChart(ticker, currentPeriod);
}

function closeModal() {
  document.getElementById('chartModal').classList.remove('open');
  if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
}

async function loadChart(ticker, period) {
  const loading = document.getElementById('chartLoading');
  loading.classList.remove('hidden');
  try {
    const res = await fetch(`/api/chart/${encodeURIComponent(ticker)}/${period}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderChart(data);
    const sign = data.change >= 0 ? '+' : '';
    document.getElementById('modalPrice').textContent =
      `${data.current.toLocaleString()}  ${sign}${data.change.toFixed(2)} (${sign}${data.change_pct.toFixed(2)}%)`;
  } catch (e) {
    console.error(e);
  } finally {
    loading.classList.add('hidden');
  }
}

function renderChart(data) {
  const ctx = document.getElementById('priceChart').getContext('2d');
  if (chartInstance) chartInstance.destroy();

  const pts = data.points || [];
  const labels = pts.map(p => {
    const d = new Date(p.t);
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  });
  const values = pts.map(p => p.v);
  const isUp = values.length > 1 ? values[values.length-1] >= values[0] : true;
  const color = isUp ? '#f04452' : '#2979ff';

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: color,
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        backgroundColor: isUp ? 'rgba(240,68,82,.08)' : 'rgba(41,121,255,.08)',
        tension: 0.3,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: {
        mode: 'index', intersect: false,
        backgroundColor: '#161b22', borderColor: '#242c3a', borderWidth: 1,
        titleColor: '#7d8590', bodyColor: '#e6edf3',
        callbacks: { label: ctx => ctx.parsed.y.toLocaleString() }
      }},
      scales: {
        x: { grid: { color: '#242c3a' }, ticks: { color: '#7d8590', maxTicksLimit: 8, font: { size: 11 } } },
        y: { grid: { color: '#242c3a' }, ticks: { color: '#7d8590', font: { size: 11 }, callback: v => v.toLocaleString() }, position: 'right' }
      },
      interaction: { mode: 'index', intersect: false },
    }
  });
}

// ── 국내 지수
function renderDomestic(data) {
  const grid = document.getElementById('domesticGrid');
  const badge = document.getElementById('domesticBadge');
  if (!data || data.error) { grid.innerHTML = `<p class="card-error">데이터를 불러올 수 없습니다.</p>`; return; }
  badge.textContent = data.market_open ? '장중' : '장마감';
  badge.className = 'market-badge ' + (data.market_open ? 'open' : 'closed');
  grid.innerHTML = data.items.map(item => {
    if (item.error) return `<div class="card"><p class="card-error">—</p></div>`;
    const ticker = TICKER_MAP[item.name] || '';
    return `
      <div class="card" onclick="openChart('${item.name}', '${ticker}')">
        <div class="card-name">${item.name}</div>
        <div class="card-price">${item.current}</div>
        <div class="card-change ${item.direction}">
          <span class="card-change-arrow">${arrow(item.direction)}</span>
          ${item.change} (${item.change_pct})
        </div>
      </div>`;
  }).join('');
}

// ── 미국 선물
function renderUSFutures(data) {
  const grid = document.getElementById('usGrid');
  const badge = document.getElementById('usBadge');
  if (!data || data.error) { grid.innerHTML = `<p class="card-error">데이터를 불러올 수 없습니다.</p>`; return; }
  badge.textContent = data.market_open ? '운영중' : '마감';
  badge.className = 'market-badge ' + (data.market_open ? 'open' : 'closed');
  grid.innerHTML = data.items.map(item => {
    if (item.error) return `<div class="card card--row"><p class="card-error">—</p></div>`;
    const ticker = TICKER_MAP[item.name] || '';
    return `
      <div class="card card--row" onclick="openChart('${item.name}', '${ticker}')">
        <div class="card-row-left"><div class="card-row-name">${item.name}</div></div>
        <div class="card-row-right">
          <div class="card-row-price ${item.direction}">${item.current}</div>
          <div class="card-row-change ${item.direction}">${arrow(item.direction)} ${item.change} (${item.change_pct})</div>
        </div>
      </div>`;
  }).join('');
}

// ── 원자재
function renderCommodity(data) {
  const grid = document.getElementById('commodityGrid');
  if (!data || data.error) { grid.innerHTML = `<p class="card-error">데이터를 불러올 수 없습니다.</p>`; return; }
  grid.innerHTML = data.items.map(item => {
    if (item.error) return `<div class="card card--row"><p class="card-error">—</p></div>`;
    const ticker = TICKER_MAP[item.name] || '';
    return `
      <div class="card card--row" onclick="openChart('${item.name}', '${ticker}')">
        <div class="card-row-left">
          <div class="card-row-name">${item.name} <span class="card-row-unit">${item.unit}</span></div>
        </div>
        <div class="card-row-right">
          <div class="card-row-price ${item.direction}">${item.current}</div>
          <div class="card-row-change ${item.direction}">${arrow(item.direction)} ${item.change} (${item.change_pct})</div>
        </div>
      </div>`;
  }).join('');
}

// ── 종목 테이블
function renderStocksTable() {
  const tbody = document.getElementById('stocksTbody');
  const list = currentTab === 'volume' ? stocksData.top_volume : stocksData.top_gainers;
  if (!list || list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="loading-td">데이터 없음 (장 마감 후에는 표시되지 않을 수 있습니다)</td></tr>`;
    return;
  }
  tbody.innerHTML = list.map((item, i) => `
    <tr>
      <td class="rank">${i + 1}</td>
      <td class="name">${item.name}</td>
      <td class="price">${item.price}</td>
      <td class="pct ${item.direction}">${arrow(item.direction)} ${item.change_pct}</td>
      <td class="vol">${item.volume}</td>
    </tr>`).join('');
}

// ── 뉴스
function renderNews(articles) {
  const list = document.getElementById('newsList');
  const count = document.getElementById('newsCount');
  if (!articles || articles.length === 0) {
    list.innerHTML = `<li class="news-item news-loading">뉴스를 불러올 수 없습니다.</li>`; return;
  }
  count.textContent = `${articles.length}건`;
  list.innerHTML = articles.map(a => `
    <li class="news-item">
      <span class="news-time">${a.published}</span>
      <span class="news-title"><a href="${a.link}" target="_blank" rel="noopener noreferrer">${a.title}</a></span>
    </li>`).join('');
}

// ── 티커바
function renderTickerBar(data) {
  const track = document.getElementById('tickerTrack');
  const items = [];
  const addItems = (list) => {
    if (!list || !list.items) return;
    list.items.forEach(item => {
      if (item.error) return;
      items.push(`
        <span class="ticker-item">
          <span class="ticker-name">${item.name}</span>
          <span class="ticker-price">${item.current}</span>
          <span class="ticker-change ${item.direction}">${arrow(item.direction)} ${item.change_pct}</span>
        </span>
        <span class="ticker-divider">|</span>`);
    });
  };
  addItems(data.domestic); addItems(data.usfutures); addItems(data.commodity);
  if (items.length === 0) return;
  track.innerHTML = items.join('') + items.join('');
}
