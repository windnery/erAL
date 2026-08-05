const CAT_ORDER = ['日常', '亲昵', '性骚扰'];
let selectedCategory = CAT_ORDER[0];

function makeCmdSpan(cmd, callbacks) {
    let span = document.createElement('span');
    span.className = 'com-cmd';
    span.textContent = cmd.name;
    span.onclick = async function () {
        if (cmd.needs_target) {
            if (cmd.frontend) {
                callbacks.showCharaInfo(callbacks.getSelectedNpc());
                return;
            }
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

function renderActDivider(allCats, cmdPanel, groups, callbacks) {
    const divider = document.createElement('div');
    divider.className = 'section-divider';

    const prefix = document.createElement('span');
    prefix.className = 'section-label';
    prefix.textContent = 'Act_COM';
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
        if (cat === selectedCategory) {
            catSpan.classList.add('selected');
        }
        catSpan.onclick = function () {
            selectedCategory = cat;
            divider.querySelectorAll('.act-cat-link').forEach(el => {
                el.classList.toggle('selected', el.dataset.cat === selectedCategory);
            });
            cmdPanel.innerHTML = '';
            renderActiveCategory(cmdPanel, groups, callbacks);
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

    const allCats = [
        ...CAT_ORDER,
        ...Object.keys(groups).filter(cat => !CAT_ORDER.includes(cat)),
    ];

    const cmdPanel = document.createElement('div');
    cmdPanel.className = 'act-commands';

    container.appendChild(renderActDivider(allCats, cmdPanel, groups, callbacks));
    container.appendChild(cmdPanel);

    renderActiveCategory(cmdPanel, groups, callbacks);
}

function renderActiveCategory(container, groups, callbacks) {
    const cmds = groups[selectedCategory] || [];
    for (let cmd of cmds) {
        container.appendChild(makeCmdSpan(cmd, callbacks));
    }
}

function renderExCommands(container, commands, callbacks) {
    container.appendChild(renderSectionDivider('Ex_COM'));

    const list = document.createElement('div');
    list.className = 'ex-command-list';
    for (let cmd of commands) {
        list.appendChild(makeCmdSpan(cmd, callbacks));
    }
    container.appendChild(list);
}

function show_options(command, options, callbacks) {
    callbacks.showFullscreenOptions(options, async (option) => {
        let result = await callbacks.doCmd(command, option.key);
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
