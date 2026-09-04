async function call(manager_name, func_name, ...args) {
    if (window.pywebview?.api?.call) {
        return await window.pywebview.api.call(manager_name, func_name, ...args);
    }

    // Browser development mode fallback via Flask HTTP server
    const response = await fetch('/api/call', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            manager: manager_name,
            func: func_name,
            args: args,
        }),
    });

    if (!response.ok) {
        const errPayload = await response.json().catch(() => ({}));
        throw new Error(errPayload.error || `HTTP ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Unknown backend error');
    }
    return data.result;
}

export async function getState(selectedNpcId = null) {
    return await call('world', 'get_state', selectedNpcId);
}

export async function getMapView(regionId = null) {
    return await call('world', 'get_map_view', regionId);
}

export async function getCmdOptions(cmd) {
    return await call('command_manager', 'get_cmd_options', cmd);
}

export async function doCmd(cmd, option = null) {
    return await call('command_manager', 'do_cmd', cmd, option);
}

export async function toggleActor(id) {
    return await call('train_manager', 'toggle_actor', id);
}

export async function toggleTarget(id) {
    return await call('train_manager', 'toggle_target', id);
}

export async function cancelContinuousCmd(cmdId) {
    return await call('train_manager', 'cancel_continuous_cmd', cmdId);
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

export async function chooseOption(optionKey) {
    return await call('event_manager', 'choose_option', optionKey);
}

export async function getInitialSettingDefs() {
    return await call('setting_manager', 'get_initial_setting_defs');
}

export async function applyInitialSettings(name, maxStamina, maxEnergy) {
    return await call('setting_manager', 'apply_initial_settings', name, maxStamina, maxEnergy);
}

export async function reportFrontendError(error) {
    if (window.pywebview?.api?.report_frontend_error) {
        try {
            await window.pywebview.api.report_frontend_error(
                error.message || 'Unknown frontend error',
                error.source || '',
                error.line || null,
                error.column || null,
                error.stack || '',
            );
            return true;
        } catch (_) {
            // Reporting must never create a second frontend error.
            return false;
        }
    }

    // Browser development mode fallback via Flask HTTP server
    try {
        await fetch('/api/report_error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: error.message || 'Unknown frontend error',
                source: error.source || '',
                line: error.line || null,
                column: error.column || null,
                stack: error.stack || '',
            }),
        });
        return true;
    } catch (_) {
        return false;
    }
}
