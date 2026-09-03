// 港区战术终端 (Juus Pad) 交互模块
// 特性：平板大视窗、双栏Master-Detail架构、纯文字无Emoji终端风格、通讯录/即时状态雷达

const FACTIONS = [
    { key: 'all', label: '[全部]' },
    { key: '0', label: '[白鹰]' },
    { key: '1', label: '[重樱]' },
    { key: '2', label: '[铁血]' },
    { key: '6', label: '[皇家]' },
    { key: '7', label: '[东煌]' },
    { key: '8', label: '[北方联合]' },
];

let contactsList = [];
let selectedContactId = null;
let selectedFaction = 'all';
let callbacksRef = null;

export async function openJuus(callbacks) {
    callbacksRef = callbacks;
    selectedFaction = 'all';

    const el = document.getElementById('juus_screen');
    const game = document.getElementById('game_screen');
    const menu = document.getElementById('menu_screen');
    const fullscreenOpts = document.getElementById('fullscreen_options');

    if (game) game.style.display = 'none';
    if (menu) menu.style.display = 'none';
    if (fullscreenOpts) fullscreenOpts.style.display = 'none';

    el.style.display = 'flex';
    await fetchAndRenderContacts();
}

export function closeJuus() {
    const el = document.getElementById('juus_screen');
    el.style.display = 'none';
    el.innerHTML = '';
    if (callbacksRef && callbacksRef.refresh) {
        callbacksRef.refresh();
    }
}

async function fetchAndRenderContacts(preserveSelection = true) {
    try {
        if (window.pywebview && window.pywebview.api) {
            contactsList = await window.pywebview.api.call('juus_manager', 'get_contacts_list') || [];
        } else {
            contactsList = [];
        }
    } catch (e) {
        console.error('获取通讯录失败:', e);
        contactsList = [];
    }

    if (!preserveSelection || !selectedContactId || !contactsList.some(c => c.id === selectedContactId)) {
        selectedContactId = contactsList[0]?.id || null;
    }

    renderJuusPad();
}

function getFilteredContacts() {
    if (selectedFaction === 'all') {
        return contactsList;
    }
    return contactsList.filter(c => c.alignment === selectedFaction);
}

function renderJuusPad() {
    const container = document.getElementById('juus_screen');
    container.innerHTML = '';

    const pad = document.createElement('div');
    pad.className = 'juus-pad';

    // 1. 顶部终端标题与Tab栏
    const header = document.createElement('div');
    header.className = 'juus-header';

    const title = document.createElement('div');
    title.className = 'juus-title';
    title.textContent = '☆JUUS·啾信☆';
    header.appendChild(title);

    const tabs = document.createElement('div');
    tabs.className = 'juus-tabs';

    const contactTab = document.createElement('span');
    contactTab.className = 'juus-tab-btn active';
    contactTab.textContent = '[通讯录]';
    tabs.appendChild(contactTab);

    const groupTab = document.createElement('span');
    groupTab.className = 'juus-tab-btn disabled';
    groupTab.textContent = '[群聊 (开发中)]';
    tabs.appendChild(groupTab);

    const momentsTab = document.createElement('span');
    momentsTab.className = 'juus-tab-btn disabled';
    momentsTab.textContent = '[朋友圈 (开发中)]';
    tabs.appendChild(momentsTab);

    header.appendChild(tabs);

    const closeBtn = document.createElement('span');
    closeBtn.className = 'juus-close-btn';
    closeBtn.textContent = '[关闭 (X)]';
    closeBtn.onclick = closeJuus;
    header.appendChild(closeBtn);

    pad.appendChild(header);

    // 2. 主体双栏区域
    const body = document.createElement('div');
    body.className = 'juus-body';

    // 左侧通讯录
    body.appendChild(renderSidebar());

    // 右侧主展示区（即时监视看板）
    const mainArea = document.createElement('div');
    mainArea.className = 'juus-main';
    mainArea.id = 'juus_main_area';

    renderDetailView(mainArea);

    body.appendChild(mainArea);
    pad.appendChild(body);
    container.appendChild(pad);
}

