from crewai import Agent
from crewai_tools import FileReadTool


# Function to initialize agents
def initialize_agents(llm,file_name,Temp_dir):
    file_read_tool = FileReadTool()
    return {
        "Data_Reader_Agent": Agent(
            role='Data_Reader_Agent',
            goal="Read the uploaded dataset and provide it to other agents.",
            backstory="Responsible for reading the uploaded dataset.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[file_read_tool]
        ),
        "Problem_Definition_Agent": Agent(
            role='Problem_Definition_Agent',
            goal="Clarify the machine learning problem the user wants to solve.",
            backstory="Expert in defining machine learning problems.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        ),
        "EDA_Agent": Agent(
            role='EDA_Agent',
            goal="Perform all possible Exploratory Data Analysis (EDA) on the data provided by the user.",
            backstory="Specializes in conducting comprehensive EDA to understand the data characteristics, distributions, and relationships.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        ),
        "Feature_Engineering_Agent": Agent(
            role='Feature_Engineering_Agent',
            goal="Perform feature engineering on the data based on the EDA results provided by the EDA agent.",
            backstory="Expert in deriving new features, transforming existing features, and preprocessing data to prepare it for modeling.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        ),
        "Model_Recommendation_Agent": Agent(
            role='Model_Recommendation_Agent',
            goal="Suggest the most suitable machine learning models.",
            backstory="Expert in recommending machine learning algorithms.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        ),
        "Starter_Code_Generator_Agent": Agent(
            role='Starter_Code_Generator_Agent',
            goal=f"Generate starter Python code for the project. Always give dataset name as '{Temp_dir}/{file_name}",
            backstory="Code wizard for generating starter code templates.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        ),
        "Code_Modification_Agent": Agent(
            role='Code_Modification_Agent',
            goal="Modify the generated Python code based on user suggestions.",
            backstory="Expert in adapting code according to user feedback.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        ),
        # "Code_Runner_Agent": Agent(
        #     role='Code_Runner_Agent',
        #     goal="Run the generated Python code and catch any errors.",
        #     backstory="Debugging expert.",
        #     verbose=True,
        #     allow_delegation=True,
        #     llm=llm,
        # ),
        "Code_Debugger_Agent": Agent(
            role='Code_Debugger_Agent',
            goal="Debug the generated Python code.",
            backstory="Seasoned code debugger.",
            verbose=True,
            allow_delegation=False,
            llm=llm,
        ),
        "Compiler_Agent":Agent(
            role = "Code_compiler",
            goal = "Extract only the python code.",
            backstory = "You are the compiler which extract only the python code.",
            verbose = True,
            allow_delegation = False,
            llm = llm
        )
    }
