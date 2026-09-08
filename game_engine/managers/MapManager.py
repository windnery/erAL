from typing import Any

from data.data_loader import load_map_meta, load_maps, load_regions
from data.time.time_data import leave_time_data


class MapManager:
    """地图管理器

    地图 = 区域内节点组成的无向连通图：
    - 每个节点通过 links: [{'to': 节点id, 'time': 通行分钟}] 声明邻接边
    - 跨区域通行时间由 leave_time.json（区域×区域矩阵）提供
    - 区域可携带字符画元数据（lines/tokens）供前端渲染 eratw 风格地图
    """

    def __init__(self):
        # 地图库
        self.maps: dict[str, dict[str, dict[str, Any]]] = load_maps()

        # 区域地图
        self.regions: dict[str, dict[str, str]] = load_regions()

        # 字符画元数据
        self.map_meta: dict[str, dict[str, Any]] = load_map_meta()

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
        nodes: list[dict[str, str]] = []
        for link in self.maps[region].get(node, {}).get("links", []):
            to = link["to"]
            if to in self.maps[region]:
                nodes.append(
                    {
                        "key": to,
                        "name": self.maps[region][to]["name"],
                        "time": link["time"],
                    }
                )
        nodes.append({"key": "return", "name": "返回"})  # 添加返回选项
        return nodes

    def get_available_regions(self, region: str):
        """获取可前往的区域"""
        regions: list[dict[str, str]] = []
        for r_id in self.regions:
            if r_id != region:  # 移除当前区域
                regions.append(
                    {
                        "key": r_id,
                        "name": self.regions[r_id]["name"],
                        "time": leave_time_data[region][r_id],
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

    # ==================== 图模型：寻路 ====================

    def _dijkstra(self, region: str, start: str, goal: str):
        """区域内 Dijkstra 最短路：返回 (总耗时, 节点路径)；不可达返回 (None, [])"""
        if start == goal:
            return 0, [start]
        import heapq

        dist = {start: 0}
        prev: dict[str, str] = {}
        pq = [(0, start)]
        visited: set[str] = set()
        while pq:
            d, cur = heapq.heappop(pq)
            if cur == goal:
                break
            if cur in visited:
                continue
            visited.add(cur)
            for link in self.maps[region].get(cur, {}).get("links", []):
                to = link["to"]
                if to not in self.maps[region]:
                    continue
                nd = d + link["time"]
                if nd < dist.get(to, float("inf")):
                    dist[to] = nd
                    prev[to] = cur
                    heapq.heappush(pq, (nd, to))
        if goal not in dist:
            return None, []
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        return dist[goal], list(reversed(path))

    def find_path(self, src_reg: str, src_node: str, dst_reg: str, dst_node: str):
        """跨图寻路：返回 {'total_time': 分钟, 'path': [节点], 'cross_region': bool}；不可达返回 None

        - 同区域：区域内 Dijkstra
        - 跨区域：leave_time（区域间通行）+ 目标区域从入口节点到目标节点的 Dijkstra
        """
        if src_reg == dst_reg:
            total, path = self._dijkstra(src_reg, src_node, dst_node)
            if total is None:
                return None
            return {"total_time": total, "path": path, "cross_region": False}

        leave_minutes = leave_time_data.get(src_reg, {}).get(dst_reg)
        if leave_minutes is None:
            return None
        entry_node = self.regions[dst_reg]["entry_node"]
        if entry_node == dst_node:
            return {
                "total_time": leave_minutes,
                "path": [dst_node],
                "cross_region": True,
            }
        total2, path2 = self._dijkstra(dst_reg, entry_node, dst_node)
        if total2 is None:
            return None
        return {
            "total_time": leave_minutes + total2,
            "path": [entry_node] + path2[1:],
            "cross_region": True,
        }

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
