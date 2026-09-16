# Insurance Claim Live Agent Team

A voice-first insurance claim intake app built on Gemini 3.8 Live, where the claim is not a form but a field notebook that writes itself while the claimant talks. The claimant can turn on their camera and show the damage. The agent looks, describes what it sees, and tapes the frame into the notebook. Once it understands the scene it draws a pen sketch of the incident and asks the claimant whether it looks right. Behind the page, a background agent team verifies the policy, extracts claim facts, applies deterministic intake rules, and builds an adjuster-ready packet.

This is designed as a realistic first notice of loss (FNOL) workflow: the claimant does not need to fill out a rigid form, the operator sees a page they can read at a glance, and the adjuster still gets a structured packet.

![Insurance Claim Live Agent Team notebook during a live call, with camera frames pinned and marked not confirmed](assets/insurance-claim-live-agent-team-notebook.png)

## What Gemini 3.8 Live makes possible

Gemini 3.8 Live takes audio and camera frames in the same session, speaks back, and runs function calls in the background while the conversation continues. This app leans on all three:

- **It listens and writes.** Facts the claim team extracts appear on the notebook page as handwritten lines with an ink animation. Blockers show up as red questions with a blank to fill. The routing decision is a rubber stamp.
- **It looks.** The claimant taps "Show camera" and frames stream into the live session at one per second. When the agent sees something relevant (a water line, a dent, a receipt), it says so out loud and calls `pin_evidence_photo`. The frame it was looking at gets taped into the notebook with the agent's own observation written underneath, and that observation feeds the claim team as evidence.
- **It draws.** Once the agent knows where it happened and what happened, it calls `draw_incident_sketch` with an illustrator brief. An image model draws a rough pen sketch (basement floor plan, intersection, hotel corridor) that gets pinned to the page, and the agent asks "does this look right?" Corrections by voice trigger a redraw. Confirming a picture catches misunderstandings a form never surfaces.
- **It reports only what it sees.** The pin tool asks the agent for its own observation, what the claimant said it was, and whether the frame confirms it. Told "you can see the big crack, right?" while looking at a smudge, the agent answers that it sees a small dark mark, asks for a closer view, and pins the frame marked not confirmed. The adjuster sees both the claim and the observation.
- **It never stops talking to wait.** Every tool is declared `NON_BLOCKING`. Routine results are scheduled `WHEN_IDLE`, so they land between turns. When the claim team detects injury or an unsafe home, the response is scheduled `INTERRUPT`, so the agent stops mid-sentence and escalates to a human.

## Features

### Live call

- Native voice conversation with Gemini 3.8 Live, with audio replies and live transcripts
- Webcam sharing so the agent can see the damage while you describe it
- Typed turns go through the same live session, so the demo works without a microphone
- A "still needed" checklist and a claim team activity feed beside the call

### The notebook

- Handwritten notes for name, policy, location, date, what happened, injuries, contact, and evidence
- Policy verification as a green tick in the margin, or a red flag for lapsed or unknown policies
- Red blanks for blocking intake items
- Camera frames taped in as polaroids with the agent's captions
- A pen sketch of the incident scene, redrawn when the claimant corrects it
- A rubber stamp for the routing decision: needs docs, ready for adjuster, SIU review, or escalate to human
- The full adjuster packet in Markdown behind one button

### Background agent team

| Tool | What it does | Scheduling |
| --- | --- | --- |
| `lookup_policy` | Verifies the policy number against a mock policy directory | When idle, or interrupt if the policy is lapsed |
| `sync_claim_packet` | Runs the ADK claim graph on the conversation plus camera observations and returns routing and the open items the packet still needs. The agent treats them as a checklist to raise when the current topic closes, not a script | When idle, or interrupt on safety escalation |
| `pin_evidence_photo` | Tapes the current camera frame into the notebook with the agent's own observation, the claimant's description, and whether the frame confirms it | When idle |
| `draw_incident_sketch` | Draws a pen sketch of the scene with the image model | When idle |

### Insurance-specific routing

- Handles home water damage, auto collision, theft/property loss, travel claims, medical reimbursement examples, and unclear claims
- Applies deterministic evidence and document checks
- Flags injury, safety, habitability, timing, SIU, and escalation signals
- Avoids promising coverage, payment, or liability

## App Engine

| Layer | Model / Engine | Purpose |
| --- | --- | --- |
| Live voice and vision | `gemini-3.8-live` | Voice-to-voice conversation, camera frame understanding, transcription, background tool calling |
| Sketches | `gemini-3.1-flash-image` | Pen sketch of the incident scene from the agent's brief |
| Background tools | `live_demo/live_tools.py` | Declares the four `NON_BLOCKING` tools, the system instruction, and the sketch prompt |
| Policy directory | `policy_directory.py` | Mock policy administration records used by `lookup_policy` |
| ADK graph | `root_agent` in `agent.py` | Source of truth for claim normalization, classification, validation, routing, and packet generation |
| Structured extraction | `gemini-3.8-flash` | Converts messy claim language and camera observations into structured claim facts inside the ADK graph |
| Business rules | Python FunctionNodes + Pydantic | Deterministic missing-field checks, evidence gates, safety routing, SIU signals, and handoff packet output |
| App backend | FastAPI | Serves the frontend, manages the Gemini Live WebSocket, executes tool calls, and calls `run_claim_workflow()` |
| Frontend | HTML, CSS, JavaScript | The desk: a call card, the notebook page, and the adjuster packet |

