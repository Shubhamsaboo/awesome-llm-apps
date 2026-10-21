const http = require('http');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const PORT = Number(process.env.PORT) || 3000;
const ROOT = path.resolve(__dirname);

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.excaliflow': 'application/json; charset=utf-8',
  '.excalidraw': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.ttf': 'font/ttf',
  '.webm': 'video/webm',
  '.mp4': 'video/mp4'
};

const AGENT_PRESETS = {
  'claude code': { name: 'Claude Code', color: '#d97757', role: 'Lead Architect' },
  'claude':      { name: 'Claude Code', color: '#d97757', role: 'Lead Architect' },
  'antigravity': { name: 'Antigravity', color: '#6965db', role: 'Systems & Flow' },
  'agy':         { name: 'Antigravity', color: '#6965db', role: 'Systems & Flow' },
  'codex':       { name: 'Codex',       color: '#10b981', role: 'Infra & Runtime' },
  'chatgpt':     { name: 'ChatGPT',     color: '#14b8a6', role: 'Product & API' },
  'grok':        { name: 'Grok Bot',    color: '#06b6d4', role: 'Chaos & Red-Team' },
  'grok bot':    { name: 'Grok Bot',    color: '#06b6d4', role: 'Chaos & Red-Team' }
};

const FALLBACK_AGENT_COLORS = ['#6965db', '#d97757', '#10b981', '#06b6d4', '#f59e0b', '#ec4899', '#0070f3'];

let idSeq = 5000;
function nextHubId(prefix = 'mcp') {
  idSeq += 1;
  return `${prefix}_${Date.now().toString(36)}_${idSeq}`;
}

