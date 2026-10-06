const PAGE = (() => {
  const path = window.location.pathname;
  if (path.includes('dashboard')) return 'dashboard';
  if (path.includes('paper'))     return 'paper';
  return 'home';
})();

let currentSearchId = null;

document.addEventListener('DOMContentLoaded', async () => {
  switch (PAGE) {
    case 'home':      initHomePage();      break;
    case 'dashboard': initDashboardPage(); break;
    case 'paper':     initPaperPage();     break;
  }
});

async function initHomePage() {
  loadRecentSearches();
  fetchHealthStats();

  const form = document.getElementById('search-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      handleHomeSearch();
    });
  }
}

function fillQuery(chip) {
  const input = document.getElementById('search-input');
  if (input) {
    input.value = chip.textContent.trim();
    input.focus();
  }
}

function handleHomeSearch() {
  const input = document.getElementById('search-input');
  const query = input?.value.trim();
  if (!query) { showToast('Please enter a research query.', 'warning'); return; }

  setLocalStorage('pending_query', query);
  window.location.href = 'dashboard.html';
}

function loadRecentSearches() {
  const container = document.getElementById('recent-section');
  const list = document.getElementById('recent-list');
  if (!container || !list) return;

  API.history(5)
    .then(data => {
      const items = data.items || [];
      if (!items.length) return;

      container.style.display = 'block';
      list.innerHTML = '';
      items.forEach(item => {
        const el = document.createElement('button');
        el.className = 'recent-search-item';
        el.setAttribute('aria-label', `Search for: ${item.query}`);
        el.innerHTML = `
          <span class="recent-search-icon" aria-hidden="true"><i class="fa-solid fa-clock-rotate-left"></i></span>
          <span class="recent-search-query">${escapeHtml(item.query)}</span>
          <span class="recent-search-count">${item.total_results} papers</span>
        `;
        el.addEventListener('click', () => {
          setLocalStorage('pending_query', item.query);
          window.location.href = 'dashboard.html';
        });
        list.appendChild(el);
      });
    })
    .catch(() => {

    });
}

async function fetchHealthStats() {
  try {
    const health = await fetch('http://localhost:8000/health').then(r => r.json());

    const vectors = document.getElementById('stat-vectors');
    if (vectors) vectors.textContent = formatNumber(health.faiss_vectors || 0);

    if (health.mongodb === 'connected') {

      const hist = await API.history(100);
      const searches = document.getElementById('stat-searches');
      if (searches) searches.textContent = hist.total || hist.items?.length || 0;
    }
  } catch (_) {

    const badge = document.createElement('div');
    badge.style.cssText = 'position:fixed;bottom:16px;left:16px;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);color:#f87171;padding:8px 14px;border-radius:8px;font-size:0.8rem;z-index:9999';
    badge.textContent = '⚠️ Backend offline — start the FastAPI server first.';
    document.body.appendChild(badge);
  }
}

function openBookmarks() {
  showToast('Sign in to view your bookmarks', 'info');
}

async function initDashboardPage() {
  const query = getLocalStorage('pending_query');

  if (query) {
    localStorage.removeItem('pending_query');
    setLocalStorage('last_query', query);
    await runDashboardSearch(query);
  } else {

    try {
      const hist = await API.history(1);
      const lastItem = hist.items?.[0];
      if (lastItem) {
        updateQueryDisplay(lastItem.query);
        showToast('Loaded most recent search.', 'info');
      }
    } catch (_) {}
  }

  const miniForm = document.getElementById('mini-search-form');
  if (miniForm) {
    miniForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = document.getElementById('mini-search-input')?.value.trim();
      if (!q) return;
      setLocalStorage('pending_query', q);
      window.location.reload();
    });
  }

  const sortSel = document.getElementById('sort-select');
  if (sortSel) sortSel.addEventListener('change', () => applyFilters());
}

function doMiniSearch() {
  const q = document.getElementById('mini-search-input')?.value.trim();
  if (!q) return;
  setLocalStorage('pending_query', q);
  if (PAGE === 'dashboard') window.location.reload();
  else window.location.href = 'dashboard.html';
}

