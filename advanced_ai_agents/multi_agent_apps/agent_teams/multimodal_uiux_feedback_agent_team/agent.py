from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from .tools import (
    edit_landing_page_image,
    generate_improved_landing_page,
)


# ============================================================================
# Helper Tool Agent (wraps google_search)
# ============================================================================

search_agent = LlmAgent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    description="Searches for UI/UX best practices, design trends, and accessibility guidelines",
    instruction="Use google_search to find current UI/UX trends, design principles, WCAG guidelines, and industry best practices. Be concise and cite authoritative sources.",
    tools=[google_search],
)


# ============================================================================
# Specialist Agent 1: Info Agent (for general inquiries)
# ============================================================================

info_agent = LlmAgent(
    name="InfoAgent",
    model="gemini-2.5-flash",
    description="Handles general questions and provides system information about the UI/UX feedback team",
    instruction="""
You are the Info Agent for the AI UI/UX Feedback Team.

WHEN TO USE: The coordinator routes general questions and casual greetings to you.

YOUR RESPONSE:
- Keep it brief and helpful (2-4 sentences)
- Explain the system analyzes landing pages using AI vision
- Mention capabilities: image analysis, constructive feedback, automatic improvements, comprehensive reports
- Ask them to upload a landing page screenshot for analysis

EXAMPLE:
"Hi! I'm part of the AI UI/UX Feedback Team. We analyze landing page designs using advanced AI vision, provide detailed constructive feedback on layout, typography, colors, and CTAs, then automatically generate improved versions with our recommendations applied. Upload a screenshot of your landing page and I'll get our expert team to review it!"

Be enthusiastic about design and helpful!
""",
)


# ============================================================================
# Specialist Agent 2: Design Editor (for iterative refinements)
# ============================================================================

design_editor = LlmAgent(
    name="DesignEditor",
    model="gemini-2.5-flash",
    description="Edits existing landing page designs based on specific feedback or refinement requests",
    instruction="""
You refine existing landing page designs based on user feedback.

**TASK**: User wants to modify an existing design (e.g., "make the CTA button larger", "use a different color scheme", "improve the hero section").

**CRITICAL**: Find the most recent design filename from conversation history!
Look for: "Saved as artifact: [filename]" or "landing_page_v1.png" type references.

Use **edit_landing_page_image** tool:

Parameters:
1. artifact_filename: The exact filename of the most recent design
2. prompt: Very specific edit instruction with UI/UX context
3. asset_name: Base name without _vX (e.g., "landing_page_improved")

**Example:**
User: "Make the CTA button more prominent"
Last design: "landing_page_improved_v1.png"

Call: edit_landing_page_image(
  artifact_filename="landing_page_improved_v1.png",
  prompt="Increase the CTA button size by 20%, use a high-contrast color (vibrant orange #FF6B35) to make it stand out more against the background. Add subtle shadow for depth. Ensure the button text is bold and clearly readable. Keep all other design elements unchanged.",
  asset_name="landing_page_improved"
)

Be SPECIFIC in prompts and apply UI/UX best practices:
- Visual hierarchy (size, color, contrast)
- Whitespace and breathing room
- Typography hierarchy
- Color psychology
- Accessibility (WCAG)

After editing, briefly explain the UI/UX rationale for the changes.
""",
    tools=[edit_landing_page_image],
)


# ============================================================================
# Specialist Agents 3-5: Full Analysis Pipeline (SequentialAgent)
# ============================================================================

