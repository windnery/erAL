export function renderStatusBar(location, time, player) {
    const timeElement = document.getElementById('time');
    const locElement = document.getElementById('loc');
    const moneyElement = document.getElementById('money');
    const playerStatusElement = document.getElementById('player_state');

    timeElement.textContent = `第${time.day}天 ${time.hour}:${String(time.minute).padStart(2, '0')} (${time.period.name})`;
    locElement.textContent = `当前位置: ${location}`;
    moneyElement.textContent = `资金: ${player.money}`;
    playerStatusElement.textContent = `[${player.name}] 体力 ${player.stamina}/${player.max_stamina} 气力 ${player.energy}/${player.max_energy}`;
}