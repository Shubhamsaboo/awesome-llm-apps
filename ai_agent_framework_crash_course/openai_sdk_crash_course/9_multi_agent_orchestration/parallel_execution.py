import asyncio
from agents import Agent, ItemHelpers, Runner, trace

# Create specialized translation agent
spanish_agent = Agent(
    name="Spanish Translator",
    instructions="You translate the user's message to Spanish. Provide natural, fluent translations."
)

# Create translation quality picker
translation_picker = Agent(
    name="Translation Quality Picker",
    instructions="""
    You are an expert in Spanish translations. 
    Given multiple Spanish translation options, pick the most natural, accurate, and fluent one.
    Explain briefly why you chose that translation.
    """
)

# Example 1: Basic parallel execution with quality selection
async def parallel_translation_example():
    """Demonstrates running the same agent multiple times in parallel for quality"""
    
    print("=== Parallel Translation with Quality Selection ===")
    
    msg = "Hello, how are you today? I hope you're having a wonderful time!"
    print(f"Original message: {msg}")
    
    # Ensure the entire workflow is a single trace
    with trace("Parallel Translation Workflow") as workflow_trace:
        print("Running 3 parallel translation attempts...")
        
        # Run 3 parallel translations
        res_1, res_2, res_3 = await asyncio.gather(
            Runner.run(spanish_agent, msg),
            Runner.run(spanish_agent, msg), 
            Runner.run(spanish_agent, msg)
        )
        
        # Extract text outputs from results
        outputs = [
            ItemHelpers.text_message_outputs(res_1.new_items),
            ItemHelpers.text_message_outputs(res_2.new_items),
            ItemHelpers.text_message_outputs(res_3.new_items)
        ]
        
        # Combine all translations for comparison
        translations = "\n\n".join([f"Translation {i+1}: {output}" for i, output in enumerate(outputs)])
        print(f"\nAll translations:\n{translations}")
        
        # Use picker agent to select best translation
        best_translation = await Runner.run(
            translation_picker,
            f"Original English: {msg}\n\nTranslations to choose from:\n{translations}"
        )
    
    print(f"\nBest translation selected: {best_translation.final_output}")
    print(f"Workflow trace ID: {workflow_trace.trace_id}")
    
    return best_translation

# Example 2: Parallel execution with different specialized agents
async def parallel_specialized_agents():
    """Shows parallel execution with different agents for diverse perspectives"""
    
    print("\n=== Parallel Execution with Specialized Agents ===")
    
    # Create different specialized agents
    formal_translator = Agent(
        name="Formal Spanish Translator",
        instructions="Translate to formal, polite Spanish using 'usted' forms."
    )
    
    casual_translator = Agent(
        name="Casual Spanish Translator", 
        instructions="Translate to casual, friendly Spanish using 'tú' forms."
    )
    
    regional_translator = Agent(
        name="Mexican Spanish Translator",
        instructions="Translate to Mexican Spanish with regional expressions and vocabulary."
    )
    
    msg = "Hey friend, want to grab some coffee later?"
    print(f"Original message: {msg}")
    
    with trace("Multi-Style Translation") as style_trace:
        print("Running parallel translations with different styles...")
        
        # Run different translation styles in parallel
        formal_result, casual_result, regional_result = await asyncio.gather(
            Runner.run(formal_translator, msg),
            Runner.run(casual_translator, msg),
            Runner.run(regional_translator, msg)
        )
        
        # Extract and display all results
        formal_text = ItemHelpers.text_message_outputs(formal_result.new_items)
        casual_text = ItemHelpers.text_message_outputs(casual_result.new_items)
        regional_text = ItemHelpers.text_message_outputs(regional_result.new_items)
        
        print(f"\nFormal style: {formal_text}")
        print(f"Casual style: {casual_text}")
        print(f"Regional style: {regional_text}")
        
        # Let user choose preferred style
        style_comparison = f"""
        Original: {msg}
        
        Formal Spanish: {formal_text}
        Casual Spanish: {casual_text}
        Mexican Spanish: {regional_text}
        """
        
        style_recommendation = await Runner.run(
            translation_picker,
            f"Compare these translation styles and recommend which is most appropriate for the context: {style_comparison}"
        )
    
    print(f"\nStyle recommendation: {style_recommendation.final_output}")
    print(f"Multi-style trace ID: {style_trace.trace_id}")
    
    return style_recommendation

# Example 3: Parallel execution for content generation diversity
async def parallel_content_generation():
    """Demonstrates parallel content generation for creative diversity"""
    
    print("\n=== Parallel Content Generation for Diversity ===")
    
    # Create content generation agents with different approaches
    creative_agent = Agent(
        name="Creative Writer",
        instructions="Write creative, engaging content with vivid imagery and storytelling."
    )
    
    informative_agent = Agent(
        name="Informative Writer", 
        instructions="Write clear, factual, informative content focused on key information."
    )
    
    persuasive_agent = Agent(
        name="Persuasive Writer",
        instructions="Write compelling, persuasive content that motivates action."
    )
    
    topic = "The benefits of learning a new language"
    print(f"Content topic: {topic}")
    
    with trace("Diverse Content Generation") as content_trace:
        print("Generating content with different writing styles in parallel...")
        
        # Generate different content approaches simultaneously
        creative_result, informative_result, persuasive_result = await asyncio.gather(
            Runner.run(creative_agent, f"Write a short paragraph about: {topic}"),
            Runner.run(informative_agent, f"Write a short paragraph about: {topic}"),
            Runner.run(persuasive_agent, f"Write a short paragraph about: {topic}")
        )
        
        # Extract content
        creative_content = ItemHelpers.text_message_outputs(creative_result.new_items)
        informative_content = ItemHelpers.text_message_outputs(informative_result.new_items)
        persuasive_content = ItemHelpers.text_message_outputs(persuasive_result.new_items)
        
        print(f"\nCreative approach:\n{creative_content}")
        print(f"\nInformative approach:\n{informative_content}")
        print(f"\nPersuasive approach:\n{persuasive_content}")
        
        # Synthesize best elements from all approaches
        synthesis_agent = Agent(
            name="Content Synthesizer",
            instructions="Combine the best elements from multiple content pieces into one cohesive, high-quality paragraph."
        )
        
        combined_content = f"""
        Topic: {topic}
        
        Creative version: {creative_content}
        
        Informative version: {informative_content}
        
        Persuasive version: {persuasive_content}
        """
        
        synthesized_result = await Runner.run(
            synthesis_agent,
            f"Create the best possible paragraph by combining elements from these approaches: {combined_content}"
        )
    
    print(f"\nSynthesized content: {synthesized_result.final_output}")
    print(f"Content generation trace ID: {content_trace.trace_id}")
    
    return synthesized_result

# Main execution
async def main():
    print("🎼 OpenAI Agents SDK - Parallel Multi-Agent Execution")
    print("=" * 60)
    
    await parallel_translation_example()
    await parallel_specialized_agents()
    await parallel_content_generation()
    
    print("\n✅ Parallel execution tutorial complete!")
    print("Parallel execution enables quality improvement through diversity and selection")

if __name__ == "__main__":
    asyncio.run(main())
