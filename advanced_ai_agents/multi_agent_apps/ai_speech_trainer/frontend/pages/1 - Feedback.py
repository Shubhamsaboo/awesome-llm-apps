import streamlit as st
import plotly.graph_objects as go
import json
from page_congif import render_page_config

render_page_config()

# Get feedback response from session state
if st.session_state.feedback_response:
    feedback_response = json.loads(st.session_state.feedback_response)
    feedback_scores = feedback_response.get("scores")

    # Evaluation scores based on the public speaking rubric
    scores = {
        "Content & Organization": feedback_scores.get("content_organization"),
        "Delivery & Vocal Quality": feedback_scores.get("delivery_vocal_quality"),
        "Body Language & Eye Contact": feedback_scores.get("body_language_eye_contact"),
        "Audience Engagement": feedback_scores.get("audience_engagement"),
        "Language & Clarity": feedback_scores.get("language_clarity")
    }

    total_score = feedback_response.get("total_score")
    interpretation = feedback_response.get("interpretation") 
    feedback_summary = feedback_response.get("feedback_summary")  
else:
    st.warning("No feedback available! Please upload a video and analyze it first.")
    scores = {
        "Content & Organization": 0,
        "Delivery & Vocal Quality": 0,
        "Body Language & Eye Contact": 0,
        "Audience Engagement": 0,
        "Language & Clarity": 0
    }

    total_score = 0
    interpretation = ""
    feedback_summary = ""

# Calculate average score
average_score = sum(scores.values()) / len(scores)

# Determine strengths, weaknesses, and suggestions for improvement
if st.session_state.response:
    strengths = st.session_state.response.get("strengths")
    weaknesses = st.session_state.response.get("weaknesses")
    suggestions = st.session_state.response.get("suggestions")
else:
    strengths = []
    weaknesses = []
    suggestions = []

# Create three columns with equal width
col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

# Left Column: Evaluation Summary
with col1:
    st.subheader("🧾 Evaluation Summary")

    st.markdown("<br>", unsafe_allow_html=True)

    for criterion, score in scores.items():
        label_col, progress_col, score_col = st.columns([2, 3, 1])  # Adjust the ratio as needed
        with label_col:
            st.markdown(f"**{criterion}**")
        with progress_col:
            st.progress(score / 5)
        with score_col:    
            st.markdown(f"<span><b>{score}/5</b></span>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display total score
    st.markdown(f"#### 🏆 Total Score: {total_score} / 25")
    # Display average score
    st.markdown(f"#### 🎯 Average Score: {average_score:.2f} / 5")

    st.markdown("""---""")

    st.markdown("##### 🗣️ Feedback Summary:")
    # Display interpretation
    st.markdown(f"📝 **Overall Assessment**: {interpretation}")
    # Display feedback summary
    st.info(f"{feedback_summary}")


# Middle Column: Strengths, Weaknesses, and Suggestions
with col2:
    # Display strengths
    st.markdown("##### 🦾 Strengths:")
    strengths_text = '\n'.join(f"- {item}" for item in strengths)
    st.success(strengths_text)

    # Display weaknesses
    st.markdown("##### ⚠️ Weaknesses:")
    weaknesses_text = '\n'.join(f"- {item}" for item in weaknesses)
    st.error(weaknesses_text)

    # Display suggestions
    st.markdown("##### 💡 Suggestions for Improvement:")
    suggestions_text = '\n'.join(f"- {item}" for item in suggestions)
    st.warning(suggestions_text)


# Right Column: Performance Chart
with col3:
    st.subheader("📊 Performance Chart")

    # Radar Chart
    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(
        r=list(scores.values()),
        theta=list(scores.keys()),
        fill='toself',
        name='Scores'
    ))
    radar_fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5])
        ),
        showlegend=False,
        margin=dict(t=50, b=50, l=50, r=50),  # Reduced margins
        width=350,
        height=350
    )
    st.plotly_chart(radar_fig, use_container_width=True)

    st.markdown("""---""")