function toggleBookmarkPanel() {
  showToast('Bookmark panel coming soon', 'info');
}

async function initPaperPage() {
  const paperId = getParam('id');
  if (!paperId) {
    showToast('No paper ID found in URL.', 'error');
    return;
  }

  await loadPaperDetail(paperId);
  await loadRelatedPapers(paperId);
}

async function loadPaperDetail(paperId) {
  try {
    const paper = await API.getPaper(paperId);
    renderPaperDetail(paper);
    initChat(paperId);
  } catch (err) {
    showToast(`Failed to load paper: ${err.message}`, 'error');
  }
}

function renderPaperDetail(paper) {

  document.title = `${paper.title} — Research AI`;

  const titleEl = document.getElementById('paper-title');
  if (titleEl) titleEl.textContent = paper.title;

  const authorsEl = document.getElementById('paper-authors');
  if (authorsEl) authorsEl.textContent = (paper.authors || []).join(', ');

  const citEl = document.getElementById('citation-count');
  if (citEl) citEl.textContent = paper.citation_count != null ? formatNumber(paper.citation_count) : '—';

  const bc = document.getElementById('breadcrumb-title');
  if (bc) bc.textContent = paper.title.slice(0, 40) + (paper.title.length > 40 ? '…' : '');

  const badges = document.getElementById('hero-badges');
  if (badges) {
    badges.innerHTML = '';
    if (paper.year)       badges.innerHTML += `<span class="badge badge-gray">${paper.year}</span>`;
    if (paper.conference) badges.innerHTML += `<span class="badge badge-purple">${escapeHtml(paper.conference)}</span>`;
    if (paper.publisher)  badges.innerHTML += `<span class="badge badge-blue">${escapeHtml(paper.publisher)}</span>`;
    if (paper.license)    badges.innerHTML += `<span class="badge badge-green">${escapeHtml(paper.license)}</span>`;
  }

  const doiEl = document.getElementById('hero-doi');
  if (doiEl && paper.doi) {
    doiEl.innerHTML = `DOI: <a href="https://doi.org/${paper.doi}" target="_blank" rel="noopener" style="color:var(--accent-primary)">${paper.doi}</a>`;
  }

  const pdfBtn = document.getElementById('pdf-btn');
  if (pdfBtn) {
    if (paper.pdf_url) {
      pdfBtn.href = paper.pdf_url;
      pdfBtn.style.display = 'flex';
    } else {
      pdfBtn.style.display = 'none';
    }
  }

  const ghBtn = document.getElementById('github-btn');
  if (ghBtn) {
    if (paper.github_url) {
      ghBtn.href = paper.github_url;
      ghBtn.style.display = 'flex';
    } else {
      ghBtn.style.display = 'none';
    }
  }

  const abstractEl = document.getElementById('abstract-text');
  if (abstractEl) {
    const rawAbs = (paper.summary && paper.summary.abstract) ? paper.summary.abstract : paper.abstract;
    abstractEl.textContent = cleanAbstractText(rawAbs) || 'No abstract available.';
    if (typeof renderMath === 'function') renderMath(abstractEl);
  }
  const absTableContainer = document.getElementById('abstract-table-container');
  if (absTableContainer) {
    buildAbstractTable(paper, absTableContainer);
  }

  const kwCloud = document.getElementById('keywords-cloud');
  if (kwCloud) {
    const keywords = paper.keywords || [];
    const parentCard = kwCloud.closest('.sidebar-card');
    if (keywords.length > 0) {
      if (parentCard) parentCard.style.display = 'block';
      kwCloud.innerHTML = keywords
        .map(k => `<span class="tag">${escapeHtml(k)}</span>`)
        .join('');
    } else {
      if (parentCard) parentCard.style.display = 'none';
    }
  }

  buildMetaTable(paper);

  buildQuickInfo(paper);

  buildPdfBanner(paper);

  renderPdfViewer(paper);

  if (paper.summary) {
    const summaryBody = document.getElementById('summary-body');
    if (summaryBody) buildSummaryBody(paper.summary, summaryBody);

    const contribs = paper.summary.key_contributions || [];
    if (contribs.length) {
      const card = document.getElementById('contributions-card');
      const list = document.getElementById('contributions-list');
      if (card && list) {
        card.style.display = 'block';
        list.innerHTML = contribs.map((c, i) => `
          <div class="contrib-card">
            <div class="contrib-num">${i + 1}</div>
            <span>${escapeHtml(c)}</span>
          </div>
        `).join('');
      }
    }
  } else {

    generateSummaryFromPage(paper.paper_id);
  }

  renderPdfViewer(paper);
}

