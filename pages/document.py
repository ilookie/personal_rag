import os

import pandas as pd
import streamlit as st

from core.search_engine import SearchEngine

st.set_page_config(page_title="文档管理", page_icon="📄", layout="wide")


# 初始化
@st.cache_resource
def get_search_engine():
    return SearchEngine("data")


search_engine = get_search_engine()

st.title("📄 文档管理")

# 标签页
tab1, tab2, tab3 = st.tabs(["📤 上传文档", "📋 文档列表", "📊 统计信息"])

with tab1:
    st.subheader("上传新文档")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_files = st.file_uploader(
            "选择文档文件",
            type=['txt', 'md', 'pdf', 'docx'],
            accept_multiple_files=True,
            help="支持格式: TXT, MD, PDF, DOCX"
        )

    with col2:
        categories = search_engine.get_categories("documents")
        selected_category = st.selectbox("选择分类", categories)

        # 添加新分类选项
        new_category = st.text_input("或创建新分类")
        if new_category:
            selected_category = new_category

    if uploaded_files:
        if st.button("上传文档", type="primary"):
            success_count = 0
            progress_bar = st.progress(0, "上传中....")
            for i, file in enumerate(uploaded_files):
                if search_engine.add_document_from_upload(file, selected_category):
                    success_count += 1
                progress_bar.progress((i + 1) / len(uploaded_files))

            if success_count > 0:
                st.success(f"成功上传 {success_count} 个文档！")
                st.rerun()
            else:
                st.error("上传失败！")

with tab2:
    st.subheader("文档列表")

    # 搜索和过滤
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("搜索文档", placeholder="输入关键词...")
    with col2:
        filter_category = st.selectbox("筛选分类", ["全部"] + search_engine.get_categories("documents"))
    with col3:
        sort_by = st.selectbox("排序方式", ["名称", "大小", "类型"])

    # 搜索文档
    if search_query or filter_category != "全部":
        category = filter_category if filter_category != "全部" else None
        documents = search_engine.doc_manager.search_documents(search_query or "", category, top_k=50)
    else:
        # 显示所有文档（简化版本）
        documents = []
        docs_dir = search_engine.doc_manager.documents_dir
        if os.path.exists(docs_dir):
            for file_name in os.listdir(docs_dir):
                file_path = os.path.join(docs_dir, file_name)
                if os.path.isfile(file_path):
                    documents.append({
                        "file_name": file_name,
                        "category": "general",
                        "file_type": os.path.splitext(file_name)[1],
                        "file_size": os.path.getsize(file_path),
                        "content": "..."
                    })

    # 显示文档列表
    if documents:
        st.write(f"找到 {len(documents)} 个文档")

        for doc in documents:
            with st.expander(f"📄 {doc['file_name']} ({doc['category']})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write("**内容预览:**")
                    st.write(doc["content"])
                with col2:
                    st.write(f"**类型:** {doc['file_type']}")
                    st.write(f"**大小:** {doc.get('file_size', 0) / 1024:.1f} KB")
                    if st.button("删除", key=f"del_doc_{doc['file_name']}", type="secondary"):
                        # 这里可以添加删除功能
                        st.warning("删除功能待实现")
    else:
        st.info("暂无文档")

with tab3:
    st.subheader("文档统计")

    stats = search_engine.doc_manager.get_document_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总文档数", stats["total_files"])
    with col2:
        st.metric("总大小", f"{stats['total_size'] / (1024 * 1024):.1f} MB")
    with col3:
        st.metric("文件类型", len(stats["file_types"]))

    # 文件类型分布图表
    if stats["file_types"]:
        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame(list(stats["file_types"].items()), columns=["类型", "数量"])
        fig = px.pie(df, values="数量", names="类型", title="文件类型分布")
        st.plotly_chart(fig, use_container_width=True)
