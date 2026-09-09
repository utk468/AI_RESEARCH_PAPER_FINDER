let _allPapers = [];
let _searchData = null;
let _pipelineTimer = null;

const PIPELINE_STEPS_ORDER = [
  'query_understanding', 'query_expansion', 'web_search',
  'academic_filter', 'metadata_extraction', 'pdf_fetch',
  'pdf_parser', 'summarization', 'research_gap', 'recommendation',
];

function startPipelineAnimation() {
  const stepsContainer = document.getElementById('pipeline-steps');
  if (stepsContainer) buildPipelineSteps(stepsContainer);

  const loadingOverlay = document.getElementById('loading-overlay');
  const progressFill = document.getElementById('loading-progress-fill');
  const statusText = document.getElementById('loading-status');

  if (loadingOverlay) loadingOverlay.style.display = 'flex';

  const labels = {
    query_understanding: 'Understanding your query...',
    query_expansion:     'Expanding search keywords...',
    web_search:          'Searching academic databases...',
    academic_filter:     'Filtering academic sources...',
    metadata_extraction: 'Extracting paper metadata...',
    pdf_fetch:           'Downloading PDFs...',
    pdf_parser:          'Parsing PDF content...',
    summarization:       'Summarizing papers with Groq...',
    research_gap:        'Analyzing research gaps...',
    recommendation:      'Generating recommendations...',
  };

  let currentIdx = 0;
  const total = PIPELINE_STEPS_ORDER.length;

  _pipelineTimer = setInterval(() => {
    if (currentIdx >= total) {
      clearInterval(_pipelineTimer);
      return;
    }
    const stepId = PIPELINE_STEPS_ORDER[currentIdx];
    if (currentIdx > 0) {
      setStepStatus(PIPELINE_STEPS_ORDER[currentIdx - 1], 'done');
    }
    setStepStatus(stepId, 'running');

    if (statusText) statusText.textContent = labels[stepId] || 'Processing...';
    const pct = Math.round(((currentIdx + 1) / total) * 90);
    if (progressFill) progressFill.style.width = `${pct}%`;

    currentIdx++;
  }, 1800);
}

function finishPipelineAnimation() {
  clearInterval(_pipelineTimer);

  PIPELINE_STEPS_ORDER.forEach(s => setStepStatus(s, 'done'));

  const progressFill = document.getElementById('loading-progress-fill');
  if (progressFill) progressFill.style.width = '100%';

  const statusText = document.getElementById('loading-status');
  if (statusText) statusText.textContent = 'Complete! Loading results...';

  setTimeout(() => {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
  }, 700);
}

async function runDashboardSearch(query) {
  if (!query?.trim()) return;

  updateQueryDisplay(query);
  startPipelineAnimation();
  showSkeleton();

  try {
    const data = await API.search(query, { max_results: 12 });
    _searchData = data;
    _allPapers = data.papers || [];

    finishPipelineAnimation();
    renderDashboard(data);
    showToast(`Found ${_allPapers.length} papers in ${data.processing_time_seconds?.toFixed(1)}s`, 'success');

  } catch (err) {
    clearInterval(_pipelineTimer);
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    showToast(`Search failed: ${err.message}`, 'error');
    showErrorState();
  }
}

function updateQueryDisplay(query) {
  const el = document.getElementById('query-display-text');
  if (el) el.textContent = `"${query}"`;
  document.title = `${query} — Research AI`;
}

function renderDashboard(data) {

  const timeBadge = document.getElementById('processing-time-badge');
  if (timeBadge) {
    if (data.processing_time_seconds) {
      timeBadge.textContent = `⚡ ${data.processing_time_seconds.toFixed(1)}s`;
      timeBadge.style.display = 'inline-flex';
    } else {
      timeBadge.style.display = 'none';
    }
  }

  const chipsEl = document.getElementById('understanding-chips');
  if (chipsEl && data.understanding) {
    const kws = [
      ...(data.understanding.keywords || []).slice(0, 4),
      ...(data.understanding.subtopics || []).slice(0, 2),
    ];
    chipsEl.innerHTML = kws.map(k =>
      `<span class="badge badge-purple" role="listitem">${escapeHtml(k)}</span>`
    ).join('');
  }

  const pdfsCount = (data.papers || []).filter(p => p.pdf_url || p.is_pdf_downloaded).length;

  setText('stat-total', data.total_results || (data.papers || []).length || 0);
  setText('stat-pdfs', pdfsCount);

  renderPaperCards(_allPapers);

  const gapsBody = document.getElementById('gaps-body');
  if (gapsBody && data.research_gaps) {
    buildGapsContent(data.research_gaps, gapsBody);
  }

  const recsBody = document.getElementById('recs-body');
  if (recsBody && data.recommendations) {
    buildRecsContent(data.recommendations, recsBody);
  }
}

function renderPaperCards(papers) {
  const list = document.getElementById('papers-list');
  const skeleton = document.getElementById('papers-skeleton');
  const empty = document.getElementById('papers-empty');

  if (skeleton) skeleton.style.display = 'none';
  if (!papers || !papers.length) {
    if (empty) empty.style.display = 'flex';
    if (list) list.style.display = 'none';
    return;
  }

  if (empty) empty.style.display = 'none';
  if (list) {
    list.style.display = 'flex';
    list.innerHTML = '';
    papers.forEach(paper => list.appendChild(buildPaperCard(paper)));
  }

  setText('results-showing', papers.length);
  setText('results-total', _allPapers.length);
}

