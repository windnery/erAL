import { getState, getCmdOptions, doCmd, getSaveList, doLoad } from './api.js';
import { renderStatusBar } from './ui/status_bar.js';
import { renderCommands } from './ui/commands.js';
import { renderPortrait, renderCharaPanel } from './ui/chara_panel.js';
import { showCharacterInfo } from './ui/chara_info.js';
import { openSkinShop } from './ui/skin_shop.js';

// 当前选中的舰娘 id（前端 UI 态，不进后端）
let selectedNpcId = null;

// 全屏翻页状态
const PAGE_SIZE = 5;
let textPages = [];
let currentPage = 0;

function showFullscreenText(pages) {
    if (pages.length === 0) return;
    textPages = pages;
    currentPage = 0;
    const el = document.getElementById('fullscreen_text');
    const main_menu = document.getElementById('game_screen');
    el.innerHTML = '';
    appendPageGroup(el, 0);
    el.scrollTop = 0;

    main_menu.style.display = 'none';
    el.style.display = 'block';
}

// 全屏选择幕：纯文字选项，悬停变黄，点空白无效（区别于叙事翻页幕）
function showFullscreenOptions(options, onPick) {
    const el = document.getElementById('fullscreen_options');
    const main_menu = document.getElementById('game_screen');
    el.innerHTML = '';

    const prompt = document.createElement('div');
    prompt.className = 'option-prompt';
    prompt.textContent = '请选择：';
    el.appendChild(prompt);

    const list = document.createElement('div');
    list.className = 'option-list';
    for (let option of options) {
        const span = document.createElement('span');
        span.className = 'option-item';
        span.textContent = option.name + (option.time ? ` (${option.time}分钟)` : '');
        span.onclick = function () {
            el.style.display = 'none';
            el.innerHTML = '';
            onPick(option);
        };
        list.appendChild(span);
    }
    el.appendChild(list);

    main_menu.style.display = 'none';
    el.style.display = 'block';
}

function appendPageGroup(el, startIdx) {
    const endIdx = Math.min(startIdx + PAGE_SIZE, textPages.length);
    for (let i = startIdx; i < endIdx; i++) {
        let p = document.createElement('p');
        p.textContent = textPages[i];
        el.appendChild(p);
    }
}

function createPageElement(text) {
    let p = document.createElement('p');
    p.textContent = text;
    return p;
}

async function selectNpc(npcId) {
    if (npcId === selectedNpcId) {
        const npc = currentNearby.find(n => n.id === npcId);
        if (npc) showFullscreenPortrait(npc);
        return;
    }
    selectedNpcId = npcId;
    // 仅重渲头像高亮、面板与指令区（不从后端重新拉取）
    const npcs = currentNearby;
    renderPortrait(npcs, selectedNpcId, selectNpc);
    renderCharaPanel(npcs, selectedNpcId, currentPalamDefs, currentPalamLvMap, currentCflagDefs);
    // 重新请求后端，只获取当前选中 NPC 可执行的指令。
    await refresh();
}

function showCharaInfo(npcId) {
    const npc = currentNearby.find(n => n.id === npcId);
    if (npc) showCharacterInfo(npc, refreshCharacterInfo);
}

// 换装等操作后：重新拉取后端数据更新 currentNearby，并重开角色信息面板
async function refreshCharacterInfo(npcId) {
    const state = await getState(selectedNpcId);
    currentNearby = state.nearby_npcs || [];
    currentActCom = state.act_com || [];
    currentPalamDefs = state.palam_defs || {};
    currentPalamLvMap = state.palam_lv_map || {};
    currentCflagDefs = state.cflag_defs || {};
    // 同步刷新游戏界面（头像选择栏/详情面板），换装后的图片立即生效
    renderPortrait(currentNearby, selectedNpcId, selectNpc);
    renderCharaPanel(currentNearby, selectedNpcId, currentPalamDefs, currentPalamLvMap, currentCflagDefs);
    const npc = currentNearby.find(n => n.id === npcId);
    if (npc) {
        showCharacterInfo(npc, refreshCharacterInfo);
    } else {
        // 舰娘已不在附近：关面板回游戏
        const el = document.getElementById('fullscreen_charinfo');
        el.style.display = 'none';
        el.innerHTML = '';
        document.getElementById('game_screen').style.display = 'block';
    }
}

function showFullscreenPortrait(npc) {
    const el = document.getElementById('fullscreen_portrait');
    // 优先用后端下发的当前穿戴皮肤立绘；无则按约定拼接默认皮肤
    const portraitPath = npc.portrait || `assets/portraits/${npc.name}/${npc.id}_default.webp`;
    el.innerHTML = `<img src="${portraitPath}" alt="${npc.name}">`;
    document.getElementById('game_screen').style.display = 'none';
    el.style.display = 'flex';
}