async function generateSummaryFromPage(paperId) {
  try {
    const summaryBody = document.getElementById('summary-body');
    if (summaryBody) {
      summaryBody.innerHTML = `
        <div style="display:flex;align-items:center;gap:var(--space-3);color:var(--text-muted)">
          <div class="spinner spinner-sm"></div>
          Generating AI summary...
        </div>`;
    }
    const result = await API.getSummary(paperId);
    if (result.summary && summaryBody) {
      buildSummaryBody(result.summary, summaryBody);
    }
  } catch (err) {
    const summaryBody = document.getElementById('summary-body');
    if (summaryBody) summaryBody.innerHTML = `<p style="color:var(--text-muted)">Summary unavailable: ${err.message}</p>`;
  }
}

async function regenerateSummary() {
  const paperId = getParam('id');
  if (!paperId) return;
  showToast('Regenerating summary...', 'info');
  await generateSummaryFromPage(paperId);
}

function buildMetaTable(paper) {
  const table = document.getElementById('meta-table');
  if (!table) return;

  const rows = [
    { label: 'Authors',     value: (paper.authors || []).join(', ') },
    { label: 'Year',        value: paper.year },
    { label: 'Conference',  value: paper.conference },
    { label: 'Publisher',   value: paper.publisher },
    { label: 'DOI',         value: paper.doi ? `<a href="https://doi.org/${paper.doi}" target="_blank" rel="noopener">${paper.doi}</a>` : null },
    { label: 'License',     value: paper.license },
    { label: 'Dataset',     value: paper.dataset },
    { label: 'GitHub',      value: paper.github_url ? `<a href="${paper.github_url}" target="_blank" rel="noopener">${paper.github_url}</a>` : null },
    { label: 'PDF',         value: paper.pdf_url ? `<a href="${paper.pdf_url}" target="_blank" rel="noopener">Download PDF</a>` : null },
    { label: 'Source',      value: paper.url ? `<a href="${paper.url}" target="_blank" rel="noopener">${paper.url}</a>` : null },
    { label: 'Citations',   value: paper.citation_count != null ? formatNumber(paper.citation_count) : null },
  ];

  table.innerHTML = rows
    .filter(r => r.value)
    .map(r => `
      <tr>
        <td>${escapeHtml(r.label)}</td>
        <td>${typeof r.value === 'string' && (r.value.startsWith('<a') || r.value.startsWith('<span'))
          ? r.value
          : escapeHtml(String(r.value))}</td>
      </tr>
    `)
    .join('');
}

function buildQuickInfo(paper) {
  const container = document.getElementById('quick-info-content');
  if (!container) return;

  container.innerHTML = `
    <div class="info-table">
      ${paper.year ? `<div class="info-row"><span class="info-label">Year</span><span class="info-value">${paper.year}</span></div>` : ''}
      ${paper.conference ? `<div class="info-row"><span class="info-label">Conference</span><span class="info-value">${escapeHtml(paper.conference)}</span></div>` : ''}
      ${paper.citation_count != null ? `<div class="info-row"><span class="info-label">Citations</span><span class="info-value" style="color:var(--yellow);font-family:var(--font-mono)"><i class="fa-solid fa-quote-right" aria-hidden="true"></i> ${formatNumber(paper.citation_count)}</span></div>` : ''}
      ${paper.similarity_score != null ? `<div class="info-row"><span class="info-label">Relevance</span><span class="score-pill ${getScoreClass(paper.similarity_score)}">${(paper.similarity_score * 100).toFixed(0)}%</span></div>` : ''}
    </div>
  `;
}

