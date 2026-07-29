const TABS = [
    { key: 'ability', name: '能力&经验', enabled: true },
    { key: 'costume', name: '服装&皮肤', enabled: false },
    { key: 'body', name: '身体情报', enabled: false },
    { key: 'personal', name: '个人情报', enabled: false },
    { key: 'fallen', name: '堕落状态', enabled: false },
];

let activeTab = 'ability';

export function showCharacterInfo(npc) {
    const el = document.getElementById('fullscreen_charinfo');
    el.innerHTML = '';

    const tabBar = document.createElement('div');
    tabBar.className = 'charinfo-tabbar';
    for (const tab of TABS) {
        const t = document.createElement('span');
        t.className = 'charinfo-tab' + (tab.key === activeTab ? ' active' : '') + (tab.enabled ? '' : ' disabled');
        t.textContent = tab.name;
        if (tab.enabled) {
            t.onclick = () => {
                activeTab = tab.key;
                showCharacterInfo(npc);
            };
        }
        tabBar.appendChild(t);
    }
    el.appendChild(tabBar);

    const content = document.createElement('div');
    content.className = 'charinfo-content';
    if (activeTab === 'ability') {
        renderAbilityTab(content, npc);
    } else {
        const hint = document.createElement('div');
        hint.className = 'charinfo-hint';
        hint.textContent = '该页面尚未开放';
        content.appendChild(hint);
    }
    el.appendChild(content);

    const closeHint = document.createElement('div');
    closeHint.className = 'charinfo-close-hint';
    closeHint.textContent = '点击空白处关闭';
    el.appendChild(closeHint);

    document.getElementById('game_screen').style.display = 'none';
    el.style.display = 'block';
}

function renderAbilityTab(content, npc) {
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
    avatar.src = `assets/avatars/${npc.name}.webp`;
    avatar.alt = npc.name;
    avatar.onclick = function (e) {
        e.stopPropagation();
        const portraitEl = document.getElementById('fullscreen_portrait');
        portraitEl.innerHTML = `<img src="assets/portraits/${npc.name}.webp" alt="${npc.name}">`;
        portraitEl.style.display = 'flex';
    };
    content.appendChild(avatar);

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
    document.getElementById('game_screen').style.display = 'block';
}
