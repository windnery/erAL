async function call(manager_name, func_name, ...args) {
    return await window.pywebview.api.call(manager_name, func_name, ...args);
}

export async function getState(selectedNpcId = null) {
    return await call('world', 'get_state', selectedNpcId);
}

export async function getCmdOptions(cmd) {
    return await call('command_manager', 'get_cmd_options', cmd);
}

export async function doCmd(cmd, option = null) {
    return await call('command_manager', 'do_cmd', cmd, option);
}

export async function getSaveList() {
    return await call('save_manager', 'get_save_list');
}

export async function doSave(slot) {
    return await call('save_manager', 'save_game', slot);
}

export async function doLoad(slot) {
    return await call('save_manager', 'load_game', slot);
}