## How It Works

`agent.py` owns the production claim workflow. It exposes the ADK `root_agent` and a `run_claim_workflow()` helper that runs the graph programmatically for the live app.

`live_demo/live_tools.py` owns the Gemini 3.8 Live configuration: the system instruction, the four background tool declarations, the sketch prompt, and the scheduling rules.

`live_demo/server.py` owns the live web transport. It manages the browser session, the Gemini Live audio and video stream, transcripts, tool execution, the pinned photos and sketch, and FastAPI routes. It does not duplicate extraction, classification, evidence, routing, or packet logic.

```text
Claimant talks, types, or shows the camera
        |
        v
Gemini 3.8 Live keeps the conversation going
        |                 \
        |                  \  NON_BLOCKING tool calls
        |                   v
        |          lookup_policy        -> policy_directory.py
        |          sync_claim_packet    -> run_claim_workflow() -> ADK graph
        |          pin_evidence_photo   -> latest camera frame + observation
        |          draw_incident_sketch -> gemini-3.1-flash-image
        |                   |
        |                   v
        |          FunctionResponse with scheduling
        |          (INTERRUPT on safety escalation, WHEN_IDLE otherwise)
        v                   |
Agent confirms the policy, describes the photo, asks about the sketch, or escalates
        |
        v
server.py streams transcript, tool activity, photos, sketch, and claim state
        |
        v
The notebook page writes, tapes, pins, and stamps
```

The claim graph also runs automatically after every finalized claimant turn, so the notebook stays current even if the model has not called `sync_claim_packet` yet. Results are cached per transcript snapshot, so a tool call that lands right after an automatic run reuses it instead of paying for a second extraction. Camera observations from `pin_evidence_photo` are appended to the text the graph reads, so the claim writer treats them as evidence.

## Demo Policy Numbers

The mock policy directory lines up with the prompts in `examples.py`. Say one of these on the call to see the policy desk in action:

| Policy number | Policyholder | Line | Status |
| --- | --- | --- | --- |
| H0-44721 | Maya Singh | Homeowners with water backup endorsement | Active |
| AUTO-90210 | Jordan Lee | Personal auto with medical payments | Active |
| RNT-3008 | Priya Shah | Renters | Active |
| TRV-7711 | Alex Chen | Single trip travel | Active |
| MED-5520 | Sam Rivera | Supplemental medical reimbursement | Active |
| AUTO-11111 | Chris Park | Personal auto | Lapsed, routes to human review |

Any other number returns a not-found result and the agent asks the claimant to confirm it.

## Project Structure

```text
insurance_claim_live_agent_team/
|-- agent.py
|-- schemas.py
|-- policies.py
|-- policy_directory.py
|-- examples.py
|-- requirements.txt
|-- .env.example
|-- assets/
|   `-- insurance-claim-live-agent-team-notebook.png
|-- live_demo/
|   |-- index.html
|   |-- styles.css
|   |-- app.js
|   |-- live_tools.py
|   `-- server.py
`-- README.md
```

## How to Get Started

From the app directory:

```bash
cd voice_ai_agents/insurance_claim_live_agent_team
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your Google API key:

```bash
GOOGLE_GENAI_USE_VERTEXAI=False
GOOGLE_API_KEY=your-google-api-key
```

Optional settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `FNOL_GEMINI_LIVE_MODEL` | `gemini-3.8-live` | Live voice and vision model |
| `FNOL_SKETCH_MODEL` | `gemini-3.1-flash-image` | Image model for the incident sketch |
| `FNOL_VOICE` | `Kore` | Prebuilt voice for audio responses |

## Run the App

Start the backend and frontend server:

```bash
python -m uvicorn live_demo.server:app --reload --host 127.0.0.1 --port 4177
```

Open the app:

```text
http://127.0.0.1:4177/index.html
```

Tap "Talk" to start the live call, or type a claimant turn into the text box; typed turns go through the same live session, so you still hear the agent and see the notebook fill in. Tap "Show camera" to let the agent see the damage. Point it at a wet wall, a dented bumper, a receipt, or even a sketch on paper, and the agent will describe what it sees and tape the frame into the notebook.

Try this opening line to see the whole team run at once:

```text
Hi, this is Maya Singh, policy H0-44721. Our finished basement in Denver flooded last night when the sump pump failed. Nobody is hurt. The water came in by the stairs and spread across the carpet toward the boxes.
```

The agent confirms the homeowners policy while the claim writer extracts the facts, draws a floor plan of the basement, and asks whether the sketch looks right, then asks for the best contact method because that is the first blocking item the rules report.
