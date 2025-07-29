import hashlib
import os

import streamlit as st


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_hash(file_content):
    """获取文件哈希值"""
    return hashlib.md5(file_content).hexdigest()

def ensure_dir(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

@st.cache_data
def load_css():
    """加载自定义CSS"""
    return """
    <style>
    .stButton > button {
        width: 100%;
    }
    .search-result {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 3px solid #007bff;
    }
    </style>
    """