function resolveAgentProfile(rawName, rawColor, rawRole) {
  const cleanName = String(rawName || process.env.EXCALIFLOW_AGENT || 'AI Agent').trim().slice(0, 36) || 'AI Agent';
  const key = cleanName.toLowerCase();
  const preset = AGENT_PRESETS[key];
  const hashIdx = Array.from(key).reduce((acc, ch) => acc + ch.charCodeAt(0), 0) % FALLBACK_AGENT_COLORS.length;
  return {
    id: 'agent_' + key.replace(/[^a-z0-9]+/g, '_'),
    name: preset ? preset.name : cleanName,
    color: (typeof rawColor === 'string' && /^#[0-9a-fA-F]{6}$/.test(rawColor))
      ? rawColor
      : (preset ? preset.color : FALLBACK_AGENT_COLORS[hashIdx]),
    role: String(rawRole || (preset ? preset.role : 'Collaborator')).slice(0, 40)
  };
}

function createInitialWorkspace() {
  const n1 = { id: 'a_user', type: 'ellipse', x: 70, y: 225, width: 146, height: 70, text: 'User Task\nSpec', strokeColor: '#0070f3', fillStyle: 'hachure', fontFamily: 'hand', fontSize: 15, roughness: 0.85, strokeWidth: 2.2, strokeStyle: 'solid', seed: 101, flowEnabled: true };
  const n2 = { id: 'a_plan', type: 'diamond', x: 285, y: 212, width: 170, height: 94, text: 'Orchestrator\nPlanner', strokeColor: '#7928ca', fillStyle: 'hachure', fontFamily: 'hand', fontSize: 15, roughness: 0.85, strokeWidth: 2.2, strokeStyle: 'solid', seed: 102, flowEnabled: true };
  const n3 = { id: 'a_code', type: 'rectangle', x: 530, y: 115, width: 160, height: 70, text: 'Coder Agent\nSandbox', strokeColor: '#10b981', fillStyle: 'hachure', fontFamily: 'hand', fontSize: 15, roughness: 0.85, strokeWidth: 2.2, strokeStyle: 'solid', seed: 103, flowEnabled: true };
  const n4 = { id: 'a_res', type: 'rectangle', x: 530, y: 325, width: 160, height: 70, text: 'Research Agent\nWeb & Docs', strokeColor: '#06b6d4', fillStyle: 'hachure', fontFamily: 'hand', fontSize: 15, roughness: 0.85, strokeWidth: 2.2, strokeStyle: 'solid', seed: 104, flowEnabled: true };
  const n5 = { id: 'a_ver', type: 'rectangle', x: 780, y: 225, width: 164, height: 70, text: 'Verifier Agent\nTest Runner', strokeColor: '#f59e0b', fillStyle: 'hachure', fontFamily: 'hand', fontSize: 15, roughness: 0.85, strokeWidth: 2.2, strokeStyle: 'solid', seed: 105, flowEnabled: true };
  const makeEdge = (id, u, v, curveOffset, color) => ({
    id,
    type: 'arrow',
    x: u.x + u.width / 2,
    y: u.y + u.height / 2,
    x2: v.x + v.width / 2,
    y2: v.y + v.height / 2,
    strokeColor: color,
    strokeWidth: 2.2,
    strokeStyle: 'solid',
    roughness: 0.85,
    curveType: 'curved',
    curveOffset,
    flowEnabled: true,
    seed: Math.floor(Math.random() * 9000) + 100,
    startBinding: { elementId: u.id, focusAngle: Math.atan2((v.y + v.height / 2) - (u.y + u.height / 2), (v.x + v.width / 2) - (u.x + u.width / 2)), side: 'right', gap: 4 },
    endBinding: { elementId: v.id, focusAngle: Math.atan2((u.y + u.height / 2) - (v.y + v.height / 2), (u.x + u.width / 2) - (v.x + v.width / 2)), side: 'left', gap: 4 }
  });
  const elements = [
    n1, n2, n3, n4, n5,
    makeEdge('a_e1', n1, n2, 0, '#0070f3'),
    makeEdge('a_e2', n2, n3, -20, '#7928ca'),
    makeEdge('a_e3', n2, n4, 20, '#7928ca'),
    makeEdge('a_e4', n3, n5, 18, '#10b981'),
    makeEdge('a_e5', n4, n5, -18, '#06b6d4')
  ];
  return {
    activeTabId: 'tab_initial',
    selectedIds: [],
    tabs: [
      {
        id: 'tab_initial',
        name: 'AI Agent Swarm',
        elements,
        scrollX: 0,
        scrollY: 0,
        zoom: 1,
        canvasBg: '#ffffff',
        flowEnabled: true,
        flowMode: 'comets',
        flowSpeed: 1
      }
    ]
  };
}

const hub = {
  workspace: createInitialWorkspace(),
  agents: new Map(),
  sseClients: new Set(),
  actionLog: []
};

function getActiveTab(tabId = null) {
  const tabs = hub.workspace.tabs;
  if (!Array.isArray(tabs) || tabs.length === 0) {
    hub.workspace = createInitialWorkspace();
  }
  if (tabId) {
    const found = hub.workspace.tabs.find(t => t.id === tabId || t.name.toLowerCase() === String(tabId).toLowerCase());
    if (found) return found;
  }
  return hub.workspace.tabs.find(t => t.id === hub.workspace.activeTabId) || hub.workspace.tabs[0];
}

function findNodeInTab(tab, idOrText) {
  if (!tab || !Array.isArray(tab.elements) || !idOrText) return null;
  const q = String(idOrText).trim();
  const byId = tab.elements.find(el => el.id === q && el.type !== 'arrow');
  if (byId) return byId;
  const qLower = q.toLowerCase();
  return tab.elements.find(el => el.type !== 'arrow' && String(el.text || '').toLowerCase().includes(qLower)) || null;
}

function resolveNonOverlappingSpot(tab, x, y, width = 152, height = 70) {
  const nodes = (tab?.elements || []).filter(e => e.type !== 'arrow');
  let cx = Number.isFinite(Number(x)) ? Number(x) : 280;
  let cy = Number.isFinite(Number(y)) ? Number(y) : 220;
  const pad = 26;

  for (let attempt = 0; attempt < 24; attempt++) {
    const overlap = nodes.find(n => {
      const nw = Number(n.width) || 144;
      const nh = Number(n.height) || 68;
      return (
        cx < n.x + nw + pad &&
        cx + width + pad > n.x &&
        cy < n.y + nh + pad &&
        cy + height + pad > n.y
      );
    });
    if (!overlap) break;
    // Fan out alternating vertically and horizontally
    if (attempt % 2 === 0) {
      cy = overlap.y + (Number(overlap.height) || 68) + 46;
    } else {
      cx = overlap.x + (Number(overlap.width) || 144) + 64;
    }
  }
  return { x: Math.round(cx), y: Math.round(cy) };
}

function extractMentions() {
  const mentions = [];
  for (const tab of hub.workspace.tabs || []) {
    for (const el of tab.elements || []) {
      const text = String(el.text || '');
      const matches = text.match(/@([a-zA-Z0-9_-]+)/g);
      if (matches && matches.length > 0) {
        mentions.push({
          tabId: tab.id,
          tabName: tab.name,
          elementId: el.id,
          type: el.type,
          text,
          mentionedHandles: matches.map(m => m.slice(1).toLowerCase()),
          x: el.x,
          y: el.y
        });
      }
    }
  }
  return mentions;
}

function updateAgentPresence(rawName, patch = {}) {
  const profile = resolveAgentProfile(rawName, patch.color, patch.role);
  const existing = hub.agents.get(profile.id) || {
    id: profile.id,
    name: profile.name,
    color: profile.color,
    role: profile.role,
    x: 240,
    y: 180,
    statusText: 'Connected via MCP',
    activeTabId: hub.workspace.activeTabId,
    actionCount: 0,
    lastActiveAt: Date.now()
  };

  const updated = {
    ...existing,
    name: profile.name,
    color: patch.color && /^#[0-9a-fA-F]{6}$/.test(patch.color) ? patch.color : existing.color,
    role: patch.role ? String(patch.role).slice(0, 40) : existing.role,
    x: Number.isFinite(Number(patch.x)) ? Math.round(Number(patch.x)) : existing.x,
    y: Number.isFinite(Number(patch.y)) ? Math.round(Number(patch.y)) : existing.y,
    statusText: patch.statusText !== undefined ? String(patch.statusText).slice(0, 80) : existing.statusText,
    activeTabId: patch.activeTabId || existing.activeTabId || hub.workspace.activeTabId,
    actionCount: existing.actionCount + (patch.incrementAction ? 1 : 0),
    lastActiveAt: Date.now()
  };
  hub.agents.set(profile.id, updated);
  return updated;
}

function broadcastSse(eventType, payload) {
  const data = `event: ${eventType}\ndata: ${JSON.stringify(payload)}\n\n`;
  for (const res of hub.sseClients) {
    try {
      res.write(data);
    } catch {
      hub.sseClients.delete(res);
    }
  }
}

/* -------------------------------------------------------------------------
 * MCP Tool Definitions & Execution Engine
 * ------------------------------------------------------------------------- */
const MCP_TOOLS = [
  {
    name: 'get_workspace_state',
    description: 'Read all Excaliflow canvas tabs, nodes, arrows, active collaborating agents, human selection, and @agent sticky mentions.',
    inputSchema: {
      type: 'object',
      properties: {
        tabId: { type: 'string', description: 'Optional tab ID or tab name to filter.' }
      }
    }
  },
  {
    name: 'move_agent_cursor',
    description: 'Smoothly glide your named agent cursor to (x, y) on the live canvas with a status bubble so the human and other agents see where you are working.',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string', description: 'Your agent name (e.g. "Claude Code", "Antigravity", "Codex", "Grok").' },
        x: { type: 'number', description: 'Target world X coordinate.' },
        y: { type: 'number', description: 'Target world Y coordinate.' },
        statusText: { type: 'string', description: 'Short status message shown next to your cursor.' },
        color: { type: 'string', description: 'Optional hex color (#6965db, #d97757, #10b981, #06b6d4).' }
      },
      required: ['agentName', 'x', 'y']
    }
  },
  {
    name: 'draw_node',
    description: 'Sketch a new shape or sticky note on the canvas with automatic collision avoidance and author attribution badge.',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string', description: 'Your agent name (e.g. "Claude Code", "Antigravity", "Codex", "Grok").' },
        type: { type: 'string', enum: ['rectangle', 'ellipse', 'diamond', 'sticky', 'text'], description: 'Shape type.' },
        text: { type: 'string', description: 'Label text inside the node (use \\n for multi-line).' },
        x: { type: 'number', description: 'Preferred world X coordinate.' },
        y: { type: 'number', description: 'Preferred world Y coordinate.' },
        strokeColor: { type: 'string', description: 'Hex stroke color (#0070f3, #7928ca, #10b981, #f59e0b, #ef4444, #06b6d4).' },
        fillStyle: { type: 'string', enum: ['hachure', 'cross-hatch', 'solid', 'none'] },
        tabId: { type: 'string', description: 'Optional target canvas tab ID or name.' }
      },
      required: ['agentName', 'text']
    }
  },
  {
    name: 'branch_from',
    description: 'Semantically branch a new connected node from an existing node (by ID or label text) in a chosen direction (right, bottom, left, top) with a live animated arrow.',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string', description: 'Your agent name.' },
        sourceIdOrText: { type: 'string', description: 'ID or label substring of the existing node to branch from.' },
        text: { type: 'string', description: 'Label text for the new branched node.' },
        type: { type: 'string', enum: ['rectangle', 'ellipse', 'diamond', 'sticky'], description: 'Shape type for the new node.' },
        direction: { type: 'string', enum: ['right', 'bottom', 'left', 'top'], description: 'Direction to place the new node.' },
        strokeColor: { type: 'string', description: 'Optional hex color.' },
        curveOffset: { type: 'number', description: 'Optional arrow curve offset (-40 to 40).' },
        tabId: { type: 'string', description: 'Optional canvas tab ID or name.' }
      },
      required: ['agentName', 'sourceIdOrText', 'text']
    }
  },
  {
    name: 'connect_nodes',
    description: 'Draw an animated causal flow arrow between two existing nodes (matched by ID or label substring).',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string', description: 'Your agent name.' },
        fromIdOrText: { type: 'string', description: 'Source node ID or label substring.' },
        toIdOrText: { type: 'string', description: 'Target node ID or label substring.' },
        curveType: { type: 'string', enum: ['curved', 'elbow', 'straight'] },
        curveOffset: { type: 'number', description: 'Curve bend offset (default 0).' },
        strokeColor: { type: 'string', description: 'Optional hex color.' },
        tabId: { type: 'string', description: 'Optional canvas tab ID or name.' }
      },
      required: ['agentName', 'fromIdOrText', 'toIdOrText']
    }
  },
  {
    name: 'insert_between',
    description: 'Split an existing arrow between two nodes and insert a new intermediary node in the middle of the flow (e.g. inserting a Cache, Queue, or Auth Guard).',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string', description: 'Your agent name.' },
        fromIdOrText: { type: 'string', description: 'Upstream node ID or label substring.' },
        toIdOrText: { type: 'string', description: 'Downstream node ID or label substring.' },
        text: { type: 'string', description: 'Label text for the inserted intermediary node.' },
        type: { type: 'string', enum: ['rectangle', 'diamond', 'ellipse'] },
        strokeColor: { type: 'string' },
        tabId: { type: 'string' }
      },
      required: ['agentName', 'fromIdOrText', 'toIdOrText', 'text']
    }
  },
  {
    name: 'add_critique_sticky',
    description: 'Attach an architecture review / critique sticky note next to a target node and optionally fire a pulse burst.',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string', description: 'Your agent name.' },
        targetIdOrText: { type: 'string', description: 'Node ID or label substring to annotate.' },
        note: { type: 'string', description: 'Review comment or architectural suggestion.' },
        severity: { type: 'string', enum: ['info', 'warning', 'critical'], description: 'Controls sticky color & pulse.' },
        tabId: { type: 'string' }
      },
      required: ['agentName', 'targetIdOrText', 'note']
    }
  },
  {
    name: 'trigger_flow_pulse',
    description: 'Fire a burst of animated data packets along outgoing arrows from a node to visually demonstrate traffic or failure propagation.',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string' },
        nodeIdOrText: { type: 'string', description: 'Node ID or label substring to pulse.' },
        color: { type: 'string', description: 'Optional pulse hex color.' },
        tabId: { type: 'string' }
      },
      required: ['agentName', 'nodeIdOrText']
    }
  },
  {
    name: 'manage_canvas_tab',
    description: 'Create a new canvas tab, fork/duplicate an existing tab for parallel agent exploration, switch active tab, or rename a tab.',
    inputSchema: {
      type: 'object',
      properties: {
        agentName: { type: 'string' },
        action: { type: 'string', enum: ['create', 'fork', 'switch', 'rename'] },
        name: { type: 'string', description: 'Name for the new, forked, or renamed canvas tab.' },
        tabId: { type: 'string', description: 'Target tab ID or name for fork/switch/rename.' },
        canvasBg: { type: 'string', enum: ['#ffffff', '#000000'] }
      },
      required: ['agentName', 'action']
    }
  }
];

