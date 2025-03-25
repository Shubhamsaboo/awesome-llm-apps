# 🚀 AI Software Development Agent

## Overview

AI Software Development Agent is an intelligent Streamlit application that leverages Gemini AI to assist developers in generating code across different domains. The application provides three main functionalities:

1. Frontend Website Generation
2. Backend API Development
3. Data Structures and Algorithms (DSA) Problem Solving

## 🌟 Features

- 🌐 Generate responsive HTML websites
- 🔧 Create FastAPI backend code
- 📊 Solve DSA problems with efficient implementations
- 💻 Real-time code preview and execution
- 🎨 Intuitive Streamlit interface

## 🛠 Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.8+
- Gemini API Key from Google AI Studio

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-software-development-agent.git
cd ai-software-development-agent
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## 🔑 API Key Setup

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Keep the key secure and ready to input in the application

## 🚀 Running the Application

```bash
streamlit run main.py
```

## 🔍 How It Works

### 1. Frontend Development

- **Input**: Describe the type of website (e.g., Portfolio, E-Commerce, Blog)
- **Process**:
  - Sends prompt to Gemini AI
  - Generates responsive HTML with CSS
  - Extracts pure HTML code
  - Provides live preview
- **Output**: Functional HTML website

### 2. Backend Development

- **Input**: Describe API requirements
- **Process**:
  - Sends detailed prompt to Gemini AI
  - Generates FastAPI backend code
  - Extracts pure Python code
  - Attempts to run the generated API
- **Output**: Functional Python API code

### 3. DSA Problem Solving

- **Input**: Describe the DSA problem
- **Process**:
  - Sends problem description to Gemini AI
  - Generates efficient Python solution
  - Extracts pure Python code
  - Executes and displays results
- **Output**: Solved algorithm with implementation

## 🛡 Error Handling

The application includes comprehensive error handling:
- Input validation
- Code extraction from AI responses
- Execution error capturing
- User-friendly error messages

## 📂 Project Structure

```
ai-software-development-agent/
│
├── main.py                 # Main Streamlit application
│
├── utils/
│   ├── code_extractor.py   # Utility to extract code blocks
│   └── code_execution.py   # Utility to execute Python code
│
├── frontend/
│   └── frontend_dev.py     # Frontend code generation module
│
├── backend/
│   └── backend_dev.py      # Backend code generation module
│
└── dsa/
    └── dsa_solver.py       # DSA problem solving module
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/)
- [Google Gemini AI](https://ai.google/)

## 🐛 Known Issues & Limitations

- Requires active internet connection
- Code generation depends on AI model's capabilities
- May produce varying results for complex requirements

## 📞 Support

For issues or questions, please open a GitHub issue or contact [Your Contact Information].
