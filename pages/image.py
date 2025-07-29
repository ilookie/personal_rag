import os

import pandas as pd
import streamlit as st

from core.search_engine import SearchEngine

st.set_page_config(page_title="图片管理", page_icon="🖼️", layout="wide")


# 初始化
@st.cache_resource
def get_search_engine():
    return SearchEngine("data")


search_engine = get_search_engine()

st.title("🖼️ 图片管理")

# 标签页
tab1, tab2, tab3 = st.tabs(["📤 上传图片", "🖼️ 图片库", "📊 统计信息"])

with tab1:
    st.subheader("上传新图片")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_files = st.file_uploader(
            "选择图片文件",
            type=['jpg', 'jpeg', 'png', 'gif', 'bmp'],
            accept_multiple_files=True,
            help="支持格式: JPG, PNG, GIF, BMP"
        )

    with col2:
        categories = search_engine.get_categories("images")
        selected_category = st.selectbox("选择分类", categories)

        # 添加新分类选项
        new_category = st.text_input("或创建新分类")
        if new_category:
            selected_category = new_category

        # 标签输入
        tags_input = st.text_input("标签 (用逗号分隔)", placeholder="风景, 旅行, 美食")
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

    if uploaded_files:
        if st.button("上传图片", type="primary"):
            success_count = 0
            progress_bar = st.progress(0, text="上传中...")
            for i, file in enumerate(uploaded_files):
                if search_engine.add_image_from_upload(file, selected_category, tags):
                    success_count += 1
                progress_bar.progress((i + 1) / len(uploaded_files))
            if success_count > 0:
                st.success(f"成功上传 {success_count} 张图片！")
                st.rerun()
            else:
                st.error("上传失败！")

with tab2:
    st.subheader("图片库")

    # 搜索和过滤控件
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search_query = st.text_input("搜索图片", placeholder="输入关键词...")
    with col2:
        filter_category = st.selectbox("筛选分类", ["全部"] + search_engine.get_categories("images"))
    with col3:
        all_tags = search_engine.img_manager.get_all_tags()
        filter_tags = st.multiselect("筛选标签", all_tags)
    with col4:
        images_per_row = st.selectbox("每行图片数", [2, 3, 4, 5], index=2)

    # 搜索图片
    category = filter_category if filter_category != "全部" else None
    images = search_engine.img_manager.search_images(search_query, category, filter_tags)

    # 显示图片
    if images:
        st.write(f"找到 {len(images)} 张图片")

        # 分页显示
        items_per_page = images_per_row * 4  # 4行
        page = st.selectbox("页面", range(1, (len(images) - 1) // items_per_page + 2))
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_images = images[start_idx:end_idx]

        # 创建图片网格
        for i in range(0, len(page_images), images_per_row):
            cols = st.columns(images_per_row)
            for j, col in enumerate(cols):
                if i + j < len(page_images):
                    img_info = page_images[i + j]
                    with col:
                        # 显示图片
                        if os.path.exists(img_info["thumbnail_path"]):
                            st.image(img_info["thumbnail_path"],
                                     caption=img_info["original_name"],
                                     use_container_width=True)
                        else:
                            st.write(f"🖼️ {img_info['original_name']}")

                        # 图片信息
                        with st.expander("详细信息"):
                            st.write(f"**分类:** {img_info['category']}")
                            st.write(f"**尺寸:** {img_info['width']}x{img_info['height']}")
                            st.write(f"**大小:** {img_info['size'] / 1024:.1f} KB")
                            st.write(f"**标签:** {', '.join(img_info['tags'])}")

                            if st.button("删除", key=f"del_img_{img_info['file_name']}", type="secondary"):
                                if search_engine.img_manager.delete_image(img_info['file_name']):
                                    st.success("删除成功！")
                                    st.rerun()
                                else:
                                    st.error("删除失败！")
    else:
        st.info("暂无图片")

with tab3:
    st.subheader("图片统计")

    stats = search_engine.img_manager.get_image_stats()

    # 基础统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总图片数", stats["total_images"])
    with col2:
        st.metric("总大小", f"{stats['total_size'] / (1024 * 1024):.1f} MB")
    with col3:
        st.metric("分类数", len(stats["categories"]))
    with col4:
        st.metric("标签数", len(stats["tags"]))

    # 图表
    if stats["categories"] or stats["formats"]:
        col1, col2 = st.columns(2)

        # 分类分布
        if stats["categories"]:
            with col1:
                import plotly.express as px

                df_cat = pd.DataFrame(list(stats["categories"].items()), columns=["分类", "数量"])
                fig_cat = px.pie(df_cat, values="数量", names="分类", title="分类分布")
                st.plotly_chart(fig_cat, use_container_width=True)

        # 格式分布
        if stats["formats"]:
            with col2:
                df_fmt = pd.DataFrame(list(stats["formats"].items()), columns=["格式", "数量"])
                fig_fmt = px.bar(df_fmt, x="格式", y="数量", title="格式分布")
                st.plotly_chart(fig_fmt, use_container_width=True)

    # 热门标签
    if stats["tags"]:
        st.subheader("🏷️ 标签统计")
        popular_tags = sorted(stats["tags"].items(), key=lambda x: x[1], reverse=True)[:10]

        col1, col2 = st.columns([2, 1])
        with col1:
            tag_df = pd.DataFrame(popular_tags, columns=["标签", "使用次数"])
            fig_tags = px.bar(tag_df, x="标签", y="使用次数", title="热门标签 (前10)")
            st.plotly_chart(fig_tags, use_container_width=True)

        with col2:
            st.write("**标签排行:**")
            for i, (tag, count) in enumerate(popular_tags[:5], 1):
                st.write(f"{i}. **{tag}**: {count}次")
