## 🛡️ AI Comment Moderation Agent

Paste the comments under a post and get each one sorted into **show**, **review** or **hide**. The app asks a decision model one typed question per comment and gets back a probability for each answer, not generated text. Your policy is two thresholds on that probability, and you can move them after the run without calling the model again.

It uses [Trio-Spark](https://github.com/machinefi/trio-spark), a hosted decision model, through the System One request shape (`POST /v1/systemone`).

### Features
- **One decision per comment**: a `choice` question with two options, `show` and `hide`. You get `P(hide)` back in a single call.
- **Policy as thresholds**: auto-hide above one value, send to a human above a lower one, and show everything else.
- **Re-tune without re-running**: probabilities are stored, so sliding a threshold re-sorts the queue instantly.
- **Cost on screen**: billed input tokens times the published price, with no output charge.
- **Sample data included**: 30 comments from the CC0 [Civil Comments](https://huggingface.co/datasets/google/civil_comments) dataset, with their human labels, so you can compare decisions against human raters.

### How to get started

1. Clone the repository:
    ```bash
    git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
    cd awesome-llm-apps/starter_ai_agents/ai_comment_moderation_agent
    ```

2. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Get a Trio-Spark API key from the [console](https://platform.machinefi.com/spark#api-keys). New accounts include 100 free decisions.

4. Run the app:
    ```bash
    streamlit run comment_moderation_agent.py
    ```
    Paste the key in the sidebar, or set `TRIO_SPARK_API_KEY` before starting.

### How it works

Each comment becomes one request:

```json
{
  "model": "trio-spark-v1.3",
  "state": "<the comment>",
  "questions": {
    "moderation": {
      "type": "choice",
      "instructions": "Moderate this comment for a public comment section. Decide whether it can be shown or should be hidden.",
      "criteria": {
        "show": "Fine to show: civil, on-topic, or just critical or opinionated",
        "hide": "Hide: insults, obscenity, harassment, hate or threats"
      }
    }
  }
}
```

The response contains `answers.moderation.probabilities.hide`, and the app applies your thresholds to it:

| P(hide) | Action |
|---|---|
| ≥ auto-hide threshold (default 0.70) | 🚫 Hide |
| ≥ review threshold (default 0.40) | 👀 Review by a human |
| otherwise | ✅ Show |

Requests are sent one at a time. If the service reports it is busy (`429`/`503`), the app backs off and retries.

### Notes
- Edit the `criteria` descriptions to match your community's rules. They are plain-language and are read by the model on every call.
- Treat the review band as the place where people decide. A model probability is a signal for your policy, not a verdict.
- Sample comments: Civil Comments (CC0 1.0), test split. Political, religious and identity topics and named individuals were filtered out.