function buildPdfBanner(paper) {
  const container = document.getElementById('pdf-banner-container');
  if (!container) return;
  if (!paper.pdf_url) return;

  container.innerHTML = `
    <div class="pdf-banner">
      <div class="pdf-banner-info">
        <div class="pdf-banner-icon" aria-hidden="true"><i class="fa-solid fa-file-pdf"></i></div>
        <div class="pdf-banner-text">
          <strong>PDF Available</strong>
          ${paper.is_pdf_downloaded ? 'Downloaded & indexed' : 'Available for download'}
        </div>
      </div>
      <a class="btn-pdf-download" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noopener" aria-label="Download PDF">
        <i class="fa-solid fa-download" aria-hidden="true"></i> Download
      </a>
    </div>
  `;
}

async function loadRelatedPapers(paperId) {
  const list = document.getElementById('related-list');
  if (!list) return;

  try {
    const data = await API.getRelated(paperId, 5);
    const related = data.related || [];

    if (!related.length) {
      list.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem">No related papers found yet.</p>';
      return;
    }

    list.innerHTML = '';
    related.forEach((rp, i) => {
      const el = document.createElement('button');
      el.className = 'related-paper-item';
      el.setAttribute('aria-label', `Related paper: ${rp.title}`);
      el.innerHTML = `
        <div class="related-paper-num" aria-hidden="true">${i + 1}</div>
        <div class="related-paper-title">${escapeHtml(rp.title)}</div>
      `;
      el.addEventListener('click', () => openPaper(null, rp.paper_id));
      list.appendChild(el);
    });
  } catch (_) {
    list.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem">Related papers unavailable.</p>';
  }
}

function switchPaperTab(tabId) {
  document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    const isActive = btn.dataset.tab === tabId;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', String(isActive));
  });
  document.querySelectorAll('[id^="ppanel-"]').forEach(panel => {
    panel.style.display = panel.id === `ppanel-${tabId}` ? 'block' : 'none';
    panel.classList.toggle('active', panel.id === `ppanel-${tabId}`);
  });

  if (tabId === 'chat') {
    prepareChatForUI();
  }
}

async function toggleBookmark() {
  const paperId = getParam('id');
  if (!paperId) return;

  try {
    await API.addBookmark(paperId);
    showToast('Paper bookmarked!', 'success');
    const btn = document.getElementById('bookmark-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-bookmark"></i> Bookmarked';
  } catch (err) {
    showToast(`Bookmark failed: ${err.message}`, 'error');
  }
}

async function bookmarkCard(event, paperId) {
  event?.stopPropagation?.();
  try {
    await API.addBookmark(paperId);
    showToast('Paper bookmarked!', 'success');
  } catch (err) {
    showToast('Already bookmarked.', 'info');
  }
}

let currentRating = 0;

function setRating(val) {
  currentRating = val;
  document.querySelectorAll('.star').forEach(star => {
    star.classList.toggle('active', parseInt(star.dataset.val) <= val);
  });
}

async function submitFeedback() {
  if (!currentRating) { showToast('Please select a rating.', 'warning'); return; }
  const paperId = getParam('id');
  const comment = document.getElementById('feedback-comment')?.value || '';

  try {
    await API.submitFeedback(paperId, currentRating, comment);
    showToast('Thank you for your feedback!', 'success');
    setRating(0);
  } catch (err) {
    showToast('Failed to submit feedback.', 'error');
  }
}

function renderPdfViewer(paper) {
  const container = document.getElementById('pdf-viewer-container');
  if (!container) return;

  if (!paper.pdf_url) {
    container.innerHTML = `
      <div style="height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--bg-card); color: var(--text-muted);">
        <i class="fa-solid fa-file-circle-xmark" style="font-size: 3rem; margin-bottom: var(--space-4); opacity: 0.5;"></i>
        <p>No PDF available to display.</p>
      </div>
    `;
    return;
  }

  const safePdfUrl = escapeHtml(paper.pdf_url);
  container.innerHTML = `
    <iframe src="${safePdfUrl}" style="width: 100%; height: 100%; border: none;" title="PDF Document Viewer"></iframe>
  `;
}
