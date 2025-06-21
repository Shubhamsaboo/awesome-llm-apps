import random
from typing import List, Dict, Optional

class ContextManager:
    def __init__(self, context_data: List[Dict]):
        self.context_data = context_data
        self.used_contexts = set()  # Track used contexts to prevent repeats

    def select_relevant_context(self, question_type: str, focus_topics: Optional[List[str]] = None) -> str:
        """Select relevant context for question generation, prioritizing focus_topics."""
        if not self.context_data:
            return ""
        
        if focus_topics:
            relevant_contexts_set = set() # Use a set to store content to avoid duplicates
            for topic in focus_topics:
                topic_lower = topic.lower()
                for ctx in self.context_data:
                    if topic_lower in ctx['content'].lower():
                        relevant_contexts_set.add(ctx['content'])
            
            if relevant_contexts_set:
                # Convert set to list, maybe shuffle or take top N based on some criteria
                # For now, take up to 3 relevant unique contexts
                return "\n\n".join(list(relevant_contexts_set)[:3])
        
        # Fallback logic if no focus_topics or no matches found
        available_contexts = [ctx for ctx in self.context_data if ctx['content'] not in self.used_contexts]
        
        # If we've used all contexts, reset and use all contexts again
        if not available_contexts:
            self.used_contexts.clear()
            available_contexts = self.context_data
        
        if question_type == "Multiple Choice":
            concepts = [ctx for ctx in available_contexts if ctx['type'] in ['Key Definition', 'Important Fact']]
            if concepts:
                selected = concepts[:2]
                for ctx in selected:
                    self.used_contexts.add(ctx['content'])
                return "\n\n".join([ctx['content'] for ctx in selected])
        # Fill-in-the-Blank question type has been removed
        
        # Random selection with diversity
        available_for_random = available_contexts if available_contexts else self.context_data
        selected = random.sample(available_for_random, min(3, len(available_for_random)))
        for ctx in selected:
            self.used_contexts.add(ctx['content'])
        return "\n\n".join([ctx['content'] for ctx in selected])
