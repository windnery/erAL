from typing import Any

from config.map_config import MAP_DB
from data.data_loader import load_map_meta, load_regions
from data.time.time_data import LEAVE_TIME_DATA

_INF = int(1e9)


class MapManager:
    """地图管理器

    地图 = 区域内节点组成的无向连通图：
    - 每个节点通过 links: {目标节点id: 通行分钟, ...} 声明邻接边（单字典模式）
    - 跨区域通行时间由 leave_time.json（区域×区域矩阵）提供
    - 区域可携带字符画元数据（lines/tokens）供前端渲染 eratw 风格地图

    启动时构建全局全对最短路表（Floyd）：dist[u][v] 耗时分钟 + nxt[u][v] 路径重建。
    玩家/舰娘寻路统一查表 O(1) 取时耗，无需每次实时计算。
    """

    def __init__(self):
        # 地图库
        self.maps: dict[str, dict[str, dict[str, Any]]] = MAP_DB

        # 区域地图
        self.regions: dict[str, dict[str, str]] = load_regions()

        # 字符画元数据
        self.map_meta: dict[str, dict[str, Any]] = load_map_meta()

        # 全局最短路表（Floyd）
        self._build_all_pairs_shortest_path()

    # ==================== Floyd 全局最短路表 ====================

    def _build_all_pairs_shortest_path(self):
        """构建全局 Floyd 全对最短路表

        - 节点 = (region, node) 复合键（corridor 等节点 id 跨区域重名，必须复合）
        - 区域内部边取各节点 links
        - 区域间边：各区域 entry_node 互连，权重 leave_time[a][b]
        - 产出 self._dist[u][v]（总耗时）/ self._nxt[u][v]（路径下一步节点索引）
        """
        self._nodes: list[tuple[str, str]] = []
        self._node_index: dict[tuple[str, str], int] = {}
        for region, region_nodes in self.maps.items():
            for node in region_nodes:
                self._node_index[(region, node)] = len(self._nodes)
                self._nodes.append((region, node))
        n = len(self._nodes)

        self._dist = [[_INF] * n for _ in range(n)]
        self._nxt: list[list[int | None]] = [[None] * n for _ in range(n)]
        for i in range(n):
            self._dist[i][i] = 0
            self._nxt[i][i] = -1

        # 区域内部边
        for region, region_nodes in self.maps.items():
            for node, node_data in region_nodes.items():
                u = self._node_index[(region, node)]
                for to, cost in node_data.get("links", {}).items():
                    v = self._node_index[(region, to)]
                    if cost < self._dist[u][v]:
                        self._dist[u][v] = cost
                        self._nxt[u][v] = v

        # 区域间边：各区域入口节点双向互连，权重 = leave_time 矩阵
        for a in self.regions:
            for b in self.regions:
                if a == b:
                    continue
                u = self._node_index[(a, self.regions[a]["entry_node"])]
                v = self._node_index[(b, self.regions[b]["entry_node"])]
                cost = LEAVE_TIME_DATA.get(a, {}).get(b)
                if cost is not None and cost < self._dist[u][v]:
                    self._dist[u][v] = cost
                    self._nxt[u][v] = v

        # Floyd 迭代
        for k in range(n):
            dk = self._dist[k]
            for i in range(n):
                via_i = self._dist[i][k]
                if via_i == _INF:
                    continue
                di, ni = self._dist[i], self._nxt[i]
                for j in range(n):
                    nd = via_i + dk[j]
                    if nd < di[j]:
                        di[j] = nd
                        # 路径 i->...->k->...->j：从 i 出发的第一步沿用 i->k 的第一步
                        ni[j] = self._nxt[i][k]

    def get_current_loc(self, character):
        """获取当前位置信息"""
        region_name = self.regions[character.location["region"]]["name"]
        node_name = self.maps[character.location["region"]][character.location["node"]][
            "name"
        ]
        mes = f"{region_name} · {node_name}"

        return mes

    def get_available_nodes(self, region: str, node: str):
        """获取当前区域可前往的节点（图邻接节点）"""
        nodes: list[dict[str, Any]] = []
        for to, cost in self.maps[region].get(node, {}).get("links", {}).items():
            if to in self.maps[region]:
                nodes.append(
                    {
                        "key": to,
                        "name": self.maps[region][to]["name"],
                        "time": cost,
                    }
                )
        nodes.append({"key": "return", "name": "返回"})  # 添加返回选项
        return nodes

    def get_available_regions(self, region: str):
        """获取可前往的区域"""
        regions: list[dict[str, str|int]] = []
        for r_id in self.regions:
            if r_id != region:  # 移除当前区域
                regions.append(
                    {
                        "key": r_id,
                        "name": self.regions[r_id]["name"],
                        "time": LEAVE_TIME_DATA[region][r_id],
                    }
                )
        regions.append({"key": "return", "name": "返回"})  # 添加返回选项
        return regions

    def get_region_name(self, region_id: str):
        """获取区域名称"""
        return self.regions[region_id]["name"]

    def get_node_name(self, region_id: str, node_id: str):
        """获取节点名称"""
        return self.maps[region_id][node_id]["name"]

    @staticmethod
    def is_same_loc(player, sg):
        """判断玩家与舰娘是否在同一位置"""
        return (
            player.location["region"] == sg.location["region"]
            and player.location["node"] == sg.location["node"]
        )

    # ==================== 图模型：寻路（查 Floyd 表） ====================

    def get_travel_time(self, src_reg: str, src_node: str, dst_reg: str, dst_node: str) -> int:
        """获取两点间最短通行总耗时（分钟）"""
        if (src_reg, src_node) == (dst_reg, dst_node):
            return 0
        u = self._node_index[(src_reg, src_node)]
        v = self._node_index[(dst_reg, dst_node)]
        return self._dist[u][v]

    def find_path(
        self, src_reg: str, src_node: str, dst_reg: str, dst_node: str
    ) -> list[dict[str, Any]]:
        """跨图寻路（查全局 Floyd 表）：直接返回带耗时的单步队列 [{'region': r, 'node': n, 'time': t}, ...]

        - 起点与终点相同时返回空列表 []
        - 返回的步骤列表不包含起点自身，第一项即为迈向的下一个节点
        """
        u = self._node_index[(src_reg, src_node)]
        v = self._node_index[(dst_reg, dst_node)]

        if (src_reg, src_node) == (dst_reg, dst_node):
            return []

        # 重建完整节点路径 [(region, node), ...]（含起点）
        node_path = [(src_reg, src_node)]
        cur = u
        while cur != v:
            step = self._nxt[cur][v]
            if step is None or step == cur:
                break  # 防御：表已全连通，正常不会走到
            node_path.append(self._nodes[step])
            cur = step

        # 将节点路径转换为带耗时的单步列表
        steps: list[dict[str, Any]] = []
        for i in range(len(node_path) - 1):
            r1, n1 = node_path[i]
            r2, n2 = node_path[i + 1]
            if r1 == r2:
                cost = self.maps[r1].get(n1, {}).get("links", {}).get(n2, 1)
            else:
                cost = LEAVE_TIME_DATA.get(r1, {}).get(r2, 1)
            steps.append({
                "region": r2,
                "node": n2,
                "time": cost,
            })

        return steps

    # ==================== 字符画地图视图 ====================

    def get_map_view(self, region_id: str):
        """获取区域字符画地图视图（供前端渲染）；无字符画的区域 lines 为空列表"""
        meta = self.map_meta.get(region_id, {})
        lines: list[str] = meta.get("lines", [])
        tokens: dict[str, dict[str, Any]] = {}
        for token, token_meta in meta.get("tokens", {}).items():
            if token_meta.get("exit"):
                tokens[token] = {"exit": True, "label": "离开"}
            elif token_meta.get("node") in self.maps.get(region_id, {}):
                node_id = token_meta["node"]
                tokens[token] = {
                    "node": node_id,
                    "label": self.maps[region_id][node_id]["name"],
                }
            else:
                continue  # 指向不存在节点的记号直接过滤（容忍字符画与数据短暂不同步）
        return {
            "region": region_id,
            "region_name": self.get_region_name(region_id),
            "lines": lines,
            "tokens": tokens,
            "has_art": bool(lines),
        }
