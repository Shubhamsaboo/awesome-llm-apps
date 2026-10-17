"""Streamlit UI for the LangGraph travel-planning workflow."""

import re
from datetime import datetime, timedelta

import streamlit as st
from icalendar import Calendar, Event

from travel_graph import run_travel_agent, split_days


def generate_ics_content(plan_text: str, start_date: datetime | None = None) -> bytes:
    """Convert the Chinese day headings into an all-day calendar file."""

    calendar = Calendar()
    calendar.add("prodid", "-//AI Travel Planner//github.com//")
    calendar.add("version", "2.0")

    if start_date is None:
        start_date = datetime.today()

    day_pattern = re.compile(
        r"(?:第\s*(\d+)\s*天|Day\s*(\d+))[^\n]*\n(.*?)"
        r"(?=(?:第\s*\d+\s*天|Day\s*\d+)|$)",
        re.DOTALL,
    )
    days = [
        (first or second, content)
        for first, second, content in day_pattern.findall(plan_text)
    ]

    if not days:
        event = Event()
        event.add("summary", "Travel Itinerary")
        event.add("description", plan_text)
        event.add("dtstart", start_date.date())
        event.add("dtend", start_date.date())
        event.add("dtstamp", datetime.now())
        calendar.add_component(event)
    else:
        for day_number, content in days:
            current_date = start_date + timedelta(days=int(day_number) - 1)
            event = Event()
            event.add("summary", f"Day {day_number} Itinerary")
            event.add("description", content.strip())
            event.add("dtstart", current_date.date())
            event.add("dtend", current_date.date())
            event.add("dtstamp", datetime.now())
            calendar.add_component(event)

    return calendar.to_ical()


st.set_page_config(page_title="AI 旅行规划师", page_icon="🧭")
st.title("AI 旅行规划师 · LangGraph 版")
st.caption("LangGraph 负责状态流转，预算由确定性工具计算，模型负责生成行程。")

if "travel_result" not in st.session_state:
    st.session_state.travel_result = None

api_key = st.text_input("输入 DeepSeek API Key", type="password")
destination = st.text_input("你想去哪里？")
num_days = st.number_input("想玩几天？", min_value=1, max_value=30, value=7)

if st.button("生成行程", type="primary"):
    if not api_key:
        st.error("请先填写 DeepSeek API Key。")
    elif not destination.strip():
        st.error("请填写目的地。")
    else:
        with st.spinner("Agent 正在生成行程并调用预算工具..."):
            try:
                st.session_state.travel_result = run_travel_agent(
                    api_key=api_key,
                    destination=destination,
                    num_days=int(num_days),
                )
            except Exception as exc:
                st.session_state.travel_result = None
                st.error(f"调用失败：{exc}")

result = st.session_state.travel_result
if result:
    if result.error:
        st.error(result.error)
    else:
        if result.planning_date:
            st.info(f"规划日期：{result.planning_date}")

        if result.total_budget is not None:
            st.success(f"💰 工具计算的全程预算约 ¥{result.total_budget:.0f}")
            breakdown = result.budget_breakdown
            st.caption(
                "费用明细："
                f"住宿 ¥{breakdown.get('hotel', 0):.0f} · "
                f"餐饮 ¥{breakdown.get('food', 0):.0f} · "
                f"交通 ¥{breakdown.get('transport', 0):.0f} · "
                f"门票 ¥{breakdown.get('tickets', 0):.0f}"
            )

        st.subheader("📅 你的行程")
        day_blocks = split_days(result.itinerary)
        if day_blocks:
            for index, block in enumerate(day_blocks):
                st.markdown(block)
                if index < len(day_blocks) - 1:
                    st.divider()
        else:
            st.markdown(result.itinerary)

        st.download_button(
            label="下载行程日历 (.ics)",
            data=generate_ics_content(result.itinerary),
            file_name="travel_itinerary.ics",
            mime="text/calendar",
        )
