const App = (() => {
  const state = {
    domain: localStorage.getItem('insightiq_domain') || 'ai-ml',
    domains: [],
    competitors: [],
    pages: ['dashboard', 'domains', 'market', 'social', 'news', 'settings'],
    apiBase: 'http://localhost:8000',
  };

  function qs(sel){ return document.querySelector(sel); }
  function qsa(sel){ return Array.from(document.querySelectorAll(sel)); }

  async function fetchJSON(path){
    const url = `${state.apiBase}${path}`;
    const r = await fetch(url);
    return await r.json();
  }

  function openModal(){ qs('#domainModal').classList.remove('hidden'); }
  function closeModal(){ qs('#domainModal').classList.add('hidden'); }
  function openInsightModal(){ qs('#insightModal').classList.remove('hidden'); }
  function closeInsightModal(){ qs('#insightModal').classList.add('hidden'); }

  function setActive(page){
    qsa('.nav-link').forEach(a => a.classList.toggle('active', a.dataset.page === page));
  }

  function navigate(page){
    if(!state.pages.includes(page)) page = 'dashboard';
    setActive(page);
    if(page === 'dashboard') renderDashboard();
    if(page === 'domains') renderDomains();
    if(page === 'market') renderMarket();
    if(page === 'social') renderSocial();
    if(page === 'news') renderNews();
    if(page === 'settings') renderSettings();
  }

  async function init(){
    // Navbar events
    qsa('.nav-link').forEach(a => a.addEventListener('click', e => { e.preventDefault(); navigate(a.dataset.page); }));
    qs('#themeToggle').addEventListener('click', () => document.body.classList.toggle('dark'));

    // Load domains
    const res = await fetchJSON('/api/domains');
    state.domains = res.domains || [];

    // Show modal if no selection
    if(!localStorage.getItem('insightiq_domain')) openModal();
    renderDomainGrid();

    navigate('dashboard');
  }

  function renderDomainGrid(){
    const grid = qs('#domainGrid');
    grid.innerHTML = '';
    state.domains.forEach(d => {
      const el = document.createElement('div');
      el.className = 'domain-tile';
      el.innerHTML = `
        <img src="/assets/default-logo.png" alt="${d.name}" />
        <div>
          <div>${d.name}</div>
          <small>${d.slug}</small>
        </div>
      `;
      el.addEventListener('click', async () => {
        state.domain = d.slug; localStorage.setItem('insightiq_domain', d.slug); closeModal();
        navigate('dashboard');
      });
      grid.appendChild(el);
    });
  }

  async function renderDashboard(){
    // Fetch competitors and CSV sample
    const comps = await fetchJSON(`/api/competitors?domain=${state.domain}`);
    state.competitors = comps.competitors || [];
    const sample = await fetchJSON(`/api/csv-sample?domain=${state.domain}`);

    const content = qs('#content');
    content.innerHTML = '';

    // Header
    const header = document.createElement('div');
    header.className = 'row';
    header.innerHTML = `<h1>Strategic Intelligence — ${state.domain}</h1>`;
    content.appendChild(header);

    // Competitor grid
    const grid = document.createElement('div');
    grid.className = 'grid';
    state.competitors.forEach(c => {
      const card = document.createElement('div');
      card.className = 'card';
      const logoPath = c.logo || '/assets/default-logo.png';
      card.innerHTML = `
        <div class="row">
          <div class="flex">
            <img src="/${logoPath}" onerror="this.src='/assets/default-logo.png'" style="width:36px;height:36px"/>
            <strong>${c.name}</strong>
          </div>
          <span class="pill">--</span>
        </div>
        <button class="btn" data-company="${c.name}">View Insights</button>
      `;
      card.querySelector('button').addEventListener('click', () => openCompetitor(c.name));
      grid.appendChild(card);
    });

    // News & Social cards
    const newsCard = document.createElement('div'); newsCard.className = 'card'; newsCard.innerHTML = `<h3>News</h3><ul id="dashNews" class="list"></ul>`;
    const socialCard = document.createElement('div'); socialCard.className = 'card'; socialCard.innerHTML = `<h3>Social</h3><ul id="dashSocial" class="list"></ul>`;

    content.appendChild(grid);
    content.appendChild(newsCard);
    content.appendChild(socialCard);

    // Populate feeds
    const news = await fetchJSON(`/api/news?domain=${state.domain}&limit=10`);
    const social = await fetchJSON(`/api/social?domain=${state.domain}&limit=10`);
    const newsList = qs('#dashNews'); newsList.innerHTML = (news.items||[]).map(i => `<li>• ${i.headline} <small>(${i.source||'-'})</small></li>`).join('');
    const socialList = qs('#dashSocial'); socialList.innerHTML = (social.items||[]).map(i => `<li>• ${i.headline} <small>(${i.source||'-'})</small></li>`).join('');
  }

  async function openCompetitor(name){
    // Load insights
    const data = await fetchJSON(`/api/insights?company=${encodeURIComponent(name)}&domain=${state.domain}`);
    qs('#insightTitle').textContent = `${name}`;
    qs('#aiInsights').textContent = data.insights || '';
    // KPIs
    qs('#insightKPIs').innerHTML = `Avg Sentiment: ${data?.sentiment_summary?.average ?? 0}`;

    // Forecast tab
    const fc = await fetchJSON(`/api/forecast?company=${encodeURIComponent(name)}&days=30`);
    renderForecastChart(fc.forecast || []);

    // News & Social lists
    const news = await fetchJSON(`/api/news?company=${encodeURIComponent(name)}&domain=${state.domain}&limit=10`);
    const social = await fetchJSON(`/api/social?company=${encodeURIComponent(name)}&domain=${state.domain}&limit=10`);
    qs('#newsList').innerHTML = (news.items||[]).map(i => `<li>• <a target="_blank" href="${i.link}">${i.headline}</a></li>`).join('');
    qs('#socialList').innerHTML = (social.items||[]).map(i => `<li>• ${i.headline}</li>`).join('');

    openInsightModal();
  }

  function renderForecastChart(points){
    const ctx = document.getElementById('forecastChart');
    if(!ctx) return;
    const labels = points.map(p => p.date);
    const data = points.map(p => p.yhat);
    new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ label: 'Forecast', data, borderColor: '#60a5fa', fill: false }] },
      options: { responsive: true, plugins: { legend: { display: true } } }
    });
  }

  async function renderDomains(){
    const content = qs('#content');
    content.innerHTML = '<h2>Domains</h2>';
    const grid = document.createElement('div'); grid.className = 'grid';
    state.domains.forEach(d => {
      const card = document.createElement('div'); card.className = 'card';
      card.innerHTML = `
        <div class="row"><strong>${d.name}</strong><small>${d.slug}</small></div>
        <div class="flex" style="flex-wrap:wrap;gap:6px;margin:8px 0;">
          ${(d.competitors||[]).slice(0,5).map(c=>`<span class="pill">${c.name}</span>`).join('')}
        </div>
        <div class="row"><button class="btn" data-insights>View Insights</button><button class="btn secondary" data-forecast>View Forecast</button></div>
      `;
      card.querySelector('[data-insights]').addEventListener('click', ()=>{ localStorage.setItem('insightiq_domain', d.slug); state.domain=d.slug; navigate('dashboard'); });
      card.querySelector('[data-forecast]').addEventListener('click', async ()=>{
        const fc = await fetchJSON(`/api/forecast?company=aggregate&days=30`);
        openInsightModal();
        qs('#insightTitle').textContent = `${d.name} — Market Forecast`;
        renderForecastChart(fc.forecast||[]);
        qs('#aiInsights').textContent = 'Forecast preview — use the Dashboard to open competitor insights.';
      });
      grid.appendChild(card);
    });
    content.appendChild(grid);
  }

  async function renderMarket(){
    const content = qs('#content');
    content.innerHTML = `
      <div class="row">
        <h2>Market</h2>
        <div>
          <select id="companySel"><option>aggregate</option>${(state.competitors||[]).map(c=>`<option>${c.name}</option>`).join('')}</select>
          <button class="btn" id="apply">Apply</button>
        </div>
      </div>
      <div class="card"><canvas id="marketChart" height="140"></canvas></div>
    `;
    async function run(){
      const company = qs('#companySel').value;
      const fc = await fetchJSON(`/api/forecast?company=${encodeURIComponent(company)}&days=30`);
      const ctx = qs('#marketChart');
      new Chart(ctx, { type: 'line', data: { labels: (fc.forecast||[]).map(p=>p.date), datasets: [{label: 'Forecast', data: (fc.forecast||[]).map(p=>p.yhat), borderColor:'#34d399'}] } });
    }
    qs('#apply').addEventListener('click', run);
    run();
  }

  async function renderSocial(){
    const content = qs('#content');
    const data = await fetchJSON(`/api/social?domain=${state.domain}&limit=20`);
    content.innerHTML = `<h2>Social</h2><div class="card"><ul class="list">${(data.items||[]).map(i=>`<li>${i.headline}</li>`).join('')}</ul></div>`;
  }

  async function renderNews(){
    const content = qs('#content');
    const data = await fetchJSON(`/api/news?domain=${state.domain}&limit=20`);
    content.innerHTML = `<h2>News</h2><div class="card"><ul class="list">${(data.items||[]).map(i=>`<li><a target="_blank" href="${i.link}">${i.headline}</a> <small>${i.source||'-'}</small></li>`).join('')}</ul></div>`;
  }

  function renderSettings(){
    const content = qs('#content');
    const envKeys = ['OPENAI_API_KEY','GNEWS_API_KEY','SERPAPI_KEY','FINNHUB_KEY','ALPHAVANTAGE_KEY','REDDIT_CLIENT_ID','REDDIT_CLIENT_SECRET','REDDIT_USER_AGENT','TWITTER_BEARER_TOKEN','SLACK_WEBHOOK_URL'];
    content.innerHTML = `
      <h2>Settings</h2>
      <div class="card">
        <p>.env keys (edit backend/.env):</p>
        <ul class="list">${envKeys.map(k=>`<li>${k}=...</li>`).join('')}</ul>
        <button class="btn" id="regen">Regenerate CSVs</button>
      </div>
    `;
    qs('#regen').addEventListener('click', async ()=>{
      await fetch(`${state.apiBase}/api/regenerate-csvs`, { method: 'POST' });
      alert('CSVs regenerated.');
    });
  }

  // Tabs in insight modal
  document.addEventListener('click', (e)=>{
    const tbtn = e.target.closest('.tab'); if(!tbtn) return;
    const tab = tbtn.dataset.tab;
    qsa('.tab').forEach(x=>x.classList.toggle('active', x===tbtn));
    qsa('.tab-pane').forEach(p=>p.classList.toggle('active', p.id===`tab-${tab}`));
  });

  // Export & create alert
  document.addEventListener('click', async (e)=>{
    if(e.target.id==='exportInsights'){
      const text = qs('#aiInsights').textContent || '';
      const blob = new Blob([text], {type: 'text/plain'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'insights.txt'; a.click(); URL.revokeObjectURL(url);
    }
    if(e.target.id==='createAlert'){
      const title = qs('#insightTitle').textContent || 'Alert';
      await fetch(`${state.apiBase}/api/webhook/alerts`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ title, severity: 'info', message: 'User created alert from UI' }) });
      alert('Alert created');
    }
  });

  return { init, openModal, closeModal, navigate, closeInsightModal };
})();

window.addEventListener('DOMContentLoaded', App.init);
