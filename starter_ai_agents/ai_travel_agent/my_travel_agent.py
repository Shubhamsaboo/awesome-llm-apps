# =============================================================================
# my_travel_agent.py  ——  AI 旅行规划 Agent（改造版 v5）
#
# 相比原版 travel_agent.py 的改动（简历上能写的"自己的改动"）：
#   1. 去掉了必须付费的 SerpAPI 联网搜索，只用大模型自身知识生成行程。
#   2. 模型换成 DeepSeek，用 openai SDK 直连（避开 agno 框架兼容问题）。
#   3. 界面只保留一个 key 输入框，操作更简单。
#   4. 【阶段2】每日预算：每天结尾附"当日预算"，顶部汇总总花费。
#   5. 【阶段2 v5】结构化排版：每天一个大标题，上午/中午/下午/晚上分段，
#      页面按天分块展示，不再是一坨挤在一起的长文字。
#
# 运行方式：双击同目录下的 run.bat
# =============================================================================

import re
import streamlit as st
from openai import OpenAI
from icalendar import Calendar, Event
from datetime import datetime, timedelta


def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
    """把行程文本转成 .ics 日历文件（适配 v5 的'第X天'格式）"""
    cal = Calendar()
    cal.add('prodid', '-//AI Travel Planner//github.com//')
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    # 同时兼容"第X天"和"Day X"两种标题写法
    day_pattern = re.compile(
        r'(?:第\s*(\d+)\s*天|Day\s*(\d+))[^\n]*\n(.*?)(?=(?:第\s*\d+\s*天|Day\s*\d+)|$)',
        re.DOTALL,
    )
    days = [(a or b, c) for a, b, c in day_pattern.findall(plan_text)]

    if not days:
        event = Event()
        event.add('summary', "Travel Itinerary")
        event.add('description', plan_text)
        event.add('dtstart', start_date.date())
        event.add('dtend', start_date.date())
        event.add("dtstamp", datetime.now())
        cal.add_component(event)
    else:
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)
            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)

    return cal.to_ical()


def call_deepseek(api_key: str, destination: str, num_days: int) -> str:
    """直接调用 DeepSeek 接口生成结构化行程（每天分段 + 每日预算）"""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
    )
    system_prompt = (
        "你是一位资深旅行规划师。根据用户给出的目的地和旅行天数，"
        "直接利用你的知识生成一份详尽、有趣且不虚构事实的行程。\n"
        "【输出格式（必须严格遵守）】\n"
        "每天必须按以下结构输出，每天之间用空行隔开：\n"
        "## 第X天：给这天起个主题名\n"
        "**🌅 上午**：活动安排（写清楚去哪、玩什么、门票大概多少钱）\n\n"
        "**🍚 中午**：午餐推荐（哪家店/哪片区域、人均大概多少钱）\n\n"
        "**☀️ 下午**：活动安排\n\n"
        "**🌙 晚上**：活动安排（含晚餐与夜生活建议）\n\n"
        "**🏨 住宿**：当晚住宿建议与每晚上价格\n\n"
        "**当日预算**：约¥XXX（住宿¥X，餐饮¥X，交通¥X，门票¥X）\n"
        "【其他要求】\n"
        "1. 上午/中午/下午/晚上各自单独成段，每段2-3句话，不要挤成一大段。\n"
        "2. '当日预算'必须是每天最后一行，格式严格照上面的模板写。\n"
        "3. 金额用人民币，凭常识合理估算，不要编造。\n"
        "4. 不要输出'好的，这是您的行程'之类的开场白，直接从第1天开始。"
    )
    user_prompt = (
        f"请为我规划一次去 {destination} 的 {num_days} 天旅行，"
        f"严格按系统设定的格式输出。"
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def extract_total_budget(plan_text: str) -> float:
    """【阶段2】从行程文本里把每天的'当日预算'抠出来求和"""
    nums = re.findall(r'当日预算\*{0,2}[：:]\s*约?\s*[¥￥]?\s*(\d+)', plan_text)
    return sum(float(n) for n in nums)


def split_days(plan_text: str):
    """【阶段2 v5】把整段行程按'第X天'切成多块，方便按天分开展示"""
    parts = re.split(r'(?=##\s*第\s*\d+\s*天)', plan_text)
    return [p.strip() for p in parts if p.strip() and re.match(r'^##?\s*第\s*\d+\s*天', p.strip())]


# ------------ Streamlit 界面 ------------
st.title("AI 旅行规划师 (DeepSeek 版)")
st.caption("输入目的地和天数，AI 为你生成个性化行程：每天分时段详细规划，结尾附当日预算")

if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

# 只填一个 DeepSeek key（在 https://platform.deepseek.com 获取）
api_key = st.text_input("输入你的 DeepSeek API Key", type="password")

destination = st.text_input("你想去哪里？")
num_days = st.number_input("想玩几天？", min_value=1, max_value=30, value=7)

if st.button("生成行程"):
    if not api_key:
        st.error("请先在上方填写你的 DeepSeek API Key")
    elif not destination:
        st.error("请先填写目的地")
    else:
        with st.spinner("AI 正在规划行程并估算每日预算，请稍候..."):
            try:
                st.session_state.itinerary = call_deepseek(api_key, destination, num_days)
            except Exception as e:
                st.error(f"调用失败：{e}")

# ------------ 展示行程 ------------
if st.session_state.itinerary:
    plan = st.session_state.itinerary

    # 【阶段2】顶部汇总总花费（从每天的当日预算累加）
    total = extract_total_budget(plan)
    if total > 0:
        st.success(f"💰 本次行程预计总花费约 **¥{total:.0f}**（{num_days} 天，含住宿/餐饮/交通/门票）")

    st.subheader("📅 你的行程")

    # 【阶段2 v5】按天分块展示：每天一个小节，之间有分隔线，阅读不拥挤
    day_blocks = split_days(plan)
    if day_blocks:
        for i, block in enumerate(day_blocks):
            st.markdown(block)
            if i < len(day_blocks) - 1:
                st.divider()
    else:
        # 万一 AI 没按格式输出，兜底原样显示
        st.markdown(plan)

    ics_content = generate_ics_content(plan)
    st.download_button(
        label="下载行程日历 (.ics)",
        data=ics_content,
        file_name="travel_itinerary.ics",
        mime="text/calendar",
    )