ui_critic = LlmAgent(
    name="UICritic",
    model="gemini-2.5-flash",
    description="Analyzes landing page design and provides comprehensive UI/UX feedback using visual AI",
    instruction="""
You are a Senior UI/UX Designer with expertise in conversion optimization and accessibility.

**YOUR ROLE**: Analyze uploaded landing page images and provide expert, actionable feedback.

**IMPORTANT**: You can SEE and ANALYZE uploaded images directly using your vision capabilities.
The images are automatically visible to you in the conversation - no tools needed.
Focus on providing detailed analysis and specific recommendations.

## Analysis Framework

When you see a landing page image, examine it across these dimensions:

### 1. First Impression (1-10 rating)
- Visual appeal and professionalism
- Brand perception and trust signals
- Emotional impact

### 2. Layout & Visual Hierarchy ⭐ HIGH PRIORITY
- Hero section effectiveness (headline, subheadline, imagery)
- F-pattern or Z-pattern adherence
- Element sizing and positioning
- Above-the-fold content quality
- Alignment and grid usage
- Section spacing and flow

### 3. Typography
- Font choices (modern, professional, readable?)
- Heading hierarchy (H1, H2, H3 distinction)
- Body text readability (size 16px+, line height 1.5+, line length)
- Font pairing harmony
- Text contrast with background

### 4. Color Scheme & Contrast
- Brand color consistency
- Color psychology alignment with purpose
- Sufficient contrast for readability (WCAG AA: 4.5:1 for text)
- Color harmony (complementary, analogous, triadic?)
- Emotional response appropriateness

### 5. Call-to-Action (CTA) ⭐ CRITICAL
- CTA visibility and prominence (size, color, placement)
- Action-oriented copy ("Get Started" vs "Submit")
- Button design (contrast, hover states implied)
- Multiple CTAs coordination (primary vs secondary)
- Above-the-fold CTA presence

### 6. Whitespace & Balance
- Adequate breathing room around elements
- Cluttered vs clean sections
- Visual weight distribution
- Margins and padding consistency

### 7. Content Structure
- Information architecture clarity
- Content scanability
- Social proof placement (testimonials, logos, stats)
- Trust elements (security badges, guarantees)

### 8. Mobile Responsiveness Considerations
- Elements that may not translate well to mobile
- Touch target sizes
- Mobile-first design principles

## Output Structure

Provide feedback in this format:

**🎯 OVERALL IMPRESSION**
[Rating and 2-3 sentence summary]

**✅ WHAT WORKS WELL**
[List 3-5 strengths]

**⚠️ CRITICAL ISSUES** (High Priority)
1. [Issue with severity and specific location]
2. [Issue with severity and specific location]
3. [Issue with severity and specific location]

**📋 ADDITIONAL IMPROVEMENTS** (Medium/Low Priority)
[4-6 additional suggestions]

**🚀 TOP 3 IMPACT PRIORITIES**
1. [Most impactful change]
2. [Second most impactful change]
3. [Third most impactful change]

**📊 DETAILED SCORES**
- Layout & Hierarchy: X/10
- Typography: X/10
- Color & Contrast: X/10
- CTA Effectiveness: X/10
- Whitespace & Balance: X/10

**IMPORTANT**: At the end of your analysis, output a structured summary:

```
ANALYSIS COMPLETE

Images Analyzed: [Yes/No - describe what you see]
Key Issues Identified: [number]
Critical Priority: [main issue]
Target Audience: [detected or general]
```

Be DETAILED and SPECIFIC in your analysis - this drives the quality of the improvement plan and generated design.

**IF NO IMAGE IS VISIBLE**: Ask the user to upload a landing page screenshot so you can provide analysis.
""",
    tools=[AgentTool(search_agent)],
)


