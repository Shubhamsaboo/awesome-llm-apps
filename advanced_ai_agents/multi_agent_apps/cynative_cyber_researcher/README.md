# 🛡️ Cynative Security Research Agent

An agentic security researcher that reasons across your **code, cloud and runtime**
together. It runs frontier models locally, generates and runs code in a built-in
sandbox to research at scale, and verifies every finding live — **read-only by
default, enforced on every call**.

Powered by [Cynative](https://github.com/cynative/cynative) (Apache-2.0).

## ✨ What It Demonstrates

- **Code-to-runtime reasoning** — connects source, cloud config and live runtime in one investigation
- **Sandboxed code execution** — the agent writes JavaScript that fans out over hundreds of resources concurrently, so only the summary returns to the model
- **Read-only guardrails** — every operation is resolved to its required IAM actions and authorized against a read-only policy *before* any credential is attached; the gate fails closed on anything classified as a write
- **Evidence-backed findings** — an always-on verifier confirms each finding against live infrastructure
- **Bring your own model** — 23+ providers (Anthropic, OpenAI, Bedrock, Vertex, Azure, Ollama, vLLM and more), running entirely in your environment

## 🔌 Connectors

Uses the credentials already in your shell — no separate credential store:

- **Cloud** — AWS, GCP, Azure
- **Kubernetes** — EKS, GKE, AKS and self-managed clusters (enforced against the cluster's own live `view` RBAC role)
- **Source & CI** — GitHub, GitLab

Read-only policies are enforced per request: `SecurityAudit` on AWS, `roles/viewer` on GCP, `Reader` on Azure.

## 🛠️ How to Get Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/advanced_ai_agents/single_agent_apps/cynative_security_agent
   ```

2. **Install the CLI and dependencies**
   ```bash
   brew install cynative/tap/cynative
   pip install -r requirements.txt
   ```
   (No Homebrew? `curl -fsSL https://raw.githubusercontent.com/cynative/cynative/main/install.sh | sh`)

3. **Set your provider, model and API key**
   ```bash
   export CYNATIVE_LLM_PROVIDER=anthropic
   export CYNATIVE_LLM_MODEL=claude-fable-5
   export ANTHROPIC_API_KEY=<your-anthropic-api-key>
   ```
   (Or place them in a `.env` file in this folder.) See
   [docs/providers/](https://github.com/cynative/cynative/blob/main/docs/providers)
   for OpenAI, Bedrock, Vertex, Azure, Ollama and others.

4. **Run the agent**
   ```bash
   python cynative_agent.py                                  # interactive session
   python cynative_agent.py "audit my S3 buckets"             # one-shot, then exit
   ```

   Or drive the CLI directly:
   ```bash
   cynative                              # interactive session
   cynative "audit my S3 buckets"        # interactive, runs the task first
   cynative -p "attack paths that lead to cloud admin access"   # one-shot
   ```

Each tool call waits for your approval before it runs: `y` runs it once, `a`
allows that tool for the rest of the session, anything else denies. With no
controlling terminal, pass `--auto-approve`.

## 💡 Example Tasks

```bash
cynative -p "high-risk cloud permissions, trace each to the PR where it was granted"
cynative -p "leaked cloud credentials and their current blast radius"
cynative -p "shadow infra - live cloud resources with no IaC trace"
cynative -p "CI workflows that can assume privileged cloud roles"
cat main.tf | cynative -p "review this Terraform for misconfigurations"
```

## 🔧 How It Works

1. **Ask a question** in natural language about your code, cloud or runtime.
2. **The agent plans and fans out** — writing sandboxed JavaScript to query many resources concurrently rather than one tool call at a time.
3. **Every call is gated** — resolved to IAM actions and authorized read-only before credentials are attached; each tool call also waits for your approval.
4. **Findings are verified live** against the real environment, not just inferred.
5. **Everything is logged** to a fail-closed JSONL audit log at `~/.cynative/audit.log`.

## 📚 Learn More

Full docs, connector hardening guides and provider references live in the
[Cynative repository](https://github.com/cynative/cynative).
