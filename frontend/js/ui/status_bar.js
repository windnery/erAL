export function renderStatusBar(location, time) {
    const timeElement = document.getElementById('time');
    const locElement = document.getElementById('loc');

    timeElement.textContent = `第${time.day}天 ${time.hour}:${String(time.minute).padStart(2, '0')} (${time.period.name})`;
    locElement.textContent = `当前位置: ${location}`;
}