from typing import Dict, List, Optional

import streamlit as st

from .document_manager import DocumentManager
from .image_manager import ImageManager


class SearchEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._init_managers()

    @st.cache_resource
    def _init_managers(_self):
        """初始化管理器（使用Streamlit缓存）"""
        doc_manager = DocumentManager(_self.data_dir)
        img_manager = ImageManager(_self.data_dir)
        return doc_manager, img_manager

    @property
    def doc_manager(self):
        if not hasattr(self, '_managers'):
            self._managers = self._init_managers()
        return self._managers[0]

    @property
    def img_manager(self):
        if not hasattr(self, '_managers'):
            self._managers = self._init_managers()
        return self._managers[1]

    def search_all(self, query: str, search_type: str = "all",
                   category: Optional[str] = None) -> Dict[str, List]:
        """统一搜索接口"""
        results = {
            "documents": [],
            "images": []
        }

        if search_type in ["all", "documents"]:
            results["documents"] = self.doc_manager.search_documents(query, category)

        if search_type in ["all", "images"]:
            results["images"] = self.img_manager.search_images(query, category)

        return results

    def add_document_from_upload(self, uploaded_file, category: str = "general") -> bool:
        """从上传文件添加文档"""
        try:
            # 临时保存上传的文件
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            result = self.doc_manager.add_document(tmp_path, category)

            # 清理临时文件
            import os
            os.unlink(tmp_path)

            return result
        except Exception as e:
            st.error(f"添加文档失败: {e}")
            return False

    def add_image_from_upload(self, uploaded_file, category: str = "general",
                              tags: List[str] = None) -> bool:
        """从上传文件添加图片"""
        return self.img_manager.add_image(uploaded_file, category, tags)

    def get_categories(self, content_type: str = "documents") -> List[str]:
        """获取分类列表"""
        if content_type == "documents":
            return self.doc_manager.get_categories()
        elif content_type == "images":
            return self.img_manager.get_categories()
        return []

    def get_stats(self) -> Dict:
        """获取统计信息"""
        doc_stats = self.doc_manager.get_document_stats()
        img_stats = self.img_manager.get_image_stats()

        return {
            "documents": doc_stats,
            "images": img_stats,
            "total_items": doc_stats["total_files"] + img_stats["total_images"]
        }
