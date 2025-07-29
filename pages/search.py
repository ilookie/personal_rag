import os
from datetime import datetime

import pandas as pd
import streamlit as st

from core.search_engine import SearchEngine

st.set_page_config(page_title="搜索中心", page_icon="🔍", layout="wide")


# 初始化
@st.cache_resource
def get_search_engine():
    return SearchEngine("data")


search_engine = get_search_engine()

st.title("🔍 搜索中心")

# 高级搜索表单
with st.container():
    st.subheader("🎯 高级搜索")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("搜索查询", placeholder="输入关键词进行搜索...")
    with col2:
        search_type = st.selectbox(
            "搜索类型",
            ["all", "documents", "images"],
            format_func=lambda x: {"all": "全部", "documents": "文档", "images": "图片"}[x]
        )
    with col3:
        max_results = st.number_input("最大结果数", min_value=5, max_value=100, value=20)

    # 分类和标签过滤
    col1, col2 = st.columns(2)
    with col1:
        if search_type in ["all", "documents"]:
            doc_categories = ["全部"] + search_engine.get_categories("documents")
            doc_category = st.selectbox("文档分类", doc_categories)
        else:
            doc_category = "全部"

    with col2:
        if search_type in ["all", "images"]:
            img_categories = ["全部"] + search_engine.get_categories("images")
            img_category = st.selectbox("图片分类", img_categories)

            # 标签选择
            all_tags = search_engine.img_manager.get_all_tags()
            selected_tags = st.multiselect("图片标签", all_tags)
        else:
            img_category = "全部"
            selected_tags = []

# 搜索按钮和结果显示
if st.button("🔍 开始搜索", type="primary", use_container_width=True):
    if search_query:
        start_time = datetime.now()

        with st.spinner("搜索中..."):
            # 执行搜索
            category = None
            if search_type == "documents" and doc_category != "全部":
                category = doc_category
            elif search_type == "images" and img_category != "全部":
                category = img_category

            results = search_engine.search_all(search_query, search_type, category)

            # 对图片结果进行标签过滤
            if selected_tags and results["images"]:
                filtered_images = []
                for img in results["images"]:
                    if any(tag.lower() in [t.lower() for t in img["tags"]] for tag in selected_tags):
                        filtered_images.append(img)
                results["images"] = filtered_images

        end_time = datetime.now()
        search_time = (end_time - start_time).total_seconds()

        # 显示搜索统计
        total_results = len(results["documents"]) + len(results["images"])
        st.success(f"搜索完成！找到 {total_results} 个结果 (用时 {search_time:.2f} 秒)")

        if total_results > 0:
            # 结果统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 文档", len(results["documents"]))
            with col2:
                st.metric("🖼️ 图片", len(results["images"]))
            with col3:
                st.metric("⏱️ 搜索时间", f"{search_time:.2f}s")

            # 显示结果
            if results["documents"]:
                st.subheader("📄 文档搜索结果")

                # 创建数据表格
                doc_data = []
                for i, doc in enumerate(results["documents"][:max_results]):
                    doc_data.append({
                        "序号": i + 1,
                        "文件名": doc["file_name"],
                        "分类": doc["category"],
                        "类型": doc["file_type"],
                        "大小": f"{doc.get('file_size', 0) / 1024:.1f} KB",
                        "相关度": f"{doc.get('score', 0):.3f}"
                    })

                if doc_data:
                    df = pd.DataFrame(doc_data)
                    st.dataframe(df, use_container_width=True)

                    # 详细结果展示
                    with st.expander("查看详细内容"):
                        for i, doc in enumerate(results["documents"][:5]):  # 只显示前5个详细内容
                            st.write(f"**{i + 1}. {doc['file_name']}**")
                            st.write(f"分类: {doc['category']} | 类型: {doc['file_type']}")
                            st.write("内容预览:")
                            st.write(doc["content"])
                            st.divider()

            if results["images"]:
                st.subheader("🖼️ 图片搜索结果")

                # 图片显示选项
                col1, col2 = st.columns([3, 1])
                with col1:
                    view_mode = st.radio("显示模式", ["网格视图", "列表视图"], horizontal=True)
                with col2:
                    images_per_row = st.selectbox("每行图片数", [2, 3, 4, 5], index=2)

                if view_mode == "网格视图":
                    # 网格显示
                    images_to_show = results["images"][:max_results]
                    for i in range(0, len(images_to_show), images_per_row):
                        cols = st.columns(images_per_row)
                        for j, col in enumerate(cols):
                            if i + j < len(images_to_show):
                                img_info = images_to_show[i + j]
                                with col:
                                    if os.path.exists(img_info["thumbnail_path"]):
                                        st.image(img_info["thumbnail_path"],
                                                 caption=img_info["original_name"],
                                                 use_container_width=True)

                                    st.write(f"**{img_info['category']}**")
                                    st.write(f"{img_info['width']}×{img_info['height']}")
                                    if img_info["tags"]:
                                        st.write(f"🏷️ {', '.join(img_info['tags'][:3])}")

                else:
                    # 列表显示
                    img_data = []
                    for i, img in enumerate(results["images"][:max_results]):
                        img_data.append({
                            "序号": i + 1,
                            "文件名": img["original_name"],
                            "分类": img["category"],
                            "尺寸": f"{img['width']}×{img['height']}",
                            "大小": f"{img['size'] / 1024:.1f} KB",
                            "格式": img["format"],
                            "标签": ", ".join(img["tags"][:3]) + ("..." if len(img["tags"]) > 3 else "")
                        })

                    if img_data:
                        df = pd.DataFrame(img_data)
                        st.dataframe(df, use_container_width=True)
        else:
            st.warning("未找到匹配的结果，请尝试：")
            st.write("- 使用不同的关键词")
            st.write("- 检查拼写")
            st.write("- 尝试更广泛的搜索词")
            st.write("- 调整分类或标签筛选")
    else:
        st.warning("请输入搜索关键词")

# 搜索历史和建议
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("💡 搜索建议")

    # 热门标签
    all_tags = search_engine.img_manager.get_all_tags()
    if all_tags:
        st.write("**热门标签:**")
        tag_cols = st.columns(3)
        for i, tag in enumerate(all_tags[:9]):
            with tag_cols[i % 3]:
                if st.button(f"#{tag}", key=f"tag_{tag}"):
                    st.session_state.search_suggestion = tag

with col2:
    st.subheader("📊 搜索统计")

    stats = search_engine.get_stats()

    # 简单的使用统计
    st.write("**数据库概况:**")
    st.write(f"- 📄 文档: {stats['documents']['total_files']} 个")
    st.write(f"- 🖼️ 图片: {stats['images']['total_images']} 张")
    st.write(f"- 💾 存储: {(stats['documents']['total_size'] + stats['images']['total_size']) / (1024 * 1024):.1f} MB")

# 处理搜索建议
if 'search_suggestion' in st.session_state:
    st.rerun()
