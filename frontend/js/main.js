import { getState, getCmdOptions, doCmd } from './api.js';
import { renderStatusBar } from './ui/status_bar.js';
import { renderCommands } from './ui/commands.js';

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

async function refresh() {
    const state = await getState();
    const callbacks = { doCmd, getCmdOptions, refresh, showFullscreenText, showFullscreenOptions };
    renderStatusBar(state.location, state.time, state.player);
    renderCommands(state.act_com, 'act', callbacks);
    renderCommands(state.ex_com, 'ex', callbacks);

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