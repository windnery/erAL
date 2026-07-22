import { getState, getCmdOptions, doCmd } from './api.js';
import { renderStatusBar } from './ui/status_bar.js';
import { renderCommands } from './ui/commands.js';

async function refresh() {
    const state = await getState();
    renderStatusBar(state.location);
    renderCommands(state.commands, { doCmd, getCmdOptions, refresh });
}

function new_game() {
    document.getElementById('main_menu').style.display = 'none';
    document.getElementById('game_screen').style.display = 'block';
    refresh();
}

function load_game() {
    // TODO: 读档功能
}


document.addEventListener('pywebviewready', refresh);

document.getElementById('new_game_btn').addEventListener('click', new_game);
document.getElementById('continue_game_btn').addEventListener('click', load_game);