function showSkeleton() {
  const skeleton = document.getElementById('papers-skeleton');
  const list = document.getElementById('papers-list');
  const empty = document.getElementById('papers-empty');
  if (skeleton) skeleton.style.display = 'flex';
  if (list) list.style.display = 'none';
  if (empty) empty.style.display = 'none';
}

function showErrorState() {
  const skeleton = document.getElementById('papers-skeleton');
  const list = document.getElementById('papers-list');
  const empty = document.getElementById('papers-empty');
  if (skeleton) skeleton.style.display = 'none';
  if (list) list.style.display = 'none';
  if (empty) {
    empty.style.display = 'flex';
    empty.querySelector('.empty-state-title').textContent = 'Search Failed';
    empty.querySelector('.empty-state-desc').textContent = 'Please check your API keys and ensure the backend server is running.';
  }
}

function applyFilters() {
  let papers = [..._allPapers];

  const sort = document.getElementById('sort-select')?.value || 'score';
  papers.sort((a, b) => {
    switch (sort) {
      case 'year_desc': return (b.year || 0) - (a.year || 0);
      case 'year_asc':  return (a.year || 0) - (b.year || 0);
      case 'citations': return (b.citation_count || 0) - (a.citation_count || 0);
      case 'title':     return (a.title || '').localeCompare(b.title || '');
      default:          return (b.similarity_score || 0) - (a.similarity_score || 0);
    }
  });

  const yearFrom = parseInt(document.getElementById('filter-year-from')?.value) || null;
  const yearTo   = parseInt(document.getElementById('filter-year-to')?.value) || null;
  if (yearFrom) papers = papers.filter(p => (p.year || 0) >= yearFrom);
  if (yearTo)   papers = papers.filter(p => (p.year || 0) <= yearTo);

  const selectedSources = Array.from(document.querySelectorAll('.source-chip.active')).map(btn => btn.dataset.value.toLowerCase());
  if (selectedSources.length > 0) {
    papers = papers.filter(p => {
      const src = (p.source || p.journal || p.publisher || '').toLowerCase();
      return selectedSources.some(s => src.includes(s));
    });
  }

  if (document.getElementById('filter-pdf')?.checked)     papers = papers.filter(p => p.pdf_url);
  if (document.getElementById('filter-github')?.checked)  papers = papers.filter(p => p.github_url);
  if (document.getElementById('filter-dataset')?.checked) papers = papers.filter(p => p.dataset);

  renderPaperCards(papers);
}

function toggleSourceChip(btn) {
  if (btn) {
    btn.classList.toggle('active');
  }
}

function resetFilters() {
  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) sortSelect.value = 'score';

  const yearFrom = document.getElementById('filter-year-from');
  if (yearFrom) yearFrom.value = '';

  const yearTo = document.getElementById('filter-year-to');
  if (yearTo) yearTo.value = '';

  document.querySelectorAll('.source-chip').forEach(btn => btn.classList.remove('active'));

  renderPaperCards(_allPapers);
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    const isActive = btn.dataset.tab === tabId;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', String(isActive));
  });

  const panels = { papers: 'panel-papers', gaps: 'panel-gaps', recommendations: 'panel-recommendations' };
  Object.entries(panels).forEach(([id, panelId]) => {
    const panel = document.getElementById(panelId);
    if (panel) {
      const active = id === tabId;
      panel.style.display = active ? 'block' : 'none';
      panel.classList.toggle('active', active);
    }
  });
}

let _viewMode = 'list';

function toggleView(mode) {
  _viewMode = mode;
  const list = document.getElementById('papers-list');
  if (!list) return;

  if (mode === 'grid') {
    list.style.display = 'grid';
    list.style.gridTemplateColumns = 'repeat(auto-fill, minmax(340px, 1fr))';
  } else {
    list.style.display = 'flex';
    list.style.gridTemplateColumns = '';
  }

  const isList = mode === 'list';
  const listBtn = document.getElementById('view-list');
  const gridBtn = document.getElementById('view-grid');

  if (listBtn) {
    listBtn.classList.toggle('active', isList);
    listBtn.setAttribute('aria-checked', String(isList));
  }
  if (gridBtn) {
    gridBtn.classList.toggle('active', !isList);
    gridBtn.setAttribute('aria-checked', String(!isList));
  }
}

function exportResults() {
  if (!_allPapers.length) { showToast('No results to export.', 'warning'); return; }

  const data = {
    query: _searchData?.query,
    total: _allPapers.length,
    exported_at: new Date().toISOString(),
    papers: _allPapers.map(p => ({
      title: p.title,
      authors: p.authors,
      year: p.year,
      doi: p.doi,
      url: p.url,
      pdf_url: p.pdf_url,
      github_url: p.github_url,
      abstract: p.abstract,
      keywords: p.keywords,
      citation_count: p.citation_count,
    })),
    research_gaps: _searchData?.research_gaps,
    recommendations: _searchData?.recommendations,
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `research-results-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Results exported!', 'success');
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}
