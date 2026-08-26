import { getState, getCmdOptions, doCmd, getSaveList, doLoad, toggleActor, toggleTarget, chooseOption } from './api.js';
import { renderStatusBar } from './ui/status_bar.js';
import { renderCommands } from './ui/commands.js';
import { renderPortrait, renderCharaPanel } from './ui/chara_panel.js';
import { renderTrainAvatars, renderTrainMembers } from './ui/train_panel.js';
import { showCharacterInfo } from './ui/chara_info.js';
import { openSkinShop } from './ui/skin_shop.js';
import { openDailyShop } from './ui/daily_shop.js';
import { openInventory } from './ui/inventory.js';
import { showPlayerInfo } from './ui/player_info.js';
import { parseColoredMessage } from './ui/colored_text.js';

// 当前选中的舰娘 id（前端 UI 态，不进后端）
let selectedNpcId = null;

// 全屏文字区展示状态：按分区块追加展示
let textBlocks = [];
let currentBlock = 0;

// 将消息数组按空行切成块（空行是分区边界，由后端 result() 生成）
function splitBlocks(pages) {
    const blocks = [];
    let cur = [];
    for (const p of pages) {
        if (p === '') {
            if (cur.length) blocks.push(cur);
            cur = [];
        } else {
            cur.push(p);
        }
    }
    if (cur.length) blocks.push(cur);
    return blocks;
}

// 在全屏文字区追加渲染第 idx 个块的消息
function appendBlock(el, idx) {
    const block = textBlocks[idx];
    if (!block || block.length === 0) return;

    // 非首块追加前插入一个空行分隔
    if (idx > 0) {
        const spacer = document.createElement('p');
        spacer.appendChild(document.createElement('br'));
        el.appendChild(spacer);
    }

    for (const text of block) {
        el.appendChild(createPageElement(text));
    }

    // 本次所有消息都显示完毕后立即在最下方打印分界线
    if (idx === textBlocks.length - 1) {
        const divider = document.createElement('div');
        divider.className = 'fullscreen-divider';
        el.appendChild(divider);
    }

    el.scrollTop = el.scrollHeight;
}

function showFullscreenText(pages) {
    if (pages.length === 0) return;
    textBlocks = splitBlocks(pages);
    currentBlock = 0;
    const el = document.getElementById('fullscreen_text');
    const main_menu = document.getElementById('game_screen');
    el.innerHTML = '';
    appendBlock(el, 0);
    el.scrollTop = 0;

    main_menu.style.display = 'none';
    el.style.display = 'block';
}

