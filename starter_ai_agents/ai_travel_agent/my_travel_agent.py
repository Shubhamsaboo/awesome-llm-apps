# =============================================================================
# my_travel_agent.py  ——  AI 旅行规划 Agent（改造版 v2）
#
# 相比原版 travel_agent.py 的改动（简历上能写的"自己的改动"）：
#   1. 去掉了必须付费的 SerpAPI 联网搜索，只用大模型自身知识生成行程。
#   2. 模型换成 DeepSeek，用 openai SDK 直连（不再经过 agno 框架，
#      因为 agno 3.x 发送的消息角色字段与 DeepSeek 接口不兼容）。
#   3. 界面只保留一个 key 输入框，操作更简单。
#
# 运行方式：双击同目录下的 run.bat
# =============================================================================

import re
import streamlit as st
from openai import OpenAI
from icalendar import Calendar, Event
from datetime import datetime, timedelta


def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
    """把行程文本转成 .ics 日历文件（原版函数，未改动）"""
    cal = Calendar()
    cal.add('prodid', '-//AI Travel Planner//github.com//')
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

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
    """直接调用 DeepSeek 接口生成行程（标准 OpenAI 兼容写法）"""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
    )
    system_prompt = (
        "你是一位资深旅行规划师。根据用户给出的目的地和旅行天数，"
        "直接利用你的知识生成一份详尽、结构清晰、有趣且不虚构事实的行程。"
        "用'第X天'作为每天的开头，方便转换成日历。"
    )
    user_prompt = f"请为我规划一次去 {destination} 的 {num_days} 天旅行，包含每日活动、餐饮与住宿建议。"

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


# ------------ Streamlit 界面 ------------
st.title("AI 旅行规划师 (DeepSeek 版)")
st.caption("输入目的地和天数，AI 直接为你生成个性化行程，无需联网搜索、零额外费用")

if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

# 只填一个 DeepSeek key（在 https://platform.deepseek.com 获取）
api_key = st.text_input("输入你的 DeepSeek API Key", type="password")

destination = st.text_input("你想去哪里？")
num_days = st.number_input("想玩几天？", min_value=1, max_value=30, value=7)

col1, col2 = st.columns(2)

with col1:
    if st.button("生成行程"):
        if not api_key:
            st.error("请先在上方填写你的 DeepSeek API Key")
        elif not destination:
            st.error("请先填写目的地")
        else:
            with st.spinner("正在为你规划行程..."):
                try:
                    st.session_state.itinerary = call_deepseek(api_key, destination, num_days)
                except Exception as e:
                    st.error(f"调用失败：{e}")

with col2:
    if st.session_state.itinerary:
        st.markdown(st.session_state.itinerary)
        ics_content = generate_ics_content(st.session_state.itinerary)
        st.download_button(
            label="下载行程日历 (.ics)",
            data=ics_content,
            file_name="travel_itinerary.ics",
            mime="text/calendar",
        )
