export function renderMessage(messages) {
    const messageElement = document.getElementById('message');
    for (let msg of messages) {
        let p = document.createElement('p');
        p.style.whiteSpace = 'pre-line';
        p.textContent = msg;
        messageElement.appendChild(p);
    }
    // 自动滚动到最新消息
    messageElement.scrollTop = messageElement.scrollHeight;
}