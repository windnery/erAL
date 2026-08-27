"""测试舰娘扩充数据完整性"""
import os
from pathlib import Path
from data.data_loader import load_shipgirls, load_maps, load_move_time, load_attr_defs
from config.map_config import CAN_SIT_LOC, HAVE_BED_LOC
from world import World

ROOT_DIR = Path(__file__).parent.parent

def test_all_34_shipgirls_loaded():
    """测试全部34位舰娘成功加载"""
    shipgirls = load_shipgirls()
    assert len(shipgirls) == 34, f"期望加载34位舰娘，实际加载了{len(shipgirls)}位"
    
    expected_ids = {
        # 初始6位
        "laffey", "javelin", "Z23", "ayanami", "shiranui", "akashi",
        # 白鹰15位
        "oklahoma", "nevada", "langley", "bogue", "ranger", "omaha", "raleigh",
        "pensacola", "cassin", "downes", "craven", "mccall", "aulick", "foote", "spence",
        # 皇家8位
        "leander", "hermes", "bulldog", "beagle", "cygnet", "comet", "crescent", "foxhound",
        # 铁血3位
        "konigsberg", "karlsruhe", "koln",
        # 重樱2位
        "furutaka", "kako"
    }
    
    assert set(shipgirls.keys()) == expected_ids, f"舰娘ID列表不匹配: {set(shipgirls.keys()) ^ expected_ids}"

def test_shipgirl_locations_and_maps():
    """测试舰娘初始位置在地图中存在且寻路配置有效"""
    shipgirls = load_shipgirls()
    maps = load_maps()
    move_time = load_move_time()
    
    for sg_id, sg in shipgirls.items():
        region = sg["location"]["region"]
        node = sg["location"]["node"]
        
        # 地图区域存在
        assert region in maps, f"舰娘 {sg_id} 的区域 {region} 不在地图中"
        # 节点在对应区域存在
        assert node in maps[region], f"舰娘 {sg_id} 的房间 {node} 不在区域 {region} 的地图中"
        # 寻路配置存在
        assert node in move_time, f"房间 {node} 不在 move_time.json 中"
        assert "corridor" in move_time[node], f"房间 {node} 到走廊无寻路配置"
        assert node in move_time["corridor"], f"走廊到房间 {node} 无寻路配置"
        # map_config 配置存在
        assert node in CAN_SIT_LOC.get(region, []), f"房间 {node} 不在 CAN_SIT_LOC[{region}] 中"
        assert node in HAVE_BED_LOC.get(region, []), f"房间 {node} 不在 HAVE_BED_LOC[{region}] 中"

def test_shipgirl_asset_files_exist():
    """测试所有舰娘的头像和立绘静态资源文件存在"""
    shipgirls = load_shipgirls()
    avatars_dir = ROOT_DIR / "frontend" / "assets" / "avatars"
    portraits_dir = ROOT_DIR / "frontend" / "assets" / "portraits"
    
    for sg_id, sg in shipgirls.items():
        name = sg["name"]
        avatar_path = avatars_dir / name / f"{sg_id}_default.webp"
        portrait_path = portraits_dir / name / f"{sg_id}_default.webp"
        
        assert avatar_path.exists(), f"舰娘 {name}({sg_id}) 头像缺失: {avatar_path}"
        assert portrait_path.exists(), f"舰娘 {name}({sg_id}) 立绘缺失: {portrait_path}"

def test_world_initializes_with_all_shipgirls():
    """测试游戏世界初始化成功加载34位舰娘实体及差异化体力气力（>=1500保底）"""
    world = World()
    assert len(world.npc_manager.shipgirls) == 34
    for sg_id, sg in world.npc_manager.shipgirls.items():
        assert sg.name
        assert sg.base["stamina"] >= 1500 and sg.base["stamina"] == sg.base["max_stamina"], f"{sg.name} 体力低于1500保底"
        assert sg.base["energy"] >= 1500 and sg.base["energy"] == sg.base["max_energy"], f"{sg.name} 气力低于1500保底"
        assert sg.talent.get("relationship") == "0"
        assert "ship_type" in sg.talent
        assert "alignment" in sg.talent
    
    # 验证战列舰体力显著高于驱逐舰
    nevada = world.npc_manager.shipgirls["nevada"]
    cassin = world.npc_manager.shipgirls["cassin"]
    assert nevada.base["max_stamina"] >= 2800
    assert cassin.base["max_stamina"] == 1500

def test_set_secretary_ship_options_metadata():
    """测试设定秘书舰选项包含完整的阵营、舰种、头像与状态元数据"""
    world = World()
    options = world.command_manager.get_cmd_options("set_secretary_ship")
    assert len(options) == 34
    for opt in options:
        assert "id" in opt and "name" in opt and "avatar" in opt
        assert "ship_type" in opt and "alignment" in opt
        assert "is_current" in opt
        assert opt["value"] == {"shipgirl_id": opt["id"]}