function renderSidebar() {
    const sidebar = document.createElement('div');
    sidebar.className = 'juus-sidebar';

    // 阵营筛选栏
    const filterBar = document.createElement('div');
    filterBar.className = 'juus-filter-bar';

    for (const f of FACTIONS) {
        const tag = document.createElement('span');
        tag.className = 'juus-filter-tag' + (selectedFaction === f.key ? ' selected' : '');
        tag.textContent = f.label;
        tag.onclick = () => {
            selectedFaction = f.key;
            // 切换阵营时默认选中筛选结果中的第一位
            const filtered = getFilteredContacts();
            selectedContactId = filtered[0]?.id || null;
            renderJuusPad();
        };
        filterBar.appendChild(tag);
    }
    sidebar.appendChild(filterBar);

    // 舰娘列表
    const list = document.createElement('div');
    list.className = 'juus-contacts-list';

    const filtered = getFilteredContacts();
    if (filtered.length !== 0) {
        for (const c of filtered) {
            const item = document.createElement('div');
            item.className = 'juus-contact-item' + (c.id === selectedContactId ? ' selected' : '');
            item.onclick = () => {
                if (selectedContactId !== c.id) {
                    selectedContactId = c.id;
                    // 仅在 DOM 中切换选中高亮，不重建侧边栏，避免滚动位置回弹
                    list.querySelectorAll('.juus-contact-item').forEach(el => el.classList.remove('selected'));
                    item.classList.add('selected');

                    const main = document.getElementById('juus_main_area');
                    if (main) renderDetailView(main);
                }
            };

            const img = document.createElement('img');
            img.src = c.avatar || `assets/avatars/${c.name}/${c.id}_default.webp`;
            img.alt = c.name;
            img.className = 'juus-contact-avatar';
            item.appendChild(img);

            const meta = document.createElement('div');
            meta.className = 'juus-contact-meta';

            const topRow = document.createElement('div');
            topRow.className = 'juus-contact-row-top';

            const name = document.createElement('span');
            name.className = 'juus-contact-name';
            name.textContent = c.name;
            topRow.appendChild(name);

            meta.appendChild(topRow);

            // 状态标签排（非按钮不使用 []）
            const tags = document.createElement('div');
            tags.className = 'juus-contact-tags';

            // 初遇/关系徽章
            const metBadge = document.createElement('span');
            metBadge.className = 'juus-badge ' + (c.first_met ? 'juus-badge-met' : 'juus-badge-unmet');
            metBadge.textContent = c.first_met_label;
            tags.appendChild(metBadge);

            // 主状态徽章
            for (const t of c.status_tags) {
                const b = document.createElement('span');
                let cls = 'juus-badge-free';
                if (t === '工作中') cls = 'juus-badge-working';
                else if (t === '睡眠中') cls = 'juus-badge-sleeping';
                else if (t === '休息中') cls = 'juus-badge-resting';
                else if (t === '秘书舰') cls = 'juus-badge-sec';
                else if (t === '疲倦') cls = 'juus-badge-tired';
                else if (t === '同行中') cls = 'juus-badge-follow';
                b.className = `juus-badge ${cls}`;
                b.textContent = t;
                tags.appendChild(b);
            }

            meta.appendChild(tags);
            item.appendChild(meta);
            list.appendChild(item);
        }
    }

    sidebar.appendChild(list);
    return sidebar;
}

async function renderDetailView(container) {
    container.innerHTML = '';

    let detail = null;

    if (window.pywebview && window.pywebview.api && selectedContactId) {
        detail = await window.pywebview.api.call('juus_manager', 'get_contact_detail', selectedContactId);
    } else {
        return;
    }

    if (!detail) {
        return;
    }

    const wrap = document.createElement('div');
    wrap.className = 'juus-detail-container';

    // 1. 实时监视看板 (Radar & Status)
    const statusSec = document.createElement('div');
    statusSec.className = 'juus-detail-status-section';

    const secTitle = document.createElement('div');
    secTitle.className = 'juus-section-title';
    secTitle.textContent = '舰娘状态';
    statusSec.appendChild(secTitle);

    const locRow = document.createElement('div');
    locRow.className = 'juus-info-row';
    locRow.innerHTML = `<span class="juus-info-label">当前位置：</span><span class="juus-info-val" style="font-weight: bold;">${detail.location_text}</span>`;

    const gotoBtn = document.createElement('span');
    if (detail.is_current_location) {
        gotoBtn.className = 'juus-goto-btn disabled';
        gotoBtn.textContent = '[当前地点]';
    } else {
        gotoBtn.className = 'juus-goto-btn';
        gotoBtn.textContent = '[前往]';
        gotoBtn.onclick = async () => {
            try {
                if (window.pywebview && window.pywebview.api) {
                    const res = await window.pywebview.api.call('juus_manager', 'navigate_to_contact', detail.id);
                    closeJuus();
                    if (res && res.success) {
                        if (callbacksRef) {
                            if (res.messages && res.messages.length > 0 && callbacksRef.showFullscreenText) {
                                callbacksRef.showFullscreenText(res.messages);
                            } else if (callbacksRef.refresh) {
                                callbacksRef.refresh();
                            }
                        }
                    }
                }
            } catch (err) {
                console.error('前往失败:', err);
            }
        };
    }
    locRow.appendChild(gotoBtn);
    statusSec.appendChild(locRow);

    const actRow = document.createElement('div');
    actRow.className = 'juus-info-row';
    const tagHtml = detail.status_tags.map(t => `<span class="juus-badge juus-badge-loc" style="margin-right: 6px;">${t}</span>`).join('');
    actRow.innerHTML = `<span class="juus-info-label">行为状态：</span><span class="juus-info-val">${tagHtml || '自由行动'}</span>`;
    statusSec.appendChild(actRow);

    const chatStatusRow = document.createElement('div');
    chatStatusRow.className = 'juus-info-row';
    chatStatusRow.innerHTML = `<span class="juus-info-label">通讯状态：</span><span class="juus-info-val">${detail.chat_status}</span>`;
    statusSec.appendChild(chatStatusRow);

    wrap.appendChild(statusSec);

    // 2. 日程概况（统一为与舰娘状态相同的标签+值列格式）
    const schedSec = document.createElement('div');
    schedSec.className = 'juus-detail-status-section';

    const schedTitle = document.createElement('div');
    schedTitle.className = 'juus-section-title';
    schedTitle.textContent = '日程概况';
    schedSec.appendChild(schedTitle);

    const sleepRow = document.createElement('div');
    sleepRow.className = 'juus-info-row';
    sleepRow.innerHTML = `<span class="juus-info-label">睡眠作息：</span><span class="juus-info-val">${detail.sleep_schedule || '无'}</span>`;
    schedSec.appendChild(sleepRow);

    const workRow = document.createElement('div');
    workRow.className = 'juus-info-row';
    workRow.innerHTML = `<span class="juus-info-label">工作安排：</span><span class="juus-info-val">${detail.work_schedule || '无'}</span>`;
    schedSec.appendChild(workRow);

    wrap.appendChild(schedSec);

    container.appendChild(wrap);
}
