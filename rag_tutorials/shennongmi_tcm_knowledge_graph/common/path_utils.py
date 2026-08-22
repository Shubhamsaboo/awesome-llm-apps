"""
项目根路径工具模块
==================

提供项目根目录的定位功能，以及基于根目录的相对路径解析功能。

核心功能:
    - _find_project_root(): 自动定位项目根目录
    - get_file_path(): 将相对于项目根目录的路径转换为绝对路径

设计原理:
    通过向上查找包含 pyproject.toml 或 .env 的目录来定位项目根目录，
    而不是简单地使用相对于 __file__ 的固定层级。这种方式更加稳健，
    即使 common/ 包的目录结构发生变化，也能正确找到项目根目录。

与其他模块的关系:
    本模块被 config.py 依赖（用于定位 .env 文件），
    且不依赖 common/ 包内的其他模块，因此可以安全地在包内其他模块之前导入。

典型用法:
    from common.path_utils import get_file_path

    env_path = get_file_path(".env")                 # 项目根目录下的 .env
    data_path = get_file_path("data/herbs.json")     # 项目根目录下的 data/herbs.json
"""

import os


def _find_project_root() -> str:
    """
    向上查找包含 pyproject.toml 或 .env 的目录作为项目根目录。

    从本文件（common/path_utils.py）所在目录开始，逐级向上查找，
    直到找到包含 pyproject.toml 或 .env 的目录。

    查找逻辑:
        1. 从包含此文件的 common/ 目录开始
        2. 检查当前目录是否包含 pyproject.toml 或 .env
        3. 如果找到，返回当前目录路径
        4. 如果未找到，向上一级目录继续查找
        5. 最多向上查找 10 层（防止无限循环）
        6. 如果 10 层内未找到，回退到旧方法：common/ 的上一级目录

    回退机制:
        当项目结构非标准（没有 pyproject.toml 或 .env）时，
        回退到基于 __file__ 的固定层级推算（common/ 的上一级）。

    Returns:
        str: 项目根目录的绝对路径
    """
    # 从 common/ 目录开始（path_utils.py 所在的目录）
    current = os.path.dirname(os.path.abspath(__file__))
    # 最多向上查找 10 层，避免在异常情况下无限循环
    for _ in range(10):
        # 检查当前目录是否包含项目根标记文件
        if os.path.exists(os.path.join(current, "pyproject.toml")) or \
           os.path.exists(os.path.join(current, ".env")):
            return current
        # 向上一级目录
        parent = os.path.dirname(current)
        if parent == current:
            # 已到达文件系统根目录（如 "/"），停止查找
            break
        current = parent
    # 回退：使用 common/ 目录的上一级作为项目根目录
    # 这种方式适用于 common/ 直接位于项目根目录下的标准结构
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# 在模块加载时计算并缓存项目根目录
# root_dir 在整个应用生命周期中保持不变
root_dir = _find_project_root()


def get_file_path(relative_path: str) -> str:
    """
    将相对于项目根目录的相对路径转换为绝对路径。

    所有需要访问项目文件的代码都应使用此函数来构造路径，
    而不是使用基于当前工作目录（CWD）的相对路径或硬编码的绝对路径。
    这样可以确保无论从哪个目录启动应用，文件路径都能正确解析。

    Args:
        relative_path (str): 相对于项目根目录的相对路径。
                             如 ".env"、"data/herbs.json"、
                             "kg_setup/neo4j_embedding_faiss.index"

    Returns:
        str: 拼接后的绝对路径。使用 os.path.join 进行拼接，
             因此传入绝对路径（以 "/" 开头）时会忽略 root_dir。

    Example:
        >>> get_file_path(".env")
        '/Users/xxx/ChineseMedicalProject/.env'

        >>> get_file_path("data/herbs.json")
        '/Users/xxx/ChineseMedicalProject/data/herbs.json'

        >>> get_file_path("/absolute/path")
        '/absolute/path'  # 绝对路径不受 root_dir 影响
    """
    return os.path.join(root_dir, relative_path)


# ============================================================
# 模块自测
# ============================================================

if __name__ == '__main__':
    # 测试路径转换功能
    print(f"项目根目录: {root_dir}")
    print(f".env 文件路径: {get_file_path('.env')}")
