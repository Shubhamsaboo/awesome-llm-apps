# Prompts

Prompts are reusable message templates with parameters that help structure AI interactions.

**Use prompts for:** Code review templates, summarization patterns, translation templates, instruction templates

---

## Basic Prompt

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

server.prompt(
  {
    name: "code-review",
    description: "Generate a code review prompt for given language",
    schema: z.object({
      language: z
        .string()
        .describe("Programming language (e.g., 'TypeScript', 'Python')"),
      focusArea: z
        .string()
        .optional()
        .describe(
          "Specific area to focus on (e.g., 'security', 'performance')",
        ),
    }),
  },
  async ({ language, focusArea }) => {
    const focus = focusArea ? ` with emphasis on ${focusArea}` : "";

    return text(
      `Please review this ${language} code for best practices and potential issues${focus}.\n\n` +
        `Consider:\n` +
        `- Code quality and readability\n` +
        `- Potential bugs or edge cases\n` +
        `- Performance implications\n` +
        `- Security vulnerabilities\n` +
        `- Adherence to ${language} idioms`,
    );
  },
);
```

**Key points:**

- First argument: prompt configuration (name, description, schema)
- Second argument: async handler that returns prompt text
- Handler receives validated input matching schema
- Returns `text()` or `markdown()` helper with prompt content

---

## Prompt Definition

### Name

Use kebab-case, descriptive names:

```typescript
✅ "code-review"
✅ "summarize-document"
✅ "translate-text"
✅ "explain-concept"

❌ "prompt1"
❌ "review"  // Too vague
```

### Description

Explain what the prompt template does:

```typescript
✅ "Generate a code review prompt for any programming language with optional focus areas"
✅ "Create a translation prompt from source to target language"
✅ "Build a summarization prompt with configurable length and style"

❌ "Code review"  // Not descriptive enough
```

### Schema

Define parameters with Zod, always use `.describe()`:

```typescript
// ✅ Good
z.object({
  language: z.string().describe("Programming language to review"),
  focusArea: z
    .enum(["security", "performance", "style", "bugs"])
    .optional()
    .describe("Specific aspect to focus on"),
  severity: z
    .enum(["all", "critical", "major"])
    .default("all")
    .describe("Minimum issue severity to report"),
});

