const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    titleBarStyle: 'hidden',
    frame: false,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, 'assets/icon.png') // Optional: add an icon
  });

  mainWindow.loadFile('index.html');
  
  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

// Window control handlers
ipcMain.handle('window-minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window-close', () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.handle('window-is-maximized', () => {
  return mainWindow ? mainWindow.isMaximized() : false;
});

// Ollama API communication
ipcMain.handle('send-to-llm', async (event, message) => {
  try {
    const response = await axios.post('http://localhost:11434/api/generate', {
      model: 'gemma3:1b',
      prompt: message,
      stream: false
    });
    
    return {
      success: true,
      response: response.data.response
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

// Generate updated thinking paths based on the current conversation context
ipcMain.handle('generate-updated-paths', async (event, { originalQuery, lastResponse, conversationContext, lastPathName, lastStepsExecuted }) => {
  try {
    const prompt = `Based on this conversation context:

Original Question: "${originalQuery}"
Last Approach Used: "${lastPathName}" (executed ${lastStepsExecuted} steps)
Latest Response: "${lastResponse.substring(0, 500)}..."

Generate 4 NEW thinking approaches that logically continue from where we left off. These should be:
1. Paths that build on the insights already gained
2. Different perspectives or deeper exploration
3. Next logical steps in the thinking process
4. Alternative directions to explore

For each path, provide:
1. A clear approach name (2-4 words) 
2. Exactly 3 specific thinking steps for that approach
3. Make steps actionable and build on current progress

Format your response as JSON:
{
  "paths": [
    {
      "name": "Continue Deep",
      "steps": ["Build on current insights", "Explore specific implications", "Develop concrete recommendations"]
    }
  ]
}

Focus on continuation and progression rather than starting over.`;

    const response = await axios.post('http://localhost:11434/api/generate', {
      model: 'gemma3:1b',
      prompt: prompt,
      stream: false
    });
    
    // Try to parse JSON from response
    let parsedPaths;
    try {
      const jsonMatch = response.data.response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        parsedPaths = JSON.parse(jsonMatch[0]);
      } else {
        throw new Error('No JSON found');
      }
    } catch (parseError) {
      // Fallback: generate contextual paths
      parsedPaths = generateContinuationPaths(lastPathName, lastStepsExecuted);
    }
    
    return {
      success: true,
      paths: parsedPaths.paths || []
    };
  } catch (error) {
    return {
      success: false,
      paths: generateContinuationPaths(lastPathName, lastStepsExecuted),
      error: error.message
    };
  }
});

function generateContinuationPaths(lastPathName, lastStepsExecuted) {
  // Generate continuation paths based on what was just executed
  return {
    paths: [
      {
        name: "Continue Deep",
        steps: ["Build on current insights", "Explore specific implications", "Develop concrete recommendations"]
      },
      {
        name: "New Angle",
        steps: ["Approach from different perspective", "Challenge current assumptions", "Synthesize alternative view"]
      },
      {
        name: "Apply Practical",
        steps: ["Focus on implementation", "Address real-world constraints", "Create actionable plan"]
      },
      {
        name: "Expand Context",
        steps: ["Broaden the scope", "Connect to related domains", "Explore wider implications"]
      }
    ]
  };
}
ipcMain.handle('generate-thinking-paths', async (event, query) => {
  try {
    const prompt = `You are a strategic thinking assistant. For the following query: "${query}"

Generate 4 different thinking approaches/paths to solve this. For each path, provide:
1. A clear approach name (2-4 words)
2. Exactly 3 specific thinking steps for that approach
3. Each step should be a concrete action or analysis

Format your response as JSON:
{
  "paths": [
    {
      "name": "Approach Name",
      "steps": ["Step 1 description", "Step 2 description", "Step 3 description"]
    }
  ]
}

Make the paths genuinely different approaches, not just variations. Think like a consultant presenting multiple strategies.`;

    const response = await axios.post('http://localhost:11434/api/generate', {
      model: 'gemma3:1b',
      prompt: prompt,
      stream: false
    });
    
    // Try to parse JSON from response
    let parsedPaths;
    try {
      // Extract JSON from the response (model might add extra text)
      const jsonMatch = response.data.response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        parsedPaths = JSON.parse(jsonMatch[0]);
      } else {
        throw new Error('No JSON found');
      }
    } catch (parseError) {
      // Fallback: generate default paths
      parsedPaths = generateFallbackPaths(query);
    }
    
    return {
      success: true,
      paths: parsedPaths.paths || []
    };
  } catch (error) {
    return {
      success: false,
      paths: generateFallbackPaths(query),
      error: error.message
    };
  }
});

// Execute a specific thinking path up to a certain step
ipcMain.handle('execute-thinking-path', async (event, { query, pathName, steps, executeUpToStep }) => {
  try {
    let prompt = `Original question: "${query}"\n\nI'm following the "${pathName}" approach. I will execute these steps and structure my response to show my thinking process:\n\n`;
    
    for (let i = 0; i < executeUpToStep; i++) {
      prompt += `Step ${i + 1}: ${steps[i]}\n`;
    }
    
    prompt += `\nIMPORTANT: You must think through and execute ONLY the ${executeUpToStep} step${executeUpToStep > 1 ? 's' : ''} listed above. Do NOT go beyond these steps or provide a complete solution.

Structure your response exactly like this format:

**Following "${pathName}" Approach:**

**Step 1: ${steps[0] || 'First Step'}**
[Think through and execute this specific step. Provide your actual reasoning, analysis, and findings for JUST this step. Be detailed but focused only on this step's scope.]

${executeUpToStep > 1 ? `**Step 2: ${steps[1] || 'Second Step'}**
[Now execute step 2, building on step 1. Show your thinking process for this specific step. What new insights emerge? How does this advance from step 1?]` : ''}

${executeUpToStep > 2 ? `**Step 3: ${steps[2] || 'Third Step'}**
[Execute the final step. Complete your analysis up to this point. What conclusions can you draw from steps 1-3?]` : ''}

**Current Progress:**
[Summarize what you've accomplished in these ${executeUpToStep} step${executeUpToStep > 1 ? 's' : ''}. Note what still needs to be explored in future steps.]

REMEMBER: Only execute the steps you're asked to. Don't provide a complete answer - just show your thinking for the specified steps. Use **bold text** for important terms and bullet points for clarity.`;

    const response = await axios.post('http://localhost:11434/api/generate', {
      model: 'gemma3:1b',
      prompt: prompt,
      stream: false
    });
    
    return {
      success: true,
      response: response.data.response,
      pathName: pathName,
      stepsExecuted: executeUpToStep
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

function generateFallbackPaths(query) {
  const isCodeRelated = query.toLowerCase().includes('code') || query.toLowerCase().includes('program') || query.toLowerCase().includes('function');
  const isAnalysisRelated = query.toLowerCase().includes('analyz') || query.toLowerCase().includes('data') || query.toLowerCase().includes('research');
  
  if (isCodeRelated) {
    return {
      paths: [
        {
          name: "Step by Step",
          steps: ["Break down requirements", "Design the algorithm", "Implement and test"]
        },
        {
          name: "Best Practices",
          steps: ["Research existing solutions", "Apply design patterns", "Optimize for performance"]
        },
        {
          name: "Quick Prototype",
          steps: ["Create minimal version", "Test core functionality", "Iterate and improve"]
        },
        {
          name: "Comprehensive",
          steps: ["Plan architecture", "Implement with documentation", "Add error handling"]
        }
      ]
    };
  } else if (isAnalysisRelated) {
    return {
      paths: [
        {
          name: "Data Driven",
          steps: ["Gather relevant data", "Analyze patterns", "Draw conclusions"]
        },
        {
          name: "Comparative",
          steps: ["Identify alternatives", "Compare pros and cons", "Recommend best option"]
        },
        {
          name: "Root Cause",
          steps: ["Identify the problem", "Trace underlying causes", "Propose solutions"]
        },
        {
          name: "Strategic",
          steps: ["Define objectives", "Evaluate resources", "Create action plan"]
        }
      ]
    };
  } else {
    return {
      paths: [
        {
          name: "Analytical",
          steps: ["Break down the question", "Examine each component", "Synthesize insights"]
        },
        {
          name: "Creative",
          steps: ["Brainstorm possibilities", "Explore unconventional ideas", "Refine the best concepts"]
        },
        {
          name: "Practical",
          steps: ["Focus on implementation", "Consider real constraints", "Provide actionable steps"]
        },
        {
          name: "Comprehensive",
          steps: ["Research thoroughly", "Consider multiple perspectives", "Provide detailed analysis"]
        }
      ]
    };
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});