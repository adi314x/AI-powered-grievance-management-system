/**
 * chatbot.js — RAG-powered floating chatbot widget
 * Communicates with the Flask backend at /api/rag/query
 */

(function () {
  'use strict';

  // ── Config ───────────────────────────────────────────────
  const API_URL = '/api/rag/query';

  const SUGGESTIONS = [
    '💧 How to apply for water connection?',
    '🏗️ What documents are needed for drainage?',
    '🏥 What was the disease camp about?',
    '📋 How to register as a citizen?',
  ];

  const WELCOME_MSG =
    "👋 Hello! I'm your **AI Grievance Assistant**. I can answer questions about government services, forms, and documents.\n\nAsk me anything — or try one of the suggestions below!";

  // ── State ─────────────────────────────────────────────────
  let isOpen = false;
  let isLoading = false;
  let suggestionsShown = false;

  // ── DOM refs (resolved after DOMContentLoaded) ────────────
  let fab, panel, messagesEl, inputEl, sendBtn, suggestionsContainer;

  // ── Init ──────────────────────────────────────────────────
  function init() {
    fab = document.getElementById('chatbot-fab');
    panel = document.getElementById('chatbot-panel');
    messagesEl = document.getElementById('chatbot-messages');
    inputEl = document.getElementById('chatbot-input');
    sendBtn = document.getElementById('chatbot-send-btn');
    suggestionsContainer = document.getElementById('chatbot-suggestions');

    if (!fab || !panel) return; // guard if not on this page

    fab.addEventListener('click', togglePanel);
    document.getElementById('chatbot-close-btn').addEventListener('click', closePanel);

    sendBtn.addEventListener('click', handleSend);
    inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });

    // Auto-resize textarea
    inputEl.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });

    // Suggestion chips
    renderSuggestions();
  }

  // ── Toggle / open / close ─────────────────────────────────
  function togglePanel() {
    isOpen ? closePanel() : openPanel();
  }

  function openPanel() {
    isOpen = true;
    panel.classList.add('visible');
    fab.classList.add('open');
    fab.setAttribute('aria-label', 'Close chatbot');
    fab.querySelector('.fab-icon').textContent = '✕';

    if (messagesEl.children.length === 0) {
      appendBotMsg(WELCOME_MSG);
      showSuggestions();
    }

    setTimeout(() => inputEl.focus(), 350);
  }

  function closePanel() {
    isOpen = false;
    panel.classList.remove('visible');
    fab.classList.remove('open');
    fab.setAttribute('aria-label', 'Open AI chatbot assistant');
    fab.querySelector('.fab-icon').textContent = '🤖';
  }

  // ── Suggestions ───────────────────────────────────────────
  function renderSuggestions() {
    suggestionsContainer.innerHTML = '';
    SUGGESTIONS.forEach(function (text) {
      const chip = document.createElement('button');
      chip.className = 'chat-suggestion-chip';
      chip.textContent = text;
      chip.addEventListener('click', function () {
        hideSuggestions();
        sendMessage(text);
      });
      suggestionsContainer.appendChild(chip);
    });
  }

  function showSuggestions() {
    if (!suggestionsShown) {
      suggestionsContainer.style.display = 'flex';
      suggestionsShown = true;
    }
  }

  function hideSuggestions() {
    suggestionsContainer.style.display = 'none';
  }

  // ── Messaging ─────────────────────────────────────────────
  function handleSend() {
    const text = inputEl.value.trim();
    if (!text || isLoading) return;
    inputEl.value = '';
    inputEl.style.height = 'auto';
    hideSuggestions();
    sendMessage(text);
  }

  function sendMessage(text) {
    appendUserMsg(text);
    setLoading(true);

    const typingId = showTyping();

    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, status: res.status, data: data };
        });
      })
      .then(function (result) {
        removeTyping(typingId);
        setLoading(false);

        if (!result.ok) {
          const errMsg = result.data && result.data.error
            ? result.data.error
            : 'Something went wrong. Please try again.';
          appendBotMsg('⚠️ ' + errMsg, { isError: true });
          return;
        }

        const { answer, supported, citations } = result.data;
        if (!supported && (!citations || citations.length === 0)) {
          appendBotMsg(answer || "I couldn't find an answer to that in my knowledge base. Please try rephrasing, or contact the helpdesk.");
        } else {
          appendBotMsg(answer, { citations: citations });
        }
      })
      .catch(function (err) {
        removeTyping(typingId);
        setLoading(false);
        appendBotMsg('🔌 Unable to connect to the assistant. Please check your network and try again.', { isError: true });
      });
  }

  // ── DOM helpers ───────────────────────────────────────────
  function appendUserMsg(text) {
    const msg = buildMsgEl('user', escapeHtml(text));
    messagesEl.appendChild(msg);
    scrollToBottom();
  }

  function appendBotMsg(text, opts) {
    opts = opts || {};
    const bubble = document.createElement('div');
    bubble.className = 'chat-msg-bubble' + (opts.isError ? ' chat-error-bubble' : '');
    bubble.innerHTML = markdownToHtml(text);

    const avatarEl = document.createElement('div');
    avatarEl.className = 'chat-msg-avatar';
    avatarEl.textContent = '🤖';

    const msg = document.createElement('div');
    msg.className = 'chat-msg bot';
    msg.appendChild(avatarEl);
    msg.appendChild(bubble);

    messagesEl.appendChild(msg);
    scrollToBottom();
  }

  function buildMsgEl(role, htmlContent) {
    const avatarEl = document.createElement('div');
    avatarEl.className = 'chat-msg-avatar';
    avatarEl.textContent = role === 'user' ? '👤' : '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'chat-msg-bubble';
    bubble.innerHTML = htmlContent;

    const msg = document.createElement('div');
    msg.className = 'chat-msg ' + role;
    msg.appendChild(avatarEl);
    msg.appendChild(bubble);
    return msg;
  }

  // Typing indicator
  let _typingCounter = 0;
  function showTyping() {
    const id = 'typing-' + (++_typingCounter);
    const avatarEl = document.createElement('div');
    avatarEl.className = 'chat-msg-avatar';
    avatarEl.textContent = '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'chat-msg-bubble';
    bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

    const msg = document.createElement('div');
    msg.className = 'chat-msg bot';
    msg.id = id;
    msg.appendChild(avatarEl);
    msg.appendChild(bubble);

    messagesEl.appendChild(msg);
    scrollToBottom();
    return id;
  }

  function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function setLoading(val) {
    isLoading = val;
    sendBtn.disabled = val;
    inputEl.disabled = val;
  }

  function scrollToBottom() {
    requestAnimationFrame(function () {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  // ── Minimal markdown-to-HTML (bold, line breaks) ──────────
  function markdownToHtml(text) {
    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ── Boot ──────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