// ❌ Bad - no descriptions
z.object({
  language: z.string(),
  focusArea: z.string().optional(),
});
```

---

## Common Prompt Patterns

### Code Review

```typescript
server.prompt(
  {
    name: "code-review",
    description: "Generate code review instructions",
    schema: z.object({
      language: z.string().describe("Programming language"),
      style: z
        .enum(["strict", "moderate", "lenient"])
        .optional()
        .describe("Review strictness"),
    }),
  },
  async ({ language, style = "moderate" }) => {
    const strictness = {
      strict:
        "Be thorough and point out all issues, including minor style problems.",
      moderate: "Focus on significant issues and best practices.",
      lenient: "Only highlight critical bugs and security issues.",
    };

    return text(
      `Review this ${language} code.\n\n` +
        `${strictness[style]}\n\n` +
        `Check for:\n` +
        `- Correctness and potential bugs\n` +
        `- Security vulnerabilities\n` +
        `- Performance issues\n` +
        `- Code clarity and maintainability`,
    );
  },
);
```

### Summarization

```typescript
server.prompt(
  {
    name: "summarize",
    description: "Create a summarization prompt",
    schema: z.object({
      length: z
        .enum(["brief", "medium", "detailed"])
        .describe("Summary length"),
      format: z
        .enum(["paragraph", "bullets", "outline"])
        .describe("Output format"),
    }),
  },
  async ({ length, format }) => {
    const lengthGuide = {
      brief: "2-3 sentences",
      medium: "1 paragraph (5-7 sentences)",
      detailed: "2-3 paragraphs with key points",
    };

    const formatGuide = {
      paragraph: "as a cohesive paragraph",
      bullets: "as bullet points",
      outline: "as a hierarchical outline",
    };

    return text(
      `Summarize the following content in ${lengthGuide[length]} ` +
        `${formatGuide[format]}.\n\n` +
        `Focus on the main points and key takeaways.`,
    );
  },
);
```

### Translation

```typescript
server.prompt(
  {
    name: "translate",
    description: "Generate translation instructions",
    schema: z.object({
      sourceLang: z.string().describe("Source language"),
      targetLang: z.string().describe("Target language"),
      tone: z
        .enum(["formal", "casual", "technical"])
        .optional()
        .describe("Translation tone"),
    }),
  },
  async ({ sourceLang, targetLang, tone = "formal" }) => {
    return text(
      `Translate the following text from ${sourceLang} to ${targetLang}.\n\n` +
        `Maintain a ${tone} tone.\n` +
        `Preserve the original meaning and nuance.\n` +
        `Keep any technical terms or proper nouns intact unless they have established translations.`,
    );
  },
);
```

### Explanation

```typescript
server.prompt(
  {
    name: "explain-concept",
    description: "Generate explanation instructions for technical concepts",
    schema: z.object({
      concept: z.string().describe("Concept to explain"),
      audience: z
        .enum(["beginner", "intermediate", "expert"])
        .describe("Target audience"),
      includeExamples: z
        .boolean()
        .default(true)
        .describe("Include code examples"),
    }),
  },
  async ({ concept, audience, includeExamples }) => {
    const audienceLevel = {
      beginner: "someone new to programming",
      intermediate: "a developer with 1-2 years experience",
      expert: "an experienced software engineer",
    };

    let prompt = `Explain ${concept} to ${audienceLevel[audience]}.\n\n`;

    if (includeExamples) {
      prompt += `Include practical code examples.\n`;
    }

    prompt += `Use clear language and avoid unnecessary jargon.`;

    return text(prompt);
  },
);
```

---

## Markdown Prompts

For longer, structured prompts use `markdown()`:

```typescript
import { markdown } from "mcp-use/server";

