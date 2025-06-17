import streamlit as st
import sys
import os
import re
from datetime import datetime

# Add parent directory to path to enable relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(grandparent_dir)

from quizmaster.database_manager import DatabaseManager
from quizmaster.insights_generator import generate_insights

def calculate_quiz_results(questions, user_answers):
    """
    Calculate quiz results and prepare data for database saving.
    Returns a tuple of: (results_dict, insight_questions, answered_questions, correct_answers, gradable_questions)
    """
    answered_questions = 0
    correct_answers = 0
    gradable_questions = 0
    
    # Prepare data for saving
    results = {
        'total_questions': len(questions),
        'answered_questions': 0,
        'correct_answers': 0,
        'completion_rate': 0,
        'score': 0
    }
    
    # Create list of questions for insight generation
    insight_questions = []
    
    # First pass: collect data for insights and results
    for i, q_data in enumerate(questions):
        q_key = f"q_{i}"
        user_ans_val = user_answers.get(q_key)
        insight_q = {
            'text': q_data['text'],
            'type': q_data['type'],
            'user_answer': user_ans_val,
            'correct_answer': q_data['answer'],
            'is_correct': False
        }
        
        if user_ans_val is not None:
            if not (isinstance(user_ans_val, str) and not user_ans_val.strip()):
                answered_questions += 1
                results['answered_questions'] = answered_questions

        # Check correctness for auto-gradable types
        if user_ans_val is not None:
            gradable_questions += 1
            q_correct_answer = q_data['answer']
            is_q_correct = False
            if q_data['type'] == "Multiple Choice":
                correct_letter_val = q_data['answer']
                user_choice_text = user_ans_val 
                actual_correct_text = ""
                
                for opt_val in q_data['options']:
                    if opt_val['letter'] == correct_letter_val:
                        actual_correct_text = opt_val['text']
                        break
                
                # More flexible comparison - strip whitespace and ignore case
                if user_choice_text and actual_correct_text and user_choice_text.strip().lower() == actual_correct_text.strip().lower():
                    is_q_correct = True
                    correct_answers += 1
            
                # Only Multiple Choice questions remain
            
            insight_q['is_correct'] = is_q_correct
            
        insight_questions.append(insight_q)
    
    results['correct_answers'] = correct_answers
    completion_rate = (answered_questions / len(questions)) * 100 if questions else 0
    score = (correct_answers / gradable_questions) * 100 if gradable_questions > 0 else 0
    results['completion_rate'] = completion_rate
    results['score'] = score
    
    return (results, insight_questions, answered_questions, correct_answers, gradable_questions)

def save_quiz_to_database(quiz_data, questions, user_answers):
    """
    Save quiz data to database and generate insights.
    Returns tuple of (session_id, insights, results)
    """
    try:
        results, insight_questions, _, _, _ = calculate_quiz_results(questions, user_answers)
        
        # Save results to database
        db = DatabaseManager()
        session_id = db.save_quiz_session(quiz_data, results)
        db.save_quiz_answers(session_id, questions, user_answers)
        
        # Generate insights
        model_used_for_quiz = quiz_data.get('model_used', 'llama3')  # Default to llama3 if not found
        insights = generate_insights(insight_questions, model_used_for_quiz)
        db.save_quiz_report(session_id, insights)
        
        return session_id, insights, results
    except Exception as e:
        st.error(f"Failed to save quiz results: {str(e)}")
        # Return default values to prevent further errors
        return None, f"Error generating insights: {str(e)}", {}

