import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
from PIL import ExifTags, Image


class ImageManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.images_dir = os.path.join(data_dir, "images")
        self.thumbnails_dir = os.path.join(data_dir, "thumbnails")
        self.metadata_file = os.path.join(data_dir, "image_metadata.json")

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

        # 加载图片元数据
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """加载图片元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_metadata(self):
        """保存图片元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"保存元数据失败: {e}")

    def _generate_thumbnail(self, image_path: str, thumbnail_size: tuple = (200, 200)) -> str:
        """生成缩略图"""
        try:
            file_name = os.path.basename(image_path)
            name, ext = os.path.splitext(file_name)
            thumbnail_name = f"{name}_thumb{ext}"
            thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_name)

            with Image.open(image_path) as img:
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, optimize=True, quality=85)

            return thumbnail_path
        except Exception as e:
            st.error(f"生成缩略图失败: {e}")
            return image_path

    def _extract_image_info(self, image_path: str) -> Dict:
        """提取图片信息"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode

                # 提取EXIF信息
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value

                return {
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "mode": mode,
                    "exif": exif_data
                }
        except Exception as e:
            st.error(f"提取图片信息失败: {e}")
            return {}

    def add_image(self, uploaded_file, category: str = "general", tags: List[str] = None) -> bool:
        """添加图片（Streamlit版本）"""
        try:
            # 检查文件类型
            if uploaded_file.type not in ["image/jpeg", "image/png", "image/gif", "image/bmp"]:
                st.error(f"不支持的图片格式: {uploaded_file.type}")
                return False

            # 生成唯一文件名
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:8]
            file_name = f"{file_hash}_{uploaded_file.name}"
            dest_path = os.path.join(self.images_dir, file_name)

            # 保存文件
            with open(dest_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # 生成缩略图
            thumbnail_path = self._generate_thumbnail(dest_path)

            # 提取图片信息
            image_info = self._extract_image_info(dest_path)

            # 保存元数据
            self.metadata[file_name] = {
                "original_name": uploaded_file.name,
                "path": dest_path,
                "thumbnail_path": thumbnail_path,
                "category": category,
                "tags": tags or [],
                "upload_time": datetime.now().isoformat(),
                "size": uploaded_file.size,
                **image_info
            }

            self._save_metadata()
            return True

        except Exception as e:
            st.error(f"添加图片失败: {e}")
            return False

    def search_images(self, query: str = "", category: Optional[str] = None,
                      tags: List[str] = None) -> List[Dict]:
        """搜索图片"""
        results = []

        for file_name, metadata in self.metadata.items():
            # 分类过滤
            if category and category != "全部" and metadata["category"] != category:
                continue

            # 标签过滤
            if tags:
                if not any(tag.lower() in [t.lower() for t in metadata["tags"]] for tag in tags):
                    continue

            # 文本搜索（文件名和标签）
            if query:
                search_text = f"{metadata['original_name']} {' '.join(metadata['tags'])}".lower()
                if query.lower() not in search_text:
                    continue

            # 检查文件是否存在
            if not os.path.exists(metadata["path"]):
                continue

            results.append({
                "file_name": file_name,
                "original_name": metadata["original_name"],
                "path": metadata["path"],
                "thumbnail_path": metadata.get("thumbnail_path", metadata["path"]),
                "category": metadata["category"],
                "tags": metadata["tags"],
                "width": metadata.get("width", 0),
                "height": metadata.get("height", 0),
                "size": metadata.get("size", 0),
                "upload_time": metadata.get("upload_time", ""),
                "format": metadata.get("format", "")
            })

        # 按上传时间排序
        results.sort(key=lambda x: x["upload_time"], reverse=True)
        return results

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for metadata in self.metadata.values():
            categories.add(metadata["category"])
        return list(categories) if categories else ["general"]

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for metadata in self.metadata.values():
            tags.update(metadata["tags"])
        return list(tags)

    def get_image_stats(self) -> Dict:
        """获取图片统计信息"""
        stats = {
            "total_images": len(self.metadata),
            "categories": {},
            "formats": {},
            "total_size": 0,
            "tags": {}
        }

        for metadata in self.metadata.values():
            # 分类统计
            category = metadata["category"]
            stats["categories"][category] = stats["categories"].get(category, 0) + 1

            # 格式统计
            format_name = metadata.get("format", "unknown")
            stats["formats"][format_name] = stats["formats"].get(format_name, 0) + 1

            # 大小统计
            stats["total_size"] += metadata.get("size", 0)

            # 标签统计
            for tag in metadata["tags"]:
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1

        return stats

    def delete_image(self, file_name: str) -> bool:
        """删除图片"""
        try:
            if file_name in self.metadata:
                metadata = self.metadata[file_name]

                # 删除原图
                if os.path.exists(metadata["path"]):
                    os.remove(metadata["path"])

                # 删除缩略图
                if "thumbnail_path" in metadata and os.path.exists(metadata["thumbnail_path"]):
                    os.remove(metadata["thumbnail_path"])

                # 删除元数据
                del self.metadata[file_name]
                self._save_metadata()

                return True
            return False
        except Exception as e:
            st.error(f"删除图片失败: {e}")
            return False
