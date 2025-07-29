import os

import pandas as pd
import plotly.express as px
import streamlit as st

from core.search_engine import SearchEngine

# 页面配置
st.set_page_config(
    page_title="个人RAG应用",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .search-box {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)




# 初始化搜索引擎
@st.cache_resource
def init_search_engine():
    return SearchEngine("data")


def main():
    # 初始化
    search_engine = init_search_engine()

    # 页面标题
    st.markdown("<h1 class='main-header'>🔍 个人RAG应用</h1>", unsafe_allow_html=True)

    # 侧边栏
    with st.sidebar:
        st.title("📊 系统概览")

        # 获取统计信息
        stats = search_engine.get_stats()

        # 显示统计卡片
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 文档", stats["documents"]["total_files"])
        with col2:
            st.metric("🖼️ 图片", stats["images"]["total_images"])

        st.metric("📊 总项目", stats["total_items"])

        # 存储空间信息
        total_size = stats["documents"]["total_size"] + stats["images"]["total_size"]
        size_mb = total_size / (1024 * 1024)
        st.metric("💾 存储空间", f"{size_mb:.1f} MB")

        st.divider()

        # 快捷操作
        st.subheader("🚀 快捷操作")
        if st.button("📄 管理文档", use_container_width=True):
            st.switch_page("pages/document.py")
        if st.button("🖼️ 管理图片", use_container_width=True):
            st.switch_page("pages/image.py")
        if st.button("🔍 搜索中心", use_container_width=True):
            st.switch_page("pages/search.py")

    # 主页面内容
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🔍 快速搜索")

        # 搜索表单
        with st.form("quick_search"):
            search_query = st.text_input("输入搜索关键词", placeholder="搜索文档或图片...")
            search_type = st.selectbox("搜索类型", ["all", "documents", "images"],
                                       format_func=lambda x: {"all": "全部", "documents": "文档", "images": "图片"}[x])
            submitted = st.form_submit_button("搜索", use_container_width=True)

        if submitted and search_query:
            with st.spinner("搜索中..."):
                results = search_engine.search_all(search_query, search_type)

                # 显示搜索结果
                if results["documents"] or results["images"]:
                    st.success(f"找到 {len(results['documents'])} 个文档和 {len(results['images'])} 张图片")

                    # 文档结果
                    if results["documents"]:
                        st.subheader("📄 文档结果")
                        for _, doc in enumerate(results["documents"][:3]):  # 只显示前3个
                            with st.expander(f"{doc['file_name']} ({doc['category']})"):
                                st.write(doc["content"])

                    # 图片结果
                    if results["images"]:
                        st.subheader("🖼️ 图片结果")
                        cols = st.columns(3)
                        for i, img in enumerate(results["images"][:6]):  # 只显示前6张
                            with cols[i % 3]:
                                if os.path.exists(img["thumbnail_path"]):
                                    st.image(img["thumbnail_path"], caption=img["original_name"])
                                else:
                                    st.write(f"🖼️ {img['original_name']}")

                    if len(results["documents"]) > 3 or len(results["images"]) > 6:
                        st.info("查看更多结果请前往搜索中心")
                else:
                    st.warning("未找到相关结果")

    with col2:
        st.subheader("📈 数据分析")

        # 文档类型分布
        if stats["documents"]["file_types"]:
            doc_df = pd.DataFrame(list(stats["documents"]["file_types"].items()),
                                  columns=["类型", "数量"])
            fig_doc = px.pie(doc_df, values="数量", names="类型", title="文档类型分布")
            fig_doc.update_layout(height=300)
            st.plotly_chart(fig_doc, use_container_width=True)

        # 图片分类分布
        if stats["images"]["categories"]:
            img_df = pd.DataFrame(list(stats["images"]["categories"].items()),
                                  columns=["分类", "数量"])
            fig_img = px.bar(img_df, x="分类", y="数量", title="图片分类分布")
            fig_img.update_layout(height=300)
            st.plotly_chart(fig_img, use_container_width=True)

        # 热门标签
        if stats["images"]["tags"]:
            popular_tags = sorted(stats["images"]["tags"].items(),
                                  key=lambda x: x[1], reverse=True)[:5]
            st.subheader("🏷️ 热门标签")
            for tag, count in popular_tags:
                st.write(f"**{tag}**: {count}")


if __name__ == "__main__":
    main()