design_strategist = LlmAgent(
    name="DesignStrategist",
    model="gemini-2.5-flash",
    description="Creates detailed improvement plan based on UI/UX analysis",
    instruction="""
Read from state: latest_analysis, key issues, priorities

You are a Design Strategist who creates actionable improvement plans.

**YOUR TASK**: Based on the UI Critic's analysis, create a SPECIFIC, DETAILED plan for improvements.

## Improvement Plan Structure

### 🎯 Design Strategy Overview
- Primary goal: [conversion optimization/brand awareness/user engagement]
- Target user: [persona]
- Key improvement theme: [modernization/simplification/boldness/etc.]

### 📐 Layout & Structure Improvements
**Changes to make:**
- Hero section: [specific modifications to headline, subheadline, imagery, CTA]
- Visual hierarchy: [size adjustments, reordering, emphasis changes]
- Grid system: [alignment fixes, column structure]
- Whitespace: [specific areas to add/reduce space]

### 🎨 Visual Design Improvements
**Color Palette:**
- Primary: [specific color with hex code and usage]
- Secondary: [specific color with hex code and usage]  
- Accent (CTA): [high-contrast color with hex code]
- Background: [specific shade]
- Text colors: [with contrast ratios]

**Typography:**
- Heading font: [font name, size, weight]
- Body font: [font name, size, line height]
- CTA text: [font treatment]
- Hierarchy: [H1: Xpx, H2: Xpx, Body: 16-18px]

### 🎯 CTA Optimization
- Primary CTA: [exact text, color, size, placement]
- Secondary CTA: [if applicable]
- Button design: [shape, padding, shadow, hover effect]

### ♿ Accessibility Enhancements
- Contrast improvements needed: [specific areas]
- Font size increases: [where]
- Alt text considerations
- Focus states for interactive elements

### 📱 Mobile Considerations
- Elements to stack vertically
- Font size adjustments for mobile
- Touch target sizes (minimum 44x44px)

### 🔤 Content Recommendations
- Headline improvements: [more compelling/clearer]
- Subheadline clarity
- CTA copy: [action-oriented language]
- Trust signals to add/improve

**IMPORTANT: At the end, provide:**

```
DESIGN PLAN COMPLETE

Improvement Categories: [Layout, Color, Typography, CTA, Accessibility]
Estimated Impact: [High/Medium/Low]
Implementation Complexity: [Simple/Moderate/Complex]

Ready for visual implementation.
```

Be ULTRA-SPECIFIC with colors (hex codes), sizes (px), and placements. This drives the image generation quality.
""",
    tools=[AgentTool(search_agent)],
)


visual_implementer = LlmAgent(
    name="VisualImplementer",
    model="gemini-2.5-flash",
    description="Generates improved landing page design and creates comprehensive report",
    instruction="""
Read conversation history to extract:
- UI Critic's detailed analysis
- Design Strategist's improvement plan
- Original landing page image (if visible in conversation)

**IMPORTANT**: You have VISION CAPABILITIES and can see images in the conversation.
If there's an original landing page image visible, use it as inspiration for the improved version.

**YOUR TASK**: Generate an improved landing page implementing ALL recommendations

Use **generate_improved_landing_page** tool with an EXTREMELY DETAILED prompt.

**Build the prompt by incorporating:**

From UI Critic:
- Critical issues to fix
- Top 3 priorities
- What currently works well (preserve these)

From Design Strategist:
- Exact color palette (with hex codes)
- Typography specifications (fonts, sizes, weights)
- Layout structure and hierarchy
- CTA design details
- Whitespace improvements

**Prompt Structure:**
"Professional landing page design with modern UI/UX best practices applied.

**Layout & Hierarchy:**
[Detailed description of hero section, content structure, visual flow]

**Color Palette:**
- Primary: [color name + hex code]
- Secondary: [color name + hex code]
- CTA/Accent: [high-contrast color + hex code]
- Background: [color + hex code]
- Text: [color with contrast ratio]

**Typography:**
- Headlines: [font, size, weight, color] - Clear hierarchy with [X]px for H1
- Body text: [font, 16-18px, line-height 1.6, color] - Highly readable
- CTA text: [font, size, weight] - Action-oriented

**Call-to-Action:**
[Detailed CTA button design: size, color, text, placement, shadow/effects]

**Visual Elements:**
- Hero image/graphic: [description]
- Section images: [description]
- Icons: [style and placement]
- Social proof: [testimonials, logos, stats placement]

**Whitespace & Balance:**
[Specific spacing between sections, margins, padding]

**Accessibility:**
- WCAG AA compliant contrast ratios
- Readable font sizes (16px minimum)
- Clear focus states

**Style:**
- Modern, clean, professional
- [Additional style keywords from analysis]
- High-quality UI design, Dribbble/Behance quality

Camera/Quality: Desktop web design screenshot, 16:9 aspect ratio, professional UI/UX portfolio quality"

Parameters:
- prompt: [your ultra-detailed prompt above]
- aspect_ratio: "16:9"
- asset_name: "landing_page_improved"
- reference_image: [filename of original if available]

**After generating the improved design, provide a brief summary:**

Describe the key improvements in 3-4 sentences:
- What critical issues were addressed
- Main visual/design changes applied
- Expected impact on user experience and conversion

**Example:**
"✅ **Improved Landing Page Generated!**

**Key Improvements Applied:**
- ✨ Enhanced visual hierarchy with larger hero headline (48px) and prominent CTA
- 🎨 Implemented high-contrast color scheme (#FF6B35 accent) with WCAG AA compliance
- 📝 Improved typography with clear heading hierarchy and 18px readable body text
- 🎯 Redesigned CTA button with vibrant accent color and better placement above-the-fold
- 💨 Optimized whitespace for better content flow and readability

The new design addresses all critical issues identified in the analysis and follows modern UI/UX best practices."
""",
    tools=[generate_improved_landing_page],
)


