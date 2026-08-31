// 调教面板：参与者头像行 + 目标区（侧别调整与情报入口）

export function renderTrainAvatars(participants, selectedId, onSelect) {
    const el = document.getElementById('charaPortrait');
    el.innerHTML = '';

    const shipgirls = (participants || []).filter(p => !p.is_player);
    if (shipgirls.length === 0) {
        el.textContent = '（本次调教没有其他参与者）';
        return;
    }

    for (let p of shipgirls) {
        const avatar = document.createElement('div');
        avatar.className = 'npc-avatar' + (p.id === selectedId ? ' selected' : '');
        avatar.title = p.name;

        const img = document.createElement('img');
        img.src = p.avatar || `assets/avatars/${p.name}/${p.id}_default.webp`;
        img.alt = p.name;
        img.className = 'npc-avatar-img';
        avatar.appendChild(img);

        const label = document.createElement('div');
        label.className = 'npc-avatar-name';
        label.textContent = p.name;
        avatar.appendChild(label);

        avatar.onclick = () => onSelect(p.id);
        el.appendChild(avatar);
    }
}

export function renderTrainMembers(participants, callbacks) {
    const el = document.getElementById('train_members');
    el.innerHTML = '';

    const divider = document.createElement('div');
    divider.className = 'section-divider';
    const span = document.createElement('span');
    span.className = 'section-label';
    span.textContent = '目标区';
    divider.appendChild(span);
    const line = document.createElement('span');
    line.className = 'section-line';
    divider.appendChild(line);
    el.appendChild(divider);

    for (let p of participants || []) {
        const row = document.createElement('div');
        row.className = 'member-row';

        const name = document.createElement('span');
        name.className = 'member-name';
        name.textContent = p.name;
        row.appendChild(name);

        const initiative = document.createElement('span');
        initiative.className = 'member-initiative';
        initiative.textContent = `主导权:${p.initiative}`;
        row.appendChild(initiative);

        const actorBtn = document.createElement('button');
        actorBtn.className = 'member-btn';
        actorBtn.textContent = p.is_actor ? '[-]' : '[+]';
        actorBtn.title = '调教者';
        actorBtn.onclick = async () => {
            await callbacks.toggleActor(p.id);
            callbacks.refresh();
        };
        row.appendChild(actorBtn);

        const arrow = document.createElement('span');
        arrow.className = 'member-arrow';
        arrow.textContent = '=>';
        row.appendChild(arrow);

        const targetBtn = document.createElement('button');
        targetBtn.className = 'member-btn';
        targetBtn.textContent = p.is_target ? '[-]' : '[+]';
        targetBtn.title = '被调教者';
        targetBtn.onclick = async () => {
            await callbacks.toggleTarget(p.id);
            callbacks.refresh();
        };
        row.appendChild(targetBtn);

        // 情报：玩家暂时没有，只给舰娘
        if (!p.is_player) {
            const infoBtn = document.createElement('button');
            infoBtn.className = 'member-btn member-info';
            infoBtn.textContent = '[情报]';
            infoBtn.onclick = () => callbacks.showCharaInfo(p.id);
            row.appendChild(infoBtn);
        }

        el.appendChild(row);
    }
}

export function renderContinuousStatus(continuousCommands, callbacks) {
    const el = document.getElementById('train_continuous_status');
    if (!el) return;
    el.innerHTML = '';
    if (!continuousCommands || continuousCommands.length === 0) {
        el.style.display = 'none';
        return;
    }
    el.style.display = 'flex';

    for (let cmd of continuousCommands) {
        const item = document.createElement('div');
        item.className = 'continuous-cmd-item';

        const textSpan = document.createElement('span');
        textSpan.className = 'continuous-cmd-text';
        textSpan.textContent = cmd.text;
        item.appendChild(textSpan);

        const cancelBtn = document.createElement('span');
        cancelBtn.className = 'continuous-cmd-cancel';
        cancelBtn.textContent = ' [解除]';
        cancelBtn.title = '解除该持续指令并归还身体部位';
        cancelBtn.onclick = async () => {
            await callbacks.cancelContinuousCmd(cmd.id);
            callbacks.refresh();
        };
        item.appendChild(cancelBtn);

        el.appendChild(item);
    }
}