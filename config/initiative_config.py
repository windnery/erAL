# 主导权配置
# 增长：每轮所有参与者有基础增长，受快感越多增长越少（下限0）
# 衰减：仅玩家射精与舰娘绝顶时下降

# 每轮基础增长值
INITIATIVE_BASE_GROWTH: int = 10
# 快感压制上限：单轮受到的快感系source之和达到该值时增长归零
INITIATIVE_S_MAX: int = 30000

# 舰娘绝顶主导权衰减率（按最高绝顶等级）
ORGASM_INITIATIVE_RATE_LV: dict[int, float] = {
    1: 0.20,
    2: 0.30,
    3: 0.45,
    4: 0.60,
}

# 绝顶部位数乘数
ORGASM_INITIATIVE_MULT_NUM: dict[int, float] = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 2.5,
    5: 3.0,
}
