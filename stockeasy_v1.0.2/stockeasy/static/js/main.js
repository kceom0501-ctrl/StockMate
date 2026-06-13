/* ── StockEasy main.js ── */

let refreshTimer = null;

// ── 초기 로드
document.addEventListener('DOMContentLoaded', () => {
  fetchAll();
  setupAutoRefresh();
  document.getElementById('manualRefresh').addEventListener('click', () => {
    fetchAll();
  });
  document.getElementById('intervalSelect').addEventListener('change', setupAutoRefresh);
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
  } catch (e) {
    console.error('fetch 오류:', e);
  } finally {
    btn.classList.remove('spinning');
  }
}

// ── 시간 업데이트
function updateTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  document.getElementById('lastUpdated').textContent = `${hh}:${mm} 기준`;
}

// ── 자동 갱신 설정
function setupAutoRefresh() {
  clearInterval(refreshTimer);
  const val = parseInt(document.getElementById('intervalSelect').value);
  if (val > 0) {
    refreshTimer = setInterval(fetchAll, val * 1000);
  }
}

// ── 방향 화살표
function arrow(direction) {
  if (direction === 'up')   return '▲';
  if (direction === 'down') return '▼';
  return '';
}

// ── 국내 지수 렌더링
function renderDomestic(data) {
  const grid = document.getElementById('domesticGrid');
  const badge = document.getElementById('domesticBadge');

  if (!data || data.error) {
    grid.innerHTML = `<p class="card-error">데이터를 불러올 수 없습니다.</p>`;
    return;
  }

  badge.textContent = data.market_open ? '장중' : '장마감';
  badge.className = 'market-badge ' + (data.market_open ? 'open' : 'closed');

  grid.innerHTML = data.items.map(item => {
    if (item.error) return `<div class="card"><p class="card-error">—</p></div>`;
    return `
      <div class="card">
        <div class="card-name">${item.name}</div>
        <div class="card-price">${item.current}</div>
        <div class="card-change ${item.direction}">
          <span class="card-change-arrow">${arrow(item.direction)}</span>
          ${item.change} (${item.change_pct})
        </div>
      </div>`;
  }).join('');
}

// ── 미국 선물 렌더링
function renderUSFutures(data) {
  const grid = document.getElementById('usGrid');
  const badge = document.getElementById('usBadge');

  if (!data || data.error) {
    grid.innerHTML = `<p class="card-error">데이터를 불러올 수 없습니다.</p>`;
    return;
  }

  badge.textContent = data.market_open ? '운영중' : '마감';
  badge.className = 'market-badge ' + (data.market_open ? 'open' : 'closed');

  grid.innerHTML = data.items.map(item => {
    if (item.error) return `<div class="card card--row"><p class="card-error">—</p></div>`;
    return `
      <div class="card card--row">
        <div class="card-row-left">
          <div class="card-row-name">${item.name}</div>
        </div>
        <div class="card-row-right">
          <div class="card-row-price ${item.direction}">${item.current}</div>
          <div class="card-row-change ${item.direction}">
            ${arrow(item.direction)} ${item.change} (${item.change_pct})
          </div>
        </div>
      </div>`;
  }).join('');
}

// ── 원자재 렌더링
function renderCommodity(data) {
  const grid = document.getElementById('commodityGrid');

  if (!data || data.error) {
    grid.innerHTML = `<p class="card-error">데이터를 불러올 수 없습니다.</p>`;
    return;
  }

  grid.innerHTML = data.items.map(item => {
    if (item.error) return `<div class="card card--row"><p class="card-error">—</p></div>`;
    return `
      <div class="card card--row">
        <div class="card-row-left">
          <div class="card-row-name">
            ${item.name}
            <span class="card-row-unit">${item.unit}</span>
          </div>
        </div>
        <div class="card-row-right">
          <div class="card-row-price ${item.direction}">${item.current}</div>
          <div class="card-row-change ${item.direction}">
            ${arrow(item.direction)} ${item.change} (${item.change_pct})
          </div>
        </div>
      </div>`;
  }).join('');
}

// ── 뉴스 렌더링
function renderNews(articles) {
  const list = document.getElementById('newsList');
  const count = document.getElementById('newsCount');

  if (!articles || articles.length === 0) {
    list.innerHTML = `<li class="news-item news-loading">뉴스를 불러올 수 없습니다.</li>`;
    return;
  }

  count.textContent = `${articles.length}건`;
  list.innerHTML = articles.map(a => `
    <li class="news-item">
      <span class="news-time">${a.published}</span>
      <span class="news-title">
        <a href="${a.link}" target="_blank" rel="noopener noreferrer">${a.title}</a>
      </span>
    </li>`).join('');
}

// ── 상단 티커바 렌더링
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
          <span class="ticker-change ${item.direction}">
            ${arrow(item.direction)} ${item.change_pct}
          </span>
        </span>
        <span class="ticker-divider">|</span>`);
    });
  };

  addItems(data.domestic);
  addItems(data.usfutures);
  addItems(data.commodity);

  if (items.length === 0) return;

  // 무한 루프를 위해 2번 반복
  const html = items.join('') + items.join('');
  track.innerHTML = html;
}
