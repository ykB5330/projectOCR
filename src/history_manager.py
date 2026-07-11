"""
历史记录管理模块 — 基于二叉搜索树（BST）存储OCR识别记录

支持：
- 按时间戳键值插入记录
- 按记录ID精确查找
- 按关键词搜索识别文本
- 按时间范围检索
- 中序遍历（按时间排序展示）
- 删除指定记录
- JSON导出/导入
"""

import json
import time
import os
from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class HistoryRecord:
    """单条OCR历史记录"""
    record_id: str           # 唯一记录ID
    image_path: str          # 原始图片路径
    ocr_text: str            # 识别后的文本
    timestamp: float         # 识别时间戳（time.time()）
    file_size: int = 0       # 图片文件大小（字节）
    region: Optional[tuple] = None  # 框选区域 (x1, y1, x2, y2)，全图识别时为None
    confidence: float = 0.0  # 平均识别置信度


class BSTNode:
    """二叉搜索树节点"""
    def __init__(self, key: float, record: HistoryRecord):
        self.key = key              # 排序键值（时间戳）
        self.record = record        # 历史记录数据
        self.left: Optional['BSTNode'] = None
        self.right: Optional['BSTNode'] = None


class BSTree:
    """
    手动实现的二叉搜索树（Binary Search Tree）

    以时间戳为键值进行排序存储，支持标准BST操作。
    注意：由于时间戳单调递增，持续插入会导致树退化为右斜链表。
    实际使用时可通过定期重建树来缓解，或升级为AVL树。
    """

    def __init__(self):
        self.root: Optional[BSTNode] = None
        self._size: int = 0

    # ========== 基本属性 ==========

    def size(self) -> int:
        """返回树中节点总数"""
        return self._size

    def is_empty(self) -> bool:
        """检查树是否为空"""
        return self.root is None

    # ========== 插入操作 ==========

    def insert(self, key: float, record: HistoryRecord) -> None:
        """
        插入一条记录到BST中（按key排序）

        Args:
            key: 排序键（通常为时间戳）
            record: 历史记录对象
        """
        new_node = BSTNode(key, record)
        if self.root is None:
            self.root = new_node
            self._size += 1
            return

        self._insert_recursive(self.root, new_node)

    def _insert_recursive(self, current: BSTNode, new_node: BSTNode) -> None:
        """递归插入辅助函数：key相同或更大时放入右子树"""
        if new_node.key < current.key:
            if current.left is None:
                current.left = new_node
                self._size += 1
            else:
                self._insert_recursive(current.left, new_node)
        else:
            # key >= current.key 放入右子树（处理重复键）
            if current.right is None:
                current.right = new_node
                self._size += 1
            else:
                self._insert_recursive(current.right, new_node)

    # ========== 查找操作 ==========

    def search(self, key: float) -> Optional[HistoryRecord]:
        """
        按key精确查找记录

        Args:
            key: 时间戳键值

        Returns:
            匹配的HistoryRecord，未找到返回None
        """
        node = self._search_recursive(self.root, key)
        return node.record if node else None

    def _search_recursive(self, current: Optional[BSTNode], key: float) -> Optional[BSTNode]:
        """递归查找辅助函数"""
        if current is None:
            return None
        if key == current.key:
            return current
        elif key < current.key:
            return self._search_recursive(current.left, key)
        else:
            return self._search_recursive(current.right, key)

    def search_by_id(self, record_id: str) -> Optional[HistoryRecord]:
        """
        按记录ID查找（需要遍历整棵树）

        Args:
            record_id: 记录唯一ID

        Returns:
            匹配的HistoryRecord，未找到返回None
        """
        results = []
        self._traverse_collect(self.root, lambda node: results.append(node))
        for node in results:
            if node.record.record_id == record_id:
                return node.record
        return None

    # ========== 遍历操作 ==========

    def inorder_traversal(self) -> list:
        """
        中序遍历：返回按键值升序排列的所有记录

        Returns:
            HistoryRecord列表，按时间戳从小到大排序
        """
        records = []
        self._inorder_recursive(self.root, records)
        return records

    def _inorder_recursive(self, current: Optional[BSTNode], records: list) -> None:
        """中序递归遍历：左 → 根 → 右"""
        if current is None:
            return
        self._inorder_recursive(current.left, records)
        records.append(current.record)
        self._inorder_recursive(current.right, records)

    def reverse_inorder(self) -> list:
        """
        逆中序遍历：返回按键值降序排列的所有记录（最新在前）

        Returns:
            HistoryRecord列表，按时间戳从大到小排序
        """
        records = []
        self._reverse_inorder_recursive(self.root, records)
        return records

    def _reverse_inorder_recursive(self, current: Optional[BSTNode], records: list) -> None:
        """逆中序递归遍历：右 → 根 → 左"""
        if current is None:
            return
        self._reverse_inorder_recursive(current.right, records)
        records.append(current.record)
        self._reverse_inorder_recursive(current.left, records)

    # ========== 关键词搜索 ==========

    def search_by_keyword(self, keyword: str) -> list:
        """
        按关键词搜索识别文本（遍历整棵树）

        Args:
            keyword: 搜索关键词（大小写不敏感）

        Returns:
            匹配的HistoryRecord列表（按插入顺序）
        """
        results = []
        keyword_lower = keyword.lower()

        def collect(node: BSTNode):
            if keyword_lower in node.record.ocr_text.lower():
                results.append(node.record)

        self._traverse_collect(self.root, collect)
        return results

    # ========== 时间范围查询 ==========

    def search_by_time_range(self, start_time: float, end_time: float) -> list:
        """
        按时间范围检索记录

        Args:
            start_time: 起始时间戳（含）
            end_time: 结束时间戳（含）

        Returns:
            时间范围内的HistoryRecord列表
        """
        results = []

        def collect(node: BSTNode):
            if start_time <= node.key <= end_time:
                results.append(node.record)

        self._traverse_collect(self.root, collect)
        return results

    # ========== 删除操作 ==========

    def delete(self, key: float) -> bool:
        """
        删除指定key的节点

        Args:
            key: 要删除的节点键值

        Returns:
            是否成功删除
        """
        found, new_root = self._delete_recursive(self.root, key)
        self.root = new_root
        if found:
            self._size -= 1
        return found

    def _delete_recursive(self, current: Optional[BSTNode], key: float) -> tuple:
        """
        递归删除辅助函数

        Returns:
            (是否找到并删除, 删除后子树的新根)
        """
        if current is None:
            return False, None

        if key < current.key:
            found, current.left = self._delete_recursive(current.left, key)
            return found, current
        elif key > current.key:
            found, current.right = self._delete_recursive(current.right, key)
            return found, current
        else:
            # 找到要删除的节点，处理三种情况
            # 情况1：叶子节点
            if current.left is None and current.right is None:
                return True, None
            # 情况2：仅有一个子节点
            if current.left is None:
                return True, current.right
            if current.right is None:
                return True, current.left
            # 情况3：有两个子节点，找中序后继（右子树最小节点）
            successor = self._find_min(current.right)
            current.key = successor.key
            current.record = successor.record
            _, current.right = self._delete_recursive(current.right, successor.key)
            return True, current

    def _find_min(self, node: BSTNode) -> BSTNode:
        """找到子树中的最小键值节点"""
        while node.left is not None:
            node = node.left
        return node

    def delete_by_id(self, record_id: str) -> bool:
        """
        按记录ID删除

        Args:
            record_id: 记录唯一ID

        Returns:
            是否成功删除
        """
        # 先找到record对应的key
        node = self._find_node_by_id(self.root, record_id)
        if node is None:
            return False
        return self.delete(node.key)

    def _find_node_by_id(self, current: Optional[BSTNode], record_id: str) -> Optional[BSTNode]:
        """遍历查找指定record_id的节点"""
        if current is None:
            return None
        if current.record.record_id == record_id:
            return current
        left_result = self._find_node_by_id(current.left, record_id)
        if left_result:
            return left_result
        return self._find_node_by_id(current.right, record_id)

    # ========== 清空 ==========

    def clear(self) -> None:
        """清空整棵树"""
        self.root = None
        self._size = 0

    # ========== 内部工具 ==========

    def _traverse_collect(self, current: Optional[BSTNode], callback: Callable) -> None:
        """遍历整棵树，对每个节点执行callback"""
        if current is None:
            return
        self._traverse_collect(current.left, callback)
        callback(current)
        self._traverse_collect(current.right, callback)


