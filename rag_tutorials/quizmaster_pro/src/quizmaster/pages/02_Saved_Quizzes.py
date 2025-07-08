import streamlit as st
import sys
import os
import json

# Add parent directory to path to enable relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(grandparent_dir)

from quizmaster.database_manager import DatabaseManager

def show_saved_quizzes_page():
    st.set_page_config(
        page_title="Saved Quizzes - QuizMaster Pro", 
        page_icon="💾", 
        layout="wide"
    )
    
    st.sidebar.page_link("streamlit_app.py", label="Quiz Setup", icon="📝")
    st.sidebar.page_link("pages/01_Interactive_Quiz.py", label="Interactive Quiz", icon="🎓")
    st.sidebar.page_link("pages/02_Saved_Quizzes.py", label="Saved Quizzes", icon="💾")
    st.sidebar.divider()

    st.title("💾 Saved Quizzes")
    st.markdown("Browse and load previously saved quizzes")

    # Initialize database manager
    db = DatabaseManager()
    
    # Refresh button
    if st.button("🔄 Refresh Quiz List"):
        st.rerun()
    
    # Get all saved quizzes
    saved_quizzes = db.list_saved_quizzes()
    
    if not saved_quizzes:
        st.info("No saved quizzes found. Generate and save some quizzes first!")
        st.page_link("streamlit_app.py", label="Go to Quiz Setup", icon="📋")
        return
    
    # Display quizzes in a table
    st.subheader(f"Found {len(saved_quizzes)} saved quizzes")
    
    # Create columns for the table header
    col1, col2, col3, col4, col5 = st.columns([1, 3, 4, 2, 2])
    with col1:
        st.markdown("**ID**")
    with col2:
        st.markdown("**Title**")
    with col3:
        st.markdown("**Description**")
    with col4:
        st.markdown("**Created**")
    with col5:
        st.markdown("**Actions**")
    
    st.divider()
    
    # Display each quiz with load and delete buttons
    for quiz in saved_quizzes:
        col1, col2, col3, col4, col5 = st.columns([1, 3, 4, 2, 2])
        
        with col1:
            st.write(quiz['id'])
        with col2:
            # Add an expander to show more details including concepts
            with st.expander(f"{quiz['title']}"):
                # Get full quiz data to check for concepts
                full_quiz = db.get_saved_quiz(quiz['id'])
                if full_quiz and 'quiz_data' in full_quiz:
                    quiz_data = full_quiz['quiz_data']
                    
                    # Show basic quiz info
                    st.write(f"**Questions:** {len(quiz_data.get('questions', []))}")
                    st.write(f"**Model Used:** {quiz_data.get('model_used', 'Unknown')}")
                    
                    # Show selected concepts if available
                    if 'selected_concepts' in quiz_data and quiz_data['selected_concepts']:
                        st.write("**Focused Concepts:**")
                        for concept in quiz_data['selected_concepts']:
                            st.markdown(f"• {concept}")
                else:
                    st.write("*Detailed quiz data not available*")
            
            # Regular quiz title outside the expander
            st.write(quiz['title'])
        with col3:
            st.write(quiz['description'] if quiz['description'] else "")
        with col4:
            # Format date nicely
            created_date = quiz['created_at'].strftime("%Y-%m-%d %H:%M")
            st.write(created_date)
        with col5:
            # Create a unique key for each button
            load_key = f"load_{quiz['id']}"
            delete_key = f"delete_{quiz['id']}"
            
            # Load button
            if st.button("📝 Load", key=load_key):
                # Get the full quiz data
                full_quiz = db.get_saved_quiz(quiz['id'])
                if full_quiz and 'quiz_data' in full_quiz:
                    # Store in session state
                    st.session_state.quiz_data = full_quiz['quiz_data']
                    st.session_state.current_question = 0
                    st.session_state.user_answers = {}
                    st.session_state.show_results = False
                    
                    # Success message and redirect
                    st.success(f"Quiz '{full_quiz['title']}' loaded successfully!")
                    st.page_link("pages/01_Interactive_Quiz.py", label="Go to Quiz", icon="➡️")
                    st.rerun()
                else:
                    st.error(f"Failed to load quiz with ID {quiz['id']}")
            
            # Delete button
            if st.button("🗑️ Delete", key=delete_key):
                if db.delete_saved_quiz(quiz['id']):
                    st.success(f"Quiz with ID {quiz['id']} deleted successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to delete quiz with ID {quiz['id']}")
        
        st.divider()
    
    # Link back to main page
    st.page_link("streamlit_app.py", label="Back to Quiz Setup")

if __name__ == "__main__":
    show_saved_quizzes_page()
