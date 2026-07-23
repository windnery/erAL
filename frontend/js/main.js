import { getState, getCmdOptions, doCmd } from './api.js';
import { renderStatusBar } from './ui/status_bar.js';
import { renderCommands } from './ui/commands.js';
import { renderPortrait, renderCharaPanel } from './ui/chara_panel.js';

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

function selectNpc(npcId) {
    selectedNpcId = npcId;
    // 仅重渲头像高亮、面板与指令区（不从后端重新拉取）
    const npcs = currentNearby;
    renderPortrait(npcs, selectedNpcId, selectNpc);
    renderCharaPanel(npcs, selectedNpcId);
    // 重新过滤并渲染 Act_COM（选中/取消选中会影响NPC交互指令的显示）
    const callbacks = { doCmd, getCmdOptions, refresh, showFullscreenText, showFullscreenOptions, getSelectedNpc: () => selectedNpcId };
    const actCom = selectedNpcId
        ? currentActCom
        : currentActCom.filter(cmd => !cmd.needs_target);
    renderCommands(actCom, 'act', callbacks);
}

// 最近一次拉取到的附近舰娘，供 selectNpc 复用
let currentNearby = [];
// 最近一次拉取到的 Act_COM 原始列表（含 needs_target 指令），供 selectNpc 复用
let currentActCom = [];

async function refresh() {
    const state = await getState();
    currentNearby = state.nearby_npcs || [];
    currentActCom = state.act_com || [];
    // 若选中舰娘已不在附近（离开了），重置选中
    if (selectedNpcId && !currentNearby.some(n => n.id === selectedNpcId)) {
        selectedNpcId = null;
    }
    const callbacks = { doCmd, getCmdOptions, refresh, showFullscreenText, showFullscreenOptions, getSelectedNpc: () => selectedNpcId };
    renderStatusBar(state.location, state.time, state.player);
    // 未选中舰娘时过滤掉需要目标的交互指令
    const actCom = selectedNpcId
        ? state.act_com
        : state.act_com.filter(cmd => !cmd.needs_target);
    renderCommands(actCom, 'act', callbacks);
    renderCommands(state.ex_com, 'ex', callbacks);
    renderPortrait(currentNearby, selectedNpcId, selectNpc);
    renderCharaPanel(currentNearby, selectedNpcId);

    const main_menu = document.getElementById('game_screen');
    main_menu.style.display = 'block';
}

function new_game() {
    document.getElementById('main_menu').style.display = 'none';
    document.getElementById('game_screen').style.display = 'block';
    refresh();
}

function load_game() {
    // TODO: 读档功能
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

// 绑定新游戏和继续游戏按钮的点击事件
document.getElementById('new_game_btn').addEventListener('click', new_game);
document.getElementById('continue_game_btn').addEventListener('click', load_game);