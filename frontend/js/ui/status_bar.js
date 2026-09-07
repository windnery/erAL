export function renderStatusBar(location, time, player, cflagDefs) {
    const dayElement = document.getElementById('day');
    const timeElement = document.getElementById('time');
    const periodElement = document.getElementById('period');
    const locElement = document.getElementById('loc');
    const moneyElement = document.getElementById('money');

    dayElement.textContent = `第${time.day}天`;
    timeElement.textContent = `${time.hour}:${String(time.minute).padStart(2, '0')}`;
    periodElement.textContent = `(${time.period.name})`;
    locElement.textContent = `${location}`;
    moneyElement.textContent = `资金: ${player.money}`;

    // 玩家名字
    document.getElementById('player_state').textContent = `[${player.name}]`;

    // 体力条
    const staPct = (player.base.stamina / player.base.max_stamina) * 100;
    document.getElementById('stamina_fill').style.width = staPct + '%';
    document.getElementById('stamina_text').textContent = `${player.base.stamina}/${player.base.max_stamina}`;

    // 气力条
    const enePct = (player.base.energy / player.base.max_energy) * 100;
    document.getElementById('energy_fill').style.width = enePct + '%';
    document.getElementById('energy_text').textContent = `${player.base.energy}/${player.base.max_energy}`;
    // vitality bar
    const vitPct = (player.base.vitality / player.base.max_vitality) * 100;
    document.getElementById('vitality_fill').style.width = vitPct + '%';
    document.getElementById('vitality_text').textContent = player.base.vitality + '/' + player.base.max_vitality;

    // cflag 状态标记（精力条后面）：与舰娘信息面板同规则——
    // 仅显示 true 且 is_shown!==false 的项，按 cflag_defs 映射名字，疲倦红色
    const flagsEl = document.getElementById('player_flags');
    flagsEl.innerHTML = '';
    const flags = Object.entries(player.cflag || {})
        .filter(([k, v]) => {
            if (v !== true) return false;
            const def = cflagDefs && cflagDefs[k];
            return !(def && typeof def === 'object' && def.is_shown === false);
        })
        .map(([k]) => {
            const def = cflagDefs && cflagDefs[k];
            if (def && typeof def === 'object') {
                return def.name || k;
            }
            return def || k;
        });
    const flagColors = { '疲倦': '#ff4d4f' };
    for (const f of flags) {
        const flagSpan = document.createElement('span');
        if (flagColors[f]) {
            flagSpan.style.color = flagColors[f];
        }
        flagSpan.textContent = ` [${f}]`;
        flagsEl.appendChild(flagSpan);
    }
}