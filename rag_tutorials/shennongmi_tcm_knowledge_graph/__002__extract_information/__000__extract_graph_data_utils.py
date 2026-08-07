"""
中医知识图谱提取工具模块

本模块定义了中医知识图谱的数据模型（实体类型、关系类型、属性结构）以及
基于 LLM 的批量异步提取流程。

核心功能：
    1. 定义实体/关系/属性的 Pydantic 数据模型（用于 LLM 输出的结构化校验）
    2. 构建 LLM 调用链（Prompt -> LLM -> JSON Parser），实现从自然语言文本到结构化图谱的转换
    3. 提供异步并发批量处理能力，支持断点续跑、批量写入和微调数据集导出

数据模型层次：
    - EntityType / RelationType: 枚举定义的实体/关系类型
    - FormulaAttributes / HerbAttributes: 方剂/药材的属性字段
    - Entity / Relation: 实体和关系的 Pydantic 结构
    - TCMKnowledgeGraph: 顶层图谱结构（包含实体列表和关系列表）

典型用法：
    from __002__extract_information.__000__extract_graph_data_utils import extract_from_folder
    extract_from_folder("文本文件夹路径", "结果保存路径", "微调保存路径")
"""

import json
import asyncio
from typing import Literal, Optional, Union, List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel
from common.llm import my_llm
import os
from tqdm import tqdm


# ======================
# 枚举定义
# ======================
# 实体类型：Literal 类型确保 LLM 输出严格限定在列表中，不允许生成其他值
# 使用 Literal 而非 Enum，是为了让 Pydantic 在 JSON Schema 中以字面量约束形式传递给 LLM
# Literal: 字面量, 严格生成列表中的某一个选项, 不允许输出其他的东西
EntityType = Literal["Symptom", "Disease", "Formula", "Herb", "Effect", "Source"]

# 关系类型：定义中医知识图谱中实体之间的六种关系
# - TREATS_DISEASE: 方剂/药材 → 治疗 → 疾病
# - ALLEVIATES_SYMPTOM: 方剂/药材 → 缓解 → 症状
# - HAS_EFFECT: 方剂/药材 → 具有 → 功效
# - HAS_INGREDIENT: 方剂 → 包含 → 药材
# - HAS_SYMPTOM: 疾病 → 包含 → 症状
# - FROM_SOURCE: 方剂 → 出自 → 文献出处
RelationType = Literal[
    "TREATS_DISEASE",
    "ALLEVIATES_SYMPTOM",
    "HAS_EFFECT",
    "HAS_INGREDIENT",
    "HAS_SYMPTOM",
    "FROM_SOURCE"
]

# ======================
# 属性定义
# ======================
class FormulaAttributes(BaseModel):
    """方剂属性模型

    定义方剂实体可包含的属性字段，所有字段均为可选。
    当 LLM 从文本中提取到对应信息时填充，未提取到时为 None（不会出现在 JSON 输出中）。

    Attributes:
        alias: 别名，方剂的其他名称
        effect: 功效，方剂的治疗效果
        indication: 主治，方剂主要治疗的疾病或症状
        taboo: 禁忌，使用方剂的禁忌症或注意事项
        usage: 用法，方剂的使用方法（如煎服、冲服等）
    """
    # Optional可选项, 如果有就生成
    alias: Optional[str] = None
    effect: Optional[str] = None
    indication: Optional[str] = None
    taboo: Optional[str] = None
    usage: Optional[str] = None


class HerbAttributes(BaseModel):
    """药材属性模型

    定义药材实体可包含的属性字段，所有字段均为可选。
    涵盖药材的性味归经、功效主治、产地炮制等中医核心信息。

    Attributes:
        dosage: 剂量，药材的常用剂量范围
        effect: 功效，药材的药理功效
        indication: 主治，药材治疗的疾病或症状
        meridian: 归经，药材作用的经络
        origin: 来源，药材的动植物来源
        place: 产地，药材的道地产区
        processing: 炮制，药材的加工方法
        property_flavor: 性味，药材的四气五味（如温、寒、甘、苦等）
        taboo: 禁忌，药材的使用禁忌
        traits: 性状，药材的物理性状描述
    """
    dosage: Optional[str] = None
    effect: Optional[str] = None
    indication: Optional[str] = None
    meridian: Optional[str] = None
    origin: Optional[str] = None
    place: Optional[str] = None
    processing: Optional[str] = None
    property_flavor: Optional[str] = None
    taboo: Optional[str] = None
    traits: Optional[str] = None

