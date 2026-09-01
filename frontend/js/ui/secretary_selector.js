// 秘书舰选择面板
// 特性：多分类多选标签（黄字态）、6x5网格头像卡片、无滚轮分页（每页30位）、分界线与确认/返回/翻页交互

let allOptions = [];
let callbacksRef = null;
let selectedShipId = null;
let currentPage = 1;
const PAGE_SIZE = 30; // 5行 x 6列 = 30位/页

// 分类标签定义（与 data/attr_defs.json 中的 ship_type / alignment 取值一一对应）
const TYPE_TAGS = [
    { label: '[驱逐]', types: ['0'] },
    { label: '[轻巡]', types: ['1'] },
    { label: '[重巡]', types: ['2'] },
    { label: '[战列]', types: ['3'] },
    { label: '[航母]', types: ['4'] },
    { label: '[潜艇]', types: ['5'] },
    { label: '[维修]', types: ['6'] },
    { label: '[航战]', types: ['7'] },
    { label: '[轻航]', types: ['8'] },
    { label: '[运输]', types: ['9'] },
    { label: '[重炮]', types: ['10'] },
    { label: '[战巡]', types: ['11'] },
    { label: '[超巡]', types: ['12'] },
];

const FACTION_TAGS = [
    { label: '[白鹰]', alignment: '0' },
    { label: '[重樱]', alignment: '1' },
    { label: '[铁血]', alignment: '2' },
    { label: '[鸢尾]', alignment: '3' },
    { label: '[维希教廷]', alignment: '4' },
    { label: '[撒丁帝国]', alignment: '5' },
    { label: '[皇家]', alignment: '6' },
    { label: '[东煌]', alignment: '7' },
    { label: '[北方联合]', alignment: '8' },
    { label: '[郁金王国]', alignment: '9' },
    { label: '[META]', alignment: '10' },
    { label: '[飓风]', alignment: '11' },
];

// 当前已选中的分类筛选集合（允许多选）
const selectedTypeFilters = new Set();
const selectedFactionFilters = new Set();

export function openSecretarySelector(options, callbacks) {
    allOptions = options || [];
    callbacksRef = callbacks;
    currentPage = 1;
    selectedTypeFilters.clear();
    selectedFactionFilters.clear();

    // 默认选中当前担任秘书舰的舰娘，若无则选中首位
    const currentSec = allOptions.find(o => o.is_current);
    selectedShipId = currentSec ? currentSec.id : (allOptions[0]?.id || null);

    const el = document.getElementById('secretary_selector_screen');
    const game = document.getElementById('game_screen');
    const menu = document.getElementById('menu_screen');
    const fullscreenOpts = document.getElementById('fullscreen_options');

    if (game) game.style.display = 'none';
    if (menu) menu.style.display = 'none';
    if (fullscreenOpts) fullscreenOpts.style.display = 'none';

    el.style.display = 'flex';
    renderSecretarySelector();
}

function closeSecretarySelector() {
    const el = document.getElementById('secretary_selector_screen');
    el.style.display = 'none';
    el.innerHTML = '';
    if (callbacksRef && callbacksRef.refresh) {
        callbacksRef.refresh();
    }
}

function getFilteredShipgirls() {
    return allOptions.filter(opt => {
        // 舰种筛选（若勾选了任意舰种，必须匹配其中之一）
        if (selectedTypeFilters.size > 0) {
            let matchType = false;
            for (const tag of TYPE_TAGS) {
                if (selectedTypeFilters.has(tag.label) && tag.types.includes(opt.ship_type)) {
                    matchType = true;
                    break;
                }
            }
            if (!matchType) return false;
        }

        // 阵营筛选（若勾选了任意阵营，必须匹配其中之一）
        if (selectedFactionFilters.size > 0) {
            let matchFaction = false;
            for (const tag of FACTION_TAGS) {
                if (selectedFactionFilters.has(tag.label) && tag.alignment === opt.alignment) {
                    matchFaction = true;
                    break;
                }
            }
            if (!matchFaction) return false;
        }

        return true;
    });
}

