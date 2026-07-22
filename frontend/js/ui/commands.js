export function renderCommands(commands, callbacks) {
    const commandsDiv = document.getElementById('commands');
    commandsDiv.innerHTML = ''; // 清空之前的指令按钮
    for (let cmd of commands) {
        let button = document.createElement('button');
        button.textContent = cmd.name;
        button.onclick = async function () {
            // 先判断该指令需要选什么
            let options = await callbacks.getCmdOptions(cmd.key);
            if (options.length > 0) {
                show_options(cmd.key, options, callbacks);
            } else {
                // 如果没有选项，直接执行指令
                await callbacks.doCmd(cmd.key);
                await callbacks.refresh(); // 重新加载游戏数据
            }
        };
        commandsDiv.appendChild(button);
    }
}

function show_options(command, options, callbacks) {
    let optionsDiv = document.getElementById('cmd_options');
    optionsDiv.innerHTML = ''; // 清空之前的选项
    optionsDiv.style.display = 'block'; // 显示选项区域

    for (let option of options) {
        let button = document.createElement('button');
        button.textContent = option.name;
        button.onclick = async function () {
            // 处理选项点击事件
            await callbacks.doCmd(command, option.key);
            optionsDiv.style.display = 'none'; // 隐藏选项区域
            await callbacks.refresh(); // 重新加载游戏数据
        };
        optionsDiv.appendChild(button);
    }
}