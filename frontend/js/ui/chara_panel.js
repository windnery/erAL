// 角色面板与立绘区（头像排）渲染
// 数据来源：state.nearby_npcs（每只舰娘含 id / name / base / talent ...）
// 选中态由 main.js 维护并传入，本模块只负责渲染。

export function renderPortrait(npcs, selectedId, onSelect) {
    const el = document.getElementById('charaPortrait');
    el.innerHTML = '';

    if (npcs.length === 0) {
        el.textContent = '（附近没有舰娘）';
        return;
    }

    for (let npc of npcs) {
        const avatar = document.createElement('div');
        avatar.className = 'npc-avatar' + (npc.id === selectedId ? ' selected' : '');
        avatar.title = npc.name;

        const img = document.createElement('img');
        // 优先用后端下发的当前穿戴皮肤头像路径；无则按约定拼接默认皮肤
        img.src = npc.avatar || `assets/avatars/${npc.name}/${npc.id}_default.webp`;
        img.alt = npc.name;
        img.className = 'npc-avatar-img';
        avatar.appendChild(img);

        const label = document.createElement('div');
        label.className = 'npc-avatar-name';
        label.textContent = npc.name;
        avatar.appendChild(label);

        avatar.onclick = () => onSelect(npc.id);
        el.appendChild(avatar);
    }
}

export function renderCharaPanel(npcs, selectedId, palamDefs, palamLvMap, cflagDefs) {
    const el = document.getElementById('charaPanel');
    el.innerHTML = '';

    const npc = npcs.find(n => n.id === selectedId);
    if (!npc) {
        const hint = document.createElement('div');
        hint.className = 'chara-hint';
        hint.textContent = '（点击头像查看舰娘信息）';
        el.appendChild(hint);
        return;
    }

    const base = npc.base || {};

    // 名字 + 好感/信赖/心情 同一行，括号包裹；末尾追加 cflag 状态标记
    const name = document.createElement('div');
    name.className = 'chara-name';
    const flags = Object.entries(npc.cflag || {})
        .filter(([, v]) => v === true)
        .map(([k]) => (cflagDefs && cflagDefs[k]) || k);

    name.appendChild(document.createTextNode(`${npc.name} (好感 ${npc.favor ?? 0} 信赖 ${npc.trust ?? 0}`));

    if (npc.mood_label) {
        const moodColors = {
            '幸福': '#ffd400',
            '好心情': '#66ccff',
            '愤怒': '#ff0000'
        };
        const moodSpan = document.createElement('span');
        moodSpan.style.color = npc.mood_color || moodColors[npc.mood_label] || '#66ccff';
        moodSpan.textContent = ` ${npc.mood_label}`;
        name.appendChild(moodSpan);
    }

    if (flags.length) {
        // 疲倦用红色展示，其余 cflag 保持默认色
        const flagColors = { '疲倦': '#ff4d4f' };
        for (const f of flags) {
            name.appendChild(document.createTextNode(' '));
            const flagSpan = document.createElement('span');
            if (flagColors[f]) {
                flagSpan.style.color = flagColors[f];
            }
            flagSpan.textContent = `[${f}]`;
            name.appendChild(flagSpan);
        }
    }
    name.appendChild(document.createTextNode(')'));
    el.appendChild(name);

    // 体力条（绿）/ 气力条（蓝）同一行
    const barRow = document.createElement('div');
    barRow.className = 'chara-bar-row';
    appendBar(barRow, '体力', base.stamina, base.max_stamina, 'chara-bar-fill-sta');
    appendBar(barRow, '气力', base.energy, base.max_energy, 'chara-bar-fill-ene');
    el.appendChild(barRow);

    // 情绪（粉色爱心）/ 理性（黄色星星）同一行，位于体力气力条与 palam 区之间
    // 情绪：每 200 一颗爱心，最多 5 颗；低于 200 不显示但固定占位 5 颗的空位
    // 理性：5 颗黄星，每少 200 少一颗（ceil 语义：900→5 颗），到 0 什么都不显示，同样固定占位
    const emoRatRow = document.createElement('div');
    emoRatRow.className = 'chara-emo-rat-row';

    const emoLabel = document.createElement('span');
    emoLabel.className = 'chara-emo-rat-label';
    emoLabel.textContent = '情绪';
    emoRatRow.appendChild(emoLabel);

    const emoHearts = document.createElement('span');
    emoHearts.className = 'chara-hearts';
    emoHearts.textContent = '❤'.repeat(Math.max(0, Math.min(5, Math.floor((base.emotion ?? 0) / 200))));
    emoRatRow.appendChild(emoHearts);

    const ratLabel = document.createElement('span');
    ratLabel.className = 'chara-emo-rat-label';
    ratLabel.textContent = '理性';
    emoRatRow.appendChild(ratLabel);

    const ratStars = document.createElement('span');
    ratStars.className = 'chara-stars';
    const ratCount = Math.max(0, Math.min(5, Math.ceil((base.rationality ?? 1000) / 200)));
    ratStars.textContent = '★'.repeat(ratCount);
    emoRatRow.appendChild(ratStars);

    el.appendChild(emoRatRow);

    // Palam 面板：每行5个，格式 [名称LvN ████░░░░ 数值]
    if (npc.palam) {
        const keys = Object.keys(npc.palam);
        const PER_ROW = 5;
        for (let i = 0; i < keys.length; i += PER_ROW) {
            const row = document.createElement('div');
            row.className = 'palam-row';
            const rowKeys = keys.slice(i, i + PER_ROW);
            for (let key of rowKeys) {
                const item = document.createElement('span');
                item.className = 'palam-item';

                const displayName = (palamDefs && palamDefs[key]) || key;
                const value = npc.palam[key];
                const lv = npc.palam_lv ? (npc.palam_lv[key] ?? 0) : 0;

                // 名称 + LV
                const nameLv = document.createElement('span');
                nameLv.className = 'palam-name-lv';
                nameLv.textContent = `${displayName}Lv${lv}`;
                item.appendChild(nameLv);

                // 进度条
                const barTrack = document.createElement('span');
                barTrack.className = 'palam-bar-track';
                const barFill = document.createElement('span');
                barFill.className = 'palam-bar-fill';

                const lower = lv === 0 ? 0 : (palamLvMap ? (Number(palamLvMap[lv]) || 0) : 0);
                const upper = palamLvMap ? (Number(palamLvMap[lv + 1])) : undefined;
                let pct = 100;
                if (upper !== undefined && upper > lower) {
                    pct = Math.max(0, Math.min(100, ((value - lower) / (upper - lower)) * 100));
                }
                barFill.style.width = pct + '%';
                barTrack.appendChild(barFill);
                item.appendChild(barTrack);

                // 数值
                const valSpan = document.createElement('span');
                valSpan.className = 'palam-val';
                valSpan.textContent = value;
                item.appendChild(valSpan);

                row.appendChild(item);
            }
            el.appendChild(row);
        }
    }
}

function appendBar(row, label, value, max, fillClass) {
    const lab = document.createElement('span');
    lab.className = 'chara-bar-label';
    lab.textContent = label;
    row.appendChild(lab);

    const track = document.createElement('div');
    track.className = 'bar-track';
    const fill = document.createElement('div');
    fill.className = 'bar-fill ' + fillClass;
    const pct = max ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
    fill.style.width = pct + '%';
    track.appendChild(fill);
    row.appendChild(track);

    const txt = document.createElement('span');
    txt.className = 'chara-bar-text';
    txt.textContent = `${value ?? 0}/${max ?? 0}`;
    row.appendChild(txt);
}