def show_quiz_page():
    st.set_page_config(
        page_title="Interactive Quiz - QuizMaster Pro", 
        page_icon="🎓", 
        layout="wide"
    )
    
    st.sidebar.page_link("streamlit_app.py", label="Quiz Setup", icon="📝")
    st.sidebar.page_link("pages/01_Interactive_Quiz.py", label="Interactive Quiz", icon="🎓")
    st.sidebar.page_link("pages/02_Saved_Quizzes.py", label="Saved Quizzes", icon="💾")
    st.sidebar.divider()

    st.title("🎓 Interactive Quiz")

    if 'quiz_data' not in st.session_state or not st.session_state.quiz_data or not st.session_state.quiz_data.get('questions'):
        st.info("👋 Please generate a quiz on the Quiz Setup page first.")
        st.page_link("streamlit_app.py", label="Quiz Setup")
        return

    quiz_data = st.session_state.quiz_data
    questions = quiz_data['questions']
    
    # Retrieve stored difficulty, default if not found (should be set by main app)
    # First check explicit config_difficulty field, then check in config dict, then fallback to Medium
    difficulty = quiz_data.get('config_difficulty', '')
    if not difficulty:
        difficulty = quiz_data.get('config', {}).get('difficulty', 'medium')
    
    # Format difficulty with proper capitalization
    if isinstance(difficulty, str):
        if difficulty.lower() == 'easy': difficulty = 'Easy'
        elif difficulty.lower() == 'medium': difficulty = 'Medium'
        elif difficulty.lower() == 'hard': difficulty = 'Hard'
        else: difficulty = 'Medium'  # Default fallback

    # Ensure quiz state variables are initialized (though main app should do this)
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {} # Should be initialized per quiz
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False

    # Quiz navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.current_question > 0:
            if st.button("⬅️ Previous"):
                st.session_state.current_question -= 1
                st.rerun()
        else:
            st.write("") # Placeholder for alignment

    with col2:
        st.write(f"Question {st.session_state.current_question + 1} of {len(questions)}")
        progress_value = (st.session_state.current_question + 1) / len(questions) if questions else 0
        st.progress(progress_value)
    
    with col3:
        if st.session_state.current_question < len(questions) - 1:
            if st.button("Next ➡️"):
                st.session_state.current_question += 1
                st.rerun()
        else:
            st.write("") # Placeholder for alignment

    # Display current question
    current_q = questions[st.session_state.current_question]
    question_key = f"q_{st.session_state.current_question}"
    
    st.subheader(f"Question {st.session_state.current_question + 1}")
    st.markdown(f"**{current_q['text']}**")
    st.markdown(f"*Type: {current_q['type']} | Difficulty: {difficulty}*")
    
    # For debugging but hidden by default
    with st.expander("Question Details", expanded=False):
        st.write("Question Structure:")
        st.json(current_q)
        st.write("Available keys:", list(current_q.keys()))
    
    # Question-specific input
    user_answer = None
    
    if current_q['type'] == "Multiple Choice" or current_q['type'] == "multiple_choice":
        # First check if 'options' exists 
        if 'options' not in current_q:
            st.error("⚠️ This multiple choice question is missing options!")
            
            # Try to find options in other common keys
            possible_option_keys = ['choices', 'answers', 'answer_options', 'answer_choices']
            found_options = None
            
            for key in possible_option_keys:
                if key in current_q and isinstance(current_q[key], list) and len(current_q[key]) > 0:
                    st.info(f"Found options in alternative field: '{key}'")
                    current_q['options'] = current_q[key]
                    found_options = True
                    break
            
            if not found_options:
                # Create dummy options as last resort
                current_q['options'] = [
                    {'letter': 'A', 'text': 'Option A (Error: No real options found)'},
                    {'letter': 'B', 'text': 'Option B (Error: No real options found)'},
                    {'letter': 'C', 'text': 'Option C (Error: No real options found)'},
                    {'letter': 'D', 'text': 'Option D (Error: No real options found)'}
                ]
                st.warning("Created placeholder options since no real options were found.")
        
        # Ensure options is a list
        if not isinstance(current_q['options'], list):
            st.error(f"Options is not a list! Type: {type(current_q['options'])}")
            if isinstance(current_q['options'], dict):
                # Try to convert dict to list
                opt_list = []
                for k, v in current_q['options'].items():
                    if k in 'ABCD':
                        opt_list.append({'letter': k, 'text': v})
                    else:
                        opt_list.append({'letter': chr(65 + len(opt_list)), 'text': f"{k}: {v}"})
                current_q['options'] = opt_list
                st.info("Converted options dictionary to list format")
            else:
                # Create default options
                current_q['options'] = [
                    {'letter': 'A', 'text': 'Option A (Error: Invalid options format)'},
                    {'letter': 'B', 'text': 'Option B (Error: Invalid options format)'},
                    {'letter': 'C', 'text': 'Option C (Error: Invalid options format)'},
                    {'letter': 'D', 'text': 'Option D (Error: Invalid options format)'}
                ]
        
        # Check if options have the expected structure with 'letter' and 'text' keys
        has_valid_structure = all('letter' in opt and 'text' in opt for opt in current_q['options'])
        if not has_valid_structure:
            # Try to fix the format on the fly
            fixed_options = []
            for i, opt in enumerate(current_q['options']):
                if isinstance(opt, dict):
                    letter = opt.get('letter', chr(65 + i))  # A, B, C, D
                    
                    # Look for text in various common keys
                    text = None
                    for text_key in ['text', 'content', 'value', 'option', 'answer']:
                        if text_key in opt:
                            text = opt[text_key]
                            break
                    
                    if text is None:
                        text = str(opt)  # Convert whole dict to string as last resort
                elif isinstance(opt, str):
                    # Check if string starts with a letter like "A: text"
                    import re
                    match = re.match(r'^([A-D])[.:\)\s-]\s*(.*)', opt)
                    if match:
                        letter = match.group(1)
                        text = match.group(2)
                    else:
                        letter = chr(65 + i)  # A, B, C, D
                        text = opt
                else:
                    letter = chr(65 + i)  # A, B, C, D
                    text = str(opt)
                
                fixed_options.append({'letter': letter, 'text': text})
            
            current_q['options'] = fixed_options
            st.info("ℹ️ Options have been reformatted to display correctly")
        
        # Display options with their letters (A, B, C, D) 
        options_with_letters = [f"{opt['letter']}: {opt['text']}" for opt in current_q['options']]
        
        # Map for looking up the option by display text
        option_map = {f"{opt['letter']}: {opt['text']}": opt['text'] for opt in current_q['options']}
        
        # Get previous answer if exists for radio button
        previous_answer_index = None
        if question_key in st.session_state.user_answers:
            user_previous_answer = st.session_state.user_answers[question_key]
            # Look for the matching option with letter prefix
            for i, opt_text in enumerate(options_with_letters):
                if opt_text.endswith(user_previous_answer):
                    previous_answer_index = i
                    break
        
        # Use a clear layout for options with radio buttons
        st.markdown("### Choose your answer:")
        st.info("Select one of the options below:")
        selected_option = st.radio(
            "Answer options",  # Provide a meaningful label for accessibility
            options_with_letters,
            key=question_key,
            index=previous_answer_index,
            horizontal=False,  # Vertical layout for better readability
            label_visibility="collapsed"  # Hide the label since we use markdown header above
        )
        
        # Add a divider before the Show Full Answer button
        st.divider()
        
        # Extract just the option text (without the letter prefix) to store in user_answers
        if selected_option:
            # Get just the option text after the letter prefix (e.g., "A: Option text" -> "Option text")
            user_answer = option_map.get(selected_option, selected_option)
        else:
            user_answer = None
        
    # Open-Ended question type has been removed
    
    # Add a divider before the Show Full Answer button
        st.divider()
        
    # Fill-in-the-Blank question type has been removed
    
    # Store user answer
    if user_answer is not None: # Check if widget returned a value
        # For radio, None means no selection yet.
        if user_answer: 
            st.session_state.user_answers[question_key] = user_answer
    
    # Show answer and explanation
    if st.button("💡 Show Full Answer & Explanation", key=f"show_{question_key}"):
        st.info("**Correct Answer:**")
        correct_option_text = "" # For MCQ
        if current_q['type'] == "Multiple Choice":
            correct_letter = current_q['answer']
            for opt in current_q['options']:
                if opt['letter'] == correct_letter:
                    correct_option_text = opt['text']
                    break
            st.write(f"{correct_letter}: {correct_option_text}")
        else:
            st.write(str(current_q['answer']))
        
        # Always show explanation if available
        if 'explanation' in current_q and current_q['explanation']:
            st.success("**Explanation:**")
            st.write(current_q['explanation'])
        
        # Show user's answer if provided and compare
        if question_key in st.session_state.user_answers:
            user_ans_display = st.session_state.user_answers[question_key]
            if user_ans_display or isinstance(user_ans_display, str): # Check if answer is not None or empty string for some types
                is_correct = False
                if current_q['type'] == "Multiple Choice":
                    # Compare just the text portion of the user answer with the correct option text
                    for opt in current_q['options']:
                        if opt['letter'] == current_q['answer'] and opt['text'] == user_ans_display:
                            is_correct = True
                            break

                # All question types are auto-graded
                # Only Multiple Choice questions remain
                if is_correct:
                    st.success(f"✅ Your answer '{user_ans_display}' is correct!")
                else:
                    st.error(f"❌ Your answer '{user_ans_display}' is incorrect.")


    # Final results
    if st.session_state.current_question == len(questions) - 1:
        st.divider()
        col1_final, col2_final, col3_final = st.columns(3)
        
        with col1_final:
            if st.button("📊 Show Final Results", type="primary"):
                st.session_state.show_results = True
                st.rerun() # Rerun to display results section
                
        with col2_final:
            if st.button("👀 Show All Answers", type="secondary"):
                st.session_state['show_all_answers'] = True
                st.rerun()
                
        with col3_final:
            if st.button("💾 Save Quiz Results", type="secondary"):
                try:
                    # Save the quiz to database using our utility function
                    session_id, insights, results = save_quiz_to_database(quiz_data, questions, st.session_state.user_answers)
                    
                    if session_id:  # Check if save was successful
                        # Get key metrics for display
                        answered_questions = results['answered_questions']
                        total_questions = results['total_questions']
                        score = results['score']
                        
                        st.success(f"✅ Quiz results saved successfully! You answered {answered_questions}/{total_questions} questions with a score of {score:.1f}%")
                        # Show a button to view saved quizzes
                        st.page_link("pages/02_Saved_Quizzes.py", label="View Saved Quizzes", icon="📚")
                    else:
                        st.error("Failed to save quiz results. Please try again.")
                except Exception as e:
                    st.error(f"Error saving quiz results: {str(e)}")

    if st.session_state.show_results:
        st.divider()
        st.header("🏆 Quiz Results")
        
        try:
            # Save the quiz to database and get results using our utility function
            session_id, insights, results = save_quiz_to_database(quiz_data, questions, st.session_state.user_answers)
            
            # Calculate detailed metrics for display
            (_, _, answered_questions, correct_answers, gradable_questions) = calculate_quiz_results(
                questions, st.session_state.user_answers
            )
            
            completion_rate = results.get('completion_rate', 0)
            score = results.get('score', 0)
        except Exception as e:
            st.error(f"Error processing quiz results: {str(e)}")
            # Set default values to prevent further errors
            session_id, insights = None, "Unable to generate insights due to error"
            answered_questions, correct_answers, gradable_questions = 0, 0, 0
            completion_rate, score = 0, 0
        
        # Notification about saving
        st.success("✅ Quiz results automatically saved to the database!")
        
        # Display results
        col1_res, col2_res, col3_res = st.columns(3)
        with col1_res:
            st.metric("Questions Answered", f"{answered_questions}/{len(questions)}")
        with col2_res:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        # Only show score if there are gradable questions
        if gradable_questions > 0:
            with col3_res:
                 st.metric("Score (Auto-graded)", f"{score:.1f}% ({correct_answers}/{gradable_questions})")
        else:
            with col3_res:
                st.write("No auto-gradable questions.")

        st.metric("Model Used for Quiz Generation", quiz_data.get('model_used', 'Unknown'))
        
        # Display insights with better formatting
        st.divider()
        st.header("📊 Knowledge Insights")
        
        # Check if insights contain markdown headings
        if "# " in insights or "## " in insights:
            # If insights already have markdown formatting, display as is
            st.markdown(insights)
        else:
            # Otherwise, display as regular text
            st.write(insights)
        
        # Display selected concepts if available
        if 'selected_concepts' in quiz_data and quiz_data['selected_concepts']:
            st.divider()
            st.header("🎯 Concepts Tested")
            st.write("This quiz was focused on the following concepts:")
            for concept in quiz_data['selected_concepts']:
                st.markdown(f"• {concept}")
        
        st.divider()
        
        # Database diagnostic section
        with st.expander("🔧 Database Diagnostic"):
            if st.button("Test Database Connection"):
                try:
                    db_test = DatabaseManager()
                    success, message = db_test.test_connection()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Failed to test database connection: {str(e)}")
        
        # Save quiz section
        with st.expander("💾 Save This Quiz"):
            quiz_title = st.text_input("Quiz Title", 
                                     value=f"{quiz_data['model_used']} Quiz - {datetime.now().strftime('%Y-%m-%d')}")
            quiz_description = st.text_area("Description (optional)")
            tags = st.text_input("Tags (comma separated, optional)")
            
            if st.button("💾 Save Quiz", type="primary"):
                if not quiz_title.strip():
                    st.error("Please enter a title for the quiz")
                else:
                    try:
                        tags_list = [t.strip() for t in tags.split(",")] if tags else []
                        # Create a new database manager instance
                        database_manager = DatabaseManager()
                        quiz_id = database_manager.save_quiz(
                            title=quiz_title,
                            quiz_data=quiz_data,
                            description=quiz_description,
                            tags=tags_list
                        )
                        st.success(f"Quiz saved successfully! (ID: {quiz_id})")
                    except Exception as e:
                        st.error(f"Failed to save quiz: {str(e)}")
                        st.error("Please check that the database is running and accessible.")
        
        if st.button("🔄 Take Quiz Again"):
            st.session_state.current_question = 0
            st.session_state.user_answers = {}
            st.session_state.show_results = False
            st.rerun()
        
        if st.button("🏠 Back to Quiz Setup"):
            st.switch_page("streamlit_app.py")
            
        if st.button("📚 View Saved Quizzes"):
            st.switch_page("pages/02_Saved_Quizzes.py")


    # Show all answers when requested
    if st.session_state.get('show_all_answers', False):
        st.divider()
        st.header("📝 All Quiz Answers")
        
        for i, q_data in enumerate(questions):
            with st.expander(f"Question {i+1}: {q_data['text'][:80]}...", expanded=True):
                st.markdown(f"**Question:** {q_data['text']}")
                
                # Display answer based on question type
                st.markdown("**Correct Answer:**")
                if q_data['type'] == "Multiple Choice":
                    correct_letter = q_data['answer']
                    correct_text = ""
                    for opt in q_data['options']:
                        if opt['letter'] == correct_letter:
                            correct_text = opt['text']
                            break
                    st.success(f"{correct_letter}: {correct_text}")
                else:
                    st.success(str(q_data['answer']))
                
                # Show explanation if available
                if 'explanation' in q_data and q_data['explanation']:
                    st.markdown("**Explanation:**")
                    st.info(q_data['explanation'])
                
                # Show user's answer if available
                user_ans_key = f"q_{i}"
                if user_ans_key in st.session_state.user_answers:
                    user_ans = st.session_state.user_answers[user_ans_key]
                    st.markdown("**Your Answer:**")
                    st.write(user_ans)
        
        # Button to hide all answers
        if st.button("Hide All Answers"):
            st.session_state['show_all_answers'] = False
            st.rerun()


if __name__ == "__main__":
    show_quiz_page()
