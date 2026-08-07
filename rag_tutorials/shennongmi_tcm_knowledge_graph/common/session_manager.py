"""
会话管理器 — 持久化多会话管理
=============================

提供完整的多会话生命周期管理功能，支持会话的创建、删除、重命名、切换，
以及消息的持久化存储。所有数据以 JSON 格式存储在磁盘上，服务重启后数据不丢失。

功能:
    - 创建新会话（默认名称为「新会话」，后续可自动命名）
    - 删除会话（同时清理索引和消息文件）
    - 重命名会话
    - 切换当前会话（配合 Streamlit session_state 使用）
    - 消息持久化（每个会话独立存储，避免单文件过大）
    - 生成内容管理（支持保存/清除/读取小红书等生成内容）
    - 自动命名（用第一条用户消息截取前 20 字符作为会话名）

设计:
    - 会话数据存储在项目根目录的 sessions/ 目录下
    - sessions/sessions_index.json 存储会话索引（元数据列表，轻量快速）
    - 每个会话的消息存储在独立的 {session_id}.json 文件中（避免单文件过大，
      且方便单个会话的读写操作）
    - SessionManager 所有方法均为 classmethod，无需实例化即可使用
    - 时间戳使用中国时区（UTC+8）

数据文件结构:
    sessions/
    ├── sessions_index.json      # 会话索引 [{"id": "...", "name": "...", ...}, ...]
    ├── a1b2c3d4e5f6.json       # 会话 a1b2... 的消息列表
    ├── 1a2b3c4d5e6f.json       # 会话 1a2b... 的消息列表
    └── ...

消息格式:
    每条消息为 {"role": "user"|"assistant"|"_generated_content", "content": "..."}
    _generated_content 是内部标记角色，用于存储生成内容，前端不会展示。
"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

# ============================================================
# 时区 & 路径工具函数
# ============================================================

# 中国标准时间（UTC+8），用于会话创建/更新时间戳
_CHINA_TZ = timezone(timedelta(hours=8))


def _now_iso() -> str:
    """
    返回当前中国时区的 ISO 格式时间字符串。

    用于会话索引中的 created_at / updated_at 字段，
    格式为 "YYYY-MM-DD HH:MM:SS"（不含时区后缀，默认为中国时间）。

    Returns:
        str: 当前时间的格式化字符串，如 "2025-01-15 14:30:00"
    """
    return datetime.now(_CHINA_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _get_project_root() -> str:
    """
    获取项目根目录的绝对路径。

    通过 common/ 目录的父目录推算，不依赖当前工作目录（CWD）。
    等价于 path_utils.get_file_path("")，但在此模块内自包含，
    避免循环导入。

    Returns:
        str: 项目根目录的绝对路径，如 "/Users/xxx/ChineseMedicalProject"
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_sessions_dir() -> str:
    """
    获取会话数据目录路径，确保目录存在。

    会话数据存储在项目根目录的 sessions/ 子目录下。
    如果目录不存在则自动创建（os.makedirs with exist_ok=True）。

    Returns:
        str: sessions/ 目录的绝对路径
    """
    sessions_dir = os.path.join(_get_project_root(), "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    return sessions_dir


def _get_index_path() -> str:
    """
    获取会话索引文件的完整路径。

    索引文件 sessions_index.json 记录了所有会话的元数据
    （ID、名称、创建时间、更新时间、消息数量），
    用于快速列出会话列表而不需要读取每个会话的消息文件。

    Returns:
        str: sessions_index.json 文件的绝对路径
    """
    return os.path.join(_get_sessions_dir(), "sessions_index.json")


# ============================================================
# 核心类
# ============================================================


class SessionManager:
    """
    会话管理器 — 对上层（Streamlit / FastAPI）提供统一的会话 CRUD 接口。

    所有方法均为 classmethod，无需实例化，直接通过类名调用。
    这是因为会话状态本质上是全局的（基于文件系统），不需要实例级别的状态隔离。

    每个会话包含:
        - id: 唯一标识符（12 位十六进制 UUID 前缀，兼顾唯一性和可读性）
        - name: 会话名称（默认为「新会话」，可自动从第一条用户消息截取命名）
        - created_at: 创建时间（中国时区）
        - updated_at: 最后更新时间（中国时区）
        - message_count: 消息数量（索引中缓存，避免每次都读消息文件）
        - messages: 消息列表 [{"role": "user/assistant", "content": "..."}]
                    存储在独立的 {session_id}.json 文件中
        - generated_content: 生成结果（如小红书文案），以特殊角色 _generated_content
                              存储在消息列表中（可选）

    并发安全:
        本实现未加文件锁。在单用户 Streamlit 应用场景下基本安全，
        因为 Streamlit 以单线程处理请求。如需多用户并发支持，
        建议添加文件锁或迁移到数据库存储。
    """

    # ---------- 内部辅助方法 ----------

    @staticmethod
    def _load_index() -> List[dict]:
        """
        从磁盘加载会话索引列表。

        索引文件 sessions_index.json 存储所有会话的元数据摘要，
        不包含消息内容。这使得列表页面可以快速加载会话列表。

        Returns:
            List[dict]: 会话元数据列表，按插入顺序排列。
                        如果文件不存在或格式异常则返回空列表。

        容错设计:
            - 文件不存在 → 返回 []
            - JSON 解码失败 → 返回 []
            - 数据不是列表 → 返回 []
            这些情况通常发生在首次使用或数据文件损坏时，
            返回空列表让调用方以为没有会话，可以从头开始创建。
        """
        path = _get_index_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, IOError):
            pass
        return []

    @staticmethod
    def _save_index(index: List[dict]) -> None:
        """
        将会话索引列表序列化写入磁盘。

        使用 UTF-8 编码和 2 空格缩进，ensure_ascii=False 确保
        中文会话名直接以 UTF-8 存储而非 \\uXXXX 转义序列，
        方便人工查看和调试索引文件。

        Args:
            index (List[dict]): 会话元数据列表，将被完整覆写到索引文件
        """
        path = _get_index_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _get_session_file_path(session_id: str) -> str:
        """
        获取某个会话的消息文件路径。

        每个会话的消息独立存储为一个 JSON 文件，文件名为 {session_id}.json。
        这种设计避免了所有会话消息放在单一大文件中导致的读写性能问题。

        Args:
            session_id (str): 会话的唯一标识符（12 位十六进制字符串）

        Returns:
            str: 消息文件的绝对路径，如 ".../sessions/a1b2c3d4e5f6.json"
        """
        return os.path.join(_get_sessions_dir(), f"{session_id}.json")

    @staticmethod
    def _load_messages(session_id: str) -> List[Dict[str, str]]:
        """
        从磁盘加载某个会话的完整消息列表。

        Args:
            session_id (str): 会话 ID

        Returns:
            List[Dict[str, str]]: 消息列表，每条消息包含 role 和 content 字段。
                                  如果会话文件不存在或格式异常则返回空列表。
        """
        path = SessionManager._get_session_file_path(session_id)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, IOError):
            pass
        return []

    @staticmethod
    def _save_messages(session_id: str, messages: List[Dict[str, str]]) -> None:
        """
        将某个会话的消息列表序列化写入磁盘。

        使用完整覆写模式（而非追加），确保磁盘数据与内存数据完全一致。
        JSON 使用 UTF-8 编码和 2 空格缩进。

        Args:
            session_id (str): 会话 ID
            messages (List[Dict[str, str]]): 要保存的消息列表
        """
        path = SessionManager._get_session_file_path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    # ---------- 公共 API ----------

    @classmethod
    def create_session(
        cls,
        name: str = "",
        initial_messages: List[Dict[str, str]] = None
    ) -> str:
        """
        创建一个新的会话。

        生成唯一的 12 位短 ID（uuid4 的前 12 个十六进制字符），
        写入会话索引和消息文件，自动记录创建时间。

        Args:
            name (str): 会话显示名称。为空或纯空格时自动设为「新会话」。
                        之后可通过 rename_session 或 auto_name_session 修改。
            initial_messages (List[Dict[str, str]], optional): 初始消息列表。
                        通常为空列表或包含一条 system 消息。默认为 None（视为空列表）。

        Returns:
            str: 新创建会话的 session_id（12 位十六进制字符串）

        Example:
            >>> session_id = SessionManager.create_session(name="中药查询")
            >>> session_id = SessionManager.create_session(
            ...     name="",
            ...     initial_messages=[{"role": "system", "content": "你是一个中医助手"}]
            ... )
        """
        # 生成 12 位短 ID：uuid4 的 hex 字符串前 12 字符
        # 12 位十六进制 = 48 bits，碰撞概率极低，同时保持可读性
        session_id = uuid.uuid4().hex[:12]
        now = _now_iso()
        # 去除首尾空格，空名称则使用默认值
        display_name = name.strip() if name.strip() else "新会话"

        # 写入会话索引（新会话插入到列表最前面，方便 UI 按最近使用排序）
        index = cls._load_index()
        index.insert(0, {  # insert(0, ...) 将新会话排在列表首位
            "id": session_id,
            "name": display_name,
            "created_at": now,
            "updated_at": now,
            "message_count": len(initial_messages or []),
        })
        cls._save_index(index)

        # 写入消息文件（独立存储，避免单文件过大）
        cls._save_messages(session_id, initial_messages or [])

        return session_id

    @classmethod
    def delete_session(cls, session_id: str) -> bool:
        """
        删除指定会话。

        同时执行两个操作:
            1. 从索引文件中移除该会话的元数据条目
            2. 删除该会话的独立消息文件（如果存在）

        Args:
            session_id (str): 要删除的会话 ID

        Returns:
            bool: 删除是否成功。False 表示未找到该会话（索引中无此 ID）。

        Side Effects:
            磁盘上的会话索引文件和消息文件可能被修改/删除。
            删除操作不可逆，请谨慎使用。
        """
        # 从索引中移除
        index = cls._load_index()
        new_index = [s for s in index if s.get("id") != session_id]
        if len(new_index) == len(index):
            # 索引长度未变，说明未找到目标会话
            return False
        cls._save_index(new_index)

        # 删除独立的消息文件
        msg_path = cls._get_session_file_path(session_id)
        if os.path.exists(msg_path):
            os.remove(msg_path)

        return True

    @classmethod
    def rename_session(cls, session_id: str, new_name: str) -> bool:
        """
        重命名指定会话。

        在索引文件中原地修改会话的 name 字段，不改变其他属性。
        纯空格名称会被 strip 处理。

        Args:
            session_id (str): 会话 ID
            new_name (str): 新的会话名称

        Returns:
            bool: 重命名是否成功。False 表示未找到该会话。
        """
        index = cls._load_index()
        for s in index:
            if s.get("id") == session_id:
                s["name"] = new_name.strip()
                cls._save_index(index)
                return True
        return False

    @classmethod
    def get_session(cls, session_id: str) -> Optional[dict]:
        """
        获取单个会话的完整数据（包含元数据和消息列表）。

        与 list_sessions 不同，此方法会从磁盘加载完整的消息列表，
        因此适用于需要展示对话内容的场景。对于只需要元数据的场景，
        请使用 list_sessions 以获得更好的性能。

        Args:
            session_id (str): 会话 ID

        Returns:
            Optional[dict]: 会话完整数据字典，结构为:
                {
                    "id": "a1b2c3d4e5f6",
                    "name": "中药查询",
                    "created_at": "2025-01-15 14:30:00",
                    "updated_at": "2025-01-15 14:35:00",
                    "message_count": 6,
                    "messages": [
                        {"role": "user", "content": "..."},
                        {"role": "assistant", "content": "..."},
                        ...
                    ]
                }
                如果会话不存在则返回 None。
        """
        index = cls._load_index()
        meta = None
        # 在索引中查找目标会话的元数据
        for s in index:
            if s.get("id") == session_id:
                meta = dict(s)  # 浅拷贝，避免修改索引中的原始数据
                break

        if meta is None:
            return None

        # 从消息文件中加载完整的消息列表
        messages = cls._load_messages(session_id)
        meta["messages"] = messages
        return meta

    @classmethod
    def list_sessions(cls) -> List[dict]:
        """
        列出所有会话的元数据（不含消息内容）。

        性能优化: 只读取轻量的索引文件（sessions_index.json），
        不触碰每个会话的消息文件。因此即使有大量会话和长对话历史，
        此方法也能快速返回。

        Returns:
            List[dict]: 会话元数据列表，按 updated_at 降序排列（最近更新的在前）。
                        每条元数据包含 id, name, created_at, updated_at, message_count。
        """
        index = cls._load_index()
        # 按更新时间降序排列，最近活跃的会话排在最前面
        index.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        return index

    @classmethod
    def add_message(cls, session_id: str, role: str, content: str) -> None:
        """
        向指定会话追加一条消息。

        该方法同时完成:
            1. 将消息追加到消息文件末尾
            2. 更新索引中的 updated_at 时间戳和 message_count 计数

        Args:
            session_id (str): 会话 ID
            role (str): 消息角色，通常为 "user" 或 "assistant"。
                        也支持 "_generated_content" 等内部角色。
            content (str): 消息文本内容
        """
        # 加载现有消息，追加新消息后完整覆写
        messages = cls._load_messages(session_id)
        messages.append({"role": role, "content": content})
        cls._save_messages(session_id, messages)

        # 更新索引中的时间戳和消息计数
        cls._touch_session(session_id, message_count=len(messages))

    @classmethod
    def auto_name_session(cls, session_id: str) -> None:
        """
        用第一条用户消息自动命名会话。

        提取第一条 role="user" 的消息内容，截取前 20 个字符作为会话名。
        换行符会被替换为空格以保持单行显示。如果内容超过 20 字符，
        会在末尾添加省略号 "…"。

        保护机制:
            - 仅在会话名称仍为「新会话」时执行，已命名过的会话不会被覆盖。
            - 如果没有用户消息，保持原名不变。

        适用场景:
            用户开始新对话后，自动用其第一条提问作为会话标题，
            方便在会话列表中快速识别对话内容。

        Args:
            session_id (str): 会话 ID
        """
        # 检查当前会话是否仍为默认名称
        index = cls._load_index()
        meta = next((s for s in index if s.get("id") == session_id), None)
        if meta is None:
            return
        if meta.get("name", "") != "新会话":
            # 已经命名过了（用户手动重命名或之前自动命名过），不覆盖
            return

        # 查找第一条用户消息
        messages = cls._load_messages(session_id)
        first_user_msg = ""
        for m in messages:
            if m.get("role") == "user":
                first_user_msg = m.get("content", "").strip()
                break

        if first_user_msg:
            # 截取前 20 个字符，将换行符替换为空格以保持单行显示
            short_name = first_user_msg.replace("\n", " ")[:20]
            if len(first_user_msg) > 20:
                short_name += "…"  # 省略号表示内容被截断
            meta["name"] = short_name
            cls._save_index(index)

    @classmethod
    def _touch_session(cls, session_id: str, message_count: int = None) -> None:
        """
        更新会话的活跃时间戳（和可选的消息计数）。

        这是一个内部辅助方法，在消息变更时被 add_message 等方法调用，
        用于刷新索引中的 updated_at 字段，使该会话在列表中排到前面。

        Args:
            session_id (str): 会话 ID
            message_count (int, optional): 新的消息总数。为 None 时不更新计数。
        """
        index = cls._load_index()
        for s in index:
            if s.get("id") == session_id:
                s["updated_at"] = _now_iso()
                if message_count is not None:
                    s["message_count"] = message_count
                cls._save_index(index)
                return

    @classmethod
    def update_generated_content(cls, session_id: str, content: dict) -> None:
        """
        更新会话中的生成内容（如小红书文案）。

        生成内容以特殊角色 "_generated_content" 存储在消息列表中，
        不会在前端聊天界面中显示，但可通过 get_generated_content 读取。
        每次更新会先移除旧的生成内容，再追加新的。

        Args:
            session_id (str): 会话 ID
            content (dict): 生成内容字典，会被 JSON 序列化后存储。
                            例如 {"title": "...", "body": "...", "tags": [...]}
        """
        # 加载消息，过滤掉旧的生成内容，再追加新的
        messages = cls._load_messages(session_id)
        # 移除旧的 _generated_content 标记（确保只有一份生成内容）
        messages = [m for m in messages if m.get("role") != "_generated_content"]
        # 追加新的生成内容（存储为 JSON 字符串）
        messages.append({
            "role": "_generated_content",
            "content": json.dumps(content, ensure_ascii=False),
        })
        cls._save_messages(session_id, messages)
        cls._touch_session(session_id, message_count=len(messages))

    @classmethod
    def clear_generated_content(cls, session_id: str) -> None:
        """
        清除会话中的生成内容。

        移除所有 role="_generated_content" 的消息，其他消息保持不变。
        适用于用户清空生成结果重新生成的场景。

        Args:
            session_id (str): 会话 ID
        """
        messages = cls._load_messages(session_id)
        # 过滤掉所有 _generated_content 标记的消息
        messages = [m for m in messages if m.get("role") != "_generated_content"]
        cls._save_messages(session_id, messages)
        cls._touch_session(session_id, message_count=len(messages))

    @classmethod
    def get_generated_content(cls, session_id: str) -> Optional[dict]:
        """
        获取会话中最近一次的生成内容。

        从消息列表末尾开始反向查找第一个 role="_generated_content" 的消息，
        将其 JSON 内容反序列化为 Python 字典返回。

        Args:
            session_id (str): 会话 ID

        Returns:
            Optional[dict]: 生成内容字典（从 JSON 反序列化）。
                            如果会话无生成内容或 JSON 解析失败则返回 None。

        容错设计:
            如果 _generated_content 消息中的 JSON 格式损坏（JSONDecodeError），
            返回 None 而非抛出异常，使前端可以优雅降级。
        """
        messages = cls._load_messages(session_id)
        # 从末尾反向查找，获取最近一次的生成内容
        for m in reversed(messages):
            if m.get("role") == "_generated_content":
                try:
                    return json.loads(m.get("content", "{}"))
                except json.JSONDecodeError:
                    return None
        return None


