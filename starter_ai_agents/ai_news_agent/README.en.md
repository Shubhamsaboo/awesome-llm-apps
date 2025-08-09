# AI News Agent

[中文版](./README.md)
[My github](https://github.com/hixyl/aiNewsAgent/)

`ai-news-briefing-generator` is a fully automated news processing tool. It automatically scrapes news from a specified website, uses a Large Language Model (LLM) for intelligent ranking, deduplication, summarization, and categorization, and finally generates a well-structured daily news briefing in Markdown format.

## ✨ Core Features

- **🤖 Automated Crawling & Discovery**: Starts from a seed URL and automatically discovers and scrapes article and category links from the website.
- **🏆 Two-Phase Tournament Ranking**: Innovatively uses a "Swiss-style" tournament system, featuring a "Qualification Round" and a "Finals Round," to efficiently and fairly select the most important news articles.
- **💡 Intelligent Clustering & Deduplication**: Intelligently groups similar articles into the same news topic by extracting keywords from titles, and selects the highest-scoring representative from each topic, ensuring news uniqueness and diversity.
- **🧠 Deeply Empowered by LLM**: Fully leverages a Large Language Model (LLM) to perform complex natural language tasks, serving as the core engine of the project:
    - **Link Classification**: Determines whether a link points to a specific article or a news category page.
    - **Content Ranking**: Ranks a set of news items by importance based on a user-defined "task description".
    - **In-depth Processing**: Conducts a comprehensive analysis and recreation of articles, outputting structured JSON data that includes:
        - A new, more concise title.
        - A "one-sentence summary" and a more "detailed summary".
        - Core keywords.
        - The most appropriate category.
    - **Editor's Introduction**: After all news has been processed, the AI mimics an editor-in-chief to write a high-level introduction for the day's briefing.
- **🛡️ Robust Parsing & Retries**: Features powerful LLM response parsing capabilities to reliably extract valid JSON objects from the LLM's text output. It also includes a multi-level retry mechanism with exponential backoff for both article processing and network requests, ensuring process stability and a high success rate.
- **📄 Comprehensive Reporting**:
    - Generates a **main daily briefing** (`News-Briefing-YYYY-MM-DD.md`) with a table of contents and an AI-generated introduction.
    - Creates an **individual Markdown file** for each successfully processed article for easy individual viewing.
- **🛠️ Highly Configurable**: Almost all parameters—from crawl depth and ranking logic to the number of articles to process and all LLM interaction prompts—can be easily adjusted in the `config.js` file.
- **🖥️ Rich Command-Line Interface**: Utilizes `ora` and `cli-progress` to provide an elegant, real-time, multi-stage progress bar, making the entire processing flow clear and transparent.

## 🚀 Workflow

The tool's execution flow is clearly divided into five main steps, orchestrated by `index.js`:

1.  **[Step 1/5] Crawl & Qualify**: The `crawler.js` module starts from the entry URL, recursively crawling links on pages. It then uses a multi-round, points-based "qualification tournament" to preliminarily filter for potentially valuable candidate articles from a large number of links.
2.  **[Step 2/5] Cluster & Deduplicate**: The `grouper.js` module performs keyword extraction and cluster analysis on the articles that passed qualification. It groups articles reporting on the same event and selects a "representative" for each group, thus filtering out duplicate content.
3.  **[Step 3/5] Finals Tournament**: The `ranker.js` module conducts the final "tournament ranking" on the list of unique articles. Through multiple rounds of group comparisons and point scoring, it precisely determines the importance order of each article.
4.  **[Step 4/5] Process & Summarize**: The `processor.js` module is responsible for processing the final selection of articles. It extracts the original text, calls the LLM for analysis and summarization, parses the returned JSON data, and includes a powerful built-in logic for retrying failed attempts.
5.  **[Step 5/5] Generate Final Report**: The `reporter.js` module handles the final wrap-up. It calls the LLM to generate an "Editor's Introduction" and then compiles all the processed article data into a beautifully formatted Markdown briefing.

## ⚙️ Setup & Usage

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/hixyl/aiNewsAgent.git](https://github.com/hixyl/aiNewsAgent.git)
    cd aiNewsAgent
    ```

2.  **Install Dependencies**
    ```bash
    npm install
    ```

3.  **Configure the Environment**
    - Open the `config.js` file.
    - **Crucial Configuration**: Modify `llm.studioUrl` to point to the address of your locally running LLM service that is compatible with the OpenAI API format (e.g., LM Studio, Ollama, LoLLMs).
    - **(Optional)** Adjust other settings according to your needs, such as `startUrl` (the initial website to crawl) and `taskDescription` (to define your news preferences).

4.  **Run the Application**
    ```bash
    npm start
    ```

5.  **Check the Results**
    - After the program finishes, all generated reports and log files will be saved in the `output/` directory (which is ignored by `.gitignore`).
    - Log files will be recorded in the `logs/` directory.