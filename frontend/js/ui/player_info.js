// 全屏玩家信息面板：目前仅「能力&经验」一页
// 展示方式与舰娘 chara_info 一致，头像处用 116px 占位框（不放图片）
// 数据来源：showPlayerInfo(player, ablDefs, expDefs)

import { appendStatsSection } from './chara_info.js';

export function showPlayerInfo(player, ablDefs, expDefs) {
    const el = document.getElementById('fullscreen_playerinfo');
    el.innerHTML = '';

    const content = document.createElement('div');
    content.className = 'charinfo-content';

    // ---- 头像占位区（116px 框，不放图片）----
    const divider1 = document.createElement('div');
    divider1.className = 'charinfo-section-divider';
    const title1 = document.createElement('span');
    title1.className = 'charinfo-section-title';
    title1.textContent = '头像';
    const line1 = document.createElement('span');
    line1.className = 'charinfo-divider-line';
    divider1.appendChild(title1);
    divider1.appendChild(line1);
    content.appendChild(divider1);

    const placeholder = document.createElement('div');
    placeholder.className = 'playerinfo-avatar-placeholder';
    placeholder.textContent = '指挥官';
    content.appendChild(placeholder);

    // ---- 能力（abl）块 ----
    appendStatsSection(content, '能力', player.abl, ablDefs, true);

    // ---- 经验（exp）块 ----
    appendStatsSection(content, '经验', player.exp, expDefs, false);

    // ---- 素质（talent）块 ----
    const divider3 = document.createElement('div');
    divider3.className = 'charinfo-section-divider';
    const title3 = document.createElement('span');
    title3.className = 'charinfo-section-title';
    title3.textContent = '素质';
    const line3 = document.createElement('span');
    line3.className = 'charinfo-divider-line';
    divider3.appendChild(title3);
    divider3.appendChild(line3);
    content.appendChild(divider3);

    const talents = player.talent_list || [];
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

    // ---- 底部操作栏：charinfo-bottom 自带 border-top 分隔线 ----
    const bar = document.createElement('div');
    bar.className = 'charinfo-bottom';

    const divider = document.createElement('div');
    divider.className = 'charinfo-bottom-divider';
    bar.appendChild(divider);

    const actions = document.createElement('div');
    actions.className = 'charinfo-bottom-actions';

    const backBtn = document.createElement('span');
    backBtn.className = 'charinfo-bottom-action';
    backBtn.textContent = '返回';
    backBtn.onclick = function () {
        hidePlayerInfo();
    };
    actions.appendChild(backBtn);

    bar.appendChild(actions);
    el.appendChild(content);
    el.appendChild(bar);

    document.getElementById('game_screen').style.display = 'none';
    el.style.display = 'block';
}

export function hidePlayerInfo() {
    const el = document.getElementById('fullscreen_playerinfo');
    el.style.display = 'none';
    el.innerHTML = '';
    document.getElementById('game_screen').style.display = 'block';
}
