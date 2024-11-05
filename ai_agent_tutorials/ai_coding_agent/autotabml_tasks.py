from crewai import Task
# Function to create tasks based on user inputs
def create_tasks(func_call,user_question,file_name, data_upload, df, suggestion, edited_code, debugger, agents):
    info = df.info()
    tasks = []
    if(func_call == "Process"):
        tasks.append(Task(
                description=f"Clarify the ML problem: {user_question}",
                agent=agents["Problem_Definition_Agent"],
                expected_output="A clear and concise definition of the ML problem."
            )
            )
        
        if data_upload:
            tasks.extend([
                Task(
                    description=f"Evaluate the data provided by the file name . This is the data: {df}",
                    agent=agents["EDA_Agent"],
                    expected_output="An assessment of the EDA and preprocessing like dataset info, missing value, duplication, outliers etc. on the data provided"
                ),
                Task(
                    description=f"Feature Engineering on data {df} based on EDA output: {info}",
                    agent=agents["Feature_Engineering_Agent"],
                    expected_output="An assessment of the Featuring Engineering and preprocessing like handling missing values, handling duplication, handling outliers, feature encoding, feature scaling etc. on the data provided"
                )
            ])

        tasks.extend([
            Task(
                description="Suggest suitable ML models.",
                agent=agents["Model_Recommendation_Agent"],
                expected_output="A list of suitable ML models."
            ),
            Task(
                description=f"Generate starter Python code based on feature engineering, where column names are {df.columns.tolist()}. Generate only the code without any extra text",
                agent=agents["Starter_Code_Generator_Agent"],
                expected_output="Starter Python code."
            ),
        ])
    if(func_call == "Modify"):
        if suggestion:
            tasks.append(
                Task(
                    description=f"Modify the already generated code {edited_code} according to the suggestion: {suggestion} \n\n Do not generate entire new code.",
                    agent=agents["Code_Modification_Agent"],
                    expected_output="Modified code."
                )
            )
    if(func_call == "Debug"):
        if debugger:
            tasks.append(
                Task(
                    description=f"Debug and fix any errors for data with column names {df.columns.tolist()} with data as {df} in the generated code: {edited_code}  \n\n According to the debugging: {debugger}. \n\n Do not generate entire new code. Just remove the error in the code by modifying only necessary parts of the code.",
                    agent=agents["Code_Debugger_Agent"],
                    expected_output="Debugged and successfully executed code."
                )
            )
    tasks.append(
        Task(
            description = "Your job is to only extract python code from string",
            agent = agents["Compiler_Agent"],
            expected_output = "Running python code."
        )
    )

    return tasks
