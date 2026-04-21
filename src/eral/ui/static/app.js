// erAL Web UI

const API = '';
const state = {
  world: {},
  player: {},
  visibleActors: [],
  selectedActorKey: null,
  activeCmdTab: null,
  activeDetailTab: 'personal',
  lastShopfront: null,
};

const CMD_CATS = [
  ['daily', '日常'],
  ['work', '工作'],
  ['follow', '同行'],
  ['date', '约会'],
  ['intimacy', '亲密'],
  ['training', '调教'],
  ['recovery', '恢复'],
];

const TIME_SLOT_LABEL = {
  dawn: '清晨', morning: '上午', afternoon: '午后',
  evening: '傍晚', night: '夜晚', late_night: '深夜',
};
const WEEKDAY_LABEL = { mon: '一', tue: '二', wed: '三', thu: '四', fri: '五', sat: '六', sun: '日' };
const SEASON_LABEL = { spring: '春之月', summer: '夏之月', autumn: '秋之月', winter: '冬之月' };
const WEATHER_LABEL = { clear: '☀ 晴', cloudy: '☁ 阴', rain: '☂ 雨', storm: '⛈ 暴风雨', snow: '❄ 雪', fog: '☁ 雾' };

const PALAM_KEYS = [
  ['快C', 'pleasure_c'], ['快V', 'pleasure_v'], ['快A', 'pleasure_a'], ['快B', 'pleasure_b'],
  ['快M', 'pleasure_m'], ['润滑', 'lubrication'], ['恭顺', 'obedience'], ['情欲', 'lust'],
  ['屈服', 'submission'], ['习得', 'mastery'], ['恥情', 'shame'], ['苦痛', 'pain'],
  ['恐怖', 'fear'], ['好意', 'favor'], ['优越', 'superiority'], ['反感', 'disgust'],
];
const PALAM_LV_THRESHOLDS = [0, 100, 500, 1500, 3000, 6000, 10000, 15000, 25000];
function palamLevel(v) {
  for (let i = PALAM_LV_THRESHOLDS.length - 1; i >= 0; i--) {
    if (v >= PALAM_LV_THRESHOLDS[i]) return i;
  }
  return 0;
}

const FACTION_COLORS = {
  royal_navy: '#3d5a8a',
  eagle_union: '#7a5a3d',
  sakura_empire: '#8a3d5a',
  iron_blood: '#4a4a5a',
  donghuang: '#5a3d3d',
  default: '#3a3a3a',
};

// ── HTTP ──────────────────────────────────────────
async function get(path) {
  try {
    const r = await fetch(API + path);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    toast(`请求失败: ${path} — ${e.message || e}`);
    throw e;
  }
}
async function post(path, body) {
  try {
    const r = await fetch(API + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    toast(`请求失败: ${path} — ${e.message || e}`);
    throw e;
  }
}

function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove('show'), 3500);
}

