import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from imageagents import create_image_generation_graph, save_graph

# Expose workflow for LangGraph Studio
def workflow():
    return create_image_generation_graph()

def main():
    print(" Initializing Image Gen + GPT Workflow ...")
    
    graph = workflow()
    
    # Save the graph visualization
    print("Saving workflow graph...")
    # save_graph(graph, "my_graph.png")
    
    print("\n Type 'quit' to exit")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n💭 Enter your message: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q', '/bye']:
                print("Goodbye!")
                break
            
            if not user_input:
                print("Not a Valid Input")
                continue
            
            # Process the message
            initial_state = {
                "message": [{"role": "user", "content": user_input}]
            }
            
            print("Processing...")
            response = graph.invoke(initial_state)
            
            print('AI-Response:', response["message"][1].content)

            if response.get("message_type") == "image":
                if response.get("refined_prompt"):
                    print(f" -- Refined Prompt-- : {response['refined_prompt']}")
                if response.get("image_url"):
                    print(f" -- Generated Image -- : {response['image_url']}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
