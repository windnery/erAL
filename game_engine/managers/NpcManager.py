from data.data_loader import load_shipgirls
from game_engine.models.shipgirl import ShipGirl

class NpcManager:
    '''NPC管理器类'''
    def __init__(self):
        # 所有舰娘的初始化数据
        self.shipgirls_db = load_shipgirls()
        # 初始化所有舰娘对象
        self.shipgirls = {sg_id: ShipGirl(**sg_data) for sg_id, sg_data in self.shipgirls_db.items()}

    def set_loc(self, shipgirl_id: str, region: str, node: str):
        '''设置舰娘位置'''
        self.shipgirls[shipgirl_id].location = {'region': region, 'node': node}

    def get_npcs_at(self, region: str, node: str):
        '''获取指定位置的NPC列表'''
        return [sg for sg in self.shipgirls.values()
            if sg.location['region'] == region and sg.location['node'] == node]