function log(text, type = 'msg') {
  const el = document.getElementById('log');
  const line = document.createElement('div');
  line.className = 'line ' + type;
  line.textContent = text;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

// ── Avatar ────────────────────────────────────────
function firstChar(name) {
  return name && name.length ? name[0] : '?';
}
function factionColor(actor) {
  const tag = (actor.tags || []).find(t => FACTION_COLORS[t]);
  return FACTION_COLORS[tag] || FACTION_COLORS.default;
}
function renderAvatar(el, actor, size = 'md') {
  el.className = 'avatar avatar-' + size;
  el.innerHTML = '';
  if (actor && actor.avatar_url) {
    const img = new Image();
    img.src = actor.avatar_url;
    img.onerror = () => { el.textContent = firstChar(actor.display_name); };
    el.appendChild(img);
    el.style.background = factionColor(actor);
  } else if (actor) {
    el.style.background = factionColor(actor);
    el.textContent = firstChar(actor.display_name);
  } else {
    el.style.background = 'var(--bg-3)';
    el.textContent = '—';
  }
}

// ── Top Bar ───────────────────────────────────────
function renderTopbar() {
  const w = state.world;
  const date = `${SEASON_LABEL[w.season] || w.season || ''} ${w.day || 1}日(${WEEKDAY_LABEL[w.weekday] || ''})`;
  document.getElementById('hDate').textContent = date;
  document.getElementById('hTime').textContent = `${String(w.hour || 0).padStart(2,'0')}:${String(w.minute || 0).padStart(2,'0')} ${TIME_SLOT_LABEL[w.time_slot] || ''}`;
  document.getElementById('hWeather').textContent = `${WEATHER_LABEL[w.weather] || w.weather || '—'}`;
  document.getElementById('hFunds').textContent = `💰 ${w.personal_funds || 0}${w.port_funds ? ` / ${w.port_funds}` : ''}`;
  document.getElementById('hLoc').textContent = w.location ? w.location.display_name : '—';
  document.getElementById('hFestival').hidden = true;
}

// ── BASE bars ─────────────────────────────────────
function renderBars(container, baseEntries) {
  container.innerHTML = '';
  if (!baseEntries || !baseEntries.length) {
    container.innerHTML = '<div class="empty">—</div>';
    return;
  }
  const displayEntries = baseEntries.filter(e => e.key !== 'reason');
  for (let i = 0; i < displayEntries.length; i += 2) {
    const pair = document.createElement('div');
    pair.className = 'bar-pair';
    for (let j = 0; j < 2 && i + j < displayEntries.length; j++) {
      const entry = displayEntries[i + j];
      const pct = entry.max > 0 ? Math.min(100, (entry.value / entry.max) * 100) : 0;
      const row = document.createElement('div');
      row.className = `bar-row bar-${entry.key}`;
      row.innerHTML = `
        <span class="label">${entry.label}</span>
        <div class="track"><div class="fill" style="width:${pct}%"></div></div>
        <span class="value">${entry.value}/${entry.max}</span>
      `;
      pair.appendChild(row);
    }
    container.appendChild(pair);
  }
}

// ── Player card ───────────────────────────────────
async function renderPlayer() {
  try {
    state.player = await get('/api/player');
  } catch (e) {
    state.player = { base: [], name: '指挥官' };
  }
  document.getElementById('playerName').textContent = state.player.name || '指挥官';
  document.getElementById('playerAvatar').textContent = firstChar(state.player.name || '指');
  renderBars(document.getElementById('playerBars'), state.player.base);
}

// ── Actor status card ─────────────────────────────
function renderActorCard() {
  const actor = state.visibleActors.find(a => a.key === state.selectedActorKey);
  const nameEl = document.getElementById('actorName');
  const tagsEl = document.getElementById('actorTags');
  const stageEl = document.getElementById('actorStage');
  const barsEl = document.getElementById('actorBars');
  const metaEl = document.getElementById('actorMeta');
  const palamEl = document.getElementById('palamGrid');
  const palamHead = document.getElementById('palamHead');

  if (!actor) {
    nameEl.textContent = '未选择舰娘';
    tagsEl.innerHTML = '<span class="tag-pill">点击下方选中</span>';
    stageEl.textContent = '';
    barsEl.innerHTML = '<div class="empty">—</div>';
    metaEl.innerHTML = '';
    palamEl.innerHTML = '';
    palamHead.hidden = true;
    return;
  }

  nameEl.textContent = actor.display_name;
  const tags = [];
  if (actor.is_following) tags.push('<span class="tag-pill follow">同行</span>');
  if (actor.is_on_date) tags.push('<span class="tag-pill date">约会</span>');
  (actor.active_persistent_states || []).slice(0, 3).forEach(s => {
    tags.push(`<span class="tag-pill">${s}</span>`);
  });
  tagsEl.innerHTML = tags.join('') || '<span class="tag-pill">—</span>';
  stageEl.textContent = actor.relationship_stage || '陌生';

  renderBars(barsEl, actor.base);

  metaEl.innerHTML = `
    <div class="meta-cell good"><span class="k">好感</span><span class="v">${actor.affection ?? 0}</span></div>
    <div class="meta-cell"><span class="k">信赖</span><span class="v">${actor.trust ?? 0}</span></div>
    <div class="meta-cell"><span class="k">服从</span><span class="v">${actor.obedience ?? 0}</span></div>
  `;

  palamHead.hidden = false;
  palamEl.innerHTML = '';
  PALAM_KEYS.forEach(([label, key]) => {
    const v = (actor.palam && actor.palam[key]) || 0;
    const lv = palamLevel(v);
    const cell = document.createElement('div');
    cell.className = `palam-cell palam-lv${lv}`;
    cell.title = `${label}: ${v}`;
    cell.innerHTML = `<span class="pk">${label}</span><span class="pv">Lv${lv}</span>`;
    palamEl.appendChild(cell);
  });
}

// ── Actor list ────────────────────────────────────
function renderActorList() {
  const el = document.getElementById('actorList');
  const countEl = document.getElementById('actorCount');
  countEl.textContent = state.visibleActors.length;
  if (!state.visibleActors.length) {
    el.innerHTML = '<div class="empty">当前地点无舰娘</div>';
    return;
  }
  el.innerHTML = '';
  state.visibleActors.forEach((a, idx) => {
    const card = document.createElement('div');
    card.className = 'actor-card' + (a.key === state.selectedActorKey ? ' active' : '');
    card.onclick = () => selectActor(a.key);

    const avatar = document.createElement('div');
    renderAvatar(avatar, a, 'lg');

    const info = document.createElement('div');
    info.className = 'info';
    info.innerHTML = `
      <div class="n">${idx + 1}. ${a.display_name}</div>
      <div class="rel">${a.relationship_stage || '陌生'} · 好感 ${a.affection}</div>
    `;

    const pills = document.createElement('div');
    pills.className = 'pills';
    if (a.is_following) pills.innerHTML += '<span class="tag-pill follow">同行</span>';
    if (a.is_on_date) pills.innerHTML += '<span class="tag-pill date">约会</span>';

    card.appendChild(avatar);
    card.appendChild(info);
    card.appendChild(pills);
    el.appendChild(card);
  });
}

// ── Commands (Act_COM) ────────────────────────────
async function renderCommands() {
  const tabsEl = document.getElementById('cmdTabs');
  const gridEl = document.getElementById('cmdGrid');
  if (!state.selectedActorKey) {
    tabsEl.innerHTML = '';
    gridEl.innerHTML = '<div class="empty">选择一位舰娘以查看可执行指令</div>';
    return;
  }

  let cmds = [];
  try {
    cmds = await get(`/api/actor/${state.selectedActorKey}/commands`);
  } catch (e) {
    cmds = [];
  }

  const groups = {};
  for (const c of cmds) {
    const cat = c.category || 'daily';
    (groups[cat] = groups[cat] || []).push(c);
  }

  const availableCats = CMD_CATS.filter(([k, _]) => groups[k] && groups[k].length);
  tabsEl.innerHTML = '';
  if (!availableCats.length) {
    gridEl.innerHTML = '<div class="empty">当前条件下无可执行指令</div>';
    return;
  }

  if (!availableCats.find(([k]) => k === state.activeCmdTab)) {
    state.activeCmdTab = availableCats[0][0];
  }

  for (const [key, label] of availableCats) {
    const tab = document.createElement('button');
    tab.className = 'cmd-tab' + (key === state.activeCmdTab ? ' active' : '');
    tab.textContent = `${label} ${groups[key].length}`;
    tab.onclick = () => { state.activeCmdTab = key; renderCommandGrid(groups); renderCmdTabs(availableCats); };
    tabsEl.appendChild(tab);
  }
  renderCommandGrid(groups);
}

function renderCmdTabs(availableCats) {
  const tabsEl = document.getElementById('cmdTabs');
  tabsEl.querySelectorAll('.cmd-tab').forEach((el, i) => {
    const key = availableCats[i] ? availableCats[i][0] : null;
    el.classList.toggle('active', key === state.activeCmdTab);
  });
}

function renderCommandGrid(groups) {
  const gridEl = document.getElementById('cmdGrid');
  gridEl.innerHTML = '';
  const list = groups[state.activeCmdTab] || [];
  if (!list.length) {
    gridEl.innerHTML = '<div class="empty">—</div>';
    return;
  }
  for (const cmd of list) {
    const btn = document.createElement('button');
    btn.className = 'cmd-btn';
    btn.textContent = cmd.display_name;
    btn.onclick = () => executeCommand(cmd);
    gridEl.appendChild(btn);
  }
}

async function executeCommand(cmd) {
  const actorKey = state.selectedActorKey;
  if (!actorKey) return;
  log(`▸ ${cmd.display_name}`, 'sys');
  try {
    const res = await post('/api/execute', { actor_key: actorKey, command_key: cmd.key });
    if (!res.success) {
      (res.messages || []).forEach(m => log(m, 'err'));
      return;
    }
    (res.messages || []).forEach(m => log(m, 'dia'));
    if (res.funds_delta) log(`资金 ${res.funds_delta > 0 ? '+' : ''}${res.funds_delta}`, 'funds');
    if (res.shopfront_key) {
      state.lastShopfront = res.shopfront_key;
      await openShop(res.shopfront_key);
    }
    await refreshAll();
  } catch (e) { }
}

// ── Commands (Ex_COM) ─────────────────────────────
function renderExDock() {
  const grid = document.getElementById('exGrid');
  const items = [
    { label: '移动', cls: 'system', handler: openMoveOverlay },
    { label: '能力显示', cls: 'system', handler: () => openDetailOverlay(state.selectedActorKey) },
    { label: '道具确认', cls: 'system', handler: openInventoryOverlay },
    { label: '日历', cls: 'system', handler: openCalendarOverlay },
    { label: '等待', cls: 'system', handler: doWait },
    { label: '配置', cls: 'system', handler: () => toast('配置：尚未接入') },
  ];
  grid.innerHTML = '';
  for (const it of items) {
    const btn = document.createElement('button');
    btn.className = 'cmd-btn ' + it.cls;
    btn.textContent = it.label;
    btn.onclick = it.handler;
    grid.appendChild(btn);
  }
}

// ── Training banner ───────────────────────────────
function renderTrainingBanner() {
  const el = document.getElementById('trainingBanner');
  const w = state.world;
  if (w.training_active && w.training_actor_key) {
    const actor = state.visibleActors.find(a => a.key === w.training_actor_key);
    const name = actor ? actor.display_name : w.training_actor_key;
    const pos = w.training_position_key ? ` · ${w.training_position_key}` : '';
    const step = typeof w.training_step_index === 'number' ? ` · Step ${w.training_step_index}` : '';
    el.textContent = `▶ 训练中 — ${name}${pos}${step}`;
    el.classList.add('open');
  } else {
    el.classList.remove('open');
  }
}

// ── Overlays ──────────────────────────────────────
function openOverlay(id) {
  document.getElementById(id).hidden = false;
}
function closeOverlay(id) {
  document.getElementById(id).hidden = true;
}

// Move overlay
async function openMoveOverlay() {
  openOverlay('moveOverlay');
  const area = document.getElementById('mapArea');
  const list = document.getElementById('destList');
  area.textContent = buildAsciiMap();
  list.innerHTML = '<div class="empty">加载中…</div>';
  let dests = [];
  try { dests = await get('/api/destinations'); } catch (e) { }

  const byArea = {};
  for (const d of dests) {
    const a = d.area_name || '其他';
    (byArea[a] = byArea[a] || []).push(d);
  }
  list.innerHTML = '';
  for (const [areaName, arr] of Object.entries(byArea)) {
    const group = document.createElement('div');
    group.className = 'dest-group';
    group.innerHTML = `<div class="dest-group-title">── ${areaName} ──</div>`;
    const grid = document.createElement('div');
    grid.className = 'dest-grid';
    for (const d of arr) {
      const btn = document.createElement('button');
      btn.className = 'dest-btn' + (d.key === state.world.location?.key ? ' current' : '');
      btn.innerHTML = `<span>${d.display_name}</span><span class="cost">${d.cost_minutes}分</span>`;
      btn.onclick = () => executeMove(d);
      grid.appendChild(btn);
    }
    group.appendChild(grid);
    list.appendChild(group);
  }
}

function buildAsciiMap() {
  return `
  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ 指挥中枢 │────│ 训练演习 │────│ 商业休闲 │
  └─────────┘    └─────────┘    └─────────┘
        │              │              │
  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ 白鹰生活 │    │ 港口外勤 │    │ 皇家生活 │
  └─────────┘    └─────────┘    └─────────┘
        │              │              │
  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ 重樱生活 │────│ 混合生活 │────│ 铁血生活 │
  └─────────┘    └─────────┘    └─────────┘
                       │
                 ┌─────────┐
                 │ 东煌生活 │
                 └─────────┘
  `.trim();
}

async function executeMove(dest) {
  log(`▸ 移动至 ${dest.display_name}`, 'sys');
  try {
    const r = await post('/api/move', { location_key: dest.key });
    (r.messages || []).forEach(m => log(m, 'msg'));
    state.selectedActorKey = null;
    closeOverlay('moveOverlay');
    await refreshAll();
  } catch (e) { }
}

// Detail overlay
async function openDetailOverlay(actorKey) {
  if (!actorKey) {
    toast('请先选择一位舰娘');
    return;
  }
  openOverlay('detailOverlay');
  const actor = state.visibleActors.find(a => a.key === actorKey) || {};
  document.getElementById('detailTitle').textContent = `═ ${actor.display_name || actorKey} · 能力显示 ═`;

  const pf = document.getElementById('portraitFrame');
  pf.innerHTML = '';
  if (actor.portrait_url) {
    const img = new Image();
    img.src = actor.portrait_url;
    img.onerror = () => {
      pf.innerHTML = `<div class="portrait-placeholder">立绘占位<br>${actor.display_name || actorKey}</div>`;
    };
    pf.appendChild(img);
    const badge = document.createElement('div');
    badge.className = 'portrait-name-badge';
    badge.textContent = `${actor.display_name} · ${actor.relationship_stage || '陌生'}`;
    pf.appendChild(badge);
  } else {
    pf.innerHTML = `<div class="portrait-placeholder">立绘占位<br>${actor.display_name || actorKey}</div>`;
  }

  document.querySelectorAll('#detailTabs .detail-tab').forEach(t => {
    t.onclick = () => {
      state.activeDetailTab = t.dataset.tab;
      document.querySelectorAll('#detailTabs .detail-tab').forEach(x => x.classList.toggle('active', x === t));
      renderDetailTab(actor, actorKey);
    };
  });
  document.querySelectorAll('#detailTabs .detail-tab').forEach(x => x.classList.toggle('active', x.dataset.tab === state.activeDetailTab));
  renderDetailTab(actor, actorKey);
}

async function renderDetailTab(actor, actorKey) {
  const body = document.getElementById('detailBody');
  body.innerHTML = '<div class="empty">加载中…</div>';
  let status;
  try { status = await get(`/api/actor/${actorKey}/status`); } catch (e) { status = {}; }

  const tab = state.activeDetailTab;
  let html = '';

  if (tab === 'personal') {
    const p = status.personal || {};
    html += `
      <div class="row"><span class="k">个性</span><span class="v">${p.personality || '—'}</span></div>
      <div class="row"><span class="k">住所</span><span class="v">${p.home || '—'}</span></div>
      <div class="row"><span class="k">活动时间</span><span class="v">${(p.activity_hours || []).join(' · ') || '—'}</span></div>
      <div class="row"><span class="k">常去区域</span><span class="v">${(p.frequent_areas || []).join(' · ') || '—'}</span></div>
      <div class="row"><span class="k">当前位置</span><span class="v">${actor.location_key || '—'}</span></div>
      <div class="row"><span class="k">标签</span><span class="v">${(actor.tags || []).join(' / ')}</span></div>
    `;
    if ((p.milestones || []).length) {
      html += `<div class="detail-section-title">里程碑</div>`;
      for (const m of p.milestones) {
        html += `<div class="row"><span class="k">D${m.day}</span><span class="v">${m.label}</span></div>`;
      }
    }
    const states = actor.active_persistent_states || [];
    if (states.length) {
      html += `<div class="detail-section-title">持续状态</div><div class="row"><span class="v">${states.map(s => `<span class="tag-pill">${s}</span>`).join(' ')}</span></div>`;
    }
    const marks = Object.entries(actor.marks || {});
    if (marks.length) {
      html += `<div class="detail-section-title">MARK</div>`;
      for (const [k, v] of marks) html += `<div class="row"><span class="k">${k}</span><span class="v">${v}</span></div>`;
    }
  } else if (tab === 'abilities') {
    const ca = status.clothing_ability || {};
    html += `<div class="detail-section-title">装备</div>`;
    html += `<div class="row"><span class="k">皮肤</span><span class="v">${ca.equipped_skin || '—'}</span></div>`;
    if ((ca.removed_slots || []).length) {
      html += `<div class="row"><span class="k">脱除</span><span class="v">${ca.removed_slots.join(', ')}</span></div>`;
    }
    const abl = ca.abilities || [];
    if (abl.length) {
      html += `<div class="detail-section-title">能力 ABL</div>`;
      for (const e of abl) html += `<div class="row"><span class="k">${e.label}</span><span class="v">Lv${e.level} <span style="color:var(--text-muted);font-size:11px;">(${e.exp || 0})</span></span></div>`;
    }
    const tal = ca.talents || [];
    if (tal.length) {
      html += `<div class="detail-section-title">天赋 Talent</div>`;
      for (const e of tal) html += `<div class="row"><span class="k">${e.label}</span><span class="v">${e.value}</span></div>`;
    }
    if (!abl.length && !tal.length) html += `<div class="empty">暂无能力数据</div>`;
  } else if (tab === 'body') {
    const b = status.body || {};
    const render = (parts) => parts.map(p => `<div class="row"><span class="k">${p.label}</span><span class="v">${(p.tags || []).join('/') || '—'} <span style="color:var(--text-muted);font-size:11px;">${p.description || ''}</span></span></div>`).join('');
    html += `<div class="detail-section-title">外部</div>` + (render(b.outer || []) || '<div class="empty">—</div>');
    html += `<div class="detail-section-title">内部</div>` + (render(b.inner || []) || '<div class="empty">—</div>');
    const counters = status.counters || {};
    if (Object.keys(counters).length) {
      html += `<div class="detail-section-title">计数</div>`;
      for (const [k, v] of Object.entries(counters)) html += `<div class="row"><span class="k">${k}</span><span class="v">${v}</span></div>`;
    }
  } else if (tab === 'likes') {
    const l = status.likes || {};
    const g = l.gift_preferences || {};
    const f = l.food_preferences || {};
    html += `<div class="detail-section-title">礼物</div>`;
    html += `<div class="row"><span class="k">喜欢</span><span class="v">${(g.liked || []).join(' / ') || '—'}</span></div>`;
    html += `<div class="row"><span class="k">厌恶</span><span class="v">${(g.disliked || []).join(' / ') || '—'}</span></div>`;
    html += `<div class="detail-section-title">饮食</div>`;
    html += `<div class="row"><span class="k">喜欢</span><span class="v">${(f.liked || []).join(' / ') || '—'}</span></div>`;
    html += `<div class="row"><span class="k">厌恶</span><span class="v">${(f.disliked || []).join(' / ') || '—'}</span></div>`;
  } else if (tab === 'fallen') {
    const f = status.fallen || {};
    html += `<div class="row"><span class="k">阶段</span><span class="v">${f.stage_name || '—'}${f.has_pledge_ring ? ' · 誓约戒指' : ''}</span></div>`;
    const prog = f.progress || [];
    if (prog.length) {
      html += `<div class="detail-section-title">阶段条件</div>`;
      for (const p of prog) {
        const affOk = p.current_affection >= (p.min_affection || 0);
        const trOk = p.current_trust >= (p.min_trust || 0);
        const inOk = p.current_intimacy >= (p.min_intimacy || 0);
        html += `<div class="row"><span class="k">${p.display_name}</span><span class="v">
          好感 ${p.current_affection}/${p.min_affection || 0} ${affOk ? '✓' : '·'} ·
          信赖 ${p.current_trust}/${p.min_trust || 0} ${trOk ? '✓' : '·'} ·
          亲密 ${p.current_intimacy}/${p.min_intimacy || 0} ${inOk ? '✓' : '·'}
        </span></div>`;
      }
    }
  } else if (tab === 'palam') {
    html += `<div class="palam-grid" style="grid-template-columns:repeat(4,1fr);">`;
    PALAM_KEYS.forEach(([label, key]) => {
      const v = (actor.palam && actor.palam[key]) || 0;
      const lv = palamLevel(v);
      html += `<div class="palam-cell palam-lv${lv}"><span class="pk">${label}</span><span class="pv">Lv${lv} <span style="color:var(--text-muted);">(${v})</span></span></div>`;
    });
    html += `</div>`;
  }

  body.innerHTML = html || '<div class="empty">暂无数据</div>';
}

// Inventory overlay
async function openInventoryOverlay() {
  openOverlay('inventoryOverlay');
  const grid = document.getElementById('invGrid');
  grid.innerHTML = '<div class="empty">加载中…</div>';
  let items = [];
  try { items = await get('/api/inventory'); } catch (e) { }
  if (!items.length) {
    grid.innerHTML = '<div class="empty">背包为空</div>';
    return;
  }
  grid.innerHTML = '';
  for (const item of items) {
    const row = document.createElement('div');
    row.className = 'inv-row';
    row.innerHTML = `
      <div class="info">
        <div class="title">${item.display_name}</div>
        <div class="desc">${item.description || ''}</div>
      </div>
      <div class="count">×${item.count}</div>
    `;
    grid.appendChild(row);
  }
}

// Calendar overlay
async function openCalendarOverlay() {
  openOverlay('calendarOverlay');
  const head = document.getElementById('calHead');
  const fl = document.getElementById('calFestivals');
  head.textContent = '加载中…';
  fl.innerHTML = '';
  try {
    const c = await get('/api/calendar');
    head.textContent = `${c.year}年 ${SEASON_LABEL[c.season] || c.season} ${c.day}日 周${WEEKDAY_LABEL[c.weekday] || c.weekday}`;
    if ((c.festivals || []).length) {
      for (const f of c.festivals) {
        const div = document.createElement('div');
        div.className = 'cal-festival';
        div.innerHTML = `<div class="date">${f.month}月${f.day}日</div><div class="name">${f.display_name}</div>`;
        fl.appendChild(div);
      }
    } else {
      fl.innerHTML = '<div class="empty">暂无节日</div>';
    }
  } catch (e) {
    head.textContent = '加载失败';
  }
}

// Shop overlay
async function openShop(shopfrontKey) {
  state.lastShopfront = shopfrontKey;
  openOverlay('shopOverlay');
  const title = shopfrontKey === 'skin_shop' ? '时装屋' : shopfrontKey === 'general_shop' ? '杂货店' : '商店';
  document.getElementById('shopTitle').textContent = `═ ${title} ═`;
  const body = document.getElementById('shopItems');
  body.innerHTML = '<div class="empty">加载中…</div>';
  try {
    const items = await get('/api/shop?shopfront=' + encodeURIComponent(shopfrontKey));
    if (!items.length) {
      body.innerHTML = '<div class="empty">暂无商品</div>';
      return;
    }
    body.innerHTML = '';
    for (const item of items) {
      const row = document.createElement('div');
      row.className = 'shop-item';
      row.innerHTML = `
        <div class="info">
          <div class="title">${item.display_name}</div>
          <div class="desc">${item.description || ''}</div>
        </div>
        <span class="price">${item.price}G</span>
        <button>购买</button>
      `;
      row.querySelector('button').onclick = () => buyItem(item.key);
      body.appendChild(row);
    }
  } catch (e) {
    body.innerHTML = '<div class="empty">加载失败</div>';
  }
}

async function buyItem(itemKey) {
  if (!state.lastShopfront) return;
  try {
    const r = await post('/api/shop/buy', { shopfront_key: state.lastShopfront, item_key: itemKey });
    if (r.success) {
      log(`购买 ${itemKey} × ${r.count} (-${r.total_price}G)`, 'funds');
      await refreshAll();
      await openShop(state.lastShopfront);
    } else {
      log(`购买失败: ${r.reason || '未知'}`, 'err');
    }
  } catch (e) { }
}

// ── Actions ───────────────────────────────────────
async function selectActor(key) {
  state.selectedActorKey = key;
  renderActorList();
  renderActorCard();
  await renderCommands();
}

async function doWait() {
  log('▸ 等待（推进时段）', 'sys');
  try {
    const r = await post('/api/wait', {});
    log(`时间推进至 ${String(r.hour).padStart(2,'0')}:${String(r.minute).padStart(2,'0')} (${TIME_SLOT_LABEL[r.time_slot] || r.time_slot})`, 'msg');
    state.selectedActorKey = null;
    await refreshAll();
  } catch (e) { }
}

async function doSave() {
  try {
    const r = await post('/api/save', {});
    log(r.saved ? '✓ 已保存' : '保存失败', r.saved ? 'msg' : 'err');
  } catch (e) { }
}

async function doLoad() {
  try {
    const r = await post('/api/load', {});
    if (r.loaded) {
      log('✓ 已读取存档', 'msg');
      state.selectedActorKey = null;
      await refreshAll();
    } else {
      log('无存档可读取', 'sys');
    }
  } catch (e) { }
}

// ── Refresh ───────────────────────────────────────
async function refreshAll() {
  try {
    const data = await get('/api/state');
    state.world = data.world || {};
    state.visibleActors = data.visible_actors || [];
  } catch (e) { return; }
  renderTopbar();
  renderTrainingBanner();
  renderActorList();
  renderActorCard();
  await renderCommands();
}

// ── Overlay background click close ────────────────
document.querySelectorAll('.overlay').forEach(ov => {
  ov.addEventListener('click', e => {
    if (e.target === ov) ov.hidden = true;
  });
});

// ── Init ──────────────────────────────────────────
async function init() {
  renderExDock();
  await renderPlayer();
  await refreshAll();
}
init();
