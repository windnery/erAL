// 道具商店（不知火商店）
// 数据源：item_manager.get_shop_items() / item_manager.buy_items()
// 交互：
//   - 点击道具 -> 选中（字体变黄），下方描述块显示 desc
//   - 选中状态点击数量设置 [-10][-5][-1][设为0][+1][+5][+10] 调整购买数量
//   - 购买数量>0 的道具即使未选中也常驻黄色
//   - 点「购买」 -> 调 buy_items(item_id, num)，成功留在商店（道具无限量，不消失）+ 同步金钱
//   - 点「返回」 -> 关闭商店，refresh 游戏界面

import { call, getState } from '../api.js';
import { parseColoredMessage } from './colored_text.js';

let shopItems = [];        // 商店在售道具列表
let selectedItemId = null; // 当前选中的道具 id
let buyCounts = {};        // item_id -> 购买数量（>0 常驻黄）
let playerMoney = 0;       // 玩家当前资金（用于购买禁用判断）
let shopOnClose = null;    // 关闭回调（由 main.js 注入，用于 refresh）

// 打开商店：拉取道具并渲染
export async function openDailyShop(onClose) {
    shopOnClose = onClose || null;
    selectedItemId = null;
    buyCounts = {};

    const el = document.getElementById('daily_shop_screen');
    const game = document.getElementById('game_screen');
    const statusBar = document.getElementById('status_bar');

    game.style.display = 'none';
    // 商店面板从状态栏底部开始，保证状态栏可见
    const sbHeight = statusBar.offsetHeight || 50;
    el.style.top = sbHeight + 'px';
    el.style.height = 'calc(100% - ' + sbHeight + 'px)';
    el.style.display = 'flex';
    el.innerHTML = '';

    await loadPlayerMoney();
    await loadShopItems();
}

// 拉取当前资金（用于购买禁用判断）
async function loadPlayerMoney() {
    try {
        const state = await getState(null);
        playerMoney = (state && state.player && state.player.money) || 0;
    } catch (e) {
        console.error('获取资金失败:', e);
        playerMoney = 0;
    }
}

// 拉取商店数据
async function loadShopItems() {
    const el = document.getElementById('daily_shop_screen');
    el.innerHTML = '';

    try {
        const data = await call('item_manager', 'get_shop_items');
        // items_db 是 {item_id: {name, desc, price, ...}}，转成列表
        shopItems = Object.entries(data || {}).map(([item_id, info]) => ({
            item_id,
            name: info.name,
            desc: info.desc,
            price: info.price,
        }));
    } catch (e) {
        console.error('获取道具列表失败:', e);
        shopItems = [];
    }

    if (shopItems.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'daily-shop-empty';
        empty.textContent = '商店暂时没有可购买的道具';
        el.appendChild(empty);
    } else {
        renderItemList(el);
    }

    renderDescBlock(el);
    renderBottomBar(el);
}

