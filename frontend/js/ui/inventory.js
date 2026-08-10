// 道具背包（系统指令「道具」）
// 数据源：item_manager.get_state() / item_manager.use_items()
// 交互：
//   - 点击道具 -> 选中（字体变黄），底部 desc 块显示描述
//   - 仅选中 is_usable=true 的道具时「使用」可点
//   - 使用成功：刷新列表（is_consumable 会减数量），留在背包
//   - 「返回」：关面板，refresh 游戏界面

import { showToast } from './daily_shop.js';

let inventoryItems = [];   // [{item_id, name, num, desc, is_consumable, is_usable, price}]
let selectedItemId = null; // 当前选中的道具 id
let invOnClose = null;     // 关闭回调（main.js 注入）

// 打开背包：拉取已拥有道具并渲染
export async function openInventory(onClose) {
    invOnClose = onClose || null;
    selectedItemId = null;

    const el = document.getElementById('inventory_screen');
    const game = document.getElementById('game_screen');
    const statusBar = document.getElementById('status_bar');

    game.style.display = 'none';
    // 面板从状态栏底部开始，状态栏始终可见
    const sbHeight = statusBar.offsetHeight || 50;
    el.style.top = sbHeight + 'px';
    el.style.height = 'calc(100% - ' + sbHeight + 'px)';
    el.style.display = 'flex';
    el.innerHTML = '';

    await loadInventory();
}

// 拉取背包数据
async function loadInventory() {
    const el = document.getElementById('inventory_screen');
    el.innerHTML = '';

    try {
        const data = await window.pywebview.api.call('item_manager', 'get_state');
        // get_state 返回 {item_id: {name, num, desc, is_consumable, is_usable, price}}
        inventoryItems = Object.entries(data || {}).map(([item_id, info]) => ({
            item_id,
            name: info.name,
            num: info.num,
            desc: info.desc,
            is_consumable: !!info.is_consumable,
            is_usable: !!info.is_usable,
            price: info.price,
        }));
    } catch (e) {
        console.error('获取背包失败:', e);
        inventoryItems = [];
    }

    if (inventoryItems.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'inv-empty';
        empty.textContent = '背包空空如也';
        el.appendChild(empty);
    } else {
        renderItemList(el);
    }

    renderDescBlock(el);
    renderBottomBar(el);
}

// 全量重渲染
function renderAll() {
    const el = document.getElementById('inventory_screen');
    el.innerHTML = '';
    if (inventoryItems.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'inv-empty';
        empty.textContent = '背包空空如也';
        el.appendChild(empty);
    } else {
        renderItemList(el);
    }
    renderDescBlock(el);
    renderBottomBar(el);
}

// 道具列表：纯文字指令风格，`道具名 x数量`
function renderItemList(el) {
    const list = document.createElement('div');
    list.className = 'inv-list';

    for (const item of inventoryItems) {
        const span = document.createElement('span');
        span.className = 'inv-item' + (item.item_id === selectedItemId ? ' selected' : '');
        span.textContent = `${item.name} x${item.num}`;
        span.onclick = function () {
            if (selectedItemId === item.item_id) {
                selectedItemId = null;
            } else {
                selectedItemId = item.item_id;
            }
            renderAll();
        };
        list.appendChild(span);
    }
    el.appendChild(list);
}

// 描述块：选中显示 desc，未选中为空
function renderDescBlock(el) {
    const desc = document.createElement('div');
    desc.className = 'inv-desc';
    const selected = inventoryItems.find(i => i.item_id === selectedItemId);
    if (selected) {
        desc.textContent = selected.desc;
    }
    el.appendChild(desc);
}

// 底部：分界线 + 使用/返回
function renderBottomBar(el) {
    const oldBar = el.querySelector('.inv-bottom');
    if (oldBar) oldBar.remove();

    const bar = document.createElement('div');
    bar.className = 'inv-bottom';

    // 分界线
    const divider = document.createElement('div');
    divider.className = 'inv-divider';
    bar.appendChild(divider);

    // 使用 / 返回
    const actionRow = document.createElement('div');
    actionRow.className = 'inv-actionrow';

    const selected = inventoryItems.find(i => i.item_id === selectedItemId);
    // 使用：仅选中且 is_usable=true 可点
    const useBtn = document.createElement('span');
    const canUse = selected && selected.is_usable;
    useBtn.className = 'inv-action' + (canUse ? '' : ' disabled');
    useBtn.textContent = '使用';
    if (canUse) {
        useBtn.onclick = async function () {
            const result = await window.pywebview.api.call('item_manager', 'use_items', selected.item_id, 1);
            // result: [ok, msg]
            if (result && result[0]) {
                // 使用成功：刷新背包（消耗品数量-1 或消失）
                await loadInventory();
            } else {
                showToast((result && result[1]) || '使用失败');
            }
        };
    }
    actionRow.appendChild(useBtn);

    // 返回
    const backBtn = document.createElement('span');
    backBtn.className = 'inv-action';
    backBtn.textContent = '返回';
    backBtn.onclick = closeInventory;
    actionRow.appendChild(backBtn);

    bar.appendChild(actionRow);
    el.appendChild(bar);
}

// 关闭背包并刷新游戏界面
function closeInventory() {
    const el = document.getElementById('inventory_screen');
    el.style.display = 'none';
    el.innerHTML = '';
    selectedItemId = null;
    if (invOnClose) invOnClose();
}