function executeMcpTool(toolName, args = {}) {
  const agentName = args.agentName || 'AI Agent';

  if (toolName === 'get_workspace_state') {
    const agent = updateAgentPresence(agentName, { statusText: 'Inspecting canvas...' });
    broadcastSse('agent_cursor', { agent });
    const mentions = extractMentions();
    return {
      activeTabId: hub.workspace.activeTabId,
      selectedIds: hub.workspace.selectedIds || [],
      agents: Array.from(hub.agents.values()),
      mentions,
      tabs: hub.workspace.tabs.map(t => ({
        id: t.id,
        name: t.name,
        canvasBg: t.canvasBg,
        flowMode: t.flowMode,
        elementCount: t.elements.length,
        elements: t.elements
      }))
    };
  }

  if (toolName === 'move_agent_cursor') {
    const agent = updateAgentPresence(agentName, {
      x: args.x,
      y: args.y,
      color: args.color,
      statusText: args.statusText || 'Exploring canvas...'
    });
    broadcastSse('agent_cursor', { agent });
    return { ok: true, agent };
  }

  if (toolName === 'manage_canvas_tab') {
    const action = args.action || 'create';
    if (action === 'create') {
      const newTab = {
        id: nextHubId('tab'),
        name: String(args.name || `${agentName} Canvas`).slice(0, 48),
        elements: [],
        scrollX: 0,
        scrollY: 0,
        zoom: 1,
        canvasBg: args.canvasBg === '#000000' ? '#000000' : '#ffffff',
        flowEnabled: true,
        flowMode: 'comets',
        flowSpeed: 1
      };
      hub.workspace.tabs.push(newTab);
      hub.workspace.activeTabId = newTab.id;
      const agent = updateAgentPresence(agentName, {
        activeTabId: newTab.id,
        statusText: `Created tab "${newTab.name}"`,
        incrementAction: true
      });
      broadcastSse('agent_action', { actionType: 'tab_create', agent, tabId: newTab.id, workspace: hub.workspace });
      return { ok: true, tab: newTab, activeTabId: hub.workspace.activeTabId };
    }

    if (action === 'fork') {
      const src = getActiveTab(args.tabId);
      const idMap = new Map();
      const cloned = (src.elements || []).map(el => {
        const newId = nextHubId(el.type);
        idMap.set(el.id, newId);
        return { ...JSON.parse(JSON.stringify(el)), id: newId };
      });
      for (const c of cloned) {
        if (c.startBinding?.elementId && idMap.has(c.startBinding.elementId)) {
          c.startBinding.elementId = idMap.get(c.startBinding.elementId);
        }
        if (c.endBinding?.elementId && idMap.has(c.endBinding.elementId)) {
          c.endBinding.elementId = idMap.get(c.endBinding.elementId);
        }
      }
      const forked = {
        ...JSON.parse(JSON.stringify(src)),
        id: nextHubId('tab'),
        name: String(args.name || `${src.name} (${agentName})`).slice(0, 48),
        elements: cloned
      };
      hub.workspace.tabs.push(forked);
      hub.workspace.activeTabId = forked.id;
      const agent = updateAgentPresence(agentName, {
        activeTabId: forked.id,
        statusText: `Forked "${forked.name}"`,
        incrementAction: true
      });
      broadcastSse('agent_action', { actionType: 'tab_fork', agent, tabId: forked.id, workspace: hub.workspace });
      return { ok: true, tab: forked, activeTabId: hub.workspace.activeTabId };
    }

    if (action === 'switch') {
      const target = getActiveTab(args.tabId || args.name);
      hub.workspace.activeTabId = target.id;
      const agent = updateAgentPresence(agentName, {
        activeTabId: target.id,
        statusText: `Switched to "${target.name}"`,
        incrementAction: true
      });
      broadcastSse('agent_action', { actionType: 'tab_switch', agent, tabId: target.id, workspace: hub.workspace });
      return { ok: true, activeTabId: target.id, tabName: target.name };
    }

    if (action === 'rename') {
      const target = getActiveTab(args.tabId);
      if (args.name) target.name = String(args.name).trim().slice(0, 48);
      const agent = updateAgentPresence(agentName, {
        statusText: `Renamed tab to "${target.name}"`,
        incrementAction: true
      });
      broadcastSse('agent_action', { actionType: 'tab_rename', agent, tabId: target.id, workspace: hub.workspace });
      return { ok: true, tabId: target.id, name: target.name };
    }
  }

  const tab = getActiveTab(args.tabId);

  if (toolName === 'draw_node') {
    const type = ['rectangle', 'ellipse', 'diamond', 'sticky', 'text'].includes(args.type) ? args.type : 'rectangle';
    const w = type === 'sticky' ? 168 : (type === 'diamond' ? 166 : 156);
    const h = type === 'sticky' ? 112 : (type === 'diamond' ? 92 : 70);
    const spot = resolveNonOverlappingSpot(tab, args.x ?? 300, args.y ?? 220, w, h);
    const profile = resolveAgentProfile(agentName, args.strokeColor);
    const node = {
      id: nextHubId(type),
      type,
      x: spot.x,
      y: spot.y,
      width: w,
      height: h,
      text: String(args.text || 'Node'),
      strokeColor: args.strokeColor || profile.color,
      fillStyle: args.fillStyle || (type === 'sticky' ? 'solid' : 'hachure'),
      fontFamily: 'hand',
      fontSize: 15,
      roughness: 0.85,
      strokeWidth: 2.2,
      strokeStyle: 'solid',
      seed: Math.floor(Math.random() * 900000) + 100,
      flowEnabled: true,
      createdBy: profile.name,
      authorColor: profile.color
    };
    tab.elements.push(node);
    const agent = updateAgentPresence(agentName, {
      x: node.x + node.width / 2,
      y: node.y + node.height / 2,
      activeTabId: tab.id,
      statusText: `Drew "${node.text.replace(/\n/g, ' ')}"`,
      incrementAction: true
    });
    broadcastSse('agent_action', {
      actionType: 'draw_node',
      agent,
      tabId: tab.id,
      element: node,
      workspace: hub.workspace
    });
    return { ok: true, tabId: tab.id, element: node, agent };
  }

  if (toolName === 'branch_from') {
    const sourceNode = findNodeInTab(tab, args.sourceIdOrText) || tab.elements.find(e => e.type !== 'arrow');
    if (!sourceNode) {
      throw new Error(`Source node "${args.sourceIdOrText}" not found on tab "${tab.name}".`);
    }
    const dir = ['right', 'bottom', 'left', 'top'].includes(args.direction) ? args.direction : 'right';
    const type = ['rectangle', 'ellipse', 'diamond', 'sticky'].includes(args.type) ? args.type : 'rectangle';
    const w = type === 'diamond' ? 166 : 156;
    const h = type === 'diamond' ? 92 : 70;
    const scx = sourceNode.x + (sourceNode.width || 144) / 2;
    const scy = sourceNode.y + (sourceNode.height || 68) / 2;
    let prefX = scx + 235 - w / 2;
    let prefY = scy - h / 2;
    if (dir === 'left') prefX = scx - 235 - w / 2;
    if (dir === 'bottom') { prefX = scx - w / 2; prefY = scy + 155 - h / 2; }
    if (dir === 'top') { prefX = scx - w / 2; prefY = scy - 155 - h / 2; }

    const spot = resolveNonOverlappingSpot(tab, prefX, prefY, w, h);
    const profile = resolveAgentProfile(agentName, args.strokeColor);
    const newNode = {
      id: nextHubId(type),
      type,
      x: spot.x,
      y: spot.y,
      width: w,
      height: h,
      text: String(args.text || 'Next Step'),
      strokeColor: args.strokeColor || profile.color,
      fillStyle: type === 'sticky' ? 'solid' : 'hachure',
      fontFamily: 'hand',
      fontSize: 15,
      roughness: 0.85,
      strokeWidth: 2.2,
      strokeStyle: 'solid',
      seed: Math.floor(Math.random() * 900000) + 100,
      flowEnabled: true,
      createdBy: profile.name,
      authorColor: profile.color
    };

    const ncx = newNode.x + newNode.width / 2;
    const ncy = newNode.y + newNode.height / 2;
    const outAng = Math.atan2(ncy - scy, ncx - scx);
    const inAng = Math.atan2(scy - ncy, scx - ncx);

    const arrow = {
      id: nextHubId('arrow'),
      type: 'arrow',
      x: scx,
      y: scy,
      x2: ncx,
      y2: ncy,
      strokeColor: args.strokeColor || profile.color,
      strokeWidth: 2.2,
      strokeStyle: 'solid',
      roughness: 0.85,
      curveType: 'curved',
      curveOffset: Number(args.curveOffset) || 0,
      flowEnabled: true,
      seed: Math.floor(Math.random() * 900000) + 100,
      createdBy: profile.name,
      authorColor: profile.color,
      startBinding: { elementId: sourceNode.id, focusAngle: outAng, side: dir, gap: 4 },
      endBinding: { elementId: newNode.id, focusAngle: inAng, gap: 4 }
    };

    tab.elements.push(newNode, arrow);
    const agent = updateAgentPresence(agentName, {
      x: ncx,
      y: ncy,
      activeTabId: tab.id,
      statusText: `Branched "${newNode.text.replace(/\n/g, ' ')}"`,
      incrementAction: true
    });
    broadcastSse('agent_action', {
      actionType: 'branch_from',
      agent,
      tabId: tab.id,
      fromPt: { x: scx, y: scy },
      element: newNode,
      arrow,
      pulse: { nodeId: sourceNode.id, arrowId: arrow.id, color: arrow.strokeColor },
      workspace: hub.workspace
    });
    return { ok: true, tabId: tab.id, sourceId: sourceNode.id, element: newNode, arrow, agent };
  }

  if (toolName === 'connect_nodes') {
    const fromNode = findNodeInTab(tab, args.fromIdOrText);
    const toNode = findNodeInTab(tab, args.toIdOrText);
    if (!fromNode || !toNode) {
      throw new Error(`Could not resolve both endpoints ("${args.fromIdOrText}" -> "${args.toIdOrText}").`);
    }
    const scx = fromNode.x + (fromNode.width || 144) / 2;
    const scy = fromNode.y + (fromNode.height || 68) / 2;
    const tcx = toNode.x + (toNode.width || 144) / 2;
    const tcy = toNode.y + (toNode.height || 68) / 2;
    const outAng = Math.atan2(tcy - scy, tcx - scx);
    const inAng = Math.atan2(scy - tcy, scx - tcx);
    const profile = resolveAgentProfile(agentName, args.strokeColor);

    const arrow = {
      id: nextHubId('arrow'),
      type: 'arrow',
      x: scx,
      y: scy,
      x2: tcx,
      y2: tcy,
      strokeColor: args.strokeColor || profile.color,
      strokeWidth: 2.2,
      strokeStyle: 'solid',
      roughness: 0.85,
      curveType: ['curved', 'elbow', 'straight'].includes(args.curveType) ? args.curveType : 'curved',
      curveOffset: Number(args.curveOffset) || 0,
      flowEnabled: true,
      seed: Math.floor(Math.random() * 900000) + 100,
      createdBy: profile.name,
      authorColor: profile.color,
      startBinding: { elementId: fromNode.id, focusAngle: outAng, gap: 4 },
      endBinding: { elementId: toNode.id, focusAngle: inAng, gap: 4 }
    };
    tab.elements.push(arrow);
    const agent = updateAgentPresence(agentName, {
      x: tcx,
      y: tcy,
      activeTabId: tab.id,
      statusText: `Connected ${fromNode.text.split('\n')[0]} → ${toNode.text.split('\n')[0]}`,
      incrementAction: true
    });
    broadcastSse('agent_action', {
      actionType: 'connect_nodes',
      agent,
      tabId: tab.id,
      fromPt: { x: scx, y: scy },
      arrow,
      pulse: { nodeId: fromNode.id, arrowId: arrow.id, color: arrow.strokeColor },
      workspace: hub.workspace
    });
    return { ok: true, tabId: tab.id, arrow, agent };
  }

  if (toolName === 'insert_between') {
    const fromNode = findNodeInTab(tab, args.fromIdOrText);
    const toNode = findNodeInTab(tab, args.toIdOrText);
    if (!fromNode || !toNode) {
      throw new Error(`Could not find both nodes ("${args.fromIdOrText}", "${args.toIdOrText}") for insert_between.`);
    }
    const existingArrowIdx = tab.elements.findIndex(
      e => e.type === 'arrow' && e.startBinding?.elementId === fromNode.id && e.endBinding?.elementId === toNode.id
    );
    if (existingArrowIdx !== -1) {
      tab.elements.splice(existingArrowIdx, 1);
    }

    const scx = fromNode.x + (fromNode.width || 144) / 2;
    const scy = fromNode.y + (fromNode.height || 68) / 2;
    const tcx = toNode.x + (toNode.width || 144) / 2;
    const tcy = toNode.y + (toNode.height || 68) / 2;
    const type = ['rectangle', 'diamond', 'ellipse'].includes(args.type) ? args.type : 'diamond';
    const w = type === 'diamond' ? 164 : 152;
    const h = type === 'diamond' ? 90 : 68;
    const spot = resolveNonOverlappingSpot(tab, (scx + tcx) / 2 - w / 2, (scy + tcy) / 2 - h / 2, w, h);
    const profile = resolveAgentProfile(agentName, args.strokeColor);

    const midNode = {
      id: nextHubId(type),
      type,
      x: spot.x,
      y: spot.y,
      width: w,
      height: h,
      text: String(args.text || 'Intermediary'),
      strokeColor: args.strokeColor || profile.color,
      fillStyle: 'hachure',
      fontFamily: 'hand',
      fontSize: 15,
      roughness: 0.85,
      strokeWidth: 2.2,
      strokeStyle: 'solid',
      seed: Math.floor(Math.random() * 900000) + 100,
      flowEnabled: true,
      createdBy: profile.name,
      authorColor: profile.color
    };
    const mcx = midNode.x + w / 2;
    const mcy = midNode.y + h / 2;
    const arr1 = {
      id: nextHubId('arrow'),
      type: 'arrow',
      x: scx, y: scy, x2: mcx, y2: mcy,
      strokeColor: midNode.strokeColor,
      strokeWidth: 2.2, strokeStyle: 'solid', roughness: 0.85, curveType: 'curved', curveOffset: 0, flowEnabled: true,
      seed: Math.floor(Math.random() * 900000) + 100,
      createdBy: profile.name,
      startBinding: { elementId: fromNode.id, focusAngle: Math.atan2(mcy - scy, mcx - scx), gap: 4 },
      endBinding: { elementId: midNode.id, focusAngle: Math.atan2(scy - mcy, scx - mcx), gap: 4 }
    };
    const arr2 = {
      id: nextHubId('arrow'),
      type: 'arrow',
      x: mcx, y: mcy, x2: tcx, y2: tcy,
      strokeColor: midNode.strokeColor,
      strokeWidth: 2.2, strokeStyle: 'solid', roughness: 0.85, curveType: 'curved', curveOffset: 0, flowEnabled: true,
      seed: Math.floor(Math.random() * 900000) + 100,
      createdBy: profile.name,
      startBinding: { elementId: midNode.id, focusAngle: Math.atan2(tcy - mcy, tcx - mcx), gap: 4 },
      endBinding: { elementId: toNode.id, focusAngle: Math.atan2(mcy - tcy, mcx - tcx), gap: 4 }
    };
    tab.elements.push(midNode, arr1, arr2);
    const agent = updateAgentPresence(agentName, {
      x: mcx,
      y: mcy,
      activeTabId: tab.id,
      statusText: `Inserted "${midNode.text.replace(/\n/g, ' ')}"`,
      incrementAction: true
    });
    broadcastSse('agent_action', {
      actionType: 'insert_between',
      agent,
      tabId: tab.id,
      element: midNode,
      arrows: [arr1, arr2],
      pulse: { nodeId: fromNode.id, arrowId: arr1.id, color: midNode.strokeColor },
      workspace: hub.workspace
    });
    return { ok: true, tabId: tab.id, element: midNode, arrows: [arr1, arr2], agent };
  }

  if (toolName === 'add_critique_sticky') {
    const targetNode = findNodeInTab(tab, args.targetIdOrText) || tab.elements.find(e => e.type !== 'arrow');
    const severityColors = { info: '#06b6d4', warning: '#f59e0b', critical: '#ef4444' };
    const color = severityColors[args.severity] || '#f59e0b';
    const prefX = targetNode ? targetNode.x + 10 : 320;
    const prefY = targetNode ? targetNode.y - 125 : 80;
    const spot = resolveNonOverlappingSpot(tab, prefX, prefY, 176, 104);
    const profile = resolveAgentProfile(agentName);

    const sticky = {
      id: nextHubId('sticky'),
      type: 'sticky',
      x: spot.x,
      y: spot.y,
      width: 176,
      height: 104,
      text: String(args.note || 'Review note'),
      strokeColor: color,
      fillStyle: 'solid',
      fontFamily: 'hand',
      fontSize: 13,
      roughness: 0.85,
      strokeWidth: 2.2,
      strokeStyle: 'solid',
      seed: Math.floor(Math.random() * 900000) + 100,
      flowEnabled: true,
      createdBy: profile.name,
      authorColor: profile.color
    };
    tab.elements.push(sticky);
    const agent = updateAgentPresence(agentName, {
      x: sticky.x + sticky.width / 2,
      y: sticky.y + sticky.height / 2,
      activeTabId: tab.id,
      statusText: `Annotated: "${sticky.text.slice(0, 32)}..."`,
      incrementAction: true
    });
    broadcastSse('agent_action', {
      actionType: 'add_critique_sticky',
      agent,
      tabId: tab.id,
      element: sticky,
      pulse: targetNode ? { nodeId: targetNode.id, color } : null,
      workspace: hub.workspace
    });
    return { ok: true, tabId: tab.id, element: sticky, agent };
  }

  if (toolName === 'trigger_flow_pulse') {
    const targetNode = findNodeInTab(tab, args.nodeIdOrText) || tab.elements.find(e => e.type !== 'arrow');
    if (!targetNode) {
      throw new Error(`Node "${args.nodeIdOrText}" not found.`);
    }
    const profile = resolveAgentProfile(agentName, args.color);
    const agent = updateAgentPresence(agentName, {
      x: targetNode.x + (targetNode.width || 144) / 2,
      y: targetNode.y + (targetNode.height || 68) / 2,
      activeTabId: tab.id,
      statusText: `Pulsed "${targetNode.text.split('\n')[0]}"`,
      incrementAction: true
    });
    const pulse = { nodeId: targetNode.id, color: args.color || profile.color };
    broadcastSse('agent_action', {
      actionType: 'trigger_flow_pulse',
      agent,
      tabId: tab.id,
      pulse
    });
    return { ok: true, tabId: tab.id, pulsedNodeId: targetNode.id, agent };
  }

  throw new Error(`Unknown MCP tool: ${toolName}`);
}

