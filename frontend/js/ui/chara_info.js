// 全屏角色信息面板：分类 tab + 内容渲染
// 数据来源：showCharacterInfo(npc) 传入的 nearby_npcs 单项（含 id/name/avatar/portrait/favor/trust/talent...）
// 皮肤页数据：通过 api.call('skin_manager', 'get_owned_skins', npc.id) 异步拉取

import { showToast } from './daily_shop.js';

const TABS = [
    { key: 'ability', name: '能力&经验', enabled: true },
    { key: 'costume', name: '服装&皮肤', enabled: true },
    { key: 'body', name: '身体情报', enabled: false },
    { key: 'personal', name: '个人情报', enabled: false },
    { key: 'fallen', name: '堕落状态', enabled: false },
];

let activeTab = 'ability';
let ownedSkins = [];       // 当前舰娘已拥有皮肤列表
let selectedSkinId = null; // 皮肤页当前选中（换装目标）
let onChanged = null;      // 换装等变更后的刷新回调（由 main.js 注入）
let ablDefsCache = {};     // 能力名称映射
let expDefsCache = {};     // 经验名称映射

export function showCharacterInfo(npc, changedCb, ablDefs, expDefs) {
    onChanged = changedCb || null;
    ablDefsCache = ablDefs || ablDefsCache;
    expDefsCache = expDefs || expDefsCache;
    const el = document.getElementById('fullscreen_charinfo');
    el.innerHTML = '';

    // ---- 顶部 tab 栏 ----
    const tabBar = document.createElement('div');
    tabBar.className = 'charinfo-tabbar';
    for (const tab of TABS) {
        const t = document.createElement('span');
        t.className = 'charinfo-tab' + (tab.key === activeTab ? ' active' : '') + (tab.enabled ? '' : ' disabled');
        t.textContent = tab.name;
        if (tab.enabled) {
            t.onclick = () => {
                activeTab = tab.key;
                selectedSkinId = null;
                showCharacterInfo(npc, onChanged);
            };
        }
        tabBar.appendChild(t);
    }
    el.appendChild(tabBar);

    // ---- 内容区 ----
    const content = document.createElement('div');
    content.className = 'charinfo-content';
    if (activeTab === 'ability') {
        renderAbilityTab(content, npc, ablDefsCache, expDefsCache);
    } else if (activeTab === 'costume') {
        renderCostumeTab(content, npc);
    } else {
        const hint = document.createElement('div');
        hint.className = 'charinfo-hint';
        hint.textContent = '该页面尚未开放';
        content.appendChild(hint);
    }
    el.appendChild(content);

    // ---- 底部操作栏（分界线 + 返回 / 更换）----
    renderCharinfoBottomBar(el, npc);

    document.getElementById('game_screen').style.display = 'none';
    el.style.display = 'block';
}

// ---------- 能力&经验页 ----------

function renderAbilityTab(content, npc, ablDefs, expDefs) {
    const base = npc.base || {};

    const infoRow = document.createElement('div');
    infoRow.className = 'charinfo-info-row';
    infoRow.textContent = `${npc.name}  好感度: ${npc.favor ?? 0}  信赖度: ${npc.trust ?? 0}`;
    content.appendChild(infoRow);

    const barRow = document.createElement('div');
    barRow.className = 'charinfo-bar-row';
    appendBar(barRow, '体力', base.stamina, base.max_stamina, '#6f6');
    appendBar(barRow, '气力', base.energy, base.max_energy, '#66c');
    content.appendChild(barRow);

    const divider1 = document.createElement('div');
    divider1.className = 'charinfo-section-divider';
    const title1 = document.createElement('span');
    title1.className = 'charinfo-section-title';
    title1.textContent = '头像&立绘(点击查看)';
    const line1 = document.createElement('span');
    line1.className = 'charinfo-divider-line';
    divider1.appendChild(title1);
    divider1.appendChild(line1);
    content.appendChild(divider1);

    const avatar = document.createElement('img');
    avatar.className = 'charinfo-avatar';
    avatar.src = npc.avatar || `assets/avatars/${npc.name}/${npc.id}_default.webp`;
    avatar.alt = npc.name;
    avatar.onclick = function (e) {
        e.stopPropagation();
        const portraitEl = document.getElementById('fullscreen_portrait');
        portraitEl.innerHTML = `<img src="${npc.portrait || `assets/portraits/${npc.name}/${npc.id}_default.webp`}" alt="${npc.name}">`;
        portraitEl.style.display = 'flex';
    };
    content.appendChild(avatar);

    // 能力（abl）块
    appendStatsSection(content, '能力', npc.abl, ablDefs);

    // 经验（exp）块
    appendStatsSection(content, '经验', npc.exp, expDefs);

    const divider2 = document.createElement('div');
    divider2.className = 'charinfo-section-divider';
    const title2 = document.createElement('span');
    title2.className = 'charinfo-section-title';
    title2.textContent = '素质';
    const line2 = document.createElement('span');
    line2.className = 'charinfo-divider-line';
    divider2.appendChild(title2);
    divider2.appendChild(line2);
    content.appendChild(divider2);

    const talents = npc.talent || [];
    if (talents.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'charinfo-hint';
        empty.textContent = '暂无素质';
        content.appendChild(empty);
        return;
    }

    const list = document.createElement('div');
    list.className = 'charinfo-talent-list';
    for (const t of talents) {
        const item = document.createElement('span');
        item.className = 'charinfo-talent-item';
        item.textContent = `[${t}]`;
        list.appendChild(item);
    }
    content.appendChild(list);
}

