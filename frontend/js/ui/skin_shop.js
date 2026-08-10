// 皮肤商店（明石商店）
// 数据源：skin_manager.get_shop_skins() / skin_manager.buy_skin()
// 交互：
//   - 点击卡片 -> 选中（高亮），下方出现「购买」按钮
//   - 选中状态下再次点击同一卡片 -> 弹全屏立绘，点击任意处关闭回商店
//   - 点「购买」 -> 调 buy_skin，成功则移除该卡片并刷新
//   - 点「取消」 -> 关闭商店，refresh 游戏界面

const SHOP_PAGE_SIZE = 10; // 每页展示皮肤数（随游戏进程可增加）

let shopSkins = [];      // 当前商店在售皮肤列表
let shopPage = 0;        // 当前页码
let selectedSkinId = null; // 当前选中的皮肤 id
let shopOnClose = null;  // 关闭回调（由 main.js 注入，用于 refresh）

// 打开商店：拉取未购买皮肤并渲染
// 状态栏保留显示，商店面板从状态栏下方开始（不遮挡状态栏）
export async function openSkinShop(onClose) {
    shopOnClose = onClose || null;
    selectedSkinId = null;
    shopPage = 0;

    const el = document.getElementById('skin_shop_screen');
    const game = document.getElementById('game_screen');
    const statusBar = document.getElementById('status_bar');

    game.style.display = 'none';
    // 商店面板从状态栏底部开始，保证状态栏可见
    const sbHeight = statusBar.offsetHeight || 50;
    el.style.top = sbHeight + 'px';
    el.style.height = 'calc(100% - ' + sbHeight + 'px)';
    el.style.display = 'flex';
    el.innerHTML = '';

    await loadShopSkins();
}

// 拉取商店数据（失败时显示错误信息）
async function loadShopSkins() {
    const el = document.getElementById('skin_shop_screen');
    el.innerHTML = '';

    try {
        shopSkins = await window.pywebview.api.call('skin_manager', 'get_shop_skins');
    } catch (e) {
        console.error('获取皮肤列表失败:', e);
        shopSkins = [];
    }

    if (shopSkins.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'skin-shop-empty';
        empty.textContent = '商店暂时没有可购买的皮肤';
        el.appendChild(empty);
    } else {
        renderSkinGrid(el);
    }

    renderBottomBar(el);
}

// 渲染商品网格（按当前页）
function renderSkinGrid(el) {
    const grid = document.createElement('div');
    grid.className = 'skin-shop-grid';

    const pageStart = shopPage * SHOP_PAGE_SIZE;
    const pageSkins = shopSkins.slice(pageStart, pageStart + SHOP_PAGE_SIZE);

    for (const skin of pageSkins) {
        grid.appendChild(makeSkinCard(skin));
    }
    el.appendChild(grid);
}

