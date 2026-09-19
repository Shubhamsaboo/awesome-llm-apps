# Insurance Claim Live Agent Team

A voice-first insurance claim intake app on Gemini 3.8 Live. The claim is not a form but a field notebook that writes itself while the claimant talks. Turn on the camera and the agent looks at the damage, says what it sees, and tapes the frame into the notebook. With the camera off, it sketches the described incident once it has enough scene detail and asks whether it looks right. With the camera on, it uses real captures unless you explicitly request a diagram. Behind the page, a background agent team verifies the policy, applies the intake rules, and builds the adjuster packet.

![Insurance Claim Live Agent Team notebook during a live call, with camera frames pinned and marked not confirmed](assets/insurance-claim-live-agent-team-notebook.png)

## What Gemini 3.8 Live makes possible

Audio and camera frames in one session, spoken replies, and function calls that run in the background while the conversation continues.

- **It listens and writes.** Extracted facts appear as handwritten lines, blockers as red blanks, the routing decision as a rubber stamp.
- **It looks.** Camera frames stream in at one per second. When the agent sees something relevant, it says so and calls `pin_evidence_photo`. The exact captured frame is checked independently, then taped into the notebook with a caption and a confirmed or unconfirmed label.
- **It draws.** With the camera off, once it knows where and what happened, it calls `draw_incident_sketch`. Camera-on sessions only draw on an explicit request or a correction to an existing sketch. An image model draws a pen sketch and the agent asks "does this look right?" Corrections by voice trigger a redraw.
- **It reports only what it sees.** Told "you can see the big crack, right?" while looking at a smudge, the agent says it sees a small dark mark, asks for a closer view, and pins the frame marked not confirmed.
- **It never stops talking to wait.** Every tool is `NON_BLOCKING`. Results land `WHEN_IDLE`; injury or an unsafe home comes back as `INTERRUPT`, and the agent stops to escalate to a human.

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
- A downloadable ZIP containing the Markdown packet, evidence manifest, original captured photos, and any generated sketch

### Background agent team

| Tool | What it does | Scheduling |
| --- | --- | --- |
| `lookup_policy` | Verifies the policy number against a mock policy directory | When idle, or interrupt if the policy is lapsed |
| `sync_claim_packet` | Runs the ADK claim graph on the conversation plus camera observations and returns routing and the open items the packet still needs. The agent treats them as a checklist to raise when the current topic closes, not a script | When idle, or interrupt on safety escalation |
| `pin_evidence_photo` | Freezes a fresh camera frame, independently checks what it shows, and adds the original image with a caption and confirmation status | When idle |
| `draw_incident_sketch` | Draws a labeled illustration from established scene details; automatic drawing is blocked while the camera is on | When idle |

### Insurance-specific routing

- Handles home water damage, auto collision, theft/property loss, travel claims, medical reimbursement examples, and unclear claims
- Tracks documents as missing, planned, available, or received; only server-captured evidence can count as received
- Applies deterministic evidence and document checks
- Flags injury, safety, habitability, timing, SIU, and escalation signals
- Routes unknown, lapsed, mismatched, or out-of-period policies for review
- Avoids promising coverage, payment, or liability; prepares a packet without contacting an adjuster

## App Engine

| Layer | Model / Engine | Purpose |
| --- | --- | --- |
| Live voice and vision | `gemini-3.8-live` | Voice-to-voice conversation, camera frame understanding, transcription, background tool calling |
| Sketches | `gemini-3.1-flash-image` | Pen sketch of the incident scene from the agent's brief |
| Background tools | `live_demo/live_tools.py` | Declares the four `NON_BLOCKING` tools, the system instruction, and the sketch prompt |
| Policy directory | `policy_directory.py` | Mock policy administration records used by `lookup_policy` |
| ADK graph | `root_agent` in `agent.py` | Source of truth for claim normalization, classification, validation, routing, and packet generation |
| Structured extraction and photo verification | `gemini-3.8-flash` | Converts the conversation into structured facts and independently checks each exact captured image |
| Business rules | Python FunctionNodes + Pydantic | Deterministic missing-field checks, evidence gates, safety routing, SIU signals, and handoff packet output |
| App backend | FastAPI | Serves the frontend, manages the Gemini Live WebSocket, executes tool calls, and calls `run_claim_workflow()` |
| Frontend | HTML, CSS, JavaScript | The desk: a call card, the notebook page, and the adjuster packet |

## How It Works

`agent.py` owns the claim workflow for this demo. It exposes the ADK `root_agent` and a `run_claim_workflow()` helper that runs the graph programmatically for the live app.

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
        |          pin_evidence_photo   -> frozen camera frame + independent verification
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

The claim graph also runs automatically after every finalized claimant turn, so the notebook stays current even if the model has not called `sync_claim_packet` yet. Results are cached per claim-fact revision, so a tool call that lands right after an automatic run reuses it instead of paying for a second extraction. The graph receives role-labeled conversation turns, verified camera observations, and a separate registry of received evidence. An agent reply or a promise to send a document does not count as new received evidence.

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
|-- tests/
|   |-- test_regressions.py
|   `-- client-regressions.cjs
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

With the camera off, the agent looks up the policy, extracts the claim facts, and can sketch the described scene. It asks for missing details as the conversation continues. The example is a fictional claim; the model decides when it has enough detail to call a tool.

### Camera or sketch?

| Situation | Expected behavior |
| --- | --- |
| Camera off; describing an incident with enough scene detail | Automatically draw an illustration using established details |
| Camera on; showing the scene | Capture the real image and add a caption and confirmation label |
| Camera on; view is unclear or unavailable | Ask for a clearer view; do not replace missing evidence with an automatic sketch |
| Explicit request for a diagram | Draw a clearly labeled illustration in either camera mode |
| Correction to an existing sketch | Redraw; a slower, older request cannot overwrite the correction |

Greetings, vague descriptions, and no-loss inspections should not trigger an automatic sketch. Turning the camera off changes the mode; continue describing the incident to give the agent a turn to act on it. Generated illustrations remain separate from captured evidence and do not prove damage.

### Local sessions and downloads

The server accepts loopback connections only. Keep the `127.0.0.1` binding above; this app is not configured for public hosting. Browser sessions use an ownership cookie and origin checks. Reconnecting or refreshing resumes the current intake while it remains available; **New intake** deletes the previous one and stops its media and background work.

Intakes and images are held in memory, with a 30-minute idle expiry and a 20-minute live-connection limit. Restarting the server clears them. Download the packet before resetting or leaving the demo. The packet prepares a handoff for human review; it does not submit a claim or notify an adjuster.

## Regression tests

After installing the Python requirements, run these from the app directory (Node.js is needed for the browser-state tests):

```bash
python tests/test_regressions.py
node tests/client-regressions.cjs
```

The tests cover evidence status and safety routing, policy corrections, session ownership and reset, frozen-frame verification, camera/sketch selection, stale generation, audio interruption, media cleanup, and packet downloads. Model calls and browser devices are mocked; a real microphone/camera and API-key rehearsal remains a separate check.