// 通用属性块：分栏标题 + 网格（名称 数值）
function appendStatsSection(content, title, data, defs) {
    const divider = document.createElement('div');
    divider.className = 'charinfo-section-divider';
    const titleEl = document.createElement('span');
    titleEl.className = 'charinfo-section-title';
    titleEl.textContent = title;
    const line = document.createElement('span');
    line.className = 'charinfo-divider-line';
    divider.appendChild(titleEl);
    divider.appendChild(line);
    content.appendChild(divider);

    if (!data || Object.keys(data).length === 0) {
        const empty = document.createElement('div');
        empty.className = 'charinfo-hint';
        empty.textContent = '暂无数据';
        content.appendChild(empty);
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'charinfo-stats-grid';
    for (const key of Object.keys(data)) {
        const name = (defs && defs[key]) || key;
        const value = data[key] ?? 0;
        const item = document.createElement('span');
        item.className = 'charinfo-stats-item';
        const nameSpan = document.createElement('span');
        nameSpan.className = 'charinfo-stats-name';
        nameSpan.textContent = name;
        const valueSpan = document.createElement('span');
        valueSpan.className = 'charinfo-stats-value';
        valueSpan.textContent = value;
        item.appendChild(nameSpan);
        item.appendChild(valueSpan);
        grid.appendChild(item);
    }
    content.appendChild(grid);
}

// ---------- 服装&皮肤页 ----------

async function renderCostumeTab(content, npc) {
    content.textContent = '';
    const hint = document.createElement('div');
    hint.className = 'charinfo-hint';
    hint.textContent = '加载中……';
    content.appendChild(hint);

    let skins = [];
    try {
        skins = await window.pywebview.api.call('skin_manager', 'get_owned_skins', npc.id) || [];
    } catch (e) {
        content.textContent = '';
        hint.textContent = '皮肤数据加载失败';
        content.appendChild(hint);
        return;
    }
    ownedSkins = skins;
    content.textContent = '';

    if (skins.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'charinfo-hint';
        empty.textContent = '暂无已拥有的皮肤';
        content.appendChild(empty);
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'charinfo-skin-grid';
    for (const skin of skins) {
        grid.appendChild(makeOwnedSkinCard(skin, npc));
    }
    content.appendChild(grid);
}

// 已拥有皮肤卡片：头像 + 名字 + 穿戴中标注；选中黄框只包围头像
function makeOwnedSkinCard(skin, npc) {
    const card = document.createElement('div');
    card.className = 'skin-card' + (skin.skin_id === selectedSkinId ? ' selected' : '');

    const avatarWrap = document.createElement('div');
    avatarWrap.className = 'skin-card-avatar';

    const img = document.createElement('img');
    img.className = 'skin-card-img';
    img.src = skin.avatar || '';
    img.alt = `${skin.chara_name}-${skin.skin_name}`;
    img.onerror = function () {
        img.remove();
        const ph = document.createElement('div');
        ph.className = 'skin-card-placeholder';
        ph.textContent = skin.skin_name;
        avatarWrap.prepend(ph);
    };
    avatarWrap.appendChild(img);
    card.appendChild(avatarWrap);

    const label = document.createElement('div');
    label.className = 'skin-card-label';
    label.textContent = skin.skin_name;
    if (skin.is_wearing) {
        label.textContent += '（穿戴中）';
        label.style.color = '#fc0';
    }
    card.appendChild(label);

    card.onclick = function () {
        if (selectedSkinId === skin.skin_id) {
            // 已选中 -> 弹全屏立绘
            showOwnedSkinPortrait(skin);
        } else {
            // 未选中 -> 选中该皮肤
            selectedSkinId = skin.skin_id;
            document.querySelectorAll('#fullscreen_charinfo .skin-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            renderCharinfoBottomBar(document.getElementById('fullscreen_charinfo'), npc);
        }
    };
    return card;
}

// 已拥有皮肤全屏立绘（点击任意处关闭回皮肤页）
function showOwnedSkinPortrait(skin) {
    const portrait = document.getElementById('skin_shop_portrait');
    portrait.innerHTML = '';

    const img = document.createElement('img');
    img.src = skin.portrait || '';
    img.alt = `${skin.chara_name}-${skin.skin_name}`;
    img.onerror = function () {
        img.remove();
        const ph = document.createElement('div');
        ph.className = 'skin-portrait-placeholder';
        ph.textContent = `${skin.chara_name}-${skin.skin_name}（暂无立绘）`;
        portrait.appendChild(ph);
    };
    portrait.appendChild(img);

    portrait.style.display = 'flex';
}

// ---------- 底部操作栏 ----------

// 所有分类页底部统一：分界线 + 操作项（指令样式）
// 皮肤页：更换（选中后可用）+ 返回；其他页：返回
function renderCharinfoBottomBar(el, npc) {
    const oldBar = el.querySelector('.charinfo-bottom');
    if (oldBar) oldBar.remove();

    const bar = document.createElement('div');
    bar.className = 'charinfo-bottom';

    const divider = document.createElement('div');
    divider.className = 'charinfo-bottom-divider';
    bar.appendChild(divider);

    const actions = document.createElement('div');
    actions.className = 'charinfo-bottom-actions';

    if (activeTab === 'costume') {
        const selected = ownedSkins.find(s => s.skin_id === selectedSkinId);
        const changeBtn = document.createElement('span');
        changeBtn.className = 'charinfo-bottom-action' + (selected ? '' : ' disabled');
        changeBtn.textContent = '更换';
        if (selected) {
            changeBtn.onclick = async function () {
                const result = await window.pywebview.api.call('skin_manager', 'equip_skin', npc.id, selected.skin_id);
                if (result && result[0]) {
                    // 换装成功：通过 onChanged 回调通知 main.js 重新拉数据
                    // （更新 currentNearby 中的 avatar/portrait，重开面板显示「穿戴中」）
                    if (onChanged) {
                        onChanged(npc.id);
                    } else {
                        // 兜底：无回调时直接留在皮肤页刷新
                        activeTab = 'costume';
                        selectedSkinId = null;
                        showCharacterInfo(npc);
                    }
                } else {
                    showToast((result && result[1]) || '更换失败');
                }
            };
        }
        actions.appendChild(changeBtn);
    }

    const backBtn = document.createElement('span');
    backBtn.className = 'charinfo-bottom-action';
    backBtn.textContent = '返回';
    backBtn.onclick = function () {
        hideCharacterInfo();
    };
    actions.appendChild(backBtn);

    bar.appendChild(actions);
    el.appendChild(bar);
}

// ---------- 通用 ----------

function appendBar(row, label, value, max, color) {
    const lab = document.createElement('span');
    lab.className = 'charinfo-bar-label';
    lab.textContent = label;
    row.appendChild(lab);

    const track = document.createElement('span');
    track.className = 'charinfo-bar-track';
    const fill = document.createElement('span');
    fill.className = 'charinfo-bar-fill';
    fill.style.background = color;
    const pct = max ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
    fill.style.width = pct + '%';
    track.appendChild(fill);
    row.appendChild(track);

    const txt = document.createElement('span');
    txt.className = 'charinfo-bar-text';
    txt.textContent = `${value ?? 0}/${max ?? 0}`;
    row.appendChild(txt);
}

export function hideCharacterInfo() {
    const el = document.getElementById('fullscreen_charinfo');
    el.style.display = 'none';
    el.innerHTML = '';
    ownedSkins = [];
    selectedSkinId = null;
    document.getElementById('game_screen').style.display = 'block';
}