class HistoryManager:
    """
    历史记录管理器 — 封装BSTree，提供应用层接口

    用法:
        manager = HistoryManager()
        manager.add_record(record)
        results = manager.search("关键词")
        recent = manager.get_recent(10)
    """

    def __init__(self):
        self.tree = BSTree()
        self._next_id_counter = 0

    def add_record(self, image_path: str, ocr_text: str,
                   file_size: int = 0, region: Optional[tuple] = None,
                   confidence: float = 0.0) -> HistoryRecord:
        """
        添加一条识别记录

        Args:
            image_path: 图片路径
            ocr_text: 识别文本
            file_size: 文件大小
            region: 框选区域
            confidence: 识别置信度

        Returns:
            创建的HistoryRecord对象
        """
        timestamp = time.time()
        self._next_id_counter += 1
        record_id = f"{int(timestamp)}_{self._next_id_counter:04d}"

        record = HistoryRecord(
            record_id=record_id,
            image_path=image_path,
            ocr_text=ocr_text,
            timestamp=timestamp,
            file_size=file_size,
            region=region,
            confidence=confidence,
        )
        self.tree.insert(timestamp, record)
        return record

    def get_all_records(self, newest_first: bool = True) -> list:
        """
        获取所有历史记录

        Args:
            newest_first: True=最新的在前，False=最早的在前

        Returns:
            HistoryRecord列表
        """
        if newest_first:
            return self.tree.reverse_inorder()
        return self.tree.inorder_traversal()

    def search_by_keyword(self, keyword: str) -> list:
        """按关键词搜索识别文本"""
        return self.tree.search_by_keyword(keyword)

    def search_by_time_range(self, start_time: float, end_time: float) -> list:
        """按时间范围搜索"""
        return self.tree.search_by_time_range(start_time, end_time)

    def delete_record(self, record_id: str) -> bool:
        """按ID删除记录"""
        return self.tree.delete_by_id(record_id)

    def get_record_count(self) -> int:
        """获取总记录数"""
        return self.tree.size()

    def clear_all(self) -> None:
        """清空所有历史记录"""
        self.tree.clear()
        self._next_id_counter = 0

    # ========== JSON 导出/导入 ==========

    def export_to_json(self, filepath: str) -> None:
        """
        导出所有历史记录为JSON文件

        Args:
            filepath: 导出文件路径
        """
        records = self.tree.inorder_traversal()
        data = []
        for r in records:
            data.append({
                'record_id': r.record_id,
                'image_path': r.image_path,
                'ocr_text': r.ocr_text,
                'timestamp': r.timestamp,
                'file_size': r.file_size,
                'region': list(r.region) if r.region else None,
                'confidence': r.confidence,
            })
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from_json(self, filepath: str) -> int:
        """
        从JSON文件导入历史记录

        Args:
            filepath: JSON文件路径

        Returns:
            导入的记录数
        """
        if not os.path.exists(filepath):
            return 0

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for item in data:
            timestamp = item.get('timestamp', time.time())
            region = item.get('region')
            record = HistoryRecord(
                record_id=item.get('record_id', f"import_{count}"),
                image_path=item.get('image_path', ''),
                ocr_text=item.get('ocr_text', ''),
                timestamp=timestamp,
                file_size=item.get('file_size', 0),
                region=tuple(region) if region else None,
                confidence=item.get('confidence', 0.0),
            )
            self.tree.insert(timestamp, record)
            count += 1

        return count