// 渲染道具列表（纯文字，指令风格，竖排）
function renderItemList(el) {
    const list = document.createElement('div');
    list.className = 'daily-shop-list';

    for (const item of shopItems) {
        const count = buyCounts[item.item_id] || 0;
        const span = document.createElement('span');
        // 选中 或 购买数量>0 -> 黄色
        span.className = 'daily-shop-item'
            + (item.item_id === selectedItemId ? ' selected' : '')
            + (count > 0 ? ' has-count' : '');
        span.textContent = `${item.name}(¥${item.price}) x${count}`;
        span.onclick = function () {
            if (selectedItemId === item.item_id) {
                // 已选中 -> 取消选中
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

// 全量重渲染（选中态/数量/描述/底部栏都更新）
function renderAll() {
    const el = document.getElementById('daily_shop_screen');
    el.innerHTML = '';
    if (shopItems.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'daily-shop-empty';
        empty.textContent = '商店暂时没有可购买的道具';
        el.appendChild(empty);
    } else {
        renderItemList(el);
    }
    renderDescBlock(el);
    renderBottomBar(el);
}

// 描述区：固定展示区域，选中道具时显示 desc，未选中为空
function renderDescBlock(el) {
    const desc = document.createElement('div');
    desc.className = 'daily-shop-desc';
    const selected = shopItems.find(i => i.item_id === selectedItemId);
    if (selected) {
        desc.textContent = selected.desc;
    }
    el.appendChild(desc);
}

// 底部：分界线 + 数量设置行 + 购买/返回行
function renderBottomBar(el) {
    const oldBar = el.querySelector('.daily-shop-bottom');
    if (oldBar) oldBar.remove();

    const bar = document.createElement('div');
    bar.className = 'daily-shop-bottom';

    // ---- 第一行：数量设置 ----
    const countRow = document.createElement('div');
    countRow.className = 'daily-shop-countrow';

    const hasSelected = shopItems.some(i => i.item_id === selectedItemId);
    const steps = [-10, -5, -1, 0, 1, 5, 10];
    for (const step of steps) {
        const btn = document.createElement('span');
        if (step === 0) {
            btn.textContent = '设为0';
        } else {
            btn.textContent = (step > 0 ? '+' : '') + step;
        }
        btn.className = 'daily-shop-action' + (hasSelected ? '' : ' disabled');
        if (hasSelected) {
            btn.onclick = function () {
                adjustCount(step);
            };
        }
        countRow.appendChild(btn);
    }
    bar.appendChild(countRow);

    // ---- 分界线 ----
    const divider = document.createElement('div');
    divider.className = 'daily-shop-divider';
    bar.appendChild(divider);

    // ---- 第二行：购买 / 返回 ----
    const actionRow = document.createElement('div');
    actionRow.className = 'daily-shop-actionrow';

    // 购买对象是「所有购买数量>0 的道具」合集，总价为它们的总和
    const entries = shopItems.filter(i => (buyCounts[i.item_id] || 0) > 0);
    const totalPrice = entries.reduce((sum, i) => sum + i.price * buyCounts[i.item_id], 0);
    const canBuy = entries.length > 0 && playerMoney >= totalPrice;
    const buyBtn = document.createElement('span');
    buyBtn.className = 'daily-shop-action' + (canBuy ? '' : ' disabled');
    buyBtn.textContent = '购买';
    if (canBuy) {
        buyBtn.onclick = async function () {
            // 依次购买所有数量>0的道具；中途失败（如资金不足）则提示并停止
            for (const item of shopItems) {
                const count = buyCounts[item.item_id] || 0;
                if (count <= 0) continue;
                const result = await call('item_manager', 'buy_items', item.item_id, count);
                if (result && result[0]) {
                    // 成功：数量清零（道具常驻，不消失）
                    buyCounts[item.item_id] = 0;
                } else {
                    showToast((result && result[1]) || '购买失败');
                    break;
                }
            }
            await refreshMoneyDisplay();
            await loadPlayerMoney();
            renderAll();
        };
    }
    actionRow.appendChild(buyBtn);

    // 总花费提示（有任一数量>0 时展示合计）
    const totalSpan = document.createElement('span');
    totalSpan.className = 'daily-shop-total';
    totalSpan.textContent = entries.length > 0 ? `(总花费：¥${totalPrice})` : '';
    actionRow.appendChild(totalSpan);

    // 返回
    const backBtn = document.createElement('span');
    backBtn.className = 'daily-shop-action';
    backBtn.textContent = '返回';
    backBtn.onclick = closeDailyShop;
    actionRow.appendChild(backBtn);

    bar.appendChild(actionRow);
    el.appendChild(bar);
}

// 调整选中道具的购买数量（不允许负数）
function adjustCount(step) {
    const current = buyCounts[selectedItemId] || 0;
    const next = step === 0 ? 0 : current + step;
    buyCounts[selectedItemId] = Math.max(0, next);
    renderAll();
}

// 关闭商店并刷新游戏界面
function closeDailyShop() {
    const el = document.getElementById('daily_shop_screen');
    el.style.display = 'none';
    el.innerHTML = '';
    selectedItemId = null;
    buyCounts = {};
    if (shopOnClose) shopOnClose();
}

// 购买成功后同步状态栏金钱显示
async function refreshMoneyDisplay() {
    try {
        const state = await getState(null);
        const moneyEl = document.getElementById('money');
        if (moneyEl && state && state.player) {
            moneyEl.textContent = `资金: ${state.player.money}`;
            playerMoney = state.player.money;
        }
    } catch (e) {
        console.error('刷新金钱失败:', e);
    }
}

// 轻提示条：界面内短暂显示消息，不打断操作；支持 [[c:#...]]彩色标记
let toastTimer = null;
export function showToast(msg) {
    let toast = document.getElementById('shop_toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'shop_toast';
        toast.className = 'shop-toast';
        document.body.appendChild(toast);
    }
    // 解析彩色标记（多条消息用全角空格连接），逐段渲染为带色 span
    const text = Array.isArray(msg) ? msg.join('　') : msg;
    toast.innerHTML = '';
    for (const node of parseColoredMessage(text)) {
        const span = document.createElement('span');
        span.textContent = node.text;
        if (node.color) span.style.color = node.color;
        toast.appendChild(span);
    }
    toast.style.display = 'block';
    toast.style.opacity = '1';
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
        toast.style.opacity = '0';
        setTimeout(function () { toast.style.display = 'none'; }, 300);
    }, 2500);
}