# ============================================================
# 便捷函数（供 Streamlit 页面直接使用）
# ============================================================


def ensure_current_session(session_id_key: str = "current_session_id") -> str:
    """
    确保当前有一个活跃的会话 ID，不存在则自动创建。

    此函数是 Streamlit 多页面应用中管理当前会话的关键入口。
    每个页面调用此函数获取当前会话 ID，确保用户始终有一个活跃的会话。

    行为逻辑:
        1. 如果 st.session_state 中已有 current_session_id → 直接返回
        2. 如果没有 → 尝试加载最近使用的会话（列表第一个）
        3. 如果没有任何会话 → 创建一个新的默认会话并设为当前

    Args:
        session_id_key (str): session_state 中存储会话 ID 的键名。
                              默认为 "current_session_id"。

    Returns:
        str: 当前会话的 session_id

    Note:
        此函数依赖 streamlit.session_state，仅在 Streamlit 运行时环境中可用。
        在非 Streamlit 环境（如命令行脚本）中会回退到直接使用 SessionManager。
    """
    try:
        import streamlit as st
    except ImportError:
        # 非 Streamlit 环境回退：返回第一个现有会话，或创建新会话
        sessions = SessionManager.list_sessions()
        return sessions[0]["id"] if sessions else SessionManager.create_session()

    if session_id_key not in st.session_state:
        # 首次加载（页面刷新或首次访问）：尝试恢复最近的会话
        sessions = SessionManager.list_sessions()
        if sessions:
            # 有历史会话，默认打开最近的一个
            st.session_state[session_id_key] = sessions[0]["id"]
        else:
            # 没有任何会话，创建一个默认会话作为起点
            new_id = SessionManager.create_session()
            st.session_state[session_id_key] = new_id

    return st.session_state[session_id_key]


