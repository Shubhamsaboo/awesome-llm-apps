# do pip install -r requirements.txt --user in the terminal
# for running the program, use  in the terminal

from pathlib import Path
import streamlit as st
import os
from dotenv import load_dotenv
import base64
import pandas as pd
from st_pages import Page, add_page_title, show_pages
from streamlit_extras.app_logo import add_logo
import cohere
import google.generativeai as palm

load_dotenv()

co = cohere.Client(os.getenv("CO_API_KEY"))
palm.configure(api_key=os.environ['PALM_API_KEY'])

# st.set_page_config(layout="wide")

#with open("app_logo.jpg", "rb") as f:
 #   data = base64.b64encode(f.read()).decode("utf-8")

  #  st.sidebar.markdown(
   #    f"""
    #    <div style="margin-top:-80%;margin-left:50%;background-position="80% 10%";>
     #      <img src="data:image/jpg;base64,{data}" width="100" height="100">
      #  </div>
       # """,
        #unsafe_allow_html=True,
   # )

# st.sidebar.header("AI4IT")
# st.sidebar.markdown("AI Interventions in APP DEV")

add_logo("app_logo1.png",height=100)

st.markdown("""
<style>
.custom-font {
    font-size:20px; color:Blue !important;
}
</style>
""", unsafe_allow_html=True)

show_pages(
        [
            Page("AI4IT.py", "Requirements", "📖"),
            # Can use :<icon-name>: or the actual icon
            Page("Design.py", "Design","📝"),
            # The pages appear in the order you pass them
            Page("Develop.py", "Development", "🛠️"),
            Page("Test.py", "Testing & QA", "🐞"),
            # Will use the default icon and name based on the filename if you don't
            # pass them
            Page("Deployment.py","Deployment","🧬"),
            Page("Hypercare.py", "Hypercare", "📟"),
        ]
    )

# add_page_title()  # Optional method to add title and icon to current page

reduce_header_height_style = """
    <style>
        .block-container {padding-top:.25rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)

st.subheader("📖 Requirements",divider="violet")
st.caption(":blue[Apply AI for Requirements related use cases]")

tab1, tab2, tab3, tab4 = st.tabs(["Requirement Summary","Functional Spec","Codegen Prompts","All-in-one"])

st.write('<style>div.row-widget.stRadio > div{flex-direction:row;} </style>', unsafe_allow_html=True)

def cohere_command_xlarge(user_prompt):
    response = co.chat(
        user_prompt,
        model='command-xlarge-nightly',
        temperature=0.7)
    return response.text

palm_defaults = {
  'model': 'models/text-bison-001',
  'temperature': 0.7,
  'candidate_count': 1,
  'top_k': 40,
  'top_p': 0.95,
  'max_output_tokens': 1024,
}

def palm_text_bison(user_prompt):
    response = palm.generate_text(
        **palm_defaults,
        prompt=user_prompt
       )
    return response.result

with tab1:
   tab1_LLM = st.radio("Model to use:",('Cohere','Llama','PaLM'),key=1)

   tab1_reqment_text=st.text_area('Enter Requirement Text: ',key=11)

   submit_tab1 = st.button('Summarize Requirement') 

   if submit_tab1:
      if tab1_reqment_text != "":
        if tab1_LLM == "Llama":
           st.write("LLama not configured") 
        elif tab1_LLM == "Cohere":
          # st.subheader("Requirement Summary:")                 
          cohere_tab1_output = cohere_command_xlarge(f"Elaborate & Summarize this requirement into detailed requirement specification for IT development: {tab1_reqment_text}")
          st.markdown('<p class="custom-font">Requirement Summary:</p>', unsafe_allow_html=True)
          st.write(cohere_tab1_output)
        elif tab1_LLM == "PaLM":
           palm_tab1_output = palm_text_bison(f"Elaborate & Summarize this requirement into detailed requirement specification for IT development: {tab1_reqment_text}")
           st.markdown('<p class="custom-font">Requirement Summary:</p>', unsafe_allow_html=True)
           st.write(palm_tab1_output)
      else:
          st.write("Enter Requirement in textbox")

with tab2:
   tab2_LLM = st.radio("Model to use:",('Cohere','Llama',"PaLM"),key=2)

   tab2_reqment_text=st.text_area('Enter Requirement Text: ',key=22)

   submit_tab2 = st.button('Generate Functional Specs') 
   
   if submit_tab2:
    if tab2_reqment_text != "":
       if tab2_LLM == "Llama":
          st.write("Llama not configured") 
       elif tab2_LLM == "Cohere":
          cohere_tab2_output = cohere_command_xlarge(f"Elaborate this requirement into detailed functional specifications. Categorize the specifications by functional modules: {tab2_reqment_text}")
          st.markdown('<p class="custom-font">Functional Specifications:</p>', unsafe_allow_html=True)
          st.write(cohere_tab2_output)
       elif tab2_LLM == "PaLM":
           palm_tab2_output = palm_text_bison(f"Elaborate this requirement into detailed functional specifications. Categorize the specifications by functional modules: {tab2_reqment_text}")
           st.markdown('<p class="custom-font">Functional Specifications:</p>', unsafe_allow_html=True)
           st.write(palm_tab2_output)
    else:
      st.write("Enter Requirement in textbox")

with tab3:
    tab3_LLM = st.radio("Model to use:",('Cohere','Llama',"PaLM"),key=3)

    tab3_reqment_text=st.text_area('Enter Requirement Text: ',key=33)

    submit_tab3 = st.button('Generate Prompt for Code Generation') 

    if submit_tab3:
       if tab3_LLM == "Llama":
          st.write("Llama not configured") 
       else:
          newline = '\n'
          codegen_prompt = (f"Elaborate the following requirement into detailed functional specifications. Categorize the specifications by functional modules. Develop the code in Java for those functional modules. Consider non-functional requirememts like scalability, performance etc. {newline} Requirement: {tab3_reqment_text}")
          st.markdown('<p class="custom-font">Prompt for Code Generation:</p>', unsafe_allow_html=True)
          st.write(codegen_prompt)

with tab4:
    tab4_LLM = st.radio("Model to use:",('Cohere','Llama','PaLM'),key=4)
    
    st.markdown("Use this feature to perform Summarize Requirement -> Functional Spec -> Prompt generation for code")

    reqment_file = st.file_uploader("Select your Requirements CSV file")

    if reqment_file is not None:
        reqment_df = pd.read_csv(reqment_file)
    else:
        st.stop()