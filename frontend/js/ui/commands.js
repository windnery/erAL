const CAT_ORDER = ['日常', '亲昵', '性骚扰'];
const TRAIN_CAT_ORDER = ['特殊', '爱抚', '亲吻', '侍奉', '身体开发', '道具', 'SM', '羞耻', '精神调教', '温柔系'];
// 每类指令区独立的分类选中态（act 与 train 互不影响）
const selectedCat = { act: CAT_ORDER[0], train: TRAIN_CAT_ORDER[0] };

function makeCmdSpan(cmd, callbacks) {
    let span = document.createElement('span');
    span.className = 'com-cmd';
    span.textContent = cmd.name;
    span.onclick = async function () {
        // 纯前端指令优先（不分 needs_target）
        if (cmd.frontend) {
            if (cmd.key === 'akashi_shop') {
                callbacks.openSkinShop(callbacks.refresh);
                return;
            }
            if (cmd.key === 'shiranui_shop') {
                callbacks.openDailyShop(callbacks.refresh);
                return;
            }
            if (cmd.key === 'items') {
                callbacks.openInventory(callbacks.refresh);
                return;
            }
            if (cmd.needs_target) {
                callbacks.showCharaInfo(callbacks.getSelectedNpc());
                return;
            }
            return;
        }
        if (cmd.needs_target) {
            let result = await callbacks.doCmd(cmd.key, callbacks.getSelectedNpc());
            show_text_result(result, callbacks);
            return;
        }
        let options = await callbacks.getCmdOptions(cmd.key);
        if (options.length > 0) {
            show_options(cmd.key, options, callbacks);
        } else {
            let result = await callbacks.doCmd(cmd.key);
            show_text_result(result, callbacks);
        }
    };
    return span;
}

function renderSectionDivider(label) {
    const divider = document.createElement('div');
    divider.className = 'section-divider';
    const span = document.createElement('span');
    span.className = 'section-label';
    span.textContent = label;
    const line = document.createElement('span');
    line.className = 'section-line';
    divider.appendChild(span);
    divider.appendChild(line);
    return divider;
}

function renderActDivider(allCats, cmdPanel, groups, callbacks, type) {
    const divider = document.createElement('div');
    divider.className = 'section-divider';

    const prefix = document.createElement('span');
    prefix.className = 'section-label';
    prefix.textContent = type === 'train' ? 'TRAIN_COM' : 'Act_COM';
    divider.appendChild(prefix);

    for (let cat of allCats) {
        const sep = document.createElement('span');
        sep.className = 'section-label';
        sep.textContent = '===';
        divider.appendChild(sep);

        const catSpan = document.createElement('span');
        catSpan.className = 'act-cat-link';
        catSpan.textContent = '[' + cat + ']';
        catSpan.dataset.cat = cat;
        if (cat === selectedCat[type]) {
            catSpan.classList.add('selected');
        }
        catSpan.onclick = function () {
            selectedCat[type] = cat;
            divider.querySelectorAll('.act-cat-link').forEach(el => {
                el.classList.toggle('selected', el.dataset.cat === selectedCat[type]);
            });
            cmdPanel.innerHTML = '';
            renderActiveCategory(cmdPanel, groups, callbacks, type);
        };
        divider.appendChild(catSpan);
    }

    const line = document.createElement('span');
    line.className = 'section-line';
    divider.appendChild(line);

    return divider;
}

export function renderCommands(commands, type, callbacks) {
    const actDiv = document.getElementById('Act_COM');
    const exDiv = document.getElementById('Ex_COM');
    const menuDiv = document.getElementById('MENU_COM');
    const trainDiv = document.getElementById('TRAIN_COM');

    if (type === 'act') {
        actDiv.innerHTML = '';
        renderActCommands(actDiv, commands, callbacks, 'act');
    } else if (type === 'train') {
        trainDiv.innerHTML = '';
        renderActCommands(trainDiv, commands, callbacks, 'train');
    } else if (type === 'ex') {
        exDiv.innerHTML = '';
        renderExCommands(exDiv, commands, callbacks, 'Ex_COM');
    } else if (type === 'menu') {
        menuDiv.innerHTML = '';
        renderExCommands(menuDiv, commands, callbacks, '【主菜单】');
    }
}

function renderActCommands(container, commands, callbacks, type) {
    const groups = {};
    for (let cmd of commands) {
        const cat = cmd.cat || (type === 'train' ? TRAIN_CAT_ORDER[0] : '日常');
        (groups[cat] = groups[cat] || []).push(cmd);
    }

    const catOrder = type === 'train' ? TRAIN_CAT_ORDER : CAT_ORDER;
    const allCats = [
        ...catOrder,
        ...Object.keys(groups).filter(cat => !catOrder.includes(cat)),
    ];

    const cmdPanel = document.createElement('div');
    cmdPanel.className = 'act-commands';

    container.appendChild(renderActDivider(allCats, cmdPanel, groups, callbacks, type));
    container.appendChild(cmdPanel);

    renderActiveCategory(cmdPanel, groups, callbacks, type);
}

function renderActiveCategory(container, groups, callbacks, type) {
    const cmds = groups[selectedCat[type]] || [];
    for (let cmd of cmds) {
        container.appendChild(makeCmdSpan(cmd, callbacks));
    }
}

function renderExCommands(container, commands, callbacks, label = 'Ex_COM') {
    container.appendChild(renderSectionDivider(label));

    const list = document.createElement('div');
    list.className = 'ex-command-list';
    for (let cmd of commands) {
        list.appendChild(makeCmdSpan(cmd, callbacks));
    }
    container.appendChild(list);
}

function show_options(command, options, callbacks) {
    callbacks.showFullscreenOptions(options, async (option) => {
        // 若选项带 value（结构化数据），传整个 option；否则回退传 option.key
        let payload = (option && option.value !== undefined) ? option.value : option.key;
        let result = await callbacks.doCmd(command, payload);
        show_text_result(result, callbacks);
    });
}

function show_text_result(result, callbacks) {
    if (result === null || result === undefined || (Array.isArray(result) && result.length === 0)) {
        if (callbacks.refresh) callbacks.refresh();
        return;
    }
    if (typeof result === 'string') {
        callbacks.showFullscreenText([result]);
    } else if (Array.isArray(result)) {
        callbacks.showFullscreenText(result);
    }
}
