// 分类展示顺序（act 面板按此顺序分组；空分类不显示标题）
const CAT_ORDER = ['日常', '亲昵', '性骚扰'];
const expandedCategories = new Set();

function makeCmdSpan(cmd, callbacks) {
    let span = document.createElement('span');
    span.className = 'com-cmd';
    span.textContent = cmd.name;
    span.onclick = async function () {
        // 需要目标的指令（NPC交互），直接传入选中的舰娘id
        if (cmd.needs_target) {
            if (cmd.frontend) {
                callbacks.showCharaInfo(callbacks.getSelectedNpc());
                return;
            }
            let result = await callbacks.doCmd(cmd.key, callbacks.getSelectedNpc());
            show_text_result(result, callbacks);
            return;
        }
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
    return span;
}

export function renderCommands(commands, type, callbacks) {
    const actDiv = document.getElementById('Act_COM');
    const exDiv = document.getElementById('Ex_COM');

    if (type === 'act') {
        actDiv.innerHTML = '';
        renderActCommands(actDiv, commands, callbacks);
    } else {
        exDiv.innerHTML = '';
        renderExCommands(exDiv, commands, callbacks);
    }
}

function renderActCommands(container, commands, callbacks) {
    const groups = {};
    for (let cmd of commands) {
        const cat = cmd.cat || '日常';
        (groups[cat] = groups[cat] || []).push(cmd);
    }

    const categories = [
        ...CAT_ORDER,
        ...Object.keys(groups).filter(cat => !CAT_ORDER.includes(cat)),
    ];

    const actBlock = document.createElement('div');
    actBlock.className = 'act-com-block';

    for (let cat of categories) {
        if (!groups[cat]) continue;

        const section = document.createElement('section');
        section.id = `Act_COM-${cat}`;
        section.className = 'act-command-group';
        section.dataset.category = cat;

        const title = document.createElement('button');
        title.type = 'button';
        title.className = 'com-cat';
        title.textContent = `【${cat}】`;
        title.setAttribute('aria-controls', `${section.id}-commands`);

        const commandList = document.createElement('div');
        commandList.id = `${section.id}-commands`;
        commandList.className = 'com-cat-commands';

        for (let cmd of groups[cat]) {
            commandList.appendChild(makeCmdSpan(cmd, callbacks));
        }

        const expanded = expandedCategories.has(cat);
        commandList.hidden = !expanded;
        title.setAttribute('aria-expanded', String(expanded));
        title.onclick = function () {
            const nextExpanded = !expandedCategories.has(cat);
            if (nextExpanded) {
                expandedCategories.add(cat);
            } else {
                expandedCategories.delete(cat);
            }
            commandList.hidden = !nextExpanded;
            title.setAttribute('aria-expanded', String(nextExpanded));
        };

        section.appendChild(title);
        section.appendChild(commandList);
        actBlock.appendChild(section);
    }
    container.appendChild(actBlock);
}

function renderExCommands(container, commands, callbacks) {
    const list = document.createElement('div');
    list.className = 'ex-command-list';
    for (let cmd of commands) {
        list.appendChild(makeCmdSpan(cmd, callbacks));
    }
    container.appendChild(list);
}

function appendCommandDivider(container) {
    const divider = document.createElement('div');
    divider.className = 'command-divider';
    divider.setAttribute('aria-hidden', 'true');
    container.appendChild(divider);
}
function show_options(command, options, callbacks) {
    // 改用全屏选择幕，不再使用弹出面板 #cmd_options
    callbacks.showFullscreenOptions(options, async (option) => {
        let result = await callbacks.doCmd(command, option.key);
        show_text_result(result, callbacks);
    });
}

function show_text_result(result, callbacks) {
    // null / undefined / 空列表 都视为无产出（如 move 返回 []），需回到游戏画面避免空白
    if (result === null || result === undefined || (Array.isArray(result) && result.length === 0)) {
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