// 全屏选择幕：纯文字选项，悬停变黄，点空白无效（区别于叙事翻页幕）
function showFullscreenOptions(options, onPick, promptText = null) {
    const el = document.getElementById('fullscreen_options');
    const main_menu = document.getElementById('game_screen');
    el.innerHTML = '';

    if (promptText) {
        const prompt = document.createElement('div');
        prompt.className = 'option-prompt';
        prompt.textContent = promptText;
        el.appendChild(prompt);
    }

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

function showEventChoice(pendingChoice, callbacks) {
    const options = pendingChoice.options.map(opt => ({
        key: opt.key,
        name: opt.text.startsWith('- ') ? opt.text : `- ${opt.text}`,
        desc: opt.desc
    }));

    showFullscreenOptions(options, async (selectedOpt) => {
        const result = await chooseOption(selectedOpt.key);
        if (result && (typeof result === 'string' || (Array.isArray(result) && result.length > 0))) {
            const pages = Array.isArray(result) ? result : [result];
            showFullscreenText(pages);
        } else {
            refresh();
        }
    }, pendingChoice.title || null);
}

function createPageElement(text) {
    const p = document.createElement('p');
    for (const node of parseColoredMessage(text)) {
        const span = document.createElement('span');
        span.textContent = node.text;
        if (node.color) span.style.color = node.color;
        p.appendChild(span);
    }
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
    refreshAvatarsPanel();
    renderCharaPanel(currentNearby, selectedNpcId, currentPalamDefs, currentPalamLvMap, currentCflagDefs);
    // 重新请求后端，只获取当前选中 NPC 可执行的指令。
    await refresh();
}

// 头像行渲染：按当前模式选择数据源（日常=附近舰娘 / 训练=参与者）
function refreshAvatarsPanel() {
    if (currentTrainMode) {
        renderTrainAvatars(currentTrainParticipants, selectedNpcId, selectNpc);
    } else {
        renderPortrait(currentNearby, selectedNpcId, selectNpc);
    }
}

function showCharaInfo(npcId) {
    const npc = currentNearby.find(n => n.id === npcId);
    if (npc) showCharacterInfo(npc, refreshCharacterInfo, currentAblDefs, currentExpDefs);
}

// 玩家信息面板（纯前端指令 show_player_info 的渲染入口）
function showPlayerInfoPanel() {
    showPlayerInfo(currentPlayer, currentAblDefs, currentExpDefs);
}

// 换装等操作后：重新拉取后端数据更新 currentNearby，并重开角色信息面板
async function refreshCharacterInfo(npcId) {
    const state = await getState(selectedNpcId);
    currentPlayer = state.player || {};
    currentNearby = state.nearby_npcs || [];
    currentActCom = state.act_com || [];
    currentPalamDefs = state.palam_defs || {};
    currentPalamLvMap = state.palam_lv_map || {};
    currentCflagDefs = state.cflag_defs || {};
    currentAblDefs = state.abl_defs || {};
    currentExpDefs = state.exp_defs || {};
    currentTrainMode = state.train_mode || false;
    currentTrainParticipants = state.train_participants || [];
    // 同步刷新游戏界面（头像选择栏/详情面板），换装后的图片立即生效
    refreshAvatarsPanel();
    renderCharaPanel(currentNearby, selectedNpcId, currentPalamDefs, currentPalamLvMap, currentCflagDefs);
    const npc = currentNearby.find(n => n.id === npcId);
    if (npc) {
        showCharacterInfo(npc, refreshCharacterInfo, currentAblDefs, currentExpDefs);
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
// 最近一次拉取到的玩家状态，供 showPlayerInfo 复用
let currentPlayer = {};
// 最近一次拉取到的 Act_COM 原始列表（含 needs_target 指令），供 selectNpc 复用
let currentActCom = [];
// palam 名称映射
let currentPalamDefs = {};
// palam 等级阈值映射
let currentPalamLvMap = {};
// cflag 名称映射
let currentCflagDefs = {};
// abl 名称映射
let currentAblDefs = {};
// exp 名称映射
let currentExpDefs = {};
// 调教模式状态与参与者（训练态渲染数据源）
let currentTrainMode = false;
let currentTrainParticipants = [];

async function refresh() {
    const state = await getState(selectedNpcId);
    currentPlayer = state.player || {};
    currentNearby = state.nearby_npcs || [];
    currentActCom = state.act_com || [];
    currentPalamDefs = state.palam_defs || {};
    currentPalamLvMap = state.palam_lv_map || {};
    currentCflagDefs = state.cflag_defs || {};
    currentAblDefs = state.abl_defs || {};
    currentExpDefs = state.exp_defs || {};
    currentTrainMode = state.train_mode || false;
    currentTrainParticipants = state.train_participants || [];
    // 若选中舰娘已不再可用（训练态看参与者、日常看附近），重置选中
    const validIds = currentTrainMode
        ? currentTrainParticipants.map(p => p.id)
        : currentNearby.map(n => n.id);
    if (selectedNpcId && !validIds.includes(selectedNpcId)) {
        selectedNpcId = null;
    }
    const callbacks = { doCmd, getCmdOptions, refresh, showFullscreenText, showFullscreenOptions, getSelectedNpc: () => selectedNpcId, showCharaInfo, showPlayerInfo: showPlayerInfoPanel, openSkinShop, openDailyShop, openInventory, toggleActor, toggleTarget };
    renderStatusBar(state.location, state.time, state.player);

    // 若有挂起的事件选择，直接展示选项幕
    if (state.pending_choice) {
        showEventChoice(state.pending_choice, callbacks);
        return;
    }

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
        // 训练态布局：头像行 + 调教指令区 + 目标区；日常布局：头像行 + 交互/系统指令区
        document.getElementById('Act_COM').style.display = currentTrainMode ? 'none' : '';
        document.getElementById('Ex_COM').style.display = currentTrainMode ? 'none' : '';
        document.getElementById('TRAIN_COM').style.display = currentTrainMode ? '' : 'none';
        document.getElementById('train_members').style.display = currentTrainMode ? '' : 'none';
        if (currentTrainMode) {
            renderTrainAvatars(currentTrainParticipants, selectedNpcId, selectNpc);
            renderCommands(state.train_com || [], 'train', callbacks);
            renderTrainMembers(currentTrainParticipants, callbacks);
        } else {
            // 后端已按当前选中的舰娘过滤交互指令
            renderCommands(state.act_com || [], 'act', callbacks);
            renderCommands(state.ex_com, 'ex', callbacks);
            renderPortrait(currentNearby, selectedNpcId, selectNpc);
        }
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

// 全屏文字区点击追加：每点一次在同页面追加展示下一个分区块（空行分隔），到底后关闭
document.getElementById('fullscreen_text').addEventListener('click', function() {
    if (currentBlock + 1 < textBlocks.length) {
        currentBlock++;
        appendBlock(this, currentBlock);
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