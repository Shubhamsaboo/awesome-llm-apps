# 💼 AI Recruitment Agent Team

A Streamlit application that simulates a full-service recruitment team using multiple AI agents to automate and streamline the hiring process. Each agent represents a different recruitment specialist role - from resume analysis and candidate evaluation to interview scheduling and communication - working together to provide comprehensive hiring solutions. The system combines the expertise of technical recruiters, HR coordinators, and scheduling specialists into a cohesive automated workflow.

## Features

#### Specialized AI Agents

- Technical Recruiter Agent: Analyzes resumes and evaluates technical skills
- Communication Agent: Handles professional email correspondence
- Scheduling Coordinator Agent: Manages interview scheduling and coordination
- Each agent has specific expertise and collaborates for comprehensive recruitment


#### End-to-End Recruitment Process
- Automated resume screening and analysis
- Role-specific technical evaluation
- Professional candidate communication
- Automated interview scheduling
- Integrated feedback system

## Important Things to do before running the application

- Create/Use a new Gmail account for the recruiter
- Enable 2-Step Verification and generate an App Password for the Gmail account
- The App Password is a 16 digit code (use without spaces) that should be generated here - [Google App Password](https://support.google.com/accounts/answer/185833?hl=en) Please go through the steps to generate the password - it will of the format - 'afec wejf awoj fwrv' (remove the spaces and enter it in the streamlit app) 
- Create/ Use a Zoom account and go to the Zoom App Marketplace to get the API credentials :
[Zoom Marketplace](https://marketplace.zoom.us)
- Go to Developer Dashboard and create a new app - Select Server to Server OAuth and get the credentials, You see 3 credentials - Client ID, Client Secret and Account ID
- After that, you need to add a few scopes to the app - so that the zoom link of the candidate is sent and created through the mail. 
- The Scopes are meeting:write:invite_links:admin, meeting:write:meeting:admin, meeting:write:meeting:master, meeting:write:invite_links:master, meeting:write:open_app:admin, user:read:email:admin, user:read:list_users:admin, billing:read:user_entitlement:admin, dashboard:read:list_meeting_participants:admin [last 3 are optional]

## How to Run

1. **Setup Environment**
   ```bash
   # Clone the repository
    git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
    cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team
    
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - OpenAI API key for GPT-4o access
   - Zoom API credentials (Account ID, Client ID, Client Secret)
   - Email App Password of Recruiter's Email

3. **Run the Application**
   ```bash
   streamlit run ai_recruitment_agent_team.py
   ```

## System Components

- **Resume Analyzer Agent**
  - Skills matching algorithm
  - Experience verification
  - Technical assessment
  - Selection decision making

- **Email Communication Agent**
  - Professional email drafting
  - Automated notifications
  - Feedback communication
  - Follow-up management

- **Interview Scheduler Agent**
  - Zoom meeting coordination
  - Calendar management
  - Timezone handling
  - Reminder system

- **Candidate Experience**
  - Simple upload interface
  - Real-time feedback
  - Clear communication
  - Streamlined process

## Technical Stack

- **Framework**: Phidata
- **Model**: OpenAI GPT-4o
- **Integration**: Zoom API, EmailTools Tool from Phidata
- **PDF Processing**: PyPDF2
- **Time Management**: pytz
- **State Management**: Streamlit Session State


## Disclaimer

This tool is designed to assist in the recruitment process but should not completely replace human judgment in hiring decisions. All automated decisions should be reviewed by human recruiters for final approval.

## Future Enhancements

- Integration with ATS systems
- Advanced candidate scoring
- Video interview capabilities
- Skills assessment integration
- Multi-language support