# ======================
# 实体与关系结构
# ======================
class Entity(BaseModel):
    """知识图谱实体

    表示中医知识图谱中的一个节点，包含名称、类型和可选属性。

    Attributes:
        name: 实体名称（如"人参"、"四君子汤"、"咳嗽"等）
        type: 实体类型，必须是 EntityType 中定义的六种之一
        attributes: 实体属性，根据 type 不同填充 FormulaAttributes 或 HerbAttributes
    """
    name: str
    type: EntityType
    attributes: Optional[Union[FormulaAttributes, HerbAttributes]] = None

class Relation(BaseModel):
    """知识图谱关系

    表示中医知识图谱中的一条有向边，连接两个实体。

    Attributes:
        subject: 主体（关系起点）的名称
        subject_type: 主体的实体类型
        relation: 关系类型，必须是 RelationType 中定义的六种之一
        object: 客体（关系终点）的名称
        object_type: 客体的实体类型
    """
    subject: str
    subject_type: EntityType
    relation: RelationType
    object: str
    object_type: EntityType

class TCMKnowledgeGraph(BaseModel):
    """中医知识图谱顶层结构

    封装一次提取操作得到的完整知识图谱，包含实体列表和关系列表。

    Attributes:
        entities: 从文本中提取的所有实体
        relations: 从文本中提取的所有关系
    """
    entities: List[Entity]
    relations: List[Relation]

# 初始化解析器
# JsonOutputParser 会根据 TCMKnowledgeGraph 的 Pydantic Schema 自动生成 JSON 格式说明，
# 并注入到 Prompt 的 format_instructions 中，同时负责对 LLM 输出进行 JSON 解析和 Pydantic 校验
parser = JsonOutputParser(pydantic_object=TCMKnowledgeGraph)


