import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.search_engine import SearchEngine
from gui.main_window import MainWindow


def main():
    # 创建数据目录
    os.makedirs("data", exist_ok=True)

    # 初始化搜索引擎
    try:
        search_engine = SearchEngine("data")

        # 创建并运行GUI
        app = MainWindow(search_engine)
        app.run()

    except Exception as e:
        print(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