function renderSecretarySelector() {
    const container = document.getElementById('secretary_selector_screen');
    container.innerHTML = '';

    const wrap = document.createElement('div');
    wrap.className = 'sec-wrap';

    // 1. 顶部标题与多分类标签筛选区
    const header = document.createElement('div');
    header.className = 'sec-header';

    const title = document.createElement('div');
    title.className = 'sec-title';
    title.textContent = '【设定秘书舰】';
    header.appendChild(title);

    const filterRow = document.createElement('div');
    filterRow.className = 'sec-filter-row';

    // 渲染舰种标签
    for (const tag of TYPE_TAGS) {
        const span = document.createElement('span');
        span.className = 'sec-tag' + (selectedTypeFilters.has(tag.label) ? ' selected' : '');
        span.textContent = tag.label;
        span.onclick = () => {
            if (selectedTypeFilters.has(tag.label)) {
                selectedTypeFilters.delete(tag.label);
            } else {
                selectedTypeFilters.add(tag.label);
            }
            currentPage = 1;
            renderSecretarySelector();
        };
        filterRow.appendChild(span);
    }

    // 两行之间的分割线（占满整行，强制换行并分隔两类）
    const filterDivider = document.createElement('div');
    filterDivider.className = 'sec-filter-divider';
    filterRow.appendChild(filterDivider);

    // 渲染阵营标签
    for (const tag of FACTION_TAGS) {
        const span = document.createElement('span');
        span.className = 'sec-tag' + (selectedFactionFilters.has(tag.label) ? ' selected' : '');
        span.textContent = tag.label;
        span.onclick = () => {
            if (selectedFactionFilters.has(tag.label)) {
                selectedFactionFilters.delete(tag.label);
            } else {
                selectedFactionFilters.add(tag.label);
            }
            currentPage = 1;
            renderSecretarySelector();
        };
        filterRow.appendChild(span);
    }

    header.appendChild(filterRow);
    wrap.appendChild(header);

    // 2. 6x5 网格内容区 (无滚轮)
    const filtered = getFilteredShipgirls();
    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    if (currentPage > totalPages) currentPage = totalPages;

    const startIdx = (currentPage - 1) * PAGE_SIZE;
    const pageItems = filtered.slice(startIdx, startIdx + PAGE_SIZE);

    const grid = document.createElement('div');
    grid.className = 'sec-grid';

    if (pageItems.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'sec-empty';
        empty.textContent = '（没有符合筛选条件的舰娘）';
        grid.appendChild(empty);
    } else {
        for (const opt of pageItems) {
            const card = document.createElement('div');
            card.className = 'sec-card' + (opt.id === selectedShipId ? ' selected' : '');
            card.onclick = () => {
                selectedShipId = opt.id;
                // 仅更新卡片选中高亮态
                grid.querySelectorAll('.sec-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
            };

            const img = document.createElement('img');
            img.src = opt.avatar || `assets/avatars/${opt.name}/${opt.id}_default.webp`;
            img.alt = opt.name;
            img.className = 'sec-avatar-img';
            card.appendChild(img);

            const nameBox = document.createElement('div');
            nameBox.className = 'sec-name-box';
            nameBox.textContent = opt.name;
            if (opt.is_current) {
                const curBadge = document.createElement('span');
                curBadge.className = 'sec-current-badge';
                curBadge.textContent = ' (当前)';
                nameBox.appendChild(curBadge);
            }
            card.appendChild(nameBox);

            grid.appendChild(card);
        }
    }
    wrap.appendChild(grid);

    // 3. 分界线
    const divider = document.createElement('div');
    divider.className = 'sec-divider';
    wrap.appendChild(divider);

    // 4. 分界线下方交互选项
    const footer = document.createElement('div');
    footer.className = 'sec-footer';

    const actions = document.createElement('div');
    actions.className = 'sec-actions';

    // - 确认
    const confirmBtn = document.createElement('span');
    confirmBtn.className = 'sec-action-btn' + (!selectedShipId ? ' disabled' : '');
    confirmBtn.textContent = '- 确认';
    confirmBtn.onclick = async () => {
        if (!selectedShipId) return;
        const selectedOpt = allOptions.find(o => o.id === selectedShipId);
        if (selectedOpt && callbacksRef) {
            closeSecretarySelector();
            let result = await callbacksRef.doCmd('set_secretary_ship', { shipgirl_id: selectedShipId });
            if (result && Array.isArray(result) && result.length > 0) {
                callbacksRef.showFullscreenText(result);
            }
        }
    };
    actions.appendChild(confirmBtn);

    // - 返回
    const cancelBtn = document.createElement('span');
    cancelBtn.className = 'sec-action-btn';
    cancelBtn.textContent = '- 返回';
    cancelBtn.onclick = () => {
        closeSecretarySelector();
    };
    actions.appendChild(cancelBtn);

    // - 上一页
    const prevBtn = document.createElement('span');
    const isPrevDisabled = currentPage <= 1;
    prevBtn.className = 'sec-action-btn' + (isPrevDisabled ? ' disabled' : '');
    prevBtn.textContent = '- 上一页';
    if (!isPrevDisabled) {
        prevBtn.onclick = () => {
            currentPage--;
            renderSecretarySelector();
        };
    }
    actions.appendChild(prevBtn);

    // - 下一页
    const nextBtn = document.createElement('span');
    const isNextDisabled = currentPage >= totalPages;
    nextBtn.className = 'sec-action-btn' + (isNextDisabled ? ' disabled' : '');
    nextBtn.textContent = '- 下一页';
    if (!isNextDisabled) {
        nextBtn.onclick = () => {
            currentPage++;
            renderSecretarySelector();
        };
    }
    actions.appendChild(nextBtn);

    footer.appendChild(actions);

    // 页码提示
    const pageInfo = document.createElement('span');
    pageInfo.className = 'sec-page-info';
    pageInfo.textContent = `第 ${currentPage} / ${totalPages} 页 (共 ${filtered.length} 位)`;
    footer.appendChild(pageInfo);

    wrap.appendChild(footer);
    container.appendChild(wrap);
}
