import uuid
from datetime import datetime

class ImageNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value 
        self.left = None
        self.right = None

class ImageBSTManager:
    def __init__(self):
        self.root = None
        self.size = 0

    def insert(self, key, value):
        if self.root is None:
            self.root = ImageNode(key, value)
        else:
            self._insert_recursive(self.root, key, value)
        self.size += 1

    def _insert_recursive(self, node, key, value):
        if key < node.key:
            if node.left is None:
                node.left = ImageNode(key, value)
            else:
                self._insert_recursive(node.left, key, value)
        elif key > node.key:
            if node.right is None:
                node.right = ImageNode(key, value)
            else:
                self._insert_recursive(node.right, key, value)
        else:
            node.value = value

    def search(self, key):
        return self._search_recursive(self.root, key)

    def _search_recursive(self, node, key):
        if node is None or node.key == key:
            return node.value if node else None
        if key < node.key:
            return self._search_recursive(node.left, key)
        return self._search_recursive(node.right, key)

    def range_query(self, low_key, high_key):
        result = []
        self._range_recursive(self.root, low_key, high_key, result)
        return result

    def _range_recursive(self, node, low, high, result):
        if node is None:
            return
        if low < node.key:
            self._range_recursive(node.left, low, high, result)
        if low <= node.key <= high:
            result.append((node.key, node.value))
        if high > node.key:
            self._range_recursive(node.right, low, high, result)

    def delete(self, key):
        self.root, deleted = self._delete_recursive(self.root, key)
        if deleted:
            self.size -= 1
        return deleted

    def _delete_recursive(self, node, key):
        if node is None:
            return node, False
        deleted = False
        if key < node.key:
            node.left, deleted = self._delete_recursive(node.left, key)
        elif key > node.key:
            node.right, deleted = self._delete_recursive(node.right, key)
        else:
            deleted = True
            if node.left is None:
                return node.right, deleted
            if node.right is None:
                return node.left, deleted
            min_larger_node = self._get_min(node.right)
            node.key, node.value = min_larger_node.key, min_larger_node.value
            node.right, _ = self._delete_recursive(node.right, min_larger_node.key)
        return node, deleted

    def _get_min(self, node):
        while node.left is not None:
            node = node.left
        return node

    def inorder_traversal(self):
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append((node.key, node.value))
            self._inorder_recursive(node.right, result)

