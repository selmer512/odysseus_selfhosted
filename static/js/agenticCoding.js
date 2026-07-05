// Agentic Coding native Odysseus UX module.
// Primary UX lives inside the Odysseus app shell as a managed tool window.

import * as Modals from './modalManager.js';
import { makeWindowDraggable } from './windowDrag.js';

const API = '/api/agentic-coding';
const MODAL_ID = 'agentic-coding-modal';
const SIDEBAR_BTN_ID = 'tool-agentic-coding-btn';
const RAIL_BTN_ID = 'rail-agentic-coding';
let latestScaffold = null;
let latestRun = null;
let metricStartedAt = 0;

function esc(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[ch]);
}

function ensureStyles() {
  if (document.getElementById('agentic-coding-native-css')) return;
  const link = document.createElement('link');
  link.id = 'agentic-coding-native-css';
  link.rel = 'stylesheet';
  link.href = '/static/agentic-coding-native.css';
  document.head.appendChild(link);
}

async function api(path, options = {}) {
  const res = await fetch(API + path, Object.assign({
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
  }, options));
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || String(res.status));
  return data;
}

function output(value) {
  const el = document.getElementById('agentic-native-output');
  if (!el) return;
  el.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
}

function setStatus(text) {
  const el = document.getElementById('agentic-native-status');
  if (el) el.textContent = text;
}

function option(value, label) {
  return `<option value="${esc(value)}">${esc(label || value || '')}</option>`;
}