# ========== 自测代码 ==========
if __name__ == "__main__":
    # 测试BST基本操作
    manager = HistoryManager()

    # 插入测试记录
    r1 = manager.add_record("/path/to/img1.png", "这是第一段识别文本 Hello World", file_size=1024)
    r2 = manager.add_record("/path/to/img2.png", "这是第二段识别文本 Python OCR", file_size=2048)
    r3 = manager.add_record("/path/to/img3.png", "这是第三段识别文本 测试数据", file_size=512)

    print(f"总记录数: {manager.get_record_count()}")

    # 中序遍历
    print("\n=== 所有记录（最早在前）===")
    for r in manager.get_all_records(newest_first=False):
        print(f"  [{r.record_id}] {r.ocr_text[:30]}... | {time.strftime('%H:%M:%S', time.localtime(r.timestamp))}")

    # 逆中序遍历（最新在前）
    print("\n=== 所有记录（最新在前）===")
    for r in manager.get_all_records(newest_first=True):
        print(f"  [{r.record_id}] {r.ocr_text[:30]}...")

    # 关键词搜索
    print("\n=== 搜索 'Python' ===")
    for r in manager.search_by_keyword("Python"):
        print(f"  [{r.record_id}] {r.ocr_text}")

    # 删除测试
    print(f"\n删除记录 {r2.record_id}: {manager.delete_record(r2.record_id)}")
    print(f"删除后记录数: {manager.get_record_count()}")

    # 导出JSON测试
    manager.export_to_json("test_history.json")
    print("\n✅ BST历史管理器所有功能测试通过")