// 生成单个皮肤卡片（头像排布：116x116头像 + 居中下方名字/价格）
function makeSkinCard(skin) {
    const card = document.createElement('div');
    card.className = 'skin-card' + (skin.skin_id === selectedSkinId ? ' selected' : '');

    // 头像容器：选中黄框只包围头像（不覆盖下方名称/资金）
    const avatarWrap = document.createElement('div');
    avatarWrap.className = 'skin-card-avatar';

    const img = document.createElement('img');
    img.className = 'skin-card-img';
    img.src = skin.avatar || '';
    img.alt = `${skin.chara_name}-${skin.skin_name}`;
    // 暂无真实图片时显示占位文字（占头像位置，插到最前面）
    img.onerror = function () {
        img.remove();
        const ph = document.createElement('div');
        ph.className = 'skin-card-placeholder';
        ph.textContent = skin.skin_name;
        avatarWrap.prepend(ph);   // 头像位置在 label/price 上方
    };
    avatarWrap.appendChild(img);
    card.appendChild(avatarWrap);

    const label = document.createElement('div');
    label.className = 'skin-card-label';
    label.textContent = `${skin.chara_name}-${skin.skin_name}`;
    card.appendChild(label);

    const price = document.createElement('div');
    price.className = 'skin-card-price';
    price.textContent = `${skin.price} 资金`;
    card.appendChild(price);

    card.onclick = function () {
        if (selectedSkinId === skin.skin_id) {
            // 已选中 -> 弹全屏立绘
            showSkinPortrait(skin);
        } else {
            // 未选中 -> 选中该皮肤
            selectedSkinId = skin.skin_id;
            document.querySelectorAll('.skin-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            renderBottomBar(document.getElementById('skin_shop_screen'));
        }
    };
    return card;
}

// 全屏立绘展示（点击任意处关闭回商店）
function showSkinPortrait(skin) {
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

    const hint = document.createElement('div');
    hint.className = 'skin-portrait-hint';
    hint.textContent = '点击任意位置返回';
    portrait.appendChild(hint);

    portrait.style.display = 'flex';
}

// 渲染底部操作栏（固定窗口最下方）：购买/上一页/下一页/取消，指令样式，上方一条纯横线
// 购买：未选中皮肤时灰色不可用（悬浮不变黄、点击无效）
// 上一页/下一页：总页数<=1 或处于边界时灰色不可用
function renderBottomBar(el) {
    const oldBar = el.querySelector('.skin-shop-bottom');
    if (oldBar) oldBar.remove();

    const bar = document.createElement('div');
    bar.className = 'skin-shop-bottom';

    const totalPages = Math.max(1, Math.ceil(shopSkins.length / SHOP_PAGE_SIZE));

    // 购买（未选中 -> disabled）
    const selected = shopSkins.find(s => s.skin_id === selectedSkinId);
    const buyBtn = document.createElement('span');
    buyBtn.className = 'skin-shop-action' + (selected ? '' : ' disabled');
    buyBtn.textContent = '购买';
    if (selected) {
        buyBtn.onclick = async function () {
            const result = await window.pywebview.api.call('skin_manager', 'buy_skin', selected.skin_id);
            // result: [ok, msg]
            if (result && result[0]) {
                // 成功：关闭商店并刷新游戏界面（金钱条同步）
                closeSkinShop();
            } else {
                // 失败：提示原因，留在商店
                alert((result && result[1]) || '购买失败');
                renderBottomBar(document.getElementById('skin_shop_screen'));
            }
        };
    }
    bar.appendChild(buyBtn);

    // 上一页
    const prevBtn = document.createElement('span');
    prevBtn.className = 'skin-shop-action' + (shopPage === 0 ? ' disabled' : '');
    prevBtn.textContent = '上一页';
    if (shopPage > 0) {
        prevBtn.onclick = function () {
            shopPage--;
            selectedSkinId = null;
            const el = document.getElementById('skin_shop_screen');
            el.innerHTML = '';
            loadShopSkins();
        };
    }
    bar.appendChild(prevBtn);

    // 下一页
    const nextBtn = document.createElement('span');
    nextBtn.className = 'skin-shop-action' + (shopPage >= totalPages - 1 ? ' disabled' : '');
    nextBtn.textContent = '下一页';
    if (shopPage < totalPages - 1) {
        nextBtn.onclick = function () {
            shopPage++;
            selectedSkinId = null;
            const el = document.getElementById('skin_shop_screen');
            el.innerHTML = '';
            loadShopSkins();
        };
    }
    bar.appendChild(nextBtn);

    // 取消
    const cancelBtn = document.createElement('span');
    cancelBtn.className = 'skin-shop-action';
    cancelBtn.textContent = '取消';
    cancelBtn.onclick = closeSkinShop;
    bar.appendChild(cancelBtn);

    el.appendChild(bar);
}

// 关闭商店并刷新游戏界面
function closeSkinShop() {
    const el = document.getElementById('skin_shop_screen');
    el.style.display = 'none';
    el.innerHTML = '';
    selectedSkinId = null;
    if (shopOnClose) shopOnClose();
}
