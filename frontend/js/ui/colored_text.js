export function parseColoredMessage(text) {
    const nodes = [];
    const marker = /\[\[c:(#[0-9a-fA-F]{6})\]\]([\s\S]*?)\[\[\/c\]\]/g;
    let lastIndex = 0;
    let match;
    while ((match = marker.exec(text)) !== null) {
        if (match.index > lastIndex) {
            nodes.push({ text: text.slice(lastIndex, match.index), color: null });
        }
        nodes.push({ text: match[2], color: match[1] });
        lastIndex = marker.lastIndex;
    }
    if (lastIndex < text.length) {
        nodes.push({ text: text.slice(lastIndex), color: null });
    }
    return nodes;
}