function codeIcon(size = 14) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline><line x1="14" y1="4" x2="10" y2="20"></line></svg>`;
}

function renderWorkspaces(rows) {
  const list = document.getElementById('agentic-native-workspaces');
  const select = document.getElementById('agentic-native-workspace-select');
  rows = rows || [];
  if (list) {
    list.innerHTML = rows.length
      ? rows.map(row => `<div class="mini-card"><b>${esc(row.title || row.path || row.id)}</b><div class="muted">${esc(row.path || '')}</div></div>`).join('')
      : '<p class="muted">No workspaces registered yet.</p>';
  }
  if (select) {
    select.innerHTML = rows.map(row => option(row.id, row.title || row.path || row.id)).join('');
  }
}

async function refreshAgenticCoding() {
  try {
    const health = await api('/health');
    const profiles = await api('/model-profiles');
    const workspaces = await api('/workspaces');
    const profileSelect = document.getElementById('agentic-native-profile-select');
    if (profileSelect) profileSelect.innerHTML = (profiles.profiles || []).map(p => option(p.id, p.label)).join('');
    renderWorkspaces(workspaces.workspaces || []);
    setStatus(health.ok ? 'Backend online' : 'Backend unavailable');
    output({ health, workspaces: workspaces.workspaces || [], profiles: profiles.profiles || [] });
  } catch (err) {
    setStatus('Backend blocked or offline');
    output(String(err));
  }
}

async function registerWorkspace() {
  try {
    const path = (document.getElementById('agentic-native-path')?.value || '').trim();
    const title = (document.getElementById('agentic-native-title')?.value || '').trim();
    if (!path) throw new Error('Workspace path is required. Use /app in Docker or /workspace/odysseus when the host repo is mounted.');
    output(`Registering workspace: ${path}`);
    const created = await api('/workspaces', { method: 'POST', body: JSON.stringify({ path, title: title || null }) });
    await refreshAgenticCoding();
    output(created);
  } catch (err) {
    output(String(err));
  }
}

async function generateScaffold() {
  try {
    metricStartedAt = performance.now();
    const workspaceId = document.getElementById('agentic-native-workspace-select')?.value;
    const model = document.getElementById('agentic-native-profile-select')?.value;
    const goal = (document.getElementById('agentic-native-goal')?.value || '').trim();
    if (!workspaceId) throw new Error('Register and select a workspace first.');
    if (!goal) throw new Error('Describe a measurable code goal first.');
    const scaffold = await api('/scaffolds', { method: 'POST', body: JSON.stringify({ workspace_id: workspaceId, user_goal: goal, model: model || null }) });
    latestScaffold = scaffold.id;
    latestRun = null;
    output(scaffold);
  } catch (err) {
    output(String(err));
  }
}

async function approveScaffold() {
  try {
    if (!latestScaffold) throw new Error('Create a scaffold first.');
    output(await api(`/scaffolds/${latestScaffold}/approve`, { method: 'POST' }));
  } catch (err) {
    output(String(err));
  }
}

async function createRun() {
  try {
    if (!latestScaffold) throw new Error('Create and approve a scaffold first.');
    const run = await api('/runs', { method: 'POST', body: JSON.stringify({ scaffold_id: latestScaffold }) });
    latestRun = run.id;
    output(run);
  } catch (err) {
    output(String(err));
  }
}

async function prepareArtifacts() {
  try {
    if (!latestRun) throw new Error('Create a run first.');
    const run = await api(`/runs/${latestRun}/execute`, { method: 'POST' });
    const artifacts = await api(`/runs/${latestRun}/artifacts`);
    const artifactRows = artifacts.artifacts || [];
    const metrics = {
      run_status: run.status,
      artifact_count: artifactRows.length,
      artifact_types: artifactRows.map(a => a.artifact_type),
      elapsed_ms: metricStartedAt ? Math.round(performance.now() - metricStartedAt) : null,
      completed: run.status === 'completed' && artifactRows.length >= 7,
    };
    output({ metrics, run, artifacts: artifactRows });
  } catch (err) {
    output(String(err));
  }
}

async function generatePatchProposal() {
  try {
    if (!latestRun) throw new Error('Create a run first.');
    output(await api(`/runs/${latestRun}/patch-proposal`, { method: 'POST' }));
  } catch (err) {
    output(String(err));
  }
}

async function approvePatchProposal() {
  try {
    if (!latestRun) throw new Error('Create a run and patch proposal first.');
    output(await api(`/runs/${latestRun}/approve-patch`, { method: 'POST' }));
  } catch (err) {
    output(String(err));
  }
}

async function applyApprovedPatch() {
  try {
    if (!latestRun) throw new Error('Create, propose, and approve a patch first.');
    const result = await api(`/runs/${latestRun}/apply-patch`, { method: 'POST' });
    const artifacts = await api(`/runs/${latestRun}/artifacts`);
    output({ result, artifacts: artifacts.artifacts || [] });
  } catch (err) {
    output(String(err));
  }
}

function registerManagedWindow() {
  const modal = document.getElementById(MODAL_ID);
  if (!modal) return;
  const content = modal.querySelector('.modal-content');
  const header = modal.querySelector('.modal-header');
  if (!Modals.isRegistered(MODAL_ID)) {
    Modals.register(MODAL_ID, {
      railBtnId: RAIL_BTN_ID,
      sidebarBtnId: SIDEBAR_BTN_ID,
      label: 'Agentic Coding',
      icon: codeIcon(),
      restoreFn: () => refreshAgenticCoding(),
      closeFn: () => {
        const live = document.getElementById(MODAL_ID);
        if (live) live.classList.add('hidden');
      },
    });
  }
  Modals.injectMinimizeButton(modal, MODAL_ID);
  if (!modal.dataset.agenticDragBound && content && header) {
    modal.dataset.agenticDragBound = '1';
    makeWindowDraggable(modal, {
      content,
      header,
      minWidth: 720,
      minHeight: 520,
      resizeStorageKey: 'winsize-agentic-coding-modal',
      skipSelector: 'button, input, select, textarea',
    });
  }
}

function openModal() {
  ensureStyles();
  ensureModal();
  if (Modals.toggle(MODAL_ID)) return;
  const modal = document.getElementById(MODAL_ID);
  if (!modal) return;
  modal.classList.remove('hidden', 'modal-minimized');
  modal.style.display = '';
  registerManagedWindow();
  refreshAgenticCoding();
}

function closeModal() {
  Modals.close(MODAL_ID);
}

function ensureModal() {
  ensureStyles();
  let modal = document.getElementById(MODAL_ID);
  if (modal) {
    registerManagedWindow();
    return;
  }
  modal = document.createElement('div');
  modal.id = MODAL_ID;
  modal.className = 'modal hidden';
  modal.innerHTML = `
    <div class="modal-content agentic-coding-window" role="dialog" aria-label="Agentic Coding">
      <div class="modal-header">
        <h4 class="agentic-coding-title">${codeIcon(16)}<span>Agentic Coding</span></h4>
        <button class="close-btn" id="close-agentic-coding-modal" aria-label="Close Agentic Coding">✖</button>
      </div>
      <div class="agentic-coding-shell">
        <section class="agentic-coding-pane">
          <span class="pill" id="agentic-native-status">Checking backend...</span>
          <h2>Workspace</h2>
          <label for="agentic-native-path">Path</label>
          <input id="agentic-native-path" placeholder="/app" value="/app">
          <label for="agentic-native-title">Title</label>
          <input id="agentic-native-title" placeholder="Odysseus container repo">
          <div class="agentic-coding-actions">
            <button id="agentic-native-register" type="button">Register workspace</button>
            <button id="agentic-native-refresh" type="button" class="secondary">Refresh</button>
          </div>
          <div id="agentic-native-workspaces" class="agentic-coding-workspaces"></div>
        </section>
        <div class="agentic-coding-main">
          <section class="agentic-coding-pane agentic-coding-run-card">
            <h2>Review-first run</h2>
            <label for="agentic-native-workspace-select">Workspace</label>
            <select id="agentic-native-workspace-select"></select>
            <label for="agentic-native-profile-select">Model profile</label>
            <select id="agentic-native-profile-select"></select>
            <label for="agentic-native-goal">Measurable goal</label>
            <textarea id="agentic-native-goal" rows="4" placeholder="Improve Agentic Coding artifact output and workspace registration UX."></textarea>
            <div class="agentic-coding-actions">
              <button id="agentic-native-scaffold" type="button">Generate scaffold</button>
              <button id="agentic-native-approve" type="button" class="secondary">Approve</button>
              <button id="agentic-native-run" type="button" class="secondary">Create run</button>
              <button id="agentic-native-artifacts" type="button" class="secondary">Prepare artifacts</button>
              <button id="agentic-native-patch" type="button" class="secondary">Generate patch</button>
              <button id="agentic-native-approve-patch" type="button" class="secondary">Approve patch</button>
              <button id="agentic-native-apply-patch" type="button" class="danger">Apply patch</button>
            </div>
            <p class="agentic-coding-metrics-note">Measurable success: source-aware artifacts, explicit patch approval, then safe workspace-confined apply.</p>
          </section>
          <section class="agentic-coding-pane agentic-coding-output-card">
            <h2>Output / metrics</h2>
            <pre id="agentic-native-output">Loading...</pre>
          </section>
        </div>
      </div>
    </div>`;
  document.body.appendChild(modal);
  document.getElementById('close-agentic-coding-modal')?.addEventListener('click', closeModal);
  document.getElementById('agentic-native-register')?.addEventListener('click', registerWorkspace);
  document.getElementById('agentic-native-refresh')?.addEventListener('click', refreshAgenticCoding);
  document.getElementById('agentic-native-scaffold')?.addEventListener('click', generateScaffold);
  document.getElementById('agentic-native-approve')?.addEventListener('click', approveScaffold);
  document.getElementById('agentic-native-run')?.addEventListener('click', createRun);
  document.getElementById('agentic-native-artifacts')?.addEventListener('click', prepareArtifacts);
  document.getElementById('agentic-native-patch')?.addEventListener('click', generatePatchProposal);
  document.getElementById('agentic-native-approve-patch')?.addEventListener('click', approvePatchProposal);
  document.getElementById('agentic-native-apply-patch')?.addEventListener('click', applyApprovedPatch);
  registerManagedWindow();
}

function makeSidebarButton() {
  const btn = document.createElement('button');
  btn.id = SIDEBAR_BTN_ID;
  btn.type = 'button';
  btn.className = 'list-item tool-item';
  btn.setAttribute('aria-label', 'Agentic Coding');
  btn.innerHTML = `${codeIcon()}<span>Agentic Coding</span>`;
  btn.addEventListener('click', openModal);
  return btn;
}

function ensureSidebarButton() {
  if (document.getElementById(SIDEBAR_BTN_ID)) return;
  const toolItems = Array.from(document.querySelectorAll('#sidebar .list-item'));
  const deepResearch = toolItems.find(el => /deep research/i.test(el.textContent || ''));
  const cookbook = toolItems.find(el => /cookbook/i.test(el.textContent || ''));
  const anchor = deepResearch || cookbook;
  const btn = makeSidebarButton();
  if (anchor && anchor.parentElement) {
    anchor.parentElement.insertBefore(btn, anchor.nextSibling);
    return;
  }
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.appendChild(btn);
}

function ensureRailButton() {
  const rail = document.getElementById('icon-rail');
  if (!rail || document.getElementById(RAIL_BTN_ID)) return;
  const btn = document.createElement('button');
  btn.id = RAIL_BTN_ID;
  btn.type = 'button';
  btn.className = 'icon-rail-btn';
  btn.title = 'Agentic Coding';
  btn.setAttribute('aria-label', 'Agentic Coding');
  btn.innerHTML = `${codeIcon(18)}<span class="rail-hover-label">Agentic Coding</span>`;
  btn.addEventListener('click', openModal);
  const settings = document.getElementById('rail-settings');
  rail.insertBefore(btn, settings || null);
}

function initAgenticCodingUx() {
  ensureStyles();
  ensureModal();
  ensureSidebarButton();
  ensureRailButton();
  if (window.location.pathname === '/agentic-coding-native') openModal();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAgenticCodingUx, { once: true });
} else {
  initAgenticCodingUx();
}

window.agenticCodingNative = { open: openModal, refresh: refreshAgenticCoding };
