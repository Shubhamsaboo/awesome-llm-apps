# AI Recruitment Agent Team

An Agentic recruitment system built on phidata and Streamlitthat automates the technical hiring proces which helps the lives of recruiters easy. The agent team consists of multiple specialized agents working together to handle resume analysis, interview scheduling with zoom and candidate communications.

## Demo

## Features

- **Automated Resume Analysis**
  - Skills Matching based on the role requirements - [AI/ML Engineer, Frontend Engineer, Backend Engineer]
  - Experience Assessment- If the resume clears 70% of the requirements, the candidate is selected for the next round

- **Automated Communications**
  - Acceptance Email and a Technical Interview Email
  - Rejection Feedback
  - Interview Scheduling with Zoom

- **Intelligent Scheduling**
  - Automated Zoom Meeting Setup
  - Timezone Management
  - Calendar Integration
  - Reminder System

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
    cd ai_agent_tutorials/ai_recruitment_agent_team

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
