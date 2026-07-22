function new_game() {
    document.getElementById('main_menu').style.display = 'none';
    document.getElementById('game_screen').style.display = 'block';
    load_game_data();
}

function load_game() {
    // TODO: 读档功能待补充
}

document.addEventListener('pywebviewready', async function () {
    // 页面加载完成后执行的代码
    await load_game_data();
});

async function get_current_loc() {
    let loc_mes = await window.pywebview.api.get_current_loc();
    document.getElementById('loc_mes').textContent = loc_mes;
}

async function get_commands() {
    let commands = await window.pywebview.api.get_commands();
    let commandsDiv = document.getElementById('commands');
    commandsDiv.innerHTML = ''; // 清空之前的指令按钮
    for (let cmd of commands) {
        let button = document.createElement('button');
        button.textContent = cmd.name;
        button.onclick = async function () {
            // 先判断该指令需要选什么
            let options = await window.pywebview.api.get_cmd_options(cmd.key);
            if (options.length > 0) {
                show_options(cmd.key, options);
            } else {
                // 如果没有选项，直接执行指令
                await window.pywebview.api.do_cmd(cmd.key);
                await load_game_data(); // 重新加载游戏数据
            }
        };
        commandsDiv.appendChild(button);
    }
}

function show_options(command, options) {
    let optionsDiv = document.getElementById('cmd_options');
    optionsDiv.innerHTML = ''; // 清空之前的选项
    optionsDiv.style.display = 'block'; // 显示选项区域

    for (let option of options) {
        let button = document.createElement('button');
        button.textContent = option.name;
        button.onclick = async function () {
            // 处理选项点击事件
            await window.pywebview.api.do_cmd(command, option.key);
            optionsDiv.style.display = 'none'; // 隐藏选项区域
            await load_game_data(); // 重新加载游戏数据
        };
        optionsDiv.appendChild(button);
    }
}


async function load_game_data() {
    // 加载数据
    await get_current_loc();
    await get_commands();
}