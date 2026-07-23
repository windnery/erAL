export function renderStatusBar(location, time, player) {
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
}