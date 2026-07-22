export function renderStatusBar(location) {
    const statusBar = document.getElementById('status_bar');
    statusBar.innerHTML = `当前位置: ${location}`;
}