server.prompt(
  {
    name: "api-design-review",
    description: "Generate comprehensive API design review prompt",
    schema: z.object({
      apiType: z.enum(["REST", "GraphQL", "gRPC"]).describe("API type"),
    }),
  },
  async ({ apiType }) => {
    return markdown(`
# ${apiType} API Design Review

Please review this ${apiType} API design for the following aspects:

## 1. Design Quality
- RESTful principles (if REST)
- Resource naming and structure
- Consistency across endpoints
- Use of HTTP methods appropriately

## 2. Security
- Authentication/authorization strategy
- Input validation
- Rate limiting considerations
- Sensitive data handling

## 3. Performance
- Pagination strategy
- Caching headers
- Payload size optimization
- N+1 query prevention

## 4. Developer Experience
- Clear, predictable patterns
- Good error messages
- Comprehensive examples
- Documentation clarity

## 5. Versioning & Evolution
- Versioning strategy
- Backward compatibility
- Deprecation plan

Please provide specific, actionable feedback with examples.
    `);
  },
);
```

---

## Dynamic Prompts

Build prompts that adapt based on context:

```typescript
server.prompt(
  {
    name: "debug-help",
    description: "Generate debugging assistance prompt",
    schema: z.object({
      errorType: z
        .string()
        .describe("Type of error (e.g., 'TypeError', 'NetworkError')"),
      language: z.string().describe("Programming language"),
      hasStackTrace: z.boolean().describe("Whether a stack trace is available"),
    }),
  },
  async ({ errorType, language, hasStackTrace }) => {
    let prompt = `Help me debug this ${errorType} in ${language}.\n\n`;

    if (hasStackTrace) {
      prompt += `I have a stack trace. Please:\n`;
      prompt += `1. Identify the root cause from the stack trace\n`;
      prompt += `2. Explain why this error occurred\n`;
      prompt += `3. Suggest fixes with code examples\n`;
    } else {
      prompt += `I don't have a full stack trace. Please:\n`;
      prompt += `1. Ask questions to narrow down the issue\n`;
      prompt += `2. Suggest common causes of ${errorType}\n`;
      prompt += `3. Recommend debugging steps\n`;
    }

    return text(prompt);
  },
);
```

---

## Multi-Step Prompts

Chain multiple prompts for complex workflows:

```typescript
server.prompt(
  {
    name: "refactor-guide",
    description: "Generate step-by-step refactoring instructions",
    schema: z.object({
      codeSmell: z.string().describe("Type of code smell to address"),
      safetyLevel: z
        .enum(["aggressive", "moderate", "conservative"])
        .describe("Refactoring approach"),
    }),
  },
  async ({ codeSmell, safetyLevel }) => {
    const steps = {
      aggressive: [
        "Identify all instances of the code smell",
        "Propose bold refactoring that may require significant changes",
        "Show before/after code",
        "List breaking changes",
      ],
      moderate: [
        "Identify the code smell",
        "Propose incremental improvements",
        "Show refactoring steps",
        "Ensure backward compatibility",
      ],
      conservative: [
        "Identify the code smell",
        "Propose minimal, safe changes",
        "Preserve existing behavior exactly",
        "Add tests before refactoring",
      ],
    };

    return text(
      `Refactor this code to address: ${codeSmell}\n\n` +
        `Approach: ${safetyLevel}\n\n` +
        `Follow these steps:\n` +
        steps[safetyLevel].map((step, i) => `${i + 1}. ${step}`).join("\n"),
    );
  },
);
```

---

## Prompt with Context

Include environmental or system context:

```typescript
server.prompt(
  {
    name: "optimize-for-runtime",
    description: "Generate optimization suggestions for specific runtime",
    schema: z.object({
      runtime: z
        .enum(["node", "browser", "edge", "serverless"])
        .describe("Target runtime"),
      metric: z
        .enum(["latency", "throughput", "memory", "cost"])
        .describe("Optimization goal"),
    }),
  },
  async ({ runtime, metric }) => {
    const runtimeContext = {
      node: "Node.js server environment with access to filesystem and native modules",
      browser:
        "Browser environment with limited resources and network constraints",
      edge: "Edge runtime with fast cold starts but limited execution time",
      serverless:
        "Serverless function with cold start concerns and pay-per-invocation pricing",
    };

    return text(
      `Optimize this code for ${runtime} runtime to improve ${metric}.\n\n` +
        `Context: ${runtimeContext[runtime]}\n\n` +
        `Consider:\n` +
        `- ${metric === "latency" ? "Reduce response time" : ""}\n` +
        `- ${metric === "throughput" ? "Increase requests/second" : ""}\n` +
        `- ${metric === "memory" ? "Reduce memory footprint" : ""}\n` +
        `- ${metric === "cost" ? "Minimize execution time and resources" : ""}\n\n` +
        `Provide specific code changes with explanations.`,
    );
  },
);
```

---

## Completion (Autocomplete)

Add autocomplete suggestions to prompt arguments using `completable()`:

```typescript
import { MCPServer, text, completable } from "mcp-use/server";
import { z } from "zod";

