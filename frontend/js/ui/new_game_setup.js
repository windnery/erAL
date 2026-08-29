// 开局设置向导面板：EraTW 经典字符终端风格
// 支持设置指挥官姓名、初始最大体力与气力 (1800~2500)

import { getInitialSettingDefs, applyInitialSettings } from '../api.js';

export async function showNewGameSetup(onConfirm, onCancel) {
    const el = document.getElementById('new_game_setup');
    el.innerHTML = '';

    // 获取后端配置默认值与范围
    let defs = {
        default_name: '指挥官',
        stamina_min: 1800,
        stamina_max: 2500,
        default_stamina: 2000,
        energy_min: 1800,
        energy_max: 2500,
        default_energy: 2000,
    };
    try {
        const remoteDefs = await getInitialSettingDefs();
        if (remoteDefs && typeof remoteDefs === 'object') {
            defs = { ...defs, ...remoteDefs };
        }
    } catch (_) {
        // 使用前端本地 fallback
    }

    let currentName = defs.default_name;
    let currentStamina = defs.default_stamina;
    let currentEnergy = defs.default_energy;
    let isEditingName = false;

    function render() {
        el.innerHTML = '';

        const screen = document.createElement('div');
        screen.className = 'era-setup-screen';

        // 顶部提示语
        const header = document.createElement('div');
        header.className = 'era-setup-header';
        header.textContent = '## 指挥官就任登记表 ##';
        header.style.fontSize = '20px';
        header.style.fontWeight = 'bold';
        header.style.color = '#5088e1';
        screen.appendChild(header);

        screen.appendChild(createDivider());

        // 名字设置行
        const nameRow = document.createElement('div');
        nameRow.className = 'era-setup-row';

        if (isEditingName) {
            const promptBox = document.createElement('div');
            promptBox.className = 'era-name-edit-box';

            const promptText = document.createElement('div');
            promptText.className = 'era-prompt-text';
            promptText.textContent = `想要变更的话请输入新的名字。(留空为默认【${defs.default_name}】)`;
            promptBox.appendChild(promptText);

            const inputRow = document.createElement('div');
            inputRow.className = 'era-input-row';

            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'era-text-input';
            input.value = currentName;
            input.maxLength = 20;
            inputRow.appendChild(input);

            const okBtn = document.createElement('span');
            okBtn.className = 'era-button';
            okBtn.textContent = '[确定]';
            okBtn.onclick = () => {
                const val = input.value.trim();
                currentName = val || defs.default_name;
                isEditingName = false;
                render();
            };
            inputRow.appendChild(okBtn);

            const resetBtn = document.createElement('span');
            resetBtn.className = 'era-button';
            resetBtn.textContent = '[恢复默认]';
            resetBtn.onclick = () => {
                currentName = defs.default_name;
                isEditingName = false;
                render();
            };
            inputRow.appendChild(resetBtn);

            const cancelBtn = document.createElement('span');
            cancelBtn.className = 'era-button era-btn-dim';
            cancelBtn.textContent = '[取消]';
            cancelBtn.onclick = () => {
                isEditingName = false;
                render();
            };
            inputRow.appendChild(cancelBtn);

            promptBox.appendChild(inputRow);
            nameRow.appendChild(promptBox);

            setTimeout(() => input.focus(), 10);
        } else {
            const label = document.createElement('span');
            label.textContent = '名字: ';
            nameRow.appendChild(label);

            const val = document.createElement('span');
            val.className = 'era-name-val';
            val.textContent = `${currentName} `;
            nameRow.appendChild(val);

            const changeBtn = document.createElement('span');
            changeBtn.className = 'era-button';
            changeBtn.textContent = '[变更]';
            changeBtn.onclick = () => {
                isEditingName = true;
                render();
            };
            nameRow.appendChild(changeBtn);
        }
        screen.appendChild(nameRow);

        screen.appendChild(createDivider());

        // 3. 体力与气力设置行
        const staRow = createBaseBarRow({
            label: '体力',
            val: currentStamina,
            min: defs.stamina_min,
            max: defs.stamina_max,
            fillColor: '#70c070',
            onStep: (delta) => {
                currentStamina = Math.max(defs.stamina_min, Math.min(defs.stamina_max, currentStamina + delta));
                render();
            }
        });
        screen.appendChild(staRow);

        const eneRow = createBaseBarRow({
            label: '气力',
            val: currentEnergy,
            min: defs.energy_min,
            max: defs.energy_max,
            fillColor: '#7080ea',
            onStep: (delta) => {
                currentEnergy = Math.max(defs.energy_min, Math.min(defs.energy_max, currentEnergy + delta));
                render();
            }
        });
        screen.appendChild(eneRow);

        screen.appendChild(createDivider());

        // 4. 底部操作按钮
        const bottomBox = document.createElement('div');
        bottomBox.className = 'era-bottom-box';

        const finishBtn = document.createElement('div');
        finishBtn.className = 'era-menu-option';
        finishBtn.textContent = '- 设定完毕';
        finishBtn.onclick = async () => {
            finishBtn.style.pointerEvents = 'none';
            finishBtn.textContent = '- 正在进入港区...';

            const finalName = currentName.trim() || defs.default_name;
            const finalStamina = Math.max(defs.stamina_min, Math.min(defs.stamina_max, Number(currentStamina) || defs.default_stamina));
            const finalEnergy = Math.max(defs.energy_min, Math.min(defs.energy_max, Number(currentEnergy) || defs.default_energy));

            try {
                await applyInitialSettings(finalName, finalStamina, finalEnergy);
                el.style.display = 'none';
                el.innerHTML = '';
                if (onConfirm) onConfirm();
            } catch (err) {
                alert('保存开局设置失败：' + (err?.message || err));
                finishBtn.style.pointerEvents = '';
                finishBtn.textContent = '- 设定完毕';
            }
        };
        bottomBox.appendChild(finishBtn);

        const backBtn = document.createElement('div');
        backBtn.className = 'era-menu-option era-btn-dim';
        backBtn.style.marginTop = '8px';
        backBtn.textContent = '- 返回主菜单';
        backBtn.onclick = () => {
            el.style.display = 'none';
            el.innerHTML = '';
            if (onCancel) onCancel();
        };
        bottomBox.appendChild(backBtn);

        screen.appendChild(bottomBox);
        el.appendChild(screen);
        el.style.display = 'block';
    }

    render();
}

