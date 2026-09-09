function saveQueryToHistory(query) {
  if (!query?.trim()) return;
  const hist = getLocalStorage('query_history', []);
  const filtered = hist.filter(q => q !== query);
  filtered.unshift(query);
  setLocalStorage('query_history', filtered.slice(0, 20));
}

function getLocalHistory() {
  return getLocalStorage('query_history', []);
}

function getAutocompleteSuggestions(input) {
  if (!input || input.length < 2) return [];
  const hist = getLocalHistory();
  return hist.filter(q => q.toLowerCase().includes(input.toLowerCase())).slice(0, 5);
}

function pushSearchState(query) {
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('q', query);
    window.history.pushState({ query }, '', url.toString());
  } catch (_) {}
}

function getQueryFromUrl() {
  return new URLSearchParams(window.location.search).get('q');
}

let _historyNavIndex = -1;
const _historyBuffer = [];

function handleHistoryNav(e, input) {
  const hist = getLocalHistory();
  if (!hist.length) return;

  if (e.key === 'ArrowUp') {
    e.preventDefault();
    _historyNavIndex = Math.min(_historyNavIndex + 1, hist.length - 1);
    input.value = hist[_historyNavIndex];
  } else if (e.key === 'ArrowDown') {
    e.preventDefault();
    _historyNavIndex = Math.max(_historyNavIndex - 1, -1);
    input.value = _historyNavIndex === -1 ? '' : hist[_historyNavIndex];
  } else {
    _historyNavIndex = -1;
  }
}

function validateQuery(query) {
  if (!query || !query.trim()) {
    return { valid: false, error: 'Please enter a research query.' };
  }
  if (query.trim().length < 3) {
    return { valid: false, error: 'Query must be at least 3 characters.' };
  }
  if (query.length > 1000) {
    return { valid: false, error: 'Query is too long (max 1000 characters).' };
  }
  return { valid: true };
}