// Static list of suggestions
server.prompt(
  {
    name: "code-review",
    schema: z.object({
      language: completable(z.string().describe("Programming language"), [
        "python",
        "typescript",
        "go",
        "rust",
      ]),
      code: z.string().describe("Code to review"),
    }),
  },
  async ({ language, code }) => text(`Review this ${language} code...`),
);
```

### Dynamic Completion

Use a callback for suggestions that depend on context or external data:

```typescript
server.prompt(
  {
    name: "analyze-project",
    schema: z.object({
      userId: completable(z.string().describe("User ID"), async (value) => {
        const users = await fetchUsers();
        return users.map((u) => u.id).filter((id) => id.startsWith(value));
      }),
      projectId: completable(
        z.string().describe("Project ID"),
        async (value, ctx) => {
          // Use other argument values for contextual suggestions
          const userId = ctx?.arguments?.userId;
          const projects = await fetchProjects(userId);
          return projects.map((p) => p.id).filter((id) => id.startsWith(value));
        },
      ),
    }),
  },
  async ({ userId, projectId }) => text(`Analyzing project ${projectId}...`),
);
```

**Key points:**

- `completable(schema, values)` — static list, prefix-matched automatically
- `completable(schema, callback)` — dynamic, receives `(value, ctx)` where `ctx.arguments` has other field values
- Works with `z.string()`, `z.number()`, and `z.enum()` schemas
- Clients request suggestions via MCP `completion/complete`

---

## Best Practices

### 1. Clear Instructions

```typescript
✅ "Translate the following text from English to Spanish. Maintain formal tone."
❌ "Translate this."
```

### 2. Structured Output

When you want structured responses, specify format:

```typescript
return text(
  `Review this code and respond in the following format:\n\n` +
    `## Issues Found\n` +
    `- [Issue description]\n\n` +
    `## Suggested Fixes\n` +
    `- [Fix description with code]\n\n` +
    `## Severity\n` +
    `[Critical/Major/Minor]`,
);
```

### 3. Provide Context

Include relevant context in the prompt:

```typescript
return text(
  `You are reviewing ${language} code for a ${projectType} project.\n` +
    `Team follows ${styleGuide} style guide.\n\n` +
    `Review the code below...`,
);
```

### 4. Be Specific

```typescript
✅ "Summarize in 3-5 bullet points, each under 20 words"
❌ "Summarize briefly"
```

---

## Prompts vs Tools

**Use a prompt when:**

- ✅ Providing instructions to the AI
- ✅ Creating reusable message templates
- ✅ Structuring AI interactions
- ✅ No backend logic needed

**Use a tool when:**

- ✅ Executing backend actions
- ✅ Calling APIs or databases
- ✅ Returning computed data
- ✅ Has side effects

**Example:**

```typescript
// ✅ Prompt - Just instructions
server.prompt(
  { name: "review-code", ... },
  async ({ language }) => text(`Review this ${language} code...`)
);

// ✅ Tool - Executes action
server.tool(
  { name: "run-linter", schema: z.object({ file: z.string() }) },
  async ({ file }) => {
    const results = await runLinter(file);
    return object(results);
  }
);
```

---

## Complete Example

```typescript
import { MCPServer, text, markdown } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "prompt-server",
  version: "1.0.0",
});

// Simple text prompt
server.prompt(
  {
    name: "explain-error",
    description: "Generate error explanation prompt",
    schema: z.object({
      errorMessage: z.string().describe("The error message"),
      context: z.string().optional().describe("Additional context"),
    }),
  },
  async ({ errorMessage, context }) => {
    let prompt = `Explain this error message in simple terms:\n"${errorMessage}"\n\n`;

    if (context) {
      prompt += `Context: ${context}\n\n`;
    }

    prompt += `Provide:\n1. What it means\n2. Common causes\n3. How to fix it`;

    return text(prompt);
  },
);

// Structured markdown prompt
server.prompt(
  {
    name: "pr-review",
    description: "Generate pull request review checklist",
    schema: z.object({
      type: z.enum(["feature", "bugfix", "refactor"]).describe("PR type"),
    }),
  },
  async ({ type }) => {
    return markdown(`
# Pull Request Review Checklist (${type})

## Code Quality
- [ ] Code follows project style guide
- [ ] No unnecessary code duplication
- [ ] Functions are small and focused
- [ ] Variable names are clear and descriptive

## Testing
- [ ] ${type === "feature" ? "New tests added for new functionality" : ""}
- [ ] ${type === "bugfix" ? "Regression test added" : ""}
- [ ] All tests pass
- [ ] Edge cases covered

## Documentation
- [ ] Code comments where necessary
- [ ] README updated if needed
- [ ] API docs updated

## ${type === "feature" ? "Feature Specific" : type === "bugfix" ? "Bug Fix Specific" : "Refactor Specific"}
${type === "feature" ? "- [ ] Feature flag implemented if needed\n- [ ] Backward compatible" : ""}
${type === "bugfix" ? "- [ ] Root cause identified\n- [ ] Fix verified in production-like environment" : ""}
${type === "refactor" ? "- [ ] No behavior changes\n- [ ] Performance impact assessed" : ""}
    `);
  },
);

server.listen();
```

---

## Next Steps

- **Format responses** → [response-helpers.md](response-helpers.md)
- **Create tools** → [tools.md](tools.md)
- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
