from typing_extensions import TypedDict, Optional
from typing import List, Literal
from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph import START, END, StateGraph
from .state import ImageState, MessageClassifier
import os
from .models import get_chat_model, get_image_gen_client
from .prompts import CREATE_IMAGE_PROMPT, CREATE_CHAT_PROMPT


def chat_agent(state: ImageState) -> ImageState:
    print('--- Chatting Based on Router ---')
    last_message = state['message'][-1]
    
    messages = [
        {
            "role": "system",
            "content": CREATE_CHAT_PROMPT
        },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    
    llm = get_chat_model()
    resp = llm.invoke(messages)
    
    return {
        "message": [{"role": "assistant", "content": resp.content}],
        "current_step": "completed"
    }

def refine_user_prompt(state: ImageState) -> ImageState:
    try:
        print('--- Refining Prompt for Image Generation ---')
        llm = get_chat_model()    
        
        last_message = state["message"][-1]
        user_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        
        prompt = f"{CREATE_IMAGE_PROMPT}\n\nUser request: {user_content}"
        response = llm.invoke(prompt)
        
        return {
            "refined_prompt": response.content,
            "current_step": "in_progress",
            "error": None
        }
    except Exception as e:
        return {
            "current_step": "error",
            "error": f"Error refining prompt: {str(e)}"
        }

def generate_images(state: ImageState) -> ImageState:
    try:
        if not state.get("refined_prompt"):
            raise ValueError("No refined prompt available")
            
        image_client = get_image_gen_client()
        
        
        image_response = image_client.images.generate(
            prompt=state["refined_prompt"],
            model="black-forest-labs/FLUX.1-schnell-Free",
            steps=4,
            n=4
        )
        
        
        image_url = []
        if hasattr(image_response, 'data'):
            # get the image url from json
            image_url = [img.url for img in image_response.data if hasattr(img, 'url')]
        else:
            image_url = [str(image_response)]
        
        return {
            "image_url": image_url,
            "current_step": "completed",
            "error": None,
            "message": [{"role": "assistant", "content": "Generated images successfully!"}]
        }
    except Exception as e:
        return {
            "current_step": "error",
            "error": f"Error generating images: {str(e)}"
        }

def handle_error(state: ImageState) -> ImageState:
    
    error_message = state.get("error", "An unknown error occurred")
    
    return {
        "message": [{"role": "assistant", "content": f"Sorry, I encountered an error: {error_message}"}],
        "current_step": "completed",
        "error": None  
    }

def classify_message(state: ImageState) -> ImageState:

    last_msg = state["message"][-1]
    
    
    content = last_msg.content 
    
    classifier_llm = get_chat_model().with_structured_output(MessageClassifier)
    
    result = classifier_llm.invoke([
        {
            "role": "system",
            "content": """
            Classify the user message as either:
            - 'image': if user asks for an image to generate, words like create, generate, draw, make an image, etc.
            - 'chat': if user asks for facts, information, solutions, or general conversation
            - 'video' : if user wants to create a video
            """
        },
        {
            "role": "user",
            "content": content
        }
    ])
    
    return {
        "message_type": result.message_type
    }

def route_decision(state: ImageState) -> str:

    message_type = state.get("message_type", "chat")
    
    if message_type == "image":
        return "prompt"
    elif message_type == "video":
        return "video"
    else:
        return "chat"

def error_check(state: ImageState) -> str:
    
    if state.get("error"):
        return "error"
    elif state.get("current_step") == "in_progress":
        return "image"
    else:
        return "end"

def completion_check(state: ImageState) -> str:

    if state.get("error"):
        return "error"
    else:
        return "end"

def create_video(state: ImageState) -> bool:
    ...

def create_image_generation_graph():
    
    workflow = StateGraph(ImageState)
    
    # Nodes
    workflow.add_node("Classify", classify_message)
    # workflow.add_node("video",  create_video)
    workflow.add_node("chat", chat_agent)
    workflow.add_node("prompt", refine_user_prompt)
    workflow.add_node("image", generate_images)
    workflow.add_node("error", handle_error)
    
    # Start
    workflow.add_edge(START, "Classify")
    
    # Route based on type of msg
    
    # workflow.add_edge("prompt", "video")
    
    workflow.add_conditional_edges(
        "Classify",
        route_decision,
        {
            "chat": "chat",
            "prompt": "prompt",
        }
    )
    
    # Chat agent goes directly to end
    workflow.add_edge("chat", END)
    
    # After refining prompt, check for errors
    workflow.add_conditional_edges(
        "prompt",
        error_check,
        {
            "image": "image",
            "error": "error",
        }
    )
    
    workflow.add_conditional_edges(
        "image",
        completion_check,
        {
            "error": "error",
            "end": END
        }
    )
    
    workflow.add_edge("error", END)
    
    return workflow.compile()

def save_graph(graph, file_name="workflow.png"):
    try:
        graph_img = graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)
        directory = os.path.dirname(file_name)
        
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(file_name, "wb") as file:
            file.write(graph_img)
            
        print(" -- Saved the Workflow --")
        return True
    except Exception as e:
        print(e)