function hideFullscreenPortrait() {
    document.getElementById('fullscreen_portrait').style.display = 'none';
    document.getElementById('fullscreen_portrait').innerHTML = '';
    const charinfo = document.getElementById('fullscreen_charinfo');
    if (charinfo.style.display !== 'block') {
        document.getElementById('game_screen').style.display = 'block';
    }
}

// 最近一次拉取到的附近舰娘，供 selectNpc 复用
let currentNearby = [];
// 最近一次拉取到的 Act_COM 原始列表（含 needs_target 指令），供 selectNpc 复用
let currentActCom = [];
// palam 名称映射
let currentPalamDefs = {};
// palam 等级阈值映射
let currentPalamLvMap = {};
// cflag 名称映射
let currentCflagDefs = {};

async function refresh() {
    const state = await getState(selectedNpcId);
    currentNearby = state.nearby_npcs || [];
    currentActCom = state.act_com || [];
    currentPalamDefs = state.palam_defs || {};
    currentPalamLvMap = state.palam_lv_map || {};
    currentCflagDefs = state.cflag_defs || {};
    // 若选中舰娘已不在附近（离开了），重置选中
    if (selectedNpcId && !currentNearby.some(n => n.id === selectedNpcId)) {
        selectedNpcId = null;
    }
    const callbacks = { doCmd, getCmdOptions, refresh, showFullscreenText, showFullscreenOptions, getSelectedNpc: () => selectedNpcId, showCharaInfo, openSkinShop };
    renderStatusBar(state.location, state.time, state.player);

    const menu_screen = document.getElementById('menu_screen');
    const main_menu = document.getElementById('game_screen');

    if (state.menu_active) {
        // 缓冲菜单：状态区 + 菜单指令区
        menu_screen.style.display = 'block';
        main_menu.style.display = 'none';
        renderCommands(state.menu_com || [], 'menu', callbacks);
    } else {
        // 正常游戏界面
        menu_screen.style.display = 'none';
        main_menu.style.display = 'block';
        // 后端已按当前选中的舰娘过滤交互指令
        const actCom = state.act_com || [];
        renderCommands(actCom, 'act', callbacks);
        renderCommands(state.ex_com, 'ex', callbacks);
        renderPortrait(currentNearby, selectedNpcId, selectNpc);
        renderCharaPanel(currentNearby, selectedNpcId, currentPalamDefs, currentPalamLvMap, currentCflagDefs);
    }
}

function showStatusBar() {
    document.getElementById('status_bar').style.display = 'block';
}

function new_game() {
    document.getElementById('main_menu').style.display = 'none';
    showStatusBar();
    // 缓冲菜单由 refresh 根据 menu_active 决定显示
    refresh();
}

async function load_game() {
    const slots = await getSaveList();
    const options = slots.map(s => ({
        key: s.slot,
        name: s.has_save
            ? `槽位${s.slot}：第${s.day}天 ${String(s.hour).padStart(2, '0')}:${String(s.minute).padStart(2, '0')} ${s.player_name}`
            : `槽位${s.slot}：空`,
    }));
    showFullscreenOptions(options, async (opt) => {
        const err = await doLoad(opt.key);
        if (err) {
            document.getElementById('fullscreen_options').style.display = 'none';
            showFullscreenText([err]);
            return;
        }
        document.getElementById('fullscreen_options').style.display = 'none';
        document.getElementById('main_menu').style.display = 'none';
        showStatusBar();
        selectedNpcId = null;
        refresh();
    });
}

// WebView初始化完成后刷新一下界面
document.addEventListener('pywebviewready', refresh);

// 全屏文字区点击翻页
document.getElementById('fullscreen_text').addEventListener('click', function() {
    const nextStart = currentPage + PAGE_SIZE;
    if (nextStart < textPages.length) {
        currentPage = nextStart;
        appendPageGroup(this, nextStart);
        this.scrollTop = this.scrollHeight;
    } else {
        this.style.display = 'none';
        this.innerHTML = '';
        refresh();
    }
});

// 全屏立绘点击关闭
document.getElementById('fullscreen_portrait').addEventListener('click', hideFullscreenPortrait);

// 全屏角色信息：不再点击空白关闭，改为底部「返回」按钮（chara_info.js renderCharinfoBottomBar）
// 皮肤立绘点击关闭（回到商店）
document.getElementById('skin_shop_portrait').addEventListener('click', function () {
    this.style.display = 'none';
    this.innerHTML = '';
});

// 绑定新游戏和继续游戏按钮的点击事件
document.getElementById('new_game_btn').addEventListener('click', new_game);
document.getElementById('continue_game_btn').addEventListener('click', load_game);