function handleMcpRpc(rpcReq) {
  if (!rpcReq || typeof rpcReq !== 'object') {
    return { jsonrpc: '2.0', id: null, error: { code: -32600, message: 'Invalid Request' } };
  }
  const { id, method, params } = rpcReq;

  if (method === 'notifications/initialized' || method === 'notifications/cancelled') {
    return null; // Notification requires no response
  }

  try {
    if (method === 'initialize') {
      const clientName = params?.clientInfo?.name || process.env.EXCALIFLOW_AGENT;
      if (clientName) {
        const agent = updateAgentPresence(clientName, { statusText: 'Connected via MCP' });
        broadcastSse('agent_cursor', { agent });
      }
      return {
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: {
            tools: { listChanged: false },
            resources: { subscribe: false, listChanged: false }
          },
          serverInfo: {
            name: 'excaliflow-multi-agent-mcp',
            version: '2.0.0'
          }
        }
      };
    }

    if (method === 'ping') {
      return { jsonrpc: '2.0', id, result: {} };
    }

    if (method === 'tools/list') {
      return {
        jsonrpc: '2.0',
        id,
        result: { tools: MCP_TOOLS }
      };
    }

    if (method === 'tools/call') {
      const name = params?.name;
      const args = params?.arguments || {};
      const output = executeMcpTool(name, args);
      return {
        jsonrpc: '2.0',
        id,
        result: {
          content: [{ type: 'text', text: JSON.stringify(output, null, 2) }],
          isError: false
        }
      };
    }

    if (method === 'resources/list') {
      return {
        jsonrpc: '2.0',
        id,
        result: {
          resources: [
            {
              uri: 'excaliflow://workspace/state',
              name: 'Excaliflow Multi-Canvas Workspace State',
              mimeType: 'application/json',
              description: 'Live multi-tab diagram state, nodes, arrows, and active agents.'
            },
            {
              uri: 'excaliflow://workspace/mentions',
              name: 'Spatial @Agent Sticky Mentions',
              mimeType: 'application/json',
              description: 'Sticky notes or nodes containing @Claude, @Antigravity, @Codex, @Grok mentions.'
            }
          ]
        }
      };
    }

    if (method === 'resources/read') {
      const uri = params?.uri || 'excaliflow://workspace/state';
      const data = uri.includes('mentions')
        ? { mentions: extractMentions() }
        : { workspace: hub.workspace, agents: Array.from(hub.agents.values()), mentions: extractMentions() };
      return {
        jsonrpc: '2.0',
        id,
        result: {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(data, null, 2)
            }
          ]
        }
      };
    }

    return {
      jsonrpc: '2.0',
      id,
      error: { code: -32601, message: `Method not found: ${method}` }
    };
  } catch (err) {
    return {
      jsonrpc: '2.0',
      id,
      result: {
        content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }],
        isError: true
      }
    };
  }
}