def switch_session(session_id_key: str, new_session_id: str) -> None:
    """
    切换当前活跃的会话。

    修改 st.session_state 中的会话 ID 引用，使后续的 add_message 等操作
    作用于新切换的会话。实际的页面刷新由 Streamlit 的 rerun 机制触发。

    Args:
        session_id_key (str): session_state 中存储会话 ID 的键名
        new_session_id (str): 要切换到的新会话 ID

    Note:
        在非 Streamlit 环境中调用此函数不会产生任何效果。
    """
    try:
        import streamlit as st
        st.session_state[session_id_key] = new_session_id
    except ImportError:
        # 非 Streamlit 环境，无法切换（无 session_state）
        pass


def load_current_messages(session_id_key: str = "current_session_id") -> list:
    """
    加载当前会话的消息列表（供 Streamlit 聊天界面渲染使用）。

    自动调用 ensure_current_session 确保会话存在，然后加载消息列表。
    过滤掉内部标记消息（以 "_" 开头的 role，如 "_generated_content"），
    返回的列表项为 (role, content) 元组，兼容现有聊天渲染代码的拆包模式。

    Args:
        session_id_key (str): session_state 中存储会话 ID 的键名

    Returns:
        list: 消息列表，每项为 (role: str, content: str) 元组。
              例如 [("user", "四君子汤是什么？"), ("assistant", "四君子汤是...")]

    Example:
        # 在 Streamlit 页面中渲染聊天历史
        for role, content in load_current_messages():
            with st.chat_message(role):
                st.markdown(content)
    """
    session_id = ensure_current_session(session_id_key)
    session = SessionManager.get_session(session_id)
    if session is None:
        return []
    # 过滤掉内部标记消息（role 以 "_" 开头），返回 (role, content) 元组格式
    # 兼容 Streamlit 的 for role, content in messages 拆包模式
    return [(m["role"], m["content"]) for m in session.get("messages", [])
            if not m.get("role", "").startswith("_")]