function createDivider() {
    const div = document.createElement('div');
    div.className = 'era-drawline';
    return div;
}

function createBaseBarRow({ label, val, min, max, fillColor, onStep }) {
    const row = document.createElement('div');
    row.className = 'era-base-row';

    const lbl = document.createElement('span');
    lbl.className = 'era-base-label';
    lbl.textContent = label;
    row.appendChild(lbl);

    // 进度条轨道
    const track = document.createElement('span');
    track.className = 'era-base-track';

    const fill = document.createElement('span');
    fill.className = 'era-base-fill';
    fill.style.width = '100%';
    fill.style.backgroundColor = fillColor;
    track.appendChild(fill);
    row.appendChild(track);

    // 数值文字 ( 2000/ 2000)
    const valText = document.createElement('span');
    valText.className = 'era-base-val';
    const padVal = String(val).padStart(4, ' ');
    valText.textContent = `( ${padVal}/ ${padVal})`;
    row.appendChild(valText);

    // 步长按钮 [-] [+]
    const canSub = val > min;
    const canAdd = val < max;

    const btnSub = document.createElement('span');
    btnSub.className = 'era-button' + (canSub ? '' : ' disabled');
    btnSub.textContent = '[-]';
    if (canSub) {
        btnSub.onclick = () => onStep(-100);
    }
    row.appendChild(btnSub);

    const btnAdd = document.createElement('span');
    btnAdd.className = 'era-button' + (canAdd ? '' : ' disabled');
    btnAdd.textContent = '[+]';
    if (canAdd) {
        btnAdd.onclick = () => onStep(100);
    }
    row.appendChild(btnAdd);

    return row;
}
