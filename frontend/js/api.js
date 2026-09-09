const BASE_URL = window.RESEARCH_API_URL || 'http://localhost:8000/api';

async function apiFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const defaultHeaders = { 'Content-Type': 'application/json' };

  try {
    const response = await fetch(url, {
      headers: { ...defaultHeaders, ...options.headers },
      ...options,
    });

    if (!response.ok) {
      let errDetail = `HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        errDetail = errJson.detail || errJson.error || errDetail;
      } catch (_) {}
      throw new Error(errDetail);
    }

    return await response.json();
  } catch (err) {
    console.error(`[API] ${options.method || 'GET'} ${endpoint} failed:`, err.message);
    throw err;
  }
}

const API = {
  search: (query, opts = {}) =>
    apiFetch('/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        max_results: opts.max_results ?? 10,
        year_from: opts.year_from ?? null,
        year_to: opts.year_to ?? null,
        force_refresh: opts.force_refresh ?? false,
      }),
    }),

  history: (limit = 20) =>
    apiFetch(`/search/history?limit=${limit}`),

  getPaper: (paperId) =>
    apiFetch(`/paper/${encodeURIComponent(paperId)}`),

  getSummary: (paperId, regenerate = false) =>
    apiFetch('/paper/summary', {
      method: 'POST',
      body: JSON.stringify({ paper_id: paperId, regenerate }),
    }),

  getRelated: (paperId, limit = 5) =>
    apiFetch(`/paper/related/${encodeURIComponent(paperId)}?limit=${limit}`),

  prepareChat: (paperId) =>
    apiFetch('/chat/prepare', {
      method: 'POST',
      body: JSON.stringify({ paper_id: paperId }),
    }),

  chat: (paperId, question, topK = 5) =>
    apiFetch('/chat', {
      method: 'POST',
      body: JSON.stringify({ paper_id: paperId, question, top_k: topK }),
    }),

  addBookmark: (paperId, userId = 'anonymous') =>
    apiFetch('/bookmarks', {
      method: 'POST',
      body: JSON.stringify({ paper_id: paperId, user_id: userId }),
    }),

  getBookmarks: (userId = 'anonymous') =>
    apiFetch(`/bookmarks?user_id=${userId}`),

  submitFeedback: (paperId, rating, comment = '') =>
    apiFetch('/feedback', {
      method: 'POST',
      body: JSON.stringify({ paper_id: paperId, rating, comment }),
    }),

  health: () => apiFetch('/health'.replace('/api', ''), { headers: {} }),
};
