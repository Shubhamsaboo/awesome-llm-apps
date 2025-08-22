# WebQA Agent

🌟 **Source Repository**: [https://github.com/MigoXLab/webqa-agent](https://github.com/MigoXLab/webqa-agent)

<!-- badges -->
<p align="left">
  <a href="https://github.com/MigoXLab/webqa-agent/blob/main/LICENSE"><img src="https://img.shields.io/github/license/MigoXLab/webqa-agent" alt="License"></a>
  <a href="https://github.com/MigoXLab/webqa-agent/stargazers"><img src="https://img.shields.io/github/stars/MigoXLab/webqa-agent" alt="GitHub stars"></a>
  <a href="https://github.com/MigoXLab/webqa-agent/network/members"><img src="https://img.shields.io/github/forks/MigoXLab/webqa-agent" alt="GitHub forks"></a>
  <a href="https://github.com/MigoXLab/webqa-agent/issues"><img src="https://img.shields.io/github/issues/MigoXLab/webqa-agent" alt="GitHub issues"></a>
  <a href="https://deepwiki.com/MigoXLab/webqa-agent"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>


**WebQA Agent** is an autonomous web agent that audits performance, functionality, and UX for any web product.

## 🚀 Core Features

### 📋 Feature Highlights

- **🤖 AI-Powered Testing**: WebQA Agent autonomously conducts website testing, from page crawling and test case generation to execution, achieving end-to-end functional test automation.
- **📊 Multi-Dimensional Test**: Covers core testing scenarios, including functionality, performance, user experience, and security, evaluating page load speed, design details, and links for comprehensive system quality assurance.
- **🎯 Precise Diagnostics**: Performs deep testing in real browser environments and provides actionable optimization recommendations.
- **📈 Visual Reports**: Generates detailed HTML test reports with a multi-dimensional visual presentation of results for easy analysis and tracking.


## Quick Start

### Prerequisites

- **Docker**: Ensure Docker is installed and running. If not installed, follow the [official Docker installation guide](https://docs.docker.com/get-started/get-docker/).
- **API Key**: You'll need an OpenAI API key or compatible LLM API key for the agent to function.

### Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_webqa_agent
   ```

2. **Configure the Agent**
   ```bash
   # Copy the configuration template
   cp config/config.yaml.example config/config.yaml
   
   # Edit the configuration file with your settings
   nano config/config.yaml  # or use your preferred editor
   
   # - **Target URL**: The website you want to test
   # - **LLM API Key**: Your OpenAI or compatible API key
   # - **Test Settings**: Enable/disable specific test types
   ```

4. **Launch the Agent**
   ```bash
   # Start the WebQA agent
   sh start.sh
   ```

### 💡 **Want to install from source?** 

Please visit [https://github.com/MigoXLab/webqa-agent](https://github.com/MigoXLab/webqa-agent) for source installation instructions. 

## Usage

### What Happens Next?

Once started, the agent will:
- Analyze your target website
- Run comprehensive tests (accessibility, performance, SEO, etc.)
- Generate detailed reports in the `reports/` directory
- Provide actionable recommendations for improvements

For detailed configuration options, see the [Test Configuration](#test-configuration) section below.

### Test Configuration

`webqa-agent` uses YAML configuration for test parameters:

```yaml
target:
  url: https://example.com/                       # Website URL to test
  description: example description

test_config:                                      # Test configuration
  function_test:                                  # Functional testing
    enabled: True
    type: ai                                      # default or ai
    business_objectives: example business objectives  # Recommended to include test scope, e.g., test search functionality
  ux_test:                                        # User experience testing
    enabled: True
  performance_test:                               # Performance testing
    enabled: False
  security_test:                                  # Security testing
    enabled: False

llm_config:                                       # Vision model configuration, currently supports OpenAI SDK compatible format only
  model: gpt-4.1                                  # Recommended
  api_key: your_api_key
  base_url: https://api.example.com/v1

browser_config:
  viewport: {"width": 1280, "height": 720}
  headless: False                                 # Automatically overridden to True in Docker environment
  language: zh-CN
  cookies: []
```

Please note the following important considerations when configuring and running tests:

#### 1. Functional Testing Notes

- **AI Mode**: When specifying the number of test cases to generate in the configuration file, the system may re-plan based on based on actual testing conditions. This may result in the final number of executed test cases differing from the initial configuration to ensure testing accuracy and effectiveness.

- **Default Mode**: The `default` mode of functional testing primarily verifies whether UI element clicks execute successfully, including basic interactive functions like button clicks and link navigation.

#### 2. User Experience Testing Notes

UX (User Experience) testing focuses on evaluating website interaction design, usability, and user-friendliness. The model output in the test results provides suggestions for improvement suggestions based on user experience best practices to guide development and design teams in optimization.

### View Results

Test results will be generated in the `reports` directory. Open the HTML report within the generated folder to view results.