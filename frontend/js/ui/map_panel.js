import { getMapView, doCmd } from '../api.js';

/**
 * 移动指令的双模式入口（由 commands.js 的 move 指令触发）
 * - 有字符画的区域：渲染 eratw 风格 ASCII 地图，点击 [记号] 移动 / [离开] 切换区域
 * - 无字符画的区域：回退到旧版文字列表（地图补全后移除）
 */

export async function openMap(callbacks) {
    const view = await getMapView(null);
    if (!view || !Array.isArray(view.lines) || view.lines.length === 0) {
        // 回退：无字符画的区域沿用旧列表（地图补全后移除）
        const options = await callbacks.getCmdOptions('move');
        callbacks.showFullscreenOptions(options, async (opt) => {
            // 取消：showFullscreenOptions 打开时隐藏了主界面，必须 refresh 恢复，否则空屏
            if (opt.key === 'return') {
                callbacks.refresh();
                return;
            }
            const result = await doCmd('move', opt.key);
            showMoveResult(result, callbacks);
        }, '前往哪里？');
        return;
    }
    renderMap(view, callbacks);
}

function closeMap() {
    const el = document.getElementById('map_screen');
    el.style.display = 'none';
    el.innerHTML = '';
}

function showMoveResult(result, callbacks) {
    closeMap();
    const pages = Array.isArray(result) ? result : (result ? [result] : []);
    if (pages.length > 0) {
        callbacks.showFullscreenText(pages);
    } else if (callbacks.refresh) {
        callbacks.refresh();
    }
}

function renderMap(view, callbacks) {
    const screen = document.getElementById('map_screen');
    screen.innerHTML = '';

    const panel = document.createElement('div');
    panel.className = 'map-panel';

    // 标题栏
    const title = document.createElement('div');
    title.className = 'map-title';
    const regionName = document.createElement('span');
    regionName.className = 'map-region-name';
    regionName.textContent = `【${view.region_name}】`;
    const closeBtn = document.createElement('span');
    closeBtn.className = 'map-close';
    closeBtn.textContent = '[返回]';
    closeBtn.onclick = closeMap;
    title.appendChild(regionName);
    title.appendChild(closeBtn);
    panel.appendChild(title);

    // 字符画主体：逐行扫描，记号包成可点击 span（行内元素天然贴在画上，无需定位）
    const pre = document.createElement('div');
    pre.className = 'map-art';
    for (const line of view.lines) {
        pre.appendChild(renderLine(line, view, callbacks));
    }
    panel.appendChild(pre);

    screen.appendChild(panel);
    screen.style.display = 'flex';
}

const TILE_CLASS_MAP = {
    '■': 'map-tile-wall',       // 实体墙壁
    '▣': 'map-tile-window',     // 窗户
    '▤': 'map-tile-floor',      // 地板
    '┃': 'map-tile-pillar',      // 隔墙立柱
    '╂': 'map-tile-door',        // 门
};

function renderLine(line, view, callbacks) {
    const div = document.createElement('div');
    div.className = 'map-line';
    const tokens = view.tokens || {};
    let i = 0;
    while (i < line.length) {
        // 记号约定：[xxx] 方括号包裹，xxx 为区域 JSON tokens 的键
        if (line[i] === '[') {
            const end = line.indexOf(']', i + 1);
            if (end !== -1) {
                const inner = line.slice(i + 1, end);
                const meta = tokens[inner];
                if (meta) {
                    div.appendChild(makeToken(`[${inner}]`, meta, view, callbacks));
                    i = end + 1;
                    continue;
                }
            }
        }

        const char = line[i];
        const tileClass = TILE_CLASS_MAP[char];

        if (tileClass) {
            // 地图元素：包成 span，便于 CSS 定位和样式（如墙壁、地板等）
            const span = document.createElement('span');
            span.className = `map-tile ${tileClass}`;
            span.textContent = char;
            div.appendChild(span);
        } else {
            // 汉字保持原样
            div.appendChild(document.createTextNode(char));
        }
        i += 1;
    }
    return div;
}

function makeToken(token, meta, view, callbacks) {
    const span = document.createElement('span');
    span.textContent = token;
    span.title = meta.label || '';

    if (meta.exit) {
        // 出口记号：打开区域选择（沿用 leave 指令的选项列表）
        span.className = 'map-token';
        span.onclick = async () => {
            const options = await callbacks.getCmdOptions('leave');
            callbacks.showFullscreenOptions(options, async (opt) => {
                // 取消：主界面被隐藏，必须 refresh 恢复，否则空屏
                if (opt.key === 'return') {
                    callbacks.refresh();
                    return;
                }
                const result = await doCmd('leave', opt.key);
                showMoveResult(result, callbacks);
            }, '离开到哪里？');
        };
        return span;
    }

    span.className = 'map-token';
    // 玩家当前所在节点：高亮且不可点击
    if (view.region === view.current_region && meta.node === view.current_node) {
        span.classList.add('map-token-current');
        return span;
    }
    span.onclick = async () => {
        const result = await doCmd('move', meta.node);
        showMoveResult(result, callbacks);
    };
    return span;
}