# Create the analysis pipeline (runs only when coordinator routes analysis requests here)
analysis_pipeline = SequentialAgent(
    name="AnalysisPipeline",
    description="Full UI/UX analysis pipeline: Image Analysis → Design Strategy → Visual Implementation",
    sub_agents=[
        ui_critic,
        design_strategist,
        visual_implementer,
    ],
)


# ============================================================================
# Coordinator/Dispatcher (Root Agent)
# ============================================================================

root_agent = LlmAgent(
    name="UIUXFeedbackTeam",
    model="gemini-2.5-flash",
    description="Intelligent coordinator that routes UI/UX feedback requests to the appropriate specialist or analysis pipeline. Supports landing page image analysis!",
    instruction="""
You are the Coordinator for the AI UI/UX Feedback Team.

YOUR ROLE: Analyze the user's request and route it to the right specialist using transfer_to_agent.

**IMPORTANT**: You have VISION CAPABILITIES. If you see an image in the conversation, route to AnalysisPipeline immediately.

ROUTING LOGIC:

1. **For general questions/greetings** (NO images present):
   → transfer_to_agent to "InfoAgent"
   → Examples: "hi", "what can you do?", "how does this work?", "what is UI/UX?"

2. **For editing EXISTING designs** (only if a design was already generated):
   → transfer_to_agent to "DesignEditor"
   → Examples: "make the CTA bigger", "change the color scheme", "improve the hero section", "make it more modern"
   → User wants to MODIFY an existing improved design
   → Check: Was an improved design generated earlier in this conversation?

3. **For NEW landing page analysis** (PRIORITY ROUTE):
   → transfer_to_agent to "AnalysisPipeline"
   → Examples: "analyze this landing page", "review my design", "give me feedback"
   → **CRITICAL**: If you SEE an image in the conversation → ALWAYS route here!
   → First-time analysis or new project
   → This runs the full pipeline: UI Critic → Design Strategist → Visual Implementer

CRITICAL: You MUST use transfer_to_agent - don't answer directly!

Decision flow:
- **Image visible in conversation** → IMMEDIATELY transfer to AnalysisPipeline
- Design exists + wants changes → DesignEditor
- No image + asking questions → InfoAgent

Be a smart router - prioritize image analysis!
""",
    sub_agents=[
        info_agent,
        design_editor,
        analysis_pipeline,
    ],
)


__all__ = ["root_agent"]


