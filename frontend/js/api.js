async function call(manager_name, func_name, ...args) {
    return await window.pywebview.api.call(manager_name, func_name, ...args);
}

export async function getState() {
    return await call('world', 'get_state');
}

export async function getCmdOptions(cmd) {
    return await call('command_manager', 'get_cmd_options', cmd);
}

export async function doCmd(cmd, option = null) {
    return await call('command_manager', 'do_cmd', cmd, option);
}