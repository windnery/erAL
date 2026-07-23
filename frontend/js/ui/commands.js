export function renderCommands(commands, type, callbacks) {
    const actDiv = document.getElementById('Act_COM');
    const exDiv = document.getElementById('Ex_COM');
    let targetDiv, sepText;
    if (type === 'act') {
        targetDiv = actDiv;
        sepText = '=== Act_COM';
    } else {
        targetDiv = exDiv;
        sepText = '=== Ex_COM';
    }
    // 清空后先插入分隔行，再渲染指令
    targetDiv.innerHTML = '';
    const sep = document.createElement('div');
    sep.className = 'com-sep';
    sep.textContent = sepText;
    targetDiv.appendChild(sep);
    for (let cmd of commands) {
        let span = document.createElement('span');
        span.className = 'com-cmd';
        span.textContent = cmd.name;
        span.onclick = async function () {
            // 先判断该指令需要选什么
            let options = await callbacks.getCmdOptions(cmd.key);
            if (options.length > 0) {
                show_options(cmd.key, options, callbacks);
            } else {
                // 如果没有选项，直接执行指令
                let result = await callbacks.doCmd(cmd.key);
                show_text_result(result, callbacks);
            }
        };
        targetDiv.appendChild(span);
    }
}

function show_options(command, options, callbacks) {
    // 改用全屏选择幕，不再使用弹出面板 #cmd_options
    callbacks.showFullscreenOptions(options, async (option) => {
        let result = await callbacks.doCmd(command, option.key);
        show_text_result(result, callbacks);
    });
}

function show_text_result(result, callbacks) {
    if (result === null || result === undefined) {
        // return / 取消 / 无产出：回到游戏画面（否则全屏选择幕已隐藏会留下空白）
        if (callbacks.refresh) callbacks.refresh();
        return;
    }
    if (typeof result === 'string') {
        // 单条消息，包成列表翻页
        callbacks.showFullscreenText([result]);
    } else if (Array.isArray(result)) {
        // 多条消息，逐条翻页
        callbacks.showFullscreenText(result);
    }
}