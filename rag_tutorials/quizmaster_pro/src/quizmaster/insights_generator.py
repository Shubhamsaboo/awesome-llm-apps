import json
import os
import logging
from litellm import completion
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsightsGenerator:
    """Enhanced Insights Generator with advanced analytics and ContextGem integration"""
    
    def __init__(self, vector_manager=None, database_manager=None):
        """
        Initialize the insights generator with optional VectorManager and DatabaseManager.
        
        Args:
            vector_manager: VectorManager instance for document analysis
            database_manager: DatabaseManager instance for historical data
        """
        self.vector_manager = vector_manager
        self.database_manager = database_manager
        
    def generate_comprehensive_insights(self, questions: List[Dict], user_answers: Dict[str, Any], 
                                      quiz_metadata: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """
        Generate comprehensive insights using advanced analytics and document context.
        
        Args:
            questions: List of question dictionaries
            user_answers: Dictionary of user answers
            quiz_metadata: Metadata about the quiz and source document
            model_name: Model to use for insight generation
            
        Returns:
            Dictionary containing comprehensive insights and analytics
        """
        logger.info(f"Generating comprehensive insights using model: {model_name}")
        
        # Prepare enhanced quiz analysis
        quiz_analysis = self._analyze_quiz_performance(questions, user_answers)
        
        # Get document context if VectorManager is available
        document_context = self._get_document_context(quiz_metadata)
        
        # Get historical performance if DatabaseManager is available
        historical_context = self._get_historical_context(quiz_metadata)
        
        # Generate learning pattern analysis
        learning_patterns = self._analyze_learning_patterns(quiz_analysis, historical_context)
        
        # Generate personalized recommendations
        recommendations = self._generate_personalized_recommendations(
            quiz_analysis, document_context, learning_patterns
        )
        
        # Generate the main insight report using LLM
        insight_report = self._generate_llm_insights(
            quiz_analysis, document_context, learning_patterns, 
            recommendations, model_name
        )
        
        # Compile comprehensive results
        comprehensive_insights = {
            "timestamp": datetime.now().isoformat(),
            "quiz_metadata": quiz_metadata,
            "performance_analytics": quiz_analysis,
            "document_context": document_context,
            "learning_patterns": learning_patterns,
            "personalized_recommendations": recommendations,
            "insight_report": insight_report,
            "actionable_items": self._extract_actionable_items(recommendations),
            "study_plan": self._generate_study_plan(quiz_analysis, recommendations),
            "progress_indicators": self._calculate_progress_indicators(quiz_analysis, historical_context)
        }
        
        return comprehensive_insights
    
    def _analyze_quiz_performance(self, questions: List[Dict], user_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quiz performance with detailed metrics"""
        
        total_questions = len(questions)
        answered_questions = 0
        correct_answers = 0
        incorrect_answers = 0
        unanswered_questions = 0
        
        # Performance by question type
        performance_by_type = {}
        # Performance by difficulty (if available)
        performance_by_difficulty = {}
        # Topic analysis
        topic_performance = {}
        # Detailed question analysis
        question_analysis = []
        
        for i, question in enumerate(questions):
            q_id = str(i)
            user_answer = user_answers.get(q_id)
            
            # Basic metrics
            if user_answer is not None and user_answer != "":
                answered_questions += 1
                is_correct = self._check_answer_correctness(question, user_answer)
                if is_correct:
                    correct_answers += 1
                else:
                    incorrect_answers += 1
            else:
                unanswered_questions += 1
                is_correct = False
            
            # Question type analysis
            q_type = question.get('type', 'unknown')
            if q_type not in performance_by_type:
                performance_by_type[q_type] = {'total': 0, 'correct': 0, 'answered': 0}
            performance_by_type[q_type]['total'] += 1
            if user_answer is not None and user_answer != "":
                performance_by_type[q_type]['answered'] += 1
                if is_correct:
                    performance_by_type[q_type]['correct'] += 1
            
            # Difficulty analysis
            difficulty = question.get('difficulty', 'medium')
            if difficulty not in performance_by_difficulty:
                performance_by_difficulty[difficulty] = {'total': 0, 'correct': 0, 'answered': 0}
            performance_by_difficulty[difficulty]['total'] += 1
            if user_answer is not None and user_answer != "":
                performance_by_difficulty[difficulty]['answered'] += 1
                if is_correct:
                    performance_by_difficulty[difficulty]['correct'] += 1
            
            # Topic analysis (extract from question context)
            topic = self._extract_question_topic(question)
            if topic not in topic_performance:
                topic_performance[topic] = {'total': 0, 'correct': 0, 'answered': 0}
            topic_performance[topic]['total'] += 1
            if user_answer is not None and user_answer != "":
                topic_performance[topic]['answered'] += 1
                if is_correct:
                    topic_performance[topic]['correct'] += 1
            
            # Detailed question analysis
            question_analysis.append({
                'question_id': i,
                'question_text': question['text'][:100] + "..." if len(question['text']) > 100 else question['text'],
                'type': q_type,
                'difficulty': difficulty,
                'topic': topic,
                'user_answer': user_answer,
                'correct_answer': question.get('correct_answer'),
                'is_correct': is_correct,
                'explanation': question.get('explanation', '')
            })
        
        # Calculate percentages and rates
        accuracy_rate = (correct_answers / answered_questions * 100) if answered_questions > 0 else 0
        completion_rate = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Calculate confidence scores
        type_confidence = self._calculate_type_confidence(performance_by_type)
        difficulty_confidence = self._calculate_difficulty_confidence(performance_by_difficulty)
        
        return {
            "basic_metrics": {
                "total_questions": total_questions,
                "answered_questions": answered_questions,
                "correct_answers": correct_answers,
                "incorrect_answers": incorrect_answers,
                "unanswered_questions": unanswered_questions,
                "accuracy_rate": round(accuracy_rate, 1),
                "completion_rate": round(completion_rate, 1)
            },
            "performance_by_type": performance_by_type,
            "performance_by_difficulty": performance_by_difficulty,
            "topic_performance": topic_performance,
            "confidence_scores": {
                "overall_confidence": round((accuracy_rate + completion_rate) / 2, 1),
                "type_confidence": type_confidence,
                "difficulty_confidence": difficulty_confidence
            },
            "question_analysis": question_analysis,
            "weakest_areas": self._identify_weakest_areas(topic_performance, performance_by_type),
            "strongest_areas": self._identify_strongest_areas(topic_performance, performance_by_type)
        }
    
    def _get_document_context(self, quiz_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced document context using VectorManager if available"""
        
        if not self.vector_manager:
            return {"available": False, "message": "VectorManager not available"}
        
        try:
            # Get document information
            doc_id = quiz_metadata.get('document_id')
            if not doc_id:
                return {"available": False, "message": "No document ID in quiz metadata"}
            
            # Retrieve document with extracted concepts
            document = self.vector_manager.get_document(doc_id)
            if not document:
                return {"available": False, "message": "Document not found"}
            
            # Extract relevant concepts and aspects
            extracted_concepts = document.get('extracted_concepts', {})
            extracted_aspects = document.get('extracted_aspects', {})
            
            # Analyze document structure and content
            document_analysis = {
                "document_type": self._extract_concept_value(extracted_concepts, 'Document Type'),
                "main_subject": self._extract_concept_value(extracted_concepts, 'Main Topic'), # Changed from Main Subject to Main Topic
                "key_topics": self._extract_concept_values(extracted_concepts, 'Key Topics'), # This might come from an Aspect
                "key_arguments": self._extract_concept_values(extracted_concepts, 'Key Arguments'),
                "conclusions": self._extract_concept_values(extracted_concepts, 'Conclusions'),
                "technical_terms_mentioned": self._extract_concept_values(extracted_concepts, 'Technical Terms'),
                "key_people_mentioned": self._extract_concept_values(extracted_concepts, 'Key People'),
                "key_organizations_mentioned": self._extract_concept_values(extracted_concepts, 'Key Organizations'),
                "locations_mentioned": self._extract_concept_values(extracted_concepts, 'Locations'),
                "key_dates_mentioned": self._extract_concept_values(extracted_concepts, 'Key Dates'), # Assuming DateConcept stores them as list of strings
                "key_figures_mentioned": self._extract_concept_values(extracted_concepts, 'Key Figures'), # Assuming NumericalConcept stores them as list of strings
                "technical_level": self._assess_technical_level(document),
                "content_density": self._assess_content_density(document),
                "concept_coverage": len(extracted_concepts), # Number of top-level concept types extracted
                "aspect_coverage": len(extracted_aspects)  # Number of top-level aspects extracted
            }
            
            # Get summary information from aspects if available
            # The 'Key Information' aspect might contain 'Summary Points'
            summary_items = []
            key_info_aspect = extracted_aspects.get('Key Information', {})
            if key_info_aspect:
                summary_items = key_info_aspect.get('concepts', {}).get('Summary Points', {}).get('items', [])
            
            # If not found in aspects, try a direct concept if it exists
            if not summary_items:
                 summary_concept_items = extracted_concepts.get('Summary Points', {}).get('items', [])
                 summary_items = [item.get('value') for item in summary_concept_items if item.get('value')]

            key_points = [item.get('value', '') for item in summary_items[:5]]  # Top 5 key points
            
            return {
                "available": True,
                "document_analysis": document_analysis,
                "extracted_concepts": extracted_concepts,
                "key_points": key_points,
                "filename": document.get('filename', 'Unknown'),
                "format": document.get('format', 'Unknown'),
                "content_length": len(document.get('content', '')),
                "metadata": document.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Error getting document context: {str(e)}")
            return {"available": False, "error": str(e)}
    
    def _get_historical_context(self, quiz_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical performance context using DatabaseManager if available"""
        
        if not self.database_manager:
            return {"available": False, "message": "DatabaseManager not available"}
        
        try:
            # Get historical quiz sessions for the same document or similar topics
            document_name = quiz_metadata.get('document_name', '')
            
            # This would require extending DatabaseManager with analytics methods
            # For now, return a placeholder structure
            return {
                "available": True,
                "previous_attempts": 0,  # Would query database
                "improvement_trend": "stable",  # Would calculate from historical data
                "best_performance": 0.0,  # Would query for best score
                "average_performance": 0.0,  # Would calculate average
                "last_attempt_date": None,  # Would get from database
                "learning_velocity": "steady"  # Would calculate improvement rate
            }
            
        except Exception as e:
            logger.error(f"Error getting historical context: {str(e)}")
            return {"available": False, "error": str(e)}
    
    def _analyze_learning_patterns(self, quiz_analysis: Dict[str, Any], 
                                 historical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze learning patterns and identify trends"""
        
        basic_metrics = quiz_analysis['basic_metrics']
        confidence_scores = quiz_analysis['confidence_scores']
        
        # Identify learning style based on performance patterns
        learning_style = self._identify_learning_style(quiz_analysis)
        
        # Identify knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(quiz_analysis)
        
        # Assess learning efficiency
        learning_efficiency = self._assess_learning_efficiency(quiz_analysis, historical_context)
        
        # Predict improvement areas
        improvement_potential = self._predict_improvement_areas(quiz_analysis)
        
        return {
            "learning_style_indicators": learning_style,
            "knowledge_gaps": knowledge_gaps,
            "learning_efficiency": learning_efficiency,
            "improvement_potential": improvement_potential,
            "cognitive_load_assessment": self._assess_cognitive_load(quiz_analysis),
            "retention_indicators": self._assess_retention_indicators(quiz_analysis)
        }
    
    def _generate_personalized_recommendations(self, quiz_analysis: Dict[str, Any],
                                             document_context: Dict[str, Any],
                                             learning_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized learning recommendations"""
        
        recommendations = {
            "immediate_actions": [],
            "study_strategies": [],
            "resource_suggestions": [],
            "practice_recommendations": [],
            "long_term_goals": []
        }
        
        # Immediate actions based on performance
        accuracy = quiz_analysis['basic_metrics']['accuracy_rate']
        completion = quiz_analysis['basic_metrics']['completion_rate']
        
        # Handle perfect/excellent performance (90%+)
        if accuracy >= 90 and completion >= 90:
            recommendations["immediate_actions"].append({
                "priority": "low",
                "action": "Explore advanced topics",
                "reason": f"Excellent performance ({accuracy}% accuracy) indicates readiness for more challenging material"
            })
            recommendations["long_term_goals"].append("Seek out more complex applications of these concepts")
            recommendations["long_term_goals"].append("Consider teaching or mentoring others in this subject")
            recommendations["long_term_goals"].append("Explore related advanced topics to broaden knowledge")
        elif accuracy >= 80:
            recommendations["immediate_actions"].append({
                "priority": "low",
                "action": "Consolidate understanding",
                "reason": f"Good performance ({accuracy}% accuracy) shows solid grasp with room for refinement"
            })
        elif accuracy < 60:
            recommendations["immediate_actions"].append({
                "priority": "high",
                "action": "Review fundamental concepts",
                "reason": f"Accuracy rate of {accuracy}% indicates gaps in basic understanding"
            })
        
        if completion < 80:
            recommendations["immediate_actions"].append({
                "priority": "medium",
                "action": "Practice time management",
                "reason": f"Completion rate of {completion}% suggests timing issues"
            })
        
        # Study strategies based on learning patterns
        learning_style = learning_patterns.get('learning_style_indicators', {})
        if learning_style.get('visual_learner_indicator', False):
            recommendations["study_strategies"].append({
                "strategy": "Visual learning techniques",
                "methods": ["Create concept maps", "Use diagrams and charts", "Watch educational videos"],
                "effectiveness": "high"
            })
        
        # Topic-specific recommendations
        weak_areas = quiz_analysis.get('weakest_areas', [])
        for area in weak_areas[:3]:  # Focus on top 3 weak areas
            recommendations["practice_recommendations"].append({
                "topic": area['topic'],
                "current_performance": f"{area['accuracy']:.1f}%",
                "target_improvement": "20-30%",
                "specific_actions": [
                    f"Review {area['topic']} concepts in the source material",
                    f"Practice additional {area['topic']} exercises",
                    f"Seek supplementary resources on {area['topic']}"
                ]
            })
        
        # Document-specific recommendations
        if document_context.get('available'):
            doc_analysis = document_context.get('document_analysis', {})
            main_subject = doc_analysis.get('main_subject', 'the subject')
            
            recommendations["resource_suggestions"].append({
                "type": "document_review",
                "suggestion": f"Re-read sections related to {main_subject}",
                "focus_areas": document_context.get('key_points', [])[:3]
            })
        
        return recommendations
    
    def _generate_llm_insights(self, quiz_analysis: Dict[str, Any], document_context: Dict[str, Any],
                             learning_patterns: Dict[str, Any], recommendations: Dict[str, Any],
                             model_name: str) -> str:
        """Generate the main insight report using LLM with enhanced context"""
        
        # Normalize model name
        original_model_name = model_name
        model_name = model_name.replace('ollama/', '')
        
        # Prepare enhanced prompt with rich context
        context_info = self._prepare_context_for_llm(quiz_analysis, document_context, learning_patterns)
        
        prompt = f"""
As an expert educational analyst, provide a comprehensive learning insights report based on the following detailed analysis:

{context_info}

CRITICAL INSTRUCTIONS:
- ALWAYS reference the specific questions answered in your analysis.
- Use the actual question content and user responses provided.
- Be specific about what topics, key arguments, technical terms, people, or dates were covered and how the user performed on each.
- If accuracy rate is 85% or higher, this indicates EXCELLENT performance that should be celebrated.
- If accuracy rate is 100%, this indicates PERFECT performance - focus on congratulating and suggesting advanced challenges.
- If accuracy rate is 70-84%, this indicates GOOD performance with room for refinement.
- If accuracy rate is below 70%, then focus on improvement areas.

Please structure your response with these sections:

## 📊 PERFORMANCE OVERVIEW
- Reference the SPECIFIC QUESTIONS answered and performance on each.
- Mention the actual topics/concepts, including any specific 'Technical Terms', 'Key Arguments', 'Key People', or 'Key Dates' that were tested.
- If accuracy is 90%+, emphasize EXCELLENT performance with specific examples.
- If accuracy is 100%, celebrate PERFECT performance citing the actual questions mastered.
- Highlight the most significant findings based on actual quiz content.

## 🎯 LEARNING ANALYSIS
- Analyze performance patterns based on the SPECIFIC QUESTION ANALYSIS provided.
- Reference the actual question types and difficulties the user encountered.
- Consider if performance varies across different types of extracted information (e.g., good on 'Key Topics' but struggled with 'Technical Terms' or 'Key Dates').
- For high performers (85%+), focus on mastery indicators from the specific questions.
- Identify learning style preferences based on actual performance data.
- Assess knowledge retention based on the specific topics covered.

## 📈 STRENGTHS & ACHIEVEMENTS
- Celebrate what the learner did well on SPECIFIC QUESTIONS and topics, including any demonstrated understanding of 'Key Arguments' or 'Conclusions' from the document.
- Reference the actual subject areas where they demonstrated mastery.
- Highlight positive learning indicators from the actual quiz performance.
- For perfect scores, emphasize exceptional understanding of the specific concepts tested.

## 🔍 IMPROVEMENT OPPORTUNITIES
- Base recommendations on the SPECIFIC AREAS identified in the analysis.
- If the document context revealed 'Key Arguments' or 'Technical Terms' and the user struggled with related questions, suggest focused review.
- For high performers (85%+), suggest ADVANCED challenges in the actual subject areas covered, perhaps involving deeper analysis of the 'Key Arguments' or application of 'Technical Terms'.
- For perfect scores (100%), focus on next-level applications of the specific topics tested.
- For lower performers, identify specific concepts, 'Technical Terms', 'Key People', or 'Key Dates' from the quiz that need attention.
- Always maintain encouraging tone while being specific about the content.

## 🛠️ PERSONALIZED RECOMMENDATIONS
- Base all recommendations on the SPECIFIC TOPICS and concepts from the quiz, cross-referencing with extracted 'Key Arguments', 'Technical Terms', etc., from the document context.
- For excellent performance: Suggest advanced applications of the actual subject matter covered.
- For good performance: Suggest deeper exploration of the specific concepts tested.
- For struggling performance: Provide targeted review of the specific areas missed.
- Include both immediate and long-term recommendations tied to the actual content.

## 🎓 NEXT STEPS & MOTIVATION
- Suggest next steps based on the SPECIFIC SUBJECT AREAS covered in the quiz.
- For high achievers: Challenge them with advanced applications of the actual topics.
- For perfect scores: Suggest exploration of related advanced concepts in the same subject area.
- Always provide encouraging guidance that acknowledges their specific achievements.
- Set appropriate difficulty level for next challenges in the same subject domain.

IMPORTANT: Your analysis must be grounded in the specific question content, topics, and performance data provided, as well as the DOCUMENT CONTEXT (like 'Key Arguments', 'Technical Terms'). Avoid generic statements - always reference the actual quiz content and user performance on specific questions and topics.
"""
        
        try:
            # Determine provider and generate insights
            if model_name.startswith("gpt-"):
                logger.info(f"Using OpenAI model: {model_name}")
                response = completion(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert educational analyst specializing in personalized learning insights and adaptive education strategies."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
            else:
                logger.info(f"Using Ollama model: {model_name}")
                response = completion(
                    model=f"ollama/{model_name}",
                    messages=[
                        {"role": "system", "content": "You are an expert educational analyst specializing in personalized learning insights and adaptive education strategies."},
                        {"role": "user", "content": prompt}
                    ],
                    api_base="http://localhost:11434",
                    temperature=0.7,
                    max_tokens=2000,
                    stream=False
                )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM insights: {str(e)}")
            return self._generate_fallback_report(quiz_analysis, recommendations)
    
    def _prepare_context_for_llm(self, quiz_analysis: Dict[str, Any], document_context: Dict[str, Any],
                                learning_patterns: Dict[str, Any]) -> str:
        """Prepare rich context information for LLM prompt"""
        
        basic_metrics = quiz_analysis['basic_metrics']
        question_analysis_list = quiz_analysis.get('question_analysis', []) # Renamed to avoid conflict
        
        context = f"""
QUIZ PERFORMANCE DATA:
- Total Questions: {basic_metrics['total_questions']}
- Accuracy Rate: {basic_metrics['accuracy_rate']}% ({basic_metrics['correct_answers']} out of {basic_metrics['answered_questions']} answered correctly)
- Completion Rate: {basic_metrics['completion_rate']}%

DOCUMENT CONTEXT:
- Document Type: {document_context.get('document_analysis', {}).get('document_type', 'N/A')}
- Main Subject/Topic: {document_context.get('document_analysis', {}).get('main_subject', 'N/A')}
- Key Topics from Document: {', '.join(document_context.get('document_analysis', {}).get('key_topics', []))}
- Key Arguments from Document: {', '.join(document_context.get('document_analysis', {}).get('key_arguments', []))}
- Conclusions from Document: {', '.join(document_context.get('document_analysis', {}).get('conclusions', []))}
- Technical Terms Mentioned: {', '.join(document_context.get('document_analysis', {}).get('technical_terms_mentioned', []))}
- Key People Mentioned: {', '.join(document_context.get('document_analysis', {}).get('key_people_mentioned', []))}
- Key Dates Mentioned: {', '.join(document_context.get('document_analysis', {}).get('key_dates_mentioned', []))}

SPECIFIC QUESTION ANALYSIS:
"""
        # Append detailed question analysis to context
        for qa_item in question_analysis_list:
            context += f"- Q{qa_item['question_id']+1} ({qa_item['type']}, {qa_item['difficulty']}, Topic: {qa_item['topic']}): User answered '{qa_item['user_answer']}', Correct: {qa_item['is_correct']}. Question: {qa_item['question_text']}\n"
        
        # Add specific details about each question
        for i, question_detail in enumerate(question_analysis_list[:5]):  # Show up to 5 questions for context
            status = "✓ CORRECT" if question_detail['is_correct'] else "✗ INCORRECT"
            context += f"Question {i+1}: {question_detail['question_text'][:80]}...\n"
            context += f"  - User answered: {question_detail['user_answer']}\n"
            context += f"  - Correct answer: {question_detail['correct_answer']}\n"
            context += f"  - Result: {status}\n"
            context += f"  - Type: {question_detail['type']}, Difficulty: {question_detail['difficulty']}\n\n"
        
        context += f"PERFORMANCE BY QUESTION TYPE:\n"
        for q_type, stats in quiz_analysis['performance_by_type'].items():
            accuracy = (stats['correct'] / stats['answered'] * 100) if stats['answered'] > 0 else 0
            context += f"- {q_type}: {accuracy:.1f}% accuracy ({stats['correct']}/{stats['answered']})\n"
        
        context += f"\nPERFORMANCE BY DIFFICULTY:\n"
        for difficulty, stats in quiz_analysis['performance_by_difficulty'].items():
            accuracy = (stats['correct'] / stats['answered'] * 100) if stats['answered'] > 0 else 0
            context += f"- {difficulty}: {accuracy:.1f}% accuracy ({stats['correct']}/{stats['answered']})\n"
        
        # Add strongest areas first (for positive reinforcement)
        strong_areas = quiz_analysis.get('strongest_areas', [])
        if strong_areas:
            context += f"\nSTRONGEST PERFORMANCE AREAS:\n"
            for area in strong_areas[:3]:
                context += f"- {area['topic']}: {area['accuracy']:.1f}% accuracy (mastered)\n"
        
        # Add weakest areas
        weak_areas = quiz_analysis.get('weakest_areas', [])
        if weak_areas:
            context += f"\nAREAS NEEDING ATTENTION:\n"
            for area in weak_areas[:3]:
                context += f"- {area['topic']}: {area['accuracy']:.1f}% accuracy\n"
        
        # Add document context if available
        if document_context.get('available'):
            doc_analysis = document_context['document_analysis']
            context += f"\nDOCUMENT CONTEXT:\n"
            context += f"- Subject: {doc_analysis.get('main_subject', 'Unknown')}\n"
            context += f"- Document Type: {doc_analysis.get('document_type', 'Unknown')}\n"
            context += f"- Technical Level: {doc_analysis.get('technical_level', 'Unknown')}\n"
            
            key_points = document_context.get('key_points', [])
            if key_points:
                context += f"- Key Topics from Document: {', '.join(key_points[:3])}\n"
        
        # IMPORTANT PERFORMANCE INTERPRETATION
        if basic_metrics['accuracy_rate'] == 100:
            context += f"\n🎯 PERFORMANCE INTERPRETATION: PERFECT SCORE - User answered ALL questions correctly (100% accuracy)\n"
        elif basic_metrics['accuracy_rate'] >= 90:
            context += f"\n🎯 PERFORMANCE INTERPRETATION: EXCELLENT PERFORMANCE - User scored {basic_metrics['accuracy_rate']}% which is outstanding\n"
        elif basic_metrics['accuracy_rate'] >= 80:
            context += f"\n🎯 PERFORMANCE INTERPRETATION: GOOD PERFORMANCE - User scored {basic_metrics['accuracy_rate']}% showing solid understanding\n"
        else:
            context += f"\n🎯 PERFORMANCE INTERPRETATION: NEEDS IMPROVEMENT - User scored {basic_metrics['accuracy_rate']}% indicating areas to focus on\n"
        
        return context
    
    # Helper methods for various analyses
    def _check_answer_correctness(self, question: Dict, user_answer: Any) -> bool:
        """Check if user answer is correct"""
        # If the question already has is_correct field (from previous processing), use it
        if 'is_correct' in question:
            return bool(question['is_correct'])
            
        correct_answer = question.get('correct_answer', '')
        q_type = question.get('type', 'multiple_choice')
          # Only multiple choice questions remain
        return str(user_answer).strip().lower() == str(correct_answer).strip().lower()
    
    def _extract_question_topic(self, question: Dict) -> str:
        """Extract meaningful topic from question for analysis"""
        # Try to get topic from question metadata first
        if 'topic' in question and question['topic'].strip():
            return question['topic']
        elif 'category' in question and question['category'].strip():
            return question['category']
        
        # Try to extract meaningful topic from question text
        text = question['text']
        
        # Look for key programming/technical concepts
        technical_patterns = [
            r'\b(DRY|SOLID|REST|API|HTTP|JSON|XML|SQL|NoSQL|OOP|MVC|CRUD)\b',
            r'\b(algorithm|data structure|database|framework|library|method|function|class|object|variable)\b',
            r'\b(python|javascript|java|html|css|react|node|django|flask|spring)\b',
            r'\b(design pattern|best practice|principle|methodology|approach)\b'
        ]
        
        import re
        for pattern in technical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].upper() if matches[0].upper() in ['DRY', 'SOLID', 'REST', 'API', 'HTTP', 'JSON', 'XML', 'SQL', 'OOP', 'MVC', 'CRUD'] else matches[0].lower()
        
        # Extract meaningful noun phrases (avoid question words and fragments)
        # Remove question words and common filler words
        stop_words = {'what', 'which', 'how', 'when', 'where', 'why', 'who', 'does', 'is', 'are', 'will', 'would', 'could', 'should', 'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from'}
        
        # Split into words and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Take first few meaningful words that might represent the topic
        if len(meaningful_words) >= 2:
            # Look for noun-like words (ending in common noun patterns)
            topic_candidates = []
            for i, word in enumerate(meaningful_words[:5]):  # Check first 5 meaningful words
                # Skip if it looks like a verb or question fragment
                if word.endswith(('ing', 'ed', 'ly')):
                    continue
                topic_candidates.append(word)
            
            if topic_candidates:
                # Return up to 2 words that seem to form a topic
                return ' '.join(topic_candidates[:2]).title()
        
        # Fallback: use question type
        q_type = question.get('type', 'general')
        if q_type != 'general':
            return f"{q_type.replace('_', ' ').title()} Questions"
        
        return 'General Knowledge'
    
    def _extract_concept_value(self, concepts: Dict, concept_name: str) -> str:
        """Extract value from ContextGem extracted concepts"""
        concept_data = concepts.get(concept_name, {})
        items = concept_data.get('items', [])
        return items[0].get('value', 'Unknown') if items else 'Unknown'
    
    def _extract_concept_values(self, concepts: Dict, concept_name: str) -> List[str]:
        """Extract multiple values from ContextGem extracted concepts"""
        concept_data = concepts.get(concept_name, {})
        items = concept_data.get('items', [])
        return [item.get('value', '') for item in items]
    
    def _assess_technical_level(self, document: Dict) -> str:
        """Assess technical level of document"""
        content = document.get('content', '')
        # Simple heuristic based on content complexity
        technical_indicators = ['algorithm', 'implementation', 'analysis', 'methodology', 'framework']
        matches = sum(1 for word in technical_indicators if word in content.lower())
        
        if matches >= 3:
            return 'high'
        elif matches >= 1:
            return 'medium'
        else:
            return 'basic'
    
    def _assess_content_density(self, document: Dict) -> str:
        """Assess content density of document"""
        content = document.get('content', '')
        words = len(content.split())
        
        if words > 5000:
            return 'high'
        elif words > 2000:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_type_confidence(self, performance_by_type: Dict) -> Dict[str, float]:
        """Calculate confidence scores by question type"""
        confidence = {}
        for q_type, stats in performance_by_type.items():
            if stats['answered'] > 0:
                accuracy = stats['correct'] / stats['answered']
                completion = stats['answered'] / stats['total']
                confidence[q_type] = round((accuracy + completion) / 2 * 100, 1)
            else:
                confidence[q_type] = 0.0
        return confidence
    
    def _calculate_difficulty_confidence(self, performance_by_difficulty: Dict) -> Dict[str, float]:
        """Calculate confidence scores by difficulty level"""
        confidence = {}
        for difficulty, stats in performance_by_difficulty.items():
            if stats['answered'] > 0:
                accuracy = stats['correct'] / stats['answered']
                completion = stats['answered'] / stats['total']
                confidence[difficulty] = round((accuracy + completion) / 2 * 100, 1)
            else:
                confidence[difficulty] = 0.0
        return confidence
    
    def _identify_weakest_areas(self, topic_performance: Dict, type_performance: Dict) -> List[Dict]:
        """Identify weakest performing areas"""
        weak_areas = []
        
        # Analyze by topic
        for topic, stats in topic_performance.items():
            if stats['answered'] > 0:
                accuracy = stats['correct'] / stats['answered'] * 100
                if accuracy < 60:  # Less than 60% accuracy
                    weak_areas.append({
                        'type': 'topic',
                        'topic': topic,
                        'accuracy': accuracy,
                        'questions': stats['total']
                    })
        
        # Analyze by question type
        for q_type, stats in type_performance.items():
            if stats['answered'] > 0:
                accuracy = stats['correct'] / stats['answered'] * 100
                if accuracy < 60:
                    weak_areas.append({
                        'type': 'question_type',
                        'topic': f"{q_type} questions",
                        'accuracy': accuracy,
                        'questions': stats['total']
                    })
        
        # Sort by accuracy (worst first)
        return sorted(weak_areas, key=lambda x: x['accuracy'])
    
    def _identify_strongest_areas(self, topic_performance: Dict, type_performance: Dict) -> List[Dict]:
        """Identify strongest performing areas"""
        strong_areas = []
        
        # Analyze by topic
        for topic, stats in topic_performance.items():
            if stats['answered'] > 0:
                accuracy = stats['correct'] / stats['answered'] * 100
                if accuracy >= 80:  # 80% or higher accuracy
                    strong_areas.append({
                        'type': 'topic',
                        'topic': topic,
                        'accuracy': accuracy,
                        'questions': stats['total']
                    })
        
        # Sort by accuracy (best first)
        return sorted(strong_areas, key=lambda x: x['accuracy'], reverse=True)
    
    def _identify_learning_style(self, quiz_analysis: Dict) -> Dict[str, Any]:
        """Identify learning style indicators from performance patterns"""
        # This is a simplified heuristic - in reality, this would be more sophisticated
        type_performance = quiz_analysis['performance_by_type']
        
        indicators = {}
        
        # Visual learner indicators
        visual_types = ['multiple_choice', 'true_false']
        visual_performance = sum(type_performance.get(t, {}).get('correct', 0) for t in visual_types)
        visual_total = sum(type_performance.get(t, {}).get('answered', 0) for t in visual_types)
        
        if visual_total > 0:
            indicators['visual_learner_indicator'] = (visual_performance / visual_total) > 0.7
        
        # Analytical learner indicators
        analytical_types = []  # No analytical question types remain
        analytical_performance = sum(type_performance.get(t, {}).get('correct', 0) for t in analytical_types)
        analytical_total = sum(type_performance.get(t, {}).get('answered', 0) for t in analytical_types)
        
        if analytical_total > 0:
            indicators['analytical_learner_indicator'] = (analytical_performance / analytical_total) > 0.7
        
        return indicators
    
    def _identify_knowledge_gaps(self, quiz_analysis: Dict) -> List[str]:
        """Identify specific knowledge gaps"""
        gaps = []
        
        # Check weak areas
        weak_areas = quiz_analysis.get('weakest_areas', [])
        for area in weak_areas:
            if area['accuracy'] < 50:
                gaps.append(f"Fundamental understanding of {area['topic']}")
            elif area['accuracy'] < 70:
                gaps.append(f"Applied knowledge of {area['topic']}")
        
        return gaps[:5]  # Return top 5 gaps
    
    def _assess_learning_efficiency(self, quiz_analysis: Dict, historical_context: Dict) -> Dict[str, Any]:
        """Assess learning efficiency metrics"""
        basic_metrics = quiz_analysis['basic_metrics']
        
        efficiency = {
            "time_efficiency": "unknown",  # Would need timing data
            "accuracy_efficiency": "high" if basic_metrics['accuracy_rate'] > 80 else "medium" if basic_metrics['accuracy_rate'] > 60 else "low",
            "completion_efficiency": "high" if basic_metrics['completion_rate'] > 90 else "medium" if basic_metrics['completion_rate'] > 70 else "low"
        }
        
        return efficiency
    
    def _predict_improvement_areas(self, quiz_analysis: Dict) -> List[Dict]:
        """Predict areas with highest improvement potential"""
        improvement_areas = []
        
        # Areas where user struggled but showed some understanding
        weak_areas = quiz_analysis.get('weakest_areas', [])
        for area in weak_areas:
            if 40 <= area['accuracy'] <= 70:  # Moderate performance suggests potential
                improvement_areas.append({
                    'area': area['topic'],
                    'current_performance': area['accuracy'],
                    'improvement_potential': 'high',
                    'reason': 'Shows partial understanding with room for growth'
                })
        
        return improvement_areas
    
    def _assess_cognitive_load(self, quiz_analysis: Dict) -> Dict[str, Any]:
        """Assess cognitive load indicators"""
        basic_metrics = quiz_analysis['basic_metrics']
        
        # Assess cognitive load based on completion and accuracy patterns
        completion_rate = basic_metrics['completion_rate']
        accuracy_rate = basic_metrics['accuracy_rate']
        
        # High cognitive load indicators
        if completion_rate < 70 and accuracy_rate < 60:
            cognitive_load = "high"
            indicators = ["Low completion and accuracy suggest cognitive overload"]
        elif completion_rate < 80 or accuracy_rate < 70:
            cognitive_load = "medium"
            indicators = ["Moderate performance suggests manageable cognitive load"]
        else:
            cognitive_load = "low"
            indicators = ["Good performance suggests appropriate cognitive load"]
        
        return {
            "cognitive_load_level": cognitive_load,
            "indicators": indicators,
            "recommendations": self._get_cognitive_load_recommendations(cognitive_load)
        }
    
    def _get_cognitive_load_recommendations(self, cognitive_load: str) -> List[str]:
        """Get recommendations based on cognitive load assessment"""
        if cognitive_load == "high":
            return [
                "Break study sessions into smaller chunks",
                "Focus on one concept at a time",
                "Use spaced repetition techniques",
                "Take regular breaks during study"
            ]
        elif cognitive_load == "medium":
            return [
                "Maintain current study pace",
                "Consider using visual aids",
                "Practice active recall techniques"
            ]
        else:
            return [
                "Consider increasing study complexity",
                "Explore advanced topics",
                "Help others to reinforce learning"
            ]
    
    def _assess_retention_indicators(self, quiz_analysis: Dict) -> Dict[str, Any]:
        """Assess retention indicators from performance patterns"""
        basic_metrics = quiz_analysis['basic_metrics']
        difficulty_performance = quiz_analysis['performance_by_difficulty']
        
        retention_score = basic_metrics['accuracy_rate']
        
        # Analyze retention patterns across difficulty levels
        retention_patterns = []
        for difficulty, stats in difficulty_performance.items():
            if stats['answered'] > 0:
                accuracy = stats['correct'] / stats['answered'] * 100
                if accuracy > 80:
                    retention_patterns.append(f"Strong retention for {difficulty} questions")
                elif accuracy > 60:
                    retention_patterns.append(f"Moderate retention for {difficulty} questions")
                else:
                    retention_patterns.append(f"Weak retention for {difficulty} questions")
        
        return {
            "overall_retention_score": round(retention_score, 1),
            "retention_patterns": retention_patterns,
            "retention_level": "high" if retention_score > 80 else "medium" if retention_score > 60 else "low"
        }
    
    def _extract_actionable_items(self, recommendations: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract actionable items from recommendations"""
        actionable_items = []
        
        # Extract immediate actions
        for action in recommendations.get('immediate_actions', []):
            actionable_items.append({
                "category": "immediate",
                "priority": action.get('priority', 'medium'),
                "item": action.get('action', ''),
                "reason": action.get('reason', '')
            })
        
        # Extract practice recommendations
        for practice in recommendations.get('practice_recommendations', []):
            actionable_items.append({
                "category": "practice",
                "priority": "medium",
                "item": f"Practice {practice.get('topic', 'identified areas')}",
                "reason": f"Current performance: {practice.get('current_performance', 'unknown')}"
            })
        
        # Extract study strategies
        for strategy in recommendations.get('study_strategies', []):
            actionable_items.append({
                "category": "strategy",
                "priority": "low",
                "item": strategy.get('strategy', ''),
                "reason": f"Effectiveness: {strategy.get('effectiveness', 'unknown')}"
            })
        
        return actionable_items
    
    def _generate_study_plan(self, quiz_analysis: Dict[str, Any], 
                           recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured study plan"""
        
        weak_areas = quiz_analysis.get('weakest_areas', [])
        strong_areas = quiz_analysis.get('strongest_areas', [])
        
        study_plan = {
            "immediate_focus": [],
            "weekly_goals": [],
            "long_term_objectives": [],
            "study_schedule": {
                "daily_minutes": 30,
                "sessions_per_week": 5,
                "focus_rotation": []
            }
        }
        
        # Immediate focus areas (next 1-2 weeks)
        for area in weak_areas[:2]:  # Top 2 weakest areas
            study_plan["immediate_focus"].append({
                "topic": area['topic'],
                "target_improvement": "15-20%",
                "estimated_time": "3-5 hours",
                "methods": ["Review source material", "Practice exercises", "Create summaries"]
            })
        
        # Weekly goals (next month)
        accuracy = quiz_analysis['basic_metrics']['accuracy_rate']
        completion = quiz_analysis['basic_metrics']['completion_rate']
        
        if accuracy < 70:
            study_plan["weekly_goals"].append("Improve overall accuracy by 10-15%")
        if completion < 90:
            study_plan["weekly_goals"].append("Complete all quiz questions within time limit")
        
        study_plan["weekly_goals"].append("Review and practice top 3 challenging topics")
        
        # Long-term objectives (2-3 months)
        study_plan["long_term_objectives"] = [
            "Achieve 85%+ accuracy across all question types",
            "Demonstrate mastery in previously weak areas",
            "Apply knowledge to new, related contexts"
        ]
        
        # Study schedule rotation
        focus_areas = [area['topic'] for area in weak_areas[:3]]
        if focus_areas:
            study_plan["study_schedule"]["focus_rotation"] = focus_areas
        
        return study_plan
    
    def _calculate_progress_indicators(self, quiz_analysis: Dict[str, Any], 
                                     historical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate progress indicators and benchmarks"""
        
        basic_metrics = quiz_analysis['basic_metrics']
        
        # Current performance indicators
        current_indicators = {
            "accuracy_level": self._get_performance_level(basic_metrics['accuracy_rate']),
            "completion_level": self._get_performance_level(basic_metrics['completion_rate']),
            "overall_grade": self._calculate_overall_grade(basic_metrics),
            "areas_mastered": len(quiz_analysis.get('strongest_areas', [])),
            "areas_needing_work": len(quiz_analysis.get('weakest_areas', []))
        }
        
        # Progress benchmarks
        benchmarks = {
            "next_accuracy_target": min(90, basic_metrics['accuracy_rate'] + 15),
            "next_completion_target": min(100, basic_metrics['completion_rate'] + 10),
            "mastery_threshold": 85,
            "improvement_timeline": "2-4 weeks"
        }
        
        # Historical comparison (placeholder - would use actual historical data)
        historical_comparison = {
            "improvement_since_last": "No previous data",
            "learning_velocity": "Establishing baseline",
            "consistency_score": "New learner"
        }
        
        return {
            "current_indicators": current_indicators,
            "benchmarks": benchmarks,
            "historical_comparison": historical_comparison,
            "milestone_progress": self._calculate_milestone_progress(basic_metrics)
        }
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level description for a score"""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "satisfactory"
        elif score >= 60:
            return "needs improvement"
        else:
            return "requires attention"
    
    def _calculate_overall_grade(self, basic_metrics: Dict[str, Any]) -> str:
        """Calculate an overall grade based on performance"""
        accuracy = basic_metrics['accuracy_rate']
        completion = basic_metrics['completion_rate']
        
        # Weighted average (accuracy 70%, completion 30%)
        weighted_score = (accuracy * 0.7) + (completion * 0.3)
        
        if weighted_score >= 90:
            return "A"
        elif weighted_score >= 80:
            return "B"
        elif weighted_score >= 70:
            return "C"
        elif weighted_score >= 60:
            return "D"
        else:
            return "F"
    
    def _calculate_milestone_progress(self, basic_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate progress toward learning milestones"""
        accuracy = basic_metrics['accuracy_rate']
        completion = basic_metrics['completion_rate']
        
        milestones = {
            "basic_understanding": {
                "target": 60,
                "current": accuracy,
                "achieved": accuracy >= 60,
                "progress": min(100, (accuracy / 60) * 100)
            },
            "proficiency": {
                "target": 75,
                "current": accuracy,
                "achieved": accuracy >= 75,
                "progress": min(100, (accuracy / 75) * 100)
            },
            "mastery": {
                "target": 85,
                "current": accuracy,
                "achieved": accuracy >= 85,
                "progress": min(100, (accuracy / 85) * 100)
            },
            "completion_excellence": {
                "target": 95,
                "current": completion,
                "achieved": completion >= 95,
                "progress": min(100, (completion / 95) * 100)
            }
        }
        
        return milestones
    
    def _generate_fallback_report(self, quiz_analysis: Dict[str, Any], 
                                 recommendations: Dict[str, Any]) -> str:
        """Generate a fallback insight report when LLM is unavailable"""
        
        basic_metrics = quiz_analysis['basic_metrics']
        weak_areas = quiz_analysis.get('weakest_areas', [])
        strong_areas = quiz_analysis.get('strongest_areas', [])
        
        report = f"""
# 📊 PERFORMANCE OVERVIEW

You completed {basic_metrics['answered_questions']}/{basic_metrics['total_questions']} questions with {basic_metrics['accuracy_rate']:.1f}% accuracy.

**Key Metrics:**
- Accuracy Rate: {basic_metrics['accuracy_rate']:.1f}%
- Completion Rate: {basic_metrics['completion_rate']:.1f}%
- Questions Correct: {basic_metrics['correct_answers']}/{basic_metrics['answered_questions']}

# 🎯 LEARNING ANALYSIS

Based on your performance patterns, this quiz has revealed both strengths and areas for improvement.

# 📈 STRENGTHS & ACHIEVEMENTS

"""
        
        if strong_areas:
            report += "**Strong Performance Areas:**\n"
            for area in strong_areas[:3]:
                report += f"- {area['topic']}: {area['accuracy']:.1f}% accuracy\n"
        else:
            report += "You showed consistent effort across all question types.\n"
        
        report += f"""
# 🔍 IMPROVEMENT OPPORTUNITIES

"""
        
        if weak_areas:
            report += "**Areas Needing Attention:**\n"
            for area in weak_areas[:3]:
                report += f"- {area['topic']}: {area['accuracy']:.1f}% accuracy - Focus on reviewing fundamental concepts\n"
        
        report += f"""
# 🛠️ PERSONALIZED RECOMMENDATIONS

**Immediate Actions:**
"""
        
        for action in recommendations.get('immediate_actions', []):
            report += f"- {action['action']}: {action['reason']}\n"
        
        report += f"""
**Study Strategies:**
- Review material related to your lowest-scoring topics
- Practice similar questions to reinforce understanding
- Break study sessions into manageable chunks
- Focus on understanding concepts rather than memorization

# 🎓 NEXT STEPS & MOTIVATION

Your quiz performance provides valuable insights into your learning progress. Focus on the identified improvement areas while building on your strengths. Remember that learning is a process, and each quiz helps you identify what you know and what needs more attention.

**Recommended Next Steps:**
1. Review the topics where you scored below 60%
2. Practice additional questions in those areas
3. Retake a similar quiz in 1-2 weeks to measure improvement

Keep up the good work and stay committed to continuous learning!
"""
        
        return report.strip()


# Legacy function for backward compatibility
def generate_insights(questions, model_name: str):
    """
    Legacy function for backward compatibility.
    Generate basic insights based on quiz performance.
    
    Args:
        questions: List of question dictionaries with user answers and correctness
        model_name: The name of the model to use for insights generation
    
    Returns:
        String containing personalized insights report
    """
    logger.warning("Using legacy generate_insights function. Consider upgrading to InsightsGenerator class.")
    
    # Convert legacy format to new format
    user_answers = {}
    for i, q in enumerate(questions):
        user_answers[str(i)] = q.get('user_answer')        # Ensure is_correct is set
        if 'is_correct' not in q and 'user_answer' in q and 'correct_answer' in q:
            # All questions can be automatically evaluated now
            q['is_correct'] = str(q['user_answer']).strip().lower() == str(q['correct_answer']).strip().lower()
    
    # Create basic insights generator
    insights_gen = InsightsGenerator()
    
    # Generate comprehensive insights
    comprehensive_insights = insights_gen.generate_comprehensive_insights(
        questions=questions,
        user_answers=user_answers,
        quiz_metadata={},
        model_name=model_name
    )
    
    return comprehensive_insights['insight_report']