function readJsonBody(req, maxBytes = 2 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk;
      if (body.length > maxBytes) {
        reject(new Error('Payload too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  let decodedUrl = '/';
  try {
    decodedUrl = decodeURIComponent((req.url || '/').split('?')[0]);
  } catch {
    res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('400 Bad Request');
    return;
  }

  // CORS headers for local multi-agent tools & browsers
  res.setHeader?.('Access-Control-Allow-Origin', '*');
  res.setHeader?.('Access-Control-Allow-Methods', 'GET, HEAD, POST, OPTIONS');
  res.setHeader?.('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // 1. Live Server-Sent Events stream for browsers (/api/events)
  if (req.method === 'GET' && decodedUrl === '/api/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive'
    });
    res.write(`event: init\ndata: ${JSON.stringify({
      workspace: hub.workspace,
      agents: Array.from(hub.agents.values())
    })}\n\n`);
    hub.sseClients.add(res);
    req.on('close', () => hub.sseClients.delete(res));
    return;
  }

  // 2. Live Workspace & Agent State snapshot (/api/state)
  if (req.method === 'GET' && decodedUrl === '/api/state') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({
      workspace: hub.workspace,
      agents: Array.from(hub.agents.values()),
      mentions: extractMentions(),
      mcpTools: MCP_TOOLS.map(t => t.name)
    }));
    return;
  }

  // 3. Browser -> Hub state sync (/api/sync)
  if (req.method === 'POST' && decodedUrl === '/api/sync') {
    try {
      const data = await readJsonBody(req);
      if (data && Array.isArray(data.tabs) && data.tabs.length > 0) {
        hub.workspace.tabs = data.tabs;
        hub.workspace.activeTabId = data.activeTabId || data.tabs[0].id;
      }
      if (data && Array.isArray(data.selectedIds)) {
        hub.workspace.selectedIds = data.selectedIds;
      }
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: true, mentions: extractMentions() }));
    } catch (err) {
      res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: false, error: err.message }));
    }
    return;
  }

  // 4. Model Context Protocol (MCP) JSON-RPC 2.0 endpoint (/mcp or /api/mcp)
  if (req.method === 'POST' && (decodedUrl === '/mcp' || decodedUrl === '/api/mcp')) {
    try {
      const rpcReq = await readJsonBody(req);
      const rpcRes = handleMcpRpc(rpcReq);
      if (!rpcRes) {
        res.writeHead(202);
        res.end();
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify(rpcRes));
    } catch (err) {
      res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({
        jsonrpc: '2.0',
        id: null,
        error: { code: -32700, message: 'Parse error: ' + err.message }
      }));
    }
    return;
  }

  // 5. Static file server (only GET and HEAD allowed)
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('405 Method Not Allowed');
    return;
  }

  const relPath = decodedUrl === '/' ? 'index.html' : decodedUrl.replace(/^\/+/, '');
  const safePath = path.resolve(ROOT, relPath);

  if (safePath !== ROOT && !safePath.startsWith(ROOT + path.sep)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('403 Forbidden');
    return;
  }

  fs.stat(safePath, (statErr, stats) => {
    if (statErr || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 Not Found');
      return;
    }

    const ext = path.extname(safePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    if (req.method === 'HEAD') {
      res.writeHead(200, {
        'Content-Type': contentType,
        'Content-Length': stats.size,
        'Cache-Control': 'no-cache'
      });
      res.end();
      return;
    }

    fs.readFile(safePath, (readErr, data) => {
      if (readErr) {
        res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('500 Internal Server Error');
        return;
      }
      res.writeHead(200, {
        'Content-Type': contentType,
        'Cache-Control': 'no-cache'
      });
      res.end(data);
    });
  });
});

