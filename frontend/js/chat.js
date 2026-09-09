let _chatPaperId = null;
let _chatActive = false;
let _chatPrepared = false;

function initChat(paperId) {
  _chatPaperId = paperId;
  _chatActive = true;
  _chatPrepared = false;

  const input = document.getElementById('chat-input');
  if (input) {
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });
  }
}

function chatKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendChat();
  }
}

async function sendChat() {
  if (!_chatActive || !_chatPaperId) {
    showToast('Chat not initialized.', 'error');
    return;
  }

  const input = document.getElementById('chat-input');
  if (!input) return;

  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  input.style.height = 'auto';

  appendChatMessage(question, 'user');

  const thinkingId = showThinking();

  try {
    const response = await API.chat(_chatPaperId, question);
    removeThinking(thinkingId);
    appendChatMessage(response.answer, 'ai', response.chunks_used);
  } catch (err) {
    removeThinking(thinkingId);
    appendChatMessage(
      `Sorry, I couldn't answer that question. Error: ${err.message}`,
      'ai'
    );
  }
}

function appendChatMessage(text, role, chunksUsed = []) {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;

  const messageEl = document.createElement('div');
  messageEl.className = `chat-message ${role}`;

  const safeText = escapeHtml(text).replace(/\n/g, '<br>');

  let chunksHtml = '';
  if (chunksUsed.length > 0 && role === 'ai') {
    chunksHtml = `
      <div style="margin-top:var(--space-2);padding-top:var(--space-2);border-top:1px solid rgba(255,255,255,0.08)">
        <div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:4px">
          📎 Based on ${chunksUsed.length} retrieved passage${chunksUsed.length > 1 ? 's' : ''}
        </div>
      </div>
    `;
  }

  messageEl.innerHTML = `
    <div class="chat-bubble">
      ${safeText}
      ${chunksHtml}
    </div>
  `;

  messages.appendChild(messageEl);
  if (typeof renderMath === 'function') renderMath(messageEl);
  messages.scrollTop = messages.scrollHeight;
}

function showThinking() {
  const messages = document.getElementById('chat-messages');
  if (!messages) return '';

  const id = `thinking-${Date.now()}`;
  const el = document.createElement('div');
  el.id = id;
  el.className = 'chat-message ai';
  el.setAttribute('aria-label', 'AI is thinking');
  el.innerHTML = `
    <div class="chat-bubble chat-thinking">
      <div class="thinking-dot" aria-hidden="true"></div>
      <div class="thinking-dot" aria-hidden="true"></div>
      <div class="thinking-dot" aria-hidden="true"></div>
    </div>
  `;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return id;
}

function removeThinking(id) {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.remove();
}

function clearChat() {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;

  messages.innerHTML = '';
}

async function prepareChatForUI() {
  if (!_chatPaperId || _chatPrepared) return;

  const input = document.getElementById('chat-input');
  const sendBtn = document.querySelector('.chat-send-btn');

  if (input) input.disabled = true;
  if (sendBtn) sendBtn.disabled = true;

  const prepId = showPrepIndicator("Preparing paper context for RAG chat... This may take a few seconds.");

  try {
    const res = await API.prepareChat(_chatPaperId);
    removeThinking(prepId);
    _chatPrepared = true;
    if (input) input.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
    appendChatMessage(`RAG context successfully loaded! Ready to answer your questions based on ${res.chunks_count} parsed sections of the paper.`, 'ai');
  } catch (err) {
    removeThinking(prepId);
    appendChatMessage(`Failed to load RAG context: ${err.message}. Answers might be limited to abstract/meta context.`, 'ai');

    if (input) input.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}

function showPrepIndicator(text) {
  const messages = document.getElementById('chat-messages');
  if (!messages) return '';

  const id = `prep-${Date.now()}`;
  const el = document.createElement('div');
  el.id = id;
  el.className = 'chat-message ai';
  el.innerHTML = `
    <div class="chat-avatar" aria-hidden="true">🤖</div>
    <div class="chat-bubble" style="display:flex;align-items:center;gap:12px;opacity:0.8">
      <div class="hero-badge-dot" style="margin:0;width:8px;height:8px;background:var(--purple-400);animation:dotPulse 1.5s infinite"></div>
      <span style="font-size:0.85rem">${escapeHtml(text)}</span>
    </div>
  `;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return id;
}