# 定义 Prompt
# 使用 LangChain 的 PromptTemplate 构建结构化提示词，
# {text} 为输入文本占位符，{format_instructions} 为 JSON 输出格式说明（由 parser 自动填充）
prompt = PromptTemplate(
    template=(
        "你是一个中医知识图谱抽取专家。请从以下文本中提取结构化知识：\n"
        "仅当文本中存在实体之间的明确关系时（如'某方剂治疗某疾病'、'某药材具有某功效'、'方剂包含药材'等），才进行抽取。\n"
        "如果文本中仅描述单个实体的信息、未涉及其他实体或关系，请不要抽取，返回空结构：\n"
        "{{\"entities\": [], \"relations\": []}}\n\n"

        "【实体类型说明】\n"
        "- Symptom：症状，如咳嗽、腹痛等\n"
        "- Disease：疾病，如感冒、肺炎、肾虚等\n"
        "- Formula：方剂，如四君子汤、桂枝汤等\n"
        "- Herb：药材，如人参、黄芪、丁香等\n"
        "- Effect：功效，如补气、活血、祛湿、止痛等\n"
        "- Source：出处，如《本草纲目》《伤寒论》等\n\n"

        "【关系类型说明】\n"
        "- TREATS_DISEASE：方剂或药材治疗某种疾病\n"
        "- ALLEVIATES_SYMPTOM：方剂或药材缓解某种症状\n"
        "- HAS_EFFECT：方剂或药材具有某种功效\n"
        "- HAS_INGREDIENT：方剂包含某种药材\n"
        "- HAS_SYMPTOM：疾病包含某种症状\n"
        "- FROM_SOURCE：方剂出自某文献或出处\n\n"

        "若文本涉及方剂或药材，请补充对应的属性字段（如功效、性味、剂量等）。\n"
        "如果文本主要是讲方剂的，请不要抽取药材的属性字段。\n"
        "如果文本主要是讲药材的，请不要抽取方剂的属性字段。\n"
        "如果值为空（null），则不必显示键的值。\n"
        "所有输出必须严格符合以下 JSON 格式：\n"
        "{format_instructions}\n\n"
        "输入文本：{text}"
    ),
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 🔧 修复：改为惰性创建 chain，避免 LLM 配置变更后仍使用旧 chain
def _get_chain():
    """构建并返回知识图谱抽取的 LangChain 调用链。

    使用惰性创建模式（每次调用时重新构建链），确保始终使用最新的 LLM 配置。
    调用链结构：Prompt 模板 -> LLM 调用 -> JSON 输出解析器

    Returns:
        LangChain Runnable: 可调用的处理链，输入 {"text": str}，输出 TCMKnowledgeGraph 字典
    """
    return prompt | my_llm | parser


# ======================
# 主函数封装
# ======================
def extract_tcm_knowledge(text: str):
    """同步版本：抽取中医知识图谱（保持向后兼容）

    对单段文本调用 LLM 抽取中医知识图谱。该函数为同步调用，会阻塞当前线程直到 LLM 返回结果。

    Args:
        text: 待抽取的中医文本内容

    Returns:
        dict: 结构化的 TCMKnowledgeGraph 字典，包含 entities 和 relations 两个列表
    """
    return _get_chain().invoke({"text": text})


async def _extract_tcm_knowledge_async(text: str, semaphore: asyncio.Semaphore):
    """异步版本：使用信号量控制并发数，避免触发 API 限流

    对单段文本进行异步 LLM 调用。通过信号量控制同时进行的 API 请求数量，
    防止因并发过高触发 LLM 服务的速率限制。

    Args:
        text: 待抽取的中医文本内容
        semaphore: asyncio.Semaphore 信号量，用于控制最大并发数

    Returns:
        dict: 结构化的 TCMKnowledgeGraph 字典
    """
    async with semaphore:
        return await _get_chain().ainvoke({"text": text})


def extract_from_folder(
    folder_path: str,
    save_path: str,
    finetune_save_path: str,
    max_concurrency: int = 50,
    save_interval: int = 50,
):
    """
    从文件夹中批量提取中医知识图谱（异步并发 + 批量写入）

    遍历指定文件夹中的所有 .txt 文件，对每个文件调用 LLM 进行知识图谱抽取，
    支持以下特性：
        - 断点续跑：自动检测已处理的文件，跳过无需重新处理的部分
        - 异步并发：同时处理多个文件，max_concurrency 控制并发上限
        - 批量落盘：每成功处理 save_interval 条数据写入一次磁盘，防止数据丢失
        - 微调数据集导出：同时生成 instruction-input-output 格式的微调训练数据
        - 并发安全：使用 asyncio.Lock 保护共享数据的并发写入

    Args:
        folder_path: 文本文件夹路径，程序将遍历其中所有 .txt 文件
        save_path: 知识图谱结果保存路径（JSON 文件）
        finetune_save_path: 微调格式数据保存路径（JSON 文件），格式为 [{instruction, input, output}, ...]
        max_concurrency: 最大并发数，默认 50（请根据 API 限流策略调整）
        save_interval: 每处理多少条数据批量写入一次磁盘，默认 50
    """

    # ======================
    # 辅助函数
    # ======================
    def load_existing_results(save_path: str):
        """加载已存在的JSON结果，用于断点续跑

        从磁盘读取之前保存的结果文件，返回已有的 results 字典。
        如果文件不存在或 JSON 格式无效，则返回空的初始结构。

        Args:
            save_path: 结果文件的磁盘路径

        Returns:
            dict: 格式为 {"results": [...]} 的字典，包含已处理的所有结果
        """
        if os.path.exists(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict) and "results" in data:
                        return data
                except json.JSONDecodeError:
                    pass
        return {"results": []}

    def save_results(data: dict, save_path: str):
        """将当前结果保存到JSON

        将累积的处理结果字典序列化为 JSON 文件写入磁盘。

        Args:
            data: 包含 "results" 键的结果字典
            save_path: 保存路径
        """
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ======================
    # 加载已有数据（断点续跑）
    # ======================
    # 加载之前保存的结果，构建已处理文件集合，避免重复处理
    all_results = load_existing_results(save_path)
    processed_files = {r['filename'] for r in all_results['results']}

    # 加载已有的微调数据（如果存在）
    finetune_data = []
    if os.path.exists(finetune_save_path):
        with open(finetune_save_path, "r", encoding="utf-8") as f:
            try:
                finetune_data = json.load(f)
            except json.JSONDecodeError:
                pass

    # 扫描文件夹中的所有 .txt 文件，过滤出未处理的文件
    txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    unprocessed = [f for f in txt_files if f not in processed_files]

    print(f"🔍 共发现 {len(txt_files)} 个文本文件，"
          f"已处理 {len(processed_files)} 个，"
          f"待处理 {len(unprocessed)} 个。")

    if not unprocessed:
        print("✅ 所有文件已处理完毕，无需重复运行。")
        return

    # ======================
    # 异步并发处理
    # ======================
    semaphore = asyncio.Semaphore(max_concurrency)  # 并发控制信号量，限制同时进行的 API 请求数
    write_lock = asyncio.Lock()                      # 写入锁，保证多协程写入共享数据时的并发安全

    # 进度与计数
    pbar = tqdm(total=len(unprocessed), desc="处理中...")
    success_count = 0
    fail_count = 0

    async def process_one(filename: str):
        """处理单个文件的协程

        异步读取文件 → 调用 LLM 抽取知识图谱 → 线程安全地写入结果。
        使用 nonlocal 引用外层计数变量来追踪处理进度。

        Args:
            filename: 待处理的文件名（不含路径前缀）
        """
        nonlocal success_count, fail_count

        file_path = os.path.join(folder_path, filename)

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        # 跳过空文件
        if not text:
            tqdm.write(f"⚠️ 文件为空：{filename}")
            fail_count += 1
            pbar.update(1)
            return

        try:
            # 异步调用 LLM（信号量自动控制并发数量）
            result_dict = await _extract_tcm_knowledge_async(text, semaphore)

            # 构建结果记录：包含文件名和提取的知识图谱
            record = {'filename': filename, 'extract_dict': result_dict}

            # 构建微调格式数据：instruction-input-output 三元组
            finetune_item = {
                "instruction": "请从以下中医文本中抽取知识图谱结构，包括实体与关系。",
                "input": text,
                "output": json.dumps(
                    result_dict,
                    ensure_ascii=False,
                    indent=2
                )
            }

            # 线程安全地追加结果 + 批量写入磁盘
            async with write_lock:
                all_results['results'].append(record)
                finetune_data.append(finetune_item)
                success_count += 1

                # 达到保存间隔（按成功条数计）时批量写入磁盘，防止数据在内存中积累过多
                if success_count % save_interval == 0:
                    save_results(all_results, save_path)
                    with open(finetune_save_path, "w", encoding="utf-8") as fout:
                        json.dump(finetune_data, fout, ensure_ascii=False, indent=2)
                    tqdm.write(f"💾 已批量保存（累计 {success_count} 条）")

            tqdm.write(f"✅ 已保存结果：{filename}")

        except Exception as e:
            # 捕获并记录处理异常，继续处理下一个文件
            tqdm.write(f"❌ 处理失败：{filename}, 错误：{e}")
            fail_count += 1
        finally:
            # 无论成功还是失败，都更新进度条
            pbar.update(1)

    # 运行所有异步任务
    async def run_all():
        """创建并等待所有文件处理的异步任务完成"""
        tasks = [process_one(f) for f in unprocessed]
        await asyncio.gather(*tasks, return_exceptions=True)

    # 🔧 修复：兼容已有事件循环的场景（如从 FastAPI 调用）
    # 检测当前是否已在事件循环中运行，如果在已有循环中调用 asyncio.run() 会导致 RuntimeError
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 无运行中的事件循环 → 创建新的（适合直接运行脚本的场景）
        asyncio.run(run_all())
    else:
        # 已有运行中的事件循环 → 在新线程中运行独立事件循环（适合 FastAPI 等框架内部调用）
        import threading
        thread_error: Exception | None = None

        def _run_in_thread():
            """在独立线程中运行 asyncio 事件循环"""
            nonlocal thread_error
            try:
                asyncio.run(run_all())
            except Exception as e:
                thread_error = e

        t = threading.Thread(target=_run_in_thread)
        t.start()
        t.join()
        # 🔧 修复：将线程内的异常传播到主线程，避免静默失败
        if thread_error is not None:
            raise RuntimeError(
                f"extract_from_folder 异步处理线程异常: {thread_error}"
            ) from thread_error
    pbar.close()

    # ======================
    # 最终保存（确保最后一批不满足 save_interval 的数据也落盘）
    # ======================
    save_results(all_results, save_path)
    with open(finetune_save_path, "w", encoding="utf-8") as f:
        json.dump(finetune_data, f, ensure_ascii=False, indent=2)
    print(f"💾 最终保存完成。")

    print(f"\n🎯 处理完成，成功 {success_count} 个，失败 {fail_count} 个，"
          f"累计 {len(all_results['results'])} 个文件结果。")