/* -------------------------------------------------------------------------
 * CLI Stdio MCP Bridge Mode: `node server.js --mcp-stdio [--agent "Claude Code"]`
 * Forwards JSON-RPC calls to localhost:3000/mcp so multiple CLI agent processes
 * share the exact same live browser canvas, or falls back to in-process execution.
 * ------------------------------------------------------------------------- */
function startMcpStdioBridge() {
  const argIdx = process.argv.indexOf('--agent');
  if (argIdx !== -1 && process.argv[argIdx + 1]) {
    process.env.EXCALIFLOW_AGENT = process.argv[argIdx + 1];
  }

  const forwardRpcToHub = (rpcObj) => new Promise((resolve) => {
    const payload = JSON.stringify(rpcObj);
    const req = http.request({
      hostname: '127.0.0.1',
      port: PORT,
      path: '/mcp',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 1500
    }, (res) => {
      let data = '';
      res.on('data', c => { data += c; });
      res.on('end', () => {
        if (res.statusCode === 202 || !data) return resolve(null);
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve(handleMcpRpc(rpcObj));
        }
      });
    });
    req.on('error', () => {
      resolve(handleMcpRpc(rpcObj));
    });
    req.write(payload);
    req.end();
  });

  // Also try to listen on PORT in background if no hub is running yet
  server.on('error', () => {});
  server.listen(PORT, '127.0.0.1');

  const rl = readline.createInterface({ input: process.stdin, terminal: false });
  rl.on('line', async (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    try {
      const rpcReq = JSON.parse(trimmed);
      if (rpcReq.method === 'tools/call' && rpcReq.params?.arguments && !rpcReq.params.arguments.agentName && process.env.EXCALIFLOW_AGENT) {
        rpcReq.params.arguments.agentName = process.env.EXCALIFLOW_AGENT;
      }
      const rpcRes = await forwardRpcToHub(rpcReq);
      if (rpcRes) {
        process.stdout.write(JSON.stringify(rpcRes) + '\n');
      }
    } catch (err) {
      process.stdout.write(JSON.stringify({
        jsonrpc: '2.0',
        id: null,
        error: { code: -32700, message: 'Parse error: ' + err.message }
      }) + '\n');
    }
  });
}

server.hub = hub;
server.MCP_TOOLS = MCP_TOOLS;
server.handleMcpRpc = handleMcpRpc;
server.executeMcpTool = executeMcpTool;

if (require.main === module) {
  if (process.argv.includes('--mcp-stdio')) {
    startMcpStdioBridge();
  } else {
    server.listen(PORT, () => {
      console.log(`Excaliflow Studio + Multi-Agent MCP Hub running at http://localhost:${PORT}`);
      console.log(`MCP HTTP Endpoint:  http://localhost:${PORT}/mcp`);
      console.log(`MCP Stdio Command:  node ${path.join(ROOT, 'server.js')} --mcp-stdio --agent "Claude Code"`);
    });
  }
}

module.exports = server;
