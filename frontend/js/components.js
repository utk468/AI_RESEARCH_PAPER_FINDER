function cleanAbstractText(text) {
  if (!text) return '';
  let cleaned = text;
  cleaned = cleaned.replace(/#{1,6}\s*\d*(?:\.\d*)*\s*[^.\n]+(?=\n|\s)/g, '');
  cleaned = cleaned.replace(/\|(?:\s*[-:]+\s*\|)+/g, ' ');
  cleaned = cleaned.replace(/\|[^|\n]+\|/g, ' ');
  cleaned = cleaned.replace(/\b[A-Z][a-zA-Z0-9\s\.\&\-]{1,40}\s+et\s+al\.\s*\(\d{4}\)/g, '');
  cleaned = cleaned.replace(/\b[A-Z][a-zA-Z0-9\s\.\&\-]{1,40}\s*\(\d{4}\)/g, '');
  cleaned = cleaned.replace(/\((?:[A-Z][a-zA-Z0-9\s\.\&\-]{1,30}(?:\s+et\s+al\.)?,?\s*)?\d{4}(?:;\s*(?:[A-Z][a-zA-Z0-9\s\.\&\-]{1,30}(?:\s+et\s+al\.)?,?\s*)?\d{4})*\)/g, '');
  cleaned = cleaned.replace(/\\[a-zA-Z]+(?:\{[^}]*\})*/g, '');
  cleaned = cleaned.replace(/[$_^{}\\]+/g, '');
  cleaned = cleaned.replace(/[\u2200-\u22FF\u2A00-\u2AFF\u2100-\u214F]/g, '');
  cleaned = cleaned.replace(/[𝒫𝒯ℛ∪∩∈∉⊂⊃⊆⊇ˆ˜¯⃗⋅×÷±=≠<>⩽⩾]/g, '');
  cleaned = cleaned.replace(/\[\s*\.\.\.\s*\]/g, ' ');
  cleaned = cleaned.replace(/\.\.\./g, ' ');
  cleaned = cleaned.replace(/\bABSTARCT\b|\bABSTRACT\b/gi, '');
  return cleaned.replace(/\s+/g, ' ').trim();
}

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <span class="toast-icon" aria-hidden="true">${icons[type] || 'ℹ️'}</span>
    <span class="toast-message">${escapeHtml(message)}</span>
    <button style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1rem;padding:0 0 0 var(--space-3)" onclick="dismissToast(this)" aria-label="Dismiss">×</button>
  `;
  container.appendChild(toast);

  if (duration > 0) {
    setTimeout(() => dismissToast(toast.querySelector('button')), duration);
  }
}

function dismissToast(btn) {
  const toast = btn.closest ? btn.closest('.toast') : btn;
  if (!toast) return;
  toast.classList.add('hiding');
  setTimeout(() => toast.remove(), 320);
}

function buildPaperCard(paper) {
  const card = document.createElement('article');
  card.className = 'paper-card';
  card.setAttribute('role', 'listitem');
  card.setAttribute('aria-label', `Paper: ${paper.title}`);
  card.setAttribute('data-paper-id', paper.paper_id);
  card.setAttribute('data-year', paper.year || 0);
  card.setAttribute('data-score', paper.similarity_score || 0);
  card.setAttribute('data-citations', paper.citation_count || 0);
  card.setAttribute('data-source', (paper.url || '').toLowerCase());

  const scoreClass = getScoreClass(paper.similarity_score);
  const yearBadge = paper.year ? `<span class="badge badge-gray">${paper.year}</span>` : '';
  const confBadge = paper.conference ? `<span class="badge badge-purple">${escapeHtml(paper.conference.slice(0, 30))}</span>` : '';
  const pdfBadge = paper.pdf_url ? `<span class="badge badge-green"><i class="fa-solid fa-file-pdf" aria-hidden="true"></i> PDF</span>` : '';
  const githubBadge = paper.github_url ? `<span class="badge badge-blue"><i class="fa-brands fa-github" aria-hidden="true"></i> Code</span>` : '';

  const authors = (paper.authors || []).slice(0, 4).join(', ');
  const moreAuthors = (paper.authors || []).length > 4 ? ` +${paper.authors.length - 4} more` : '';

  const abstract = cleanAbstractText(paper.abstract || '').slice(0, 280);
  const keywords = (paper.keywords || []).slice(0, 5);

  const summarySnippet = paper.summary?.summary_100_words
    ? `<div class="paper-card-summary" style="margin-bottom:var(--space-3)">
        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--accent-primary);margin-bottom:6px">
          <i class="fa-solid fa-sparkles" aria-hidden="true"></i> AI Summary
        </div>
        <p style="font-size:0.85rem;color:var(--text-secondary);line-height:1.6">${escapeHtml(paper.summary.summary_100_words)}</p>
       </div>`
    : '';

  card.innerHTML = `
    <div class="paper-card-header">
      <div style="flex:1;min-width:0">
        <div class="paper-card-meta">
          ${yearBadge}
          ${confBadge}
          ${pdfBadge}
          ${githubBadge}
        </div>
        <h2 class="paper-card-title">${escapeHtml(paper.title)}</h2>
        <div class="paper-card-authors">${escapeHtml(authors)}${moreAuthors ? `<span style="color:var(--text-muted)">${moreAuthors}</span>` : ''}</div>
      </div>
      <div class="paper-score-badge">
        ${paper.similarity_score != null
          ? `<span class="score-pill ${scoreClass}" title="Relevance score" aria-label="Relevance score ${(paper.similarity_score * 100).toFixed(0)}%">
               ${(paper.similarity_score * 100).toFixed(0)}%
             </span>`
          : ''}
        ${paper.citation_count != null
          ? `<span style="font-size:0.72rem;color:var(--text-muted);font-family:var(--font-mono)">
               <i class="fa-solid fa-quote-right" style="color:var(--yellow)" aria-hidden="true"></i>
               ${formatNumber(paper.citation_count)}
             </span>`
          : ''}
      </div>
    </div>

    ${summarySnippet}

    ${!summarySnippet && abstract ? `<p class="paper-card-abstract">${escapeHtml(abstract)}${paper.abstract?.length > 280 ? '...' : ''}</p>` : ''}

    ${keywords.length > 0
      ? `<div class="paper-card-keywords" aria-label="Keywords">
           ${keywords.map(k => `<span class="tag">${escapeHtml(k)}</span>`).join('')}
         </div>`
      : ''}

    <div class="paper-card-footer">
      <div class="paper-card-actions">
        <button class="paper-action-btn chat-btn" onclick="openPaper(event, '${paper.paper_id}')" aria-label="View paper details">
          <i class="fa-solid fa-eye" aria-hidden="true"></i> View
        </button>
        ${paper.pdf_url
          ? `<a class="paper-action-btn pdf-btn" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" aria-label="Download PDF">
               <i class="fa-solid fa-download" aria-hidden="true"></i> PDF
             </a>`
          : ''}
        ${paper.github_url
          ? `<a class="paper-action-btn github-btn" href="${escapeHtml(paper.github_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" aria-label="View GitHub">
               <i class="fa-brands fa-github" aria-hidden="true"></i> Code
             </a>`
          : ''}
      </div>
      <div class="flex items-center gap-2" style="font-size:0.75rem;color:var(--text-muted)">
        ${paper.dataset ? `<span><i class="fa-solid fa-database" aria-hidden="true"></i> ${escapeHtml(paper.dataset.slice(0, 30))}</span>` : ''}
        ${paper.publisher ? `<span>· ${escapeHtml(paper.publisher.slice(0, 25))}</span>` : ''}
      </div>
    </div>
  `;

  card.addEventListener('click', (e) => {
    if (!e.target.closest('.paper-action-btn') && !e.target.closest('a')) {
      openPaper(e, paper.paper_id);
    }
  });

  return card;
}

const PIPELINE_STEPS = [
  { id: 'query_understanding',   label: 'Query Understanding' },
  { id: 'query_expansion',       label: 'Query Expansion' },
  { id: 'web_search',            label: 'Web Search' },
  { id: 'academic_filter',       label: 'Academic Filter' },
  { id: 'metadata_extraction',   label: 'Metadata Extraction' },
  { id: 'pdf_fetch',             label: 'PDF Fetch' },
  { id: 'pdf_parser',            label: 'PDF Parsing' },
  { id: 'summarization',         label: 'Groq Summarization' },
  { id: 'research_gap',          label: 'Gap Analysis' },
  { id: 'recommendation',        label: 'Recommendations' },
];

function buildPipelineSteps(container) {
  if (!container) return;
  container.innerHTML = '';
  PIPELINE_STEPS.forEach((step, idx) => {
    const el = document.createElement('div');
    el.className = 'pipeline-step pending';
    el.id = `step-${step.id}`;
    el.setAttribute('role', 'listitem');
    el.setAttribute('aria-label', `${step.label}: pending`);
    el.innerHTML = `
      <div class="step-indicator" aria-hidden="true">${idx + 1}</div>
      <span class="step-label">${step.label}</span>
    `;
    container.appendChild(el);
  });
}

function setStepStatus(stepId, status) {
  const el = document.getElementById(`step-${stepId}`);
  if (!el) return;
  el.className = `pipeline-step ${status}`;
  const icons = { running: '⟳', done: '✓', error: '✗', pending: String(PIPELINE_STEPS.findIndex(s => s.id === stepId) + 1) };
  const indicator = el.querySelector('.step-indicator');
  if (indicator) indicator.textContent = icons[status] || '?';
  el.setAttribute('aria-label', `${el.querySelector('.step-label').textContent}: ${status}`);
}

function buildGapsContent(gaps, container) {
  if (!container || !gaps) return;
  container.innerHTML = '';

  const sections = [
    { key: 'current_trends',     label: 'Current Trends',     icon: '📈' },
    { key: 'open_challenges',    label: 'Open Challenges',     icon: '⚡' },
    { key: 'research_gaps',      label: 'Research Gaps',       icon: '🔍' },
    { key: 'future_directions',  label: 'Future Directions',   icon: '🚀' },
    { key: 'potential_thesis_ideas', label: 'Thesis Ideas',    icon: '💡' },
    { key: 'novel_ideas',        label: 'Novel Ideas',         icon: '✨' },
  ];

  sections.forEach(({ key, label, icon }) => {
    const items = gaps[key] || [];
    if (!items.length) return;

    const section = document.createElement('div');
    section.style.marginBottom = 'var(--space-6)';
    section.innerHTML = `
      <div style="font-size:0.8rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--accent-primary);margin-bottom:var(--space-3)">
        ${icon} ${label}
      </div>
      <div class="gap-grid">
        ${items.map(item => `
          <div class="gap-item">
            <span class="gap-item-icon" aria-hidden="true">${icon}</span>
            <span>${escapeHtml(item)}</span>
          </div>
        `).join('')}
      </div>
    `;
    container.appendChild(section);
  });
}

function buildRecsContent(recs, container) {
  if (!container || !recs) return;
  container.innerHTML = '';

  const sections = [
    { key: 'survey_papers',           label: 'Survey Papers',        icon: '📚' },
    { key: 'code_repositories',       label: 'Code Repositories',    icon: '💻' },
    { key: 'recommended_datasets',    label: 'Datasets',             icon: '🗄️' },
    { key: 'key_authors',             label: 'Key Authors',          icon: '👤' },
    { key: 'recommended_conferences', label: 'Conferences',          icon: '🎯' },
    { key: 'learning_path',           label: 'Learning Path',        icon: '🛤️' },
  ];

  sections.forEach(({ key, label, icon }) => {
    const items = recs[key] || [];
    if (!items.length) return;

    const section = document.createElement('div');
    section.style.marginBottom = 'var(--space-6)';
    section.innerHTML = `
      <div style="font-size:0.8rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--accent-primary);margin-bottom:var(--space-3)">
        ${icon} ${label}
      </div>
      <div class="rec-grid">
        ${items.map((item, i) => `
          <div class="rec-item">
            <div class="rec-item-type">#${i + 1}</div>
            <div class="rec-item-text">${escapeHtml(typeof item === 'object' ? JSON.stringify(item) : item)}</div>
          </div>
        `).join('')}
      </div>
    `;
    container.appendChild(section);
  });

  const related = recs.related_papers || [];
  if (related.length) {
    const section = document.createElement('div');
    section.innerHTML = `
      <div style="font-size:0.8rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--accent-primary);margin-bottom:var(--space-3)">
        🔗 Related Papers to Explore
      </div>
      <div style="display:flex;flex-direction:column;gap:var(--space-2)">
        ${related.map(p => `
          <div class="rec-item">
            <div class="rec-item-type">Paper</div>
            <div class="rec-item-text"><strong>${escapeHtml(p.title || '')}</strong> — ${escapeHtml(p.reason || '')}</div>
          </div>
        `).join('')}
      </div>
    `;
    container.appendChild(section);
  }
}

function buildSummaryBody(summary, container) {
  if (!container || !summary) return;

  const blocks = [
    { key: 'abstract',          label: 'Abstract',           icon: '📄' },
    { key: 'summary_100_words', label: '100-Word Overview',  icon: '📝' },
    { key: 'detailed_summary',  label: 'Detailed Summary',   icon: '📖' },
    { key: 'methodology',       label: 'Methodology',        icon: '⚙️' },
    { key: 'architecture',      label: 'Architecture',       icon: '🏗️' },
    { key: 'dataset',           label: 'Dataset',            icon: '🗄️' },
    { key: 'experiments',       label: 'Experiments',        icon: '🧪' },
    { key: 'results',           label: 'Results',            icon: '📊' },
  ];

  const listBlocks = [
    { key: 'strengths',         label: 'Strengths',     icon: '💪' },
    { key: 'weaknesses',        label: 'Weaknesses',    icon: '⚠️' },
    { key: 'limitations',       label: 'Limitations',   icon: '🚧' },
    { key: 'future_work',       label: 'Future Work',   icon: '🔮' },
    { key: 'applications',      label: 'Applications',  icon: '🎯' },
    { key: 'key_contributions', label: 'Contributions', icon: '🏆' },
  ];

  let html = '';

  blocks.forEach(({ key, label }) => {
    const val = summary[key];
    const displayVal = (val && val !== 'null' && String(val).trim() !== '') ? val : 'Not specified';
    html += `
      <div class="summary-block">
        <div class="summary-block-label">${label}</div>
        <div class="summary-block-content ${displayVal === 'Not specified' ? 'text-muted-summary' : ''}">${escapeHtml(displayVal)}</div>
      </div>
    `;
  });

  listBlocks.forEach(({ key, label }) => {
    let items = summary[key];
    if (typeof items === 'string') {
      try {
        items = JSON.parse(items);
      } catch (_) {
        items = [items];
      }
    }

    const hasItems = items && Array.isArray(items) && items.length > 0 && items.some(i => i && String(i).trim() !== '' && i !== 'null');

    html += `
      <div class="summary-block">
        <div class="summary-block-label">${label}</div>
        <ul class="summary-list ${!hasItems ? 'text-muted-summary' : ''}" aria-label="${label}">
          ${hasItems
            ? items.map(i => `<li>${escapeHtml(i)}</li>`).join('')
            : `<li>Not specified</li>`
          }
        </ul>
      </div>
    `;
  });

  container.innerHTML = html || '<p style="color:var(--text-muted)">No summary available.</p>';
  renderMath(container);
}

function buildAbstractTable(paper, container) {
  if (!container || !paper) return;

  const s = paper.summary || {};

  const rows = [
    {
      label: ' Overview',
      value: s.summary_100_words || cleanAbstractText(paper.abstract).slice(0, 250)
    },
    {
      label: ' Methodology',
      value: s.methodology || 'Detailed in paper methodology section'
    },
    {
      label: ' Architecture',
      value: s.architecture || 'System architecture & model design'
    },
    {
      label: ' Dataset & Data',
      value: s.dataset || paper.dataset || 'Experimental benchmark data'
    },
    {
      label: ' Key Results',
      value: s.results || 'Empirical performance and evaluation metrics'
    },
    {
      label: ' Main Contributions',
      value: Array.isArray(s.key_contributions) && s.key_contributions.length
        ? s.key_contributions.join(' • ')
        : 'Novel framework formulation and benchmark evaluation'
    }
  ];

  container.innerHTML = `
    <div class="abstract-table-wrapper">
      <div class="section-hdr" style="margin-bottom:var(--space-4)">
        <i class="fa-solid fa-table-list" aria-hidden="true"></i> Structured Abstract Table
      </div>
      <table class="abstract-table" aria-label="Structured paper abstract">
        <thead>
          <tr>
            <th>Aspect</th>
            <th>Details & Findings</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(r => `
            <tr>
              <td class="abstract-aspect-col">${escapeHtml(r.label)}</td>
              <td class="abstract-details-col">${escapeHtml(r.value)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
  renderMath(container);
}

function renderMath(element) {
  if (!element) return;
  setTimeout(() => {
    if (typeof renderMathInElement === 'function') {
      try {
        renderMathInElement(element, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true }
          ],
          throwOnError: false
        });
      } catch (e) {
        console.warn('[MathRender] KaTeX render warning:', e);
      }
    }
  }, 60);
}

function escapeHtml(text) {
  if (typeof text !== 'string') return String(text ?? '');
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function formatNumber(n) {
  if (n == null) return '—';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return n.toString();
}

function getScoreClass(score) {
  if (!score) return 'score-low';
  if (score >= 0.7) return 'score-high';
  if (score >= 0.4) return 'score-mid';
  return 'score-low';
}

function openPaper(event, paperId) {
  event?.stopPropagation?.();
  window.location.href = `paper.html?id=${encodeURIComponent(paperId)}`;
}

function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function setLocalStorage(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) {}
}

function getLocalStorage(key, fallback = null) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (_) { return fallback; }
}
