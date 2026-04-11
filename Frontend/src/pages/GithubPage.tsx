import React, { useState, useRef, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Github, Send, Link as LinkIcon, X, Bot, User, ArrowRight, LayoutDashboard, Plus, Grid3X3, Layers, Sparkles, Code2, BarChart3, GitBranch, Copy, Check, SquarePen, FileDown } from "lucide-react";
import { Component as MorphingCardStack } from "@/src/components/ui/morphing-card-stack";
import { useToast } from "@/src/components/ui/use-toast";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/* ─────────────────────────────────────────────
   Content Parsing & Visualization Engine
   ───────────────────────────────────────────── */

type ContentBlock = 
  | { type: "text"; content: string }
  | { type: "code"; language: string; content: string }
  | { type: "mermaid"; content: string }
  | { type: "chart"; data: ChartData }
  | { type: "json"; content: string; parsed: any };

interface ChartData {
  type: "bar" | "pie" | "donut";
  title?: string;
  labels: string[];
  values: number[];
  colors?: string[];
}

const CHART_COLORS = ["#8b5cf6","#06b6d4","#f59e0b","#ef4444","#22c55e","#ec4899","#3b82f6","#f97316"];

/** Parse a message string into structured content blocks */
function parseContentBlocks(content: string): ContentBlock[] {
  const blocks: ContentBlock[] = [];
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Text before this block
    if (match.index > lastIndex) {
      const textBefore = content.slice(lastIndex, match.index).trim();
      if (textBefore) blocks.push({ type: "text", content: textBefore });
    }

    const lang = match[1].toLowerCase();
    const code = match[2].trim();

    if (lang === "mermaid") {
      blocks.push({ type: "mermaid", content: code });
    } else if (lang === "json" || lang === "chart") {
      try {
        const parsed = JSON.parse(code);
        // Check if it's chart data
        if (parsed.type && parsed.labels && parsed.values) {
          blocks.push({ type: "chart", data: parsed as ChartData });
        } else {
          blocks.push({ type: "json", content: code, parsed });
        }
      } catch {
        blocks.push({ type: "code", language: lang || "text", content: code });
      }
    } else {
      blocks.push({ type: "code", language: lang || "text", content: code });
    }

    lastIndex = match.index + match[0].length;
  }

  // Remaining text
  if (lastIndex < content.length) {
    const remaining = content.slice(lastIndex).trim();
    if (remaining) blocks.push({ type: "text", content: remaining });
  }

  return blocks.length > 0 ? blocks : [{ type: "text", content }];
}

/** Copy-to-clipboard button */
const CopyButton = ({ text }: { text: string }) => {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="p-1.5 rounded-lg hover:bg-[#f5f0e8]/10 text-[#f5f0e8]/40 hover:text-[#f5f0e8]/70 transition-all"
      title="Copy"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
};

/** Code block with syntax display */
const CodeBlockRenderer = ({ language, content }: { language: string; content: string }) => (
  <div className="rounded-xl overflow-hidden border border-neutral-200 dark:border-[#f5f0e8]/[0.06] my-3">
    <div className="flex items-center justify-between px-4 py-2 bg-neutral-100 dark:bg-[#f5f0e8]/[0.04] border-b border-neutral-200 dark:border-[#f5f0e8]/[0.06]">
      <div className="flex items-center gap-2">
        <Code2 className="w-3.5 h-3.5 text-neutral-500 dark:text-[#f5f0e8]/40" />
        <span className="text-xs font-mono text-neutral-500 dark:text-[#f5f0e8]/40">{language}</span>
      </div>
      <CopyButton text={content} />
    </div>
    <pre className="p-4 overflow-x-auto text-sm leading-relaxed bg-neutral-50 dark:bg-black">
      <code className="text-neutral-800 dark:text-[#f5f0e8]/80 font-mono text-[13px]">{content}</code>
    </pre>
  </div>
);

/** JSON tree viewer */
const JsonRenderer = ({ content, parsed }: { content: string; parsed: any }) => (
  <div className="rounded-xl overflow-hidden border border-neutral-200 dark:border-[#f5f0e8]/[0.06] my-3">
    <div className="flex items-center justify-between px-4 py-2 bg-neutral-100 dark:bg-[#f5f0e8]/[0.04] border-b border-neutral-200 dark:border-[#f5f0e8]/[0.06]">
      <div className="flex items-center gap-2">
        <BarChart3 className="w-3.5 h-3.5 text-purple-500" />
        <span className="text-xs font-mono text-neutral-500 dark:text-[#f5f0e8]/40">JSON Data</span>
      </div>
      <CopyButton text={content} />
    </div>
    <pre className="p-4 overflow-x-auto text-sm bg-neutral-50 dark:bg-black">
      <code className="text-neutral-800 dark:text-[#f5f0e8]/80 font-mono text-[13px]">{JSON.stringify(parsed, null, 2)}</code>
    </pre>
  </div>
);

/** Bar / Pie / Donut chart from JSON data */
const ChartRenderer = ({ data }: { data: ChartData }) => {
  const maxVal = Math.max(...data.values, 1);
  const total = data.values.reduce((a, b) => a + b, 0);
  const colors = data.colors || CHART_COLORS;

  if (data.type === "pie" || data.type === "donut") {
    // SVG pie chart
    let cumAngle = 0;
    const slices = data.values.map((val, i) => {
      const pct = val / total;
      const startAngle = cumAngle * 2 * Math.PI;
      cumAngle += pct;
      const endAngle = cumAngle * 2 * Math.PI;
      const largeArc = pct > 0.5 ? 1 : 0;
      const x1 = 50 + 40 * Math.cos(startAngle);
      const y1 = 50 + 40 * Math.sin(startAngle);
      const x2 = 50 + 40 * Math.cos(endAngle);
      const y2 = 50 + 40 * Math.sin(endAngle);
      return (
        <path
          key={i}
          d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
          fill={colors[i % colors.length]}
          opacity={0.85}
          className="hover:opacity-100 transition-opacity cursor-pointer"
        />
      );
    });

    return (
      <div className="rounded-xl border border-neutral-200 dark:border-[#f5f0e8]/[0.06] p-5 my-3 bg-neutral-50 dark:bg-[#f5f0e8]/[0.02]">
        {data.title && <p className="text-sm font-semibold dark:text-[#f5f0e8] mb-4 text-center">{data.title}</p>}
        <div className="flex items-center gap-6 justify-center">
          <svg viewBox="0 0 100 100" className="w-36 h-36">
            {slices}
            {data.type === "donut" && <circle cx="50" cy="50" r="22" className="fill-white dark:fill-black" />}
          </svg>
          <div className="space-y-1.5">
            {data.labels.map((label, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: colors[i % colors.length] }} />
                <span className="text-neutral-600 dark:text-[#f5f0e8]/60">{label}</span>
                <span className="font-mono font-medium text-neutral-800 dark:text-[#f5f0e8]/80 ml-auto">{data.values[i]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Bar chart (default)
  return (
    <div className="rounded-xl border border-neutral-200 dark:border-[#f5f0e8]/[0.06] p-5 my-3 bg-neutral-50 dark:bg-[#f5f0e8]/[0.02]">
      {data.title && <p className="text-sm font-semibold dark:text-[#f5f0e8] mb-4">{data.title}</p>}
      <div className="space-y-3">
        {data.labels.map((label, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="text-xs text-neutral-500 dark:text-[#f5f0e8]/50 w-24 truncate text-right shrink-0">{label}</span>
            <div className="flex-1 h-7 bg-neutral-200/50 dark:bg-[#f5f0e8]/[0.04] rounded-lg overflow-hidden relative">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(data.values[i] / maxVal) * 100}%` }}
                transition={{ duration: 0.8, delay: i * 0.1, ease: [0.23, 1, 0.32, 1] }}
                className="h-full rounded-lg flex items-center justify-end pr-2"
                style={{ backgroundColor: colors[i % colors.length] }}
              >
                <span className="text-[11px] font-mono font-bold text-white drop-shadow-sm">{data.values[i]}</span>
              </motion.div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/** Mermaid diagram renderer (renders as styled code since we don't have mermaid lib) */
const MermaidRenderer = ({ content }: { content: string }) => {
  // Parse mermaid to visual nodes/edges for a simple flowchart
  const { nodes, edges } = useMemo(() => parseMermaidSimple(content), [content]);

  if (nodes.length === 0) {
    // Fallback: just render as code
    return <CodeBlockRenderer language="mermaid" content={content} />;
  }

  return (
    <div className="rounded-xl border border-neutral-200 dark:border-[#f5f0e8]/[0.06] my-3 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-neutral-100 dark:bg-[#f5f0e8]/[0.04] border-b border-neutral-200 dark:border-[#f5f0e8]/[0.06]">
        <div className="flex items-center gap-2">
          <GitBranch className="w-3.5 h-3.5 text-purple-500" />
          <span className="text-xs font-medium text-neutral-500 dark:text-[#f5f0e8]/40">Architecture Flow</span>
        </div>
        <CopyButton text={content} />
      </div>
      <div className="p-6 bg-neutral-50 dark:bg-black relative min-h-[200px]">
        {/* Grid bg */}
        <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle, rgba(128,128,128,0.1) 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
        
        {/* SVG edges */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
          {edges.map((edge, i) => {
            const from = nodes.find(n => n.id === edge.from);
            const to = nodes.find(n => n.id === edge.to);
            if (!from || !to) return null;
            return (
              <line
                key={i}
                x1={`${from.x}%`} y1={`${from.y + 6}%`}
                x2={`${to.x}%`} y2={`${to.y - 2}%`}
                stroke="currentColor"
                className="text-neutral-300 dark:text-[#f5f0e8]/10"
                strokeWidth="1.5"
                strokeDasharray="5 4"
              />
            );
          })}
        </svg>

        {/* Nodes */}
        <div className="relative z-10">
          {nodes.map((node, i) => (
            <motion.div
              key={node.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="absolute transform -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
            >
              <motion.div
                animate={{ y: [0, -3, 0] }}
                transition={{ repeat: Infinity, duration: 2.5, delay: i * 0.2 }}
                className="px-4 py-2.5 bg-white dark:bg-[#f5f0e8]/[0.04] border border-neutral-200 dark:border-[#f5f0e8]/[0.08] rounded-xl shadow-sm text-xs font-semibold text-neutral-700 dark:text-[#f5f0e8]/70 whitespace-nowrap"
              >
                {node.label}
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

/** Simple mermaid parser — extracts nodes and edges from `graph TD` style */
function parseMermaidSimple(code: string): { nodes: {id: string; label: string; x: number; y: number}[]; edges: {from: string; to: string}[] } {
  const nodeMap = new Map<string, string>();
  const edges: {from: string; to: string}[] = [];
  
  const lines = code.split("\n").filter(l => l.trim() && !l.trim().startsWith("graph") && !l.trim().startsWith("%%"));
  
  for (const line of lines) {
    // Match: A[Label] --> B[Label] or A --> B
    const arrowMatch = line.match(/(\w+)(?:\[([^\]]*)\])?\s*-->?\s*(?:\|[^|]*\|\s*)?(\w+)(?:\[([^\]]*)\])?/);
    if (arrowMatch) {
      const [, fromId, fromLabel, toId, toLabel] = arrowMatch;
      if (fromLabel) nodeMap.set(fromId, fromLabel);
      else if (!nodeMap.has(fromId)) nodeMap.set(fromId, fromId);
      if (toLabel) nodeMap.set(toId, toLabel);
      else if (!nodeMap.has(toId)) nodeMap.set(toId, toId);
      edges.push({ from: fromId, to: toId });
    } else {
      // Just a node definition: A[Label]
      const nodeMatch = line.match(/(\w+)\[([^\]]*)\]/);
      if (nodeMatch) {
        nodeMap.set(nodeMatch[1], nodeMatch[2]);
      }
    }
  }

  // Layout: position in tiers
  const allIds = Array.from(nodeMap.keys());
  const roots = allIds.filter(id => !edges.some(e => e.to === id));
  const visited = new Set<string>();
  const tiers: string[][] = [];
  
  let current = roots.length > 0 ? roots : [allIds[0]].filter(Boolean);
  while (current.length > 0 && tiers.length < 6) {
    tiers.push(current);
    current.forEach(id => visited.add(id));
    const next = new Set<string>();
    current.forEach(id => {
      edges.filter(e => e.from === id && !visited.has(e.to)).forEach(e => next.add(e.to));
    });
    current = Array.from(next);
  }
  // Add any orphans
  allIds.filter(id => !visited.has(id)).forEach(id => {
    if (tiers.length > 0) tiers[tiers.length - 1].push(id);
    else tiers.push([id]);
  });

  const nodes = tiers.flatMap((tier, tierIdx) =>
    tier.map((id, i) => ({
      id,
      label: nodeMap.get(id) || id,
      x: ((i + 1) / (tier.length + 1)) * 100,
      y: ((tierIdx + 1) / (tiers.length + 1)) * 100
    }))
  );

  return { nodes, edges };
}

/** Renders a parsed content block */
const ContentBlockView: React.FC<{ block: ContentBlock }> = ({ block }) => {
  switch (block.type) {
    case "text": 
      return (
        <div className="prose dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:p-0 prose-pre:bg-transparent">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{block.content}</ReactMarkdown>
        </div>
      );
    case "code": return <CodeBlockRenderer language={block.language} content={block.content} />;
    case "mermaid": return <MermaidRenderer content={block.content} />;
    case "chart": return <ChartRenderer data={block.data} />;
    case "json": return <JsonRenderer content={block.content} parsed={block.parsed} />;
    default: return null;
  }
};

type ProjectLink = { url: string; type: "GitHub" | "Jira" };

export default function GithubPage() {
  const { error } = useToast();
  
  const analyzerCards = [
    {
      id: "1",
      title: "Dynamic Visualisation",
      description: "Real-time updates and flow graphs of your architecture.",
      icon: <Grid3X3 className="h-5 w-5" />,
    },
    {
      id: "2",
      title: "Jira Analyse",
      description: "Deep dive into sprint tickets and board tracking.",
      icon: <LayoutDashboard className="h-5 w-5" />,
    },
    {
      id: "3",
      title: "Github Analyse",
      description: "Context-aware repository scans and PR reviews.",
      icon: <Github className="h-5 w-5" />,
    },
    {
      id: "4",
      title: "Make your project better",
      description: "AI-suggested improvements and refactoring checks.",
      icon: <Layers className="h-5 w-5" />,
    },
    {
      id: "5",
      title: "AI Chat",
      description: "Have better context with integrated conversation streams.",
      icon: <Bot className="h-5 w-5" />,
    },
  ];

  const [links, setLinks] = useState<ProjectLink[]>([]);
  const [tempRepoUrl, setTempRepoUrl] = useState("");
  const [hasStarted, setHasStarted] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRepoInput, setShowRepoInput] = useState(false);
  const [visualMode, setVisualMode] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const JIRA_LOGO = "https://assets.streamlinehq.com/image/private/w_300,h_300,ar_1/f_auto/v1/icons/professional-tools/jira-software-2-tfcc3k607k9mwgzab3lul.png/jira-software-2-wcevcgjziue4ibno342wv.png?_a=DATAiZAAZAA0";

  const [platform, setPlatform] = useState<"GitHub" | "Jira">("GitHub");

  useEffect(() => {
    const interval = setInterval(() => {
      setPlatform(prev => prev === "GitHub" ? "Jira" : "GitHub");
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const saveChatAsPDF = () => {
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;
    const chatHtml = messages.map(msg => `
      <div class="msg ${msg.role}">
        <span class="label">${msg.role === "user" ? "You" : "UpLink AI"}</span>
        <div class="bubble">${msg.content.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br/>")}</div>
      </div>
    `).join("");
    printWindow.document.write(`
      <!DOCTYPE html><html><head>
      <title>UpLink Chat — ${new Date().toLocaleDateString()}</title>
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 40px; color: #111; max-width: 800px; margin: 0 auto; }
        h1 { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
        .subtitle { font-size: 13px; color: #666; margin-bottom: 32px; }
        .msg { margin-bottom: 20px; display: flex; flex-direction: column; }
        .msg.user { align-items: flex-end; }
        .msg.assistant { align-items: flex-start; }
        .label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 6px; }
        .bubble { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; max-width: 85%; }
        .user .bubble { background: #111; color: #fff; }
        .assistant .bubble { background: #f4f4f4; color: #111; border: 1px solid #e0e0e0; }
        @media print { body { padding: 20px; } }
      </style>
      </head><body>
      <h1>UpLink Project Analyser</h1>
      <p class="subtitle">Chat exported on ${new Date().toLocaleString()}</p>
      ${chatHtml}
      </body></html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => { printWindow.print(); printWindow.close(); }, 400);
    setShowSaveModal(false);
  };

  const handleNewChat = () => {
    setMessages([]);
    setLinks([]);
    setInput("");
    setHasStarted(false);
    setShowRepoInput(false);
    setVisualMode(false);
    setShowSaveModal(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAnalyzing]);

  const detectPlatform = (url: string): "GitHub" | "Jira" | null => {
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/.*$/i;
    const jiraRegex = /^https?:\/\/[a-zA-Z0-9_-]+\.atlassian\.net\/.*$/i;
    
    if (githubRegex.test(url)) return "GitHub";
    if (jiraRegex.test(url)) return "Jira";
    return null;
  };

  const handleAddLink = (newUrl: string) => {
    if (!newUrl.trim() || links.length >= 2) return false;
    
    const type = detectPlatform(newUrl);
    if (!type) {
      error("Invalid link. Please provide a valid GitHub or Jira URL.");
      return false;
    }

    if (links.some(l => l.type === type)) {
      error(`You can only link one ${type} workspace at a time.`);
      return false;
    }

    setLinks(prev => [...prev, { url: newUrl, type }]);
    
    // TRIGGER BACKGROUND ANALYSIS
    try {
      const workspace_id = newUrl.includes("github") ? newUrl.split("/").slice(-2).join("/") : newUrl;
      const payload = type === "GitHub" ? { github_url: newUrl } : { jira_url: newUrl };
      fetch("/api/main/v1/workspaces/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meta: { action: "analyze", workspace_id }, payload })
      }).catch(console.error);
    } catch (err) {}

    setTempRepoUrl("");
    return true;
  };

  const handleRemoveLink = (index: number) => {
    setLinks(prev => prev.filter((_, i) => i !== index));
  };

  const handleStart = (e?: React.FormEvent) => {
    e?.preventDefault();
    let currentLinks = [...links];
    if (tempRepoUrl.trim() && currentLinks.length < 2) {
      const type = detectPlatform(tempRepoUrl);
      if (!type) {
        error("Invalid link. Please provide a valid GitHub or Jira URL.");
        return;
      }
      if (currentLinks.some(l => l.type === type)) {
        error(`You can only link one ${type} workspace at a time.`);
        return;
      }
      currentLinks.push({ url: tempRepoUrl, type });
      setLinks(currentLinks);
      
      // TRIGGER BACKGROUND ANALYSIS
      try {
        const workspace_id = tempRepoUrl.includes("github") ? tempRepoUrl.split("/").slice(-2).join("/") : tempRepoUrl;
        const payload = type === "GitHub" ? { github_url: tempRepoUrl } : { jira_url: tempRepoUrl };
        fetch("/api/main/v1/workspaces/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ meta: { action: "analyze", workspace_id }, payload })
        }).catch(console.error);
      } catch (err) {}

      setTempRepoUrl("");
    }
    
    setHasStarted(true);
    
    if (currentLinks.length > 0) {
      const urlsInfo = currentLinks.map(l => `\`${l.url}\` (${l.type})`).join(' and ');
      setMessages([{ role: "assistant", content: `I'm ready to act on ${urlsInfo}. What would you like me to do?` }]);
    } else {
      setMessages([{ role: "assistant", content: "Hello! I'm your project assistant. You haven't linked any repos or boards yet, but you can add them below or just ask a general question." }]);
    }
  };

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;
    
    const userMessage = input;
    const newMessages = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);
    setInput("");
    setIsAnalyzing(true);
    
    try {
      const response = await fetch("/api/main/v1/workspaces/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          meta: { action: "chat" },
          payload: {
            query: userMessage,
            workspace_id: links.length > 0 ? (links[0].url.includes("github") ? links[0].url.split("/").slice(-2).join("/") : links[0].url) : "default_chat",
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        if (data.meta?.status === "failed" || data.status === "failed") {
          const errMsg = data.errors?.[0]?.message || "Backend encountered an error.";
          error(errMsg);
          setMessages([...newMessages, { role: "assistant", content: `**Error:** ${errMsg}` }]);
        } else {
          const reply = data.data?.answer || "No response received.";
          setMessages([...newMessages, { role: "assistant", content: reply }]);
        }
      } else {
        // Backend HTTP error
        throw new Error("Backend error");
      }
    } catch {
      // Backend offline — provide a smart mock response with notification
      error("Backend offline — showing demo visualization.");
      const mockResponse = generateMockResponse(userMessage, links);
      setMessages([...newMessages, { role: "assistant", content: mockResponse }]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  /** Generate context-aware mock responses with rich content blocks */
  const generateMockResponse = (query: string, linkedProjects: ProjectLink[]): string => {
    const q = query.toLowerCase();
    
    if (q.includes("architect") || q.includes("structure") || q.includes("flow") || q.includes("diagram")) {
      return `Here's the architecture diagram for your project:\n\n\`\`\`mermaid\ngraph TD\n    A[Frontend React] --> B[API Gateway]\n    B --> C[Auth Service]\n    B --> D[RAG Pipeline]\n    D --> E[Vector DB Qdrant]\n    D --> F[LLM Gemini]\n    B --> G[Scheduler]\n    G --> H[Postgres]\n    C --> H\n\`\`\`\n\nThis shows the main service dependencies. The Frontend communicates through the API Gateway, which routes to Auth, RAG Pipeline, and Scheduler services.`;
    }

    if (q.includes("language") || q.includes("tech") || q.includes("stack") || q.includes("breakdown")) {
      return `Here's the technology breakdown:\n\n\`\`\`json\n${JSON.stringify({ type: "bar", title: "Lines of Code by Language", labels: ["TypeScript", "Python", "CSS", "JSON", "Markdown"], values: [4200, 2800, 1500, 600, 400] }, null, 2)}\n\`\`\`\n\nTypeScript dominates the frontend, while Python powers the backend RAG pipeline and document parser.`;
    }

    if (q.includes("commit") || q.includes("contribut") || q.includes("activity")) {
      return `Here's the contribution activity:\n\n\`\`\`json\n${JSON.stringify({ type: "pie", title: "Commits by Area", labels: ["Frontend", "Backend", "Infra", "Docs"], values: [45, 30, 15, 10] }, null, 2)}\n\`\`\`\n\nMost development activity is concentrated in the Frontend and Backend services.`;
    }

    if (q.includes("code") || q.includes("example") || q.includes("implementation") || q.includes("function")) {
      return `Here's a key implementation pattern from the project:\n\n\`\`\`typescript\n// RAG Chat Integration — Frontend Hook\nasync function sendQuery(query: string, sources: Source[]) {\n  const response = await fetch("/api/rag/chat", {\n    method: "POST",\n    headers: { "Content-Type": "application/json" },\n    body: JSON.stringify({ query, sources, history: [] })\n  });\n  return response.json();\n}\n\`\`\`\n\nThis pattern is used across the project for backend communication.`;
    }

    if (q.includes("file") || q.includes("depend") || q.includes("import")) {
      return `Here's the dependency graph:\n\n\`\`\`mermaid\ngraph TD\n    A[App.tsx] --> B[DashboardLayout]\n    B --> C[GithubPage]\n    B --> D[EventsPage]\n    B --> E[ResumePage]\n    C --> F[MorphingCardStack]\n    C --> G[RAG API]\n    D --> H[Scheduler API]\n    E --> I[Document Parser]\n\`\`\`\n\nAll pages are mounted inside the DashboardLayout component and communicate with their respective backend services.`;
    }

    // Default contextual response
    const ctx = linkedProjects.length > 0 
      ? `Based on your linked projects (${linkedProjects.map(l => l.type).join(' & ')}), `
      : "";
    return `${ctx}here's what I found:\n\n\`\`\`json\n${JSON.stringify({ type: "donut", title: "Project Health Score", labels: ["Code Quality", "Test Coverage", "Documentation", "Dependencies"], values: [85, 62, 70, 90] }, null, 2)}\n\`\`\`\n\nOverall your project scores well on code quality and dependencies, but could benefit from improved test coverage and documentation.`;
  };

  const handleSetRepoInside = (e: React.FormEvent) => {
    e.preventDefault();
    if (tempRepoUrl.trim() && links.length < 2) {
      const added = handleAddLink(tempRepoUrl);
      if (added) {
        setShowRepoInput(false);
        setMessages([...messages, { role: "assistant", content: `I have anchored a new project: \`${tempRepoUrl}\`.` }]);
      }
    }
  };

  const JiraIcon = ({ className = "w-5 h-5" }: { className?: string }) => (
    <img src={JIRA_LOGO} alt="Jira" className={className} />
  );

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col bg-[#faf8f4] dark:bg-black">
      {!hasStarted ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-1 flex flex-col items-center justify-center max-w-3xl mx-auto w-full px-4 gap-0"
        >
          {/* Morphing Feature Card — above the title, vanishes on typing */}
          <AnimatePresence>
            {!tempRepoUrl.trim() && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="mb-10"
              >
                <MorphingCardStack cards={analyzerCards} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Title */}
          <div className="flex flex-col items-center mb-6">
            <h1 className="text-3xl md:text-4xl font-bold text-neutral-900 dark:text-white mb-2 text-center tracking-tight flex items-center justify-center gap-2 flex-wrap">
              Link your 
              <motion.div 
                animate={{ width: platform === "GitHub" ? "130px" : "70px" }}
                transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                className="relative h-[40px] md:h-[48px] overflow-hidden inline-flex items-center justify-center mx-2"
              >
                <AnimatePresence mode="wait">
                  <motion.div
                    key={platform}
                    initial={{ y: 20, opacity: 0, scale: 0.8 }}
                    animate={{ y: 0, opacity: 1, scale: 1 }}
                    exit={{ y: -20, opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                    className="absolute font-extrabold text-neutral-900 dark:text-white"
                  >
                    {platform}
                  </motion.div>
                </AnimatePresence>
              </motion.div>
               workspace
            </h1>
            <p className="text-neutral-500 dark:text-neutral-400 text-sm">Paste a repository or project link below to begin analysis</p>
          </div>

          {/* Link Badges */}
          {links.length > 0 && (
            <div className="flex gap-2 mb-4 flex-wrap justify-center">
              <AnimatePresence>
                {links.map((link, i) => (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    key={i} 
                    className="flex items-center gap-2 bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-full px-4 py-2 text-sm font-medium text-neutral-600 dark:text-neutral-300 shadow-sm"
                  >
                    {link.type === 'GitHub' ? <Github className="w-4 h-4" /> : <JiraIcon className="w-4 h-4" />}
                    <span className="truncate max-w-[200px]">{link.url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                    <button type="button" onClick={() => handleRemoveLink(i)} className="ml-1 hover:text-neutral-500 transition-colors p-1">
                      <X className="w-4 h-4" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          {/* URL Input */}
          <div className="w-full max-w-3xl">
            <form onSubmit={handleStart} className="w-full relative flex items-center">
              <div className="absolute left-4 text-neutral-400 flex items-center justify-center w-5 h-5">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={platform}
                    initial={{ scale: 0.5, opacity: 0, rotate: -45 }}
                    animate={{ scale: 1, opacity: 1, rotate: 0 }}
                    exit={{ scale: 0.5, opacity: 0, rotate: 45 }}
                    transition={{ duration: 0.3 }}
                    className="absolute"
                  >
                    {platform === "GitHub" ? <Github className="w-5 h-5" /> : <JiraIcon className="w-5 h-5" />}
                  </motion.div>
                </AnimatePresence>
              </div>
              <input 
                type="url"
                value={tempRepoUrl}
                onChange={e => setTempRepoUrl(e.target.value)}
                disabled={links.length >= 2}
                placeholder={links.length >= 2 ? "Maximum links added" : `Paste ${platform} URL here...`}
                className="w-full bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-2xl py-4 pl-12 pr-44 text-lg focus:outline-none focus:ring-2 focus:ring-neutral-500/50 shadow-sm text-neutral-900 dark:text-white placeholder:text-neutral-400 transition-all disabled:opacity-50"
              />
              <div className="absolute right-2 flex items-center gap-2">
                {tempRepoUrl.trim() && links.length < 2 ? (
                  <button 
                    type="button" 
                    onClick={() => handleAddLink(tempRepoUrl)} 
                    className="p-2 text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors bg-neutral-100 dark:bg-neutral-800 rounded-xl"
                    title="Add this link"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                ) : (
                  <button type="button" onClick={() => handleStart()} className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors">
                    Skip
                  </button>
                )}
                <button disabled={(!tempRepoUrl.trim() && links.length === 0) || (links.length >= 2 && tempRepoUrl.trim().length > 0)} type="submit" className="bg-neutral-600 hover:bg-neutral-700 disabled:bg-neutral-300 dark:disabled:bg-neutral-800 disabled:text-neutral-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 shadow-sm">
                  Start <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
          </div>
        </motion.div>
      ) : (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full"
        >
          {/* Header */}
          <header className="py-4 px-6 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between bg-white/50 dark:bg-neutral-900/50 backdrop-blur-sm shrink-0 rounded-t-3xl">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-neutral-100 dark:bg-neutral-500/20 rounded-lg flex items-center justify-center relative overflow-hidden">
                 <AnimatePresence mode="wait">
                    <motion.div
                      key={platform}
                      initial={{ y: 10, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      exit={{ y: -10, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="absolute inset-0 flex items-center justify-center"
                    >
                      {platform === "GitHub" ? <Github className="w-4 h-4 text-neutral-600 dark:text-neutral-400" /> : <JiraIcon className="w-4 h-4" />}
                    </motion.div>
                  </AnimatePresence>
              </div>
              <div>
                <h2 className="font-semibold text-neutral-900 dark:text-white leading-none mb-1">Project Analyser</h2>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-none">AI Code & Task Assistant</p>
              </div>
            </div>

            {/* New Chat Button */}
            <button
              onClick={() => setShowSaveModal(true)}
              title="New Chat"
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-medium text-neutral-500 dark:text-[#f5f0e8]/50 hover:text-neutral-900 dark:hover:text-[#f5f0e8] hover:bg-neutral-100 dark:hover:bg-[#f5f0e8]/[0.06] border border-transparent hover:border-neutral-200 dark:hover:border-[#f5f0e8]/[0.08] transition-all"
            >
              <SquarePen className="w-4 h-4" />
              <span className="hidden sm:inline">New Chat</span>
            </button>
          </header>

          {/* Messages / Visualiser Area */}
          {visualMode ? (
            <div className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar flex flex-col items-center justify-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-2xl"
              >
                <div className="bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center">
                      <Grid3X3 className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                    </div>
                    <div>
                      <h3 className="font-bold text-neutral-900 dark:text-white">Dynamic Visualiser</h3>
                      <p className="text-xs text-neutral-500">Real-time project architecture flow</p>
                    </div>
                  </div>
                  {/* Flow Visualisation Placeholder */}
                  <div className="relative w-full aspect-video bg-[#faf8f4] dark:bg-black rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden">
                    {/* Grid background */}
                    <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle, rgba(128,128,128,0.15) 1px, transparent 1px)', backgroundSize: '20px 20px' }} />

                    {/* Animated nodes */}
                    <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 2.5, ease: 'easeInOut' }} className="absolute top-[20%] left-[15%] w-20 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm">Frontend</motion.div>
                    <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 2.5, delay: 0.3, ease: 'easeInOut' }} className="absolute top-[20%] right-[15%] w-20 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm">Backend</motion.div>
                    <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 2.5, delay: 0.6, ease: 'easeInOut' }} className="absolute top-[55%] left-[35%] w-24 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm">Database</motion.div>
                    <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 2.5, delay: 0.9, ease: 'easeInOut' }} className="absolute bottom-[12%] left-[20%] w-16 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm">Auth</motion.div>
                    <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 2.5, delay: 1.2, ease: 'easeInOut' }} className="absolute bottom-[12%] right-[20%] w-16 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm">API</motion.div>

                    {/* Connection lines (SVG) */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                      <line x1="25%" y1="35%" x2="47%" y2="60%" stroke="currentColor" className="text-neutral-300 dark:text-neutral-700" strokeWidth="1.5" strokeDasharray="4 4" />
                      <line x1="75%" y1="35%" x2="53%" y2="60%" stroke="currentColor" className="text-neutral-300 dark:text-neutral-700" strokeWidth="1.5" strokeDasharray="4 4" />
                      <line x1="47%" y1="72%" x2="28%" y2="85%" stroke="currentColor" className="text-neutral-300 dark:text-neutral-700" strokeWidth="1.5" strokeDasharray="4 4" />
                      <line x1="53%" y1="72%" x2="72%" y2="85%" stroke="currentColor" className="text-neutral-300 dark:text-neutral-700" strokeWidth="1.5" strokeDasharray="4 4" />
                    </svg>
                  </div>
                  <p className="text-xs text-neutral-400 text-center mt-4">Link a repository to generate a live architecture graph</p>
                </div>
              </motion.div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 custom-scrollbar">
              {messages.map((msg, i) => (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={i} 
                  className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.3)] flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                  )}
                  <div className={`max-w-[85%] md:max-w-[80%] rounded-2xl px-5 py-3.5 ${msg.role === 'user' ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md shadow-violet-500/20' : 'bg-white dark:bg-black border border-neutral-200 dark:border-[#f5f0e8]/[0.06] text-neutral-800 dark:text-[#f5f0e8]/80 shadow-sm'}`}>
                    {msg.role === 'assistant' ? (
                      <div className="space-y-2">
                        {parseContentBlocks(msg.content).map((block, j) => (
                          <ContentBlockView key={j} block={block} />
                        ))}
                      </div>
                    ) : (
                      <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-neutral-200 dark:bg-[#f5f0e8]/[0.06] flex items-center justify-center shrink-0 mt-1">
                      <User className="w-5 h-5 text-neutral-600 dark:text-[#f5f0e8]/40" />
                    </div>
                  )}
                </motion.div>
              ))}
              {isAnalyzing && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 justify-start">
                  <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.3)] flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="bg-white dark:bg-black border border-neutral-200 dark:border-[#f5f0e8]/[0.06] rounded-2xl px-5 py-4 flex items-center gap-2 shadow-sm">
                    <div className="w-2 h-2 bg-purple-500/60 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-purple-500/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-purple-500/60 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 bg-[#faf8f4] dark:bg-black shrink-0">
            <div className="max-w-3xl mx-auto relative pt-8">
              {/* Floating Badges */}
              {links.length > 0 && !showRepoInput && (
                <div className="absolute top-0 left-0 flex items-center gap-2 flex-wrap">
                  <AnimatePresence>
                    {links.map((link, i) => (
                      <motion.div 
                         initial={{ opacity: 0, y: 10 }}
                         animate={{ opacity: 1, y: 0 }}
                         exit={{ opacity: 0, scale: 0.8 }}
                         key={i} 
                         className="flex items-center gap-2 bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-full px-3 py-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-300 shadow-sm"
                      >
                        {link.type === 'GitHub' ? <Github className="w-3.5 h-3.5" /> : <JiraIcon className="w-3.5 h-3.5" />}
                        <span className="truncate max-w-[150px]">{link.url.replace(/^https?:\/\/(www\.)?/, '')}</span>
                        <button onClick={() => handleRemoveLink(i)} className="ml-1 hover:text-neutral-500 transition-colors">
                          <X className="w-3 h-3" />
                        </button>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}

              {/* Repo Badge / Input */}
              {showRepoInput ? (
                <form onSubmit={handleSetRepoInside} className="relative flex items-center gap-2 bg-white dark:bg-black border border-neutral-500 rounded-2xl p-2 shadow-sm transition-all ring-2 ring-neutral-500/20">
                  <div className="p-3 text-neutral-600 dark:text-neutral-400 shrink-0 relative w-11 h-11 flex items-center justify-center">
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={platform}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="absolute"
                      >
                        {platform === "GitHub" ? <Github className="w-5 h-5" /> : <JiraIcon className="w-5 h-5" />}
                      </motion.div>
                    </AnimatePresence>
                  </div>
                  <input 
                    autoFocus
                    type="url"
                    value={tempRepoUrl}
                    onChange={e => setTempRepoUrl(e.target.value)}
                    disabled={links.length >= 2}
                    placeholder={links.length >= 2 ? "Maximum 2 links attached..." : `Link another ${platform} URL...`}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-base py-2 px-2 text-neutral-900 dark:text-white placeholder:text-neutral-400 outline-none disabled:opacity-50"
                  />
                  <button type="button" onClick={() => setShowRepoInput(false)} className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors shrink-0">
                    Cancel
                  </button>
                  <button disabled={!tempRepoUrl.trim() || links.length >= 2} type="submit" className="px-4 py-2 bg-black disabled:bg-neutral-300 dark:bg-white dark:disabled:bg-neutral-800 disabled:text-neutral-500 text-white dark:text-black rounded-xl text-sm font-medium transition-colors shrink-0">
                    Add
                  </button>
                </form>
              ) : (
                <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-white dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-2xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-purple-500/50 focus-within:border-purple-500 transition-all">
                  <button 
                    type="button"
                    onClick={() => setShowRepoInput(true)}
                    className={`relative w-11 h-11 rounded-xl transition-colors shrink-0 flex items-center justify-center ${links.length > 0 ? 'text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-500/10' : 'text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800'}`}
                    title="Manage References"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                  
                  <button 
                    type="button"
                    onClick={() => setVisualMode(!visualMode)}
                    className={`relative w-11 h-11 rounded-xl transition-colors shrink-0 flex items-center justify-center ${visualMode ? 'text-white bg-neutral-700 dark:bg-white dark:text-neutral-900' : 'text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800'}`}
                    title="Dynamic Visualiser"
                  >
                    <Grid3X3 className="w-5 h-5" />
                  </button>
                  
                  <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder={links.length > 0 ? "Ask about your attached projects..." : `Ask a general question or attach a ${platform} repo...`}
                    className="flex-1 max-h-32 min-h-[44px] bg-transparent border-none focus:ring-0 resize-none py-3 px-2 text-neutral-900 dark:text-white placeholder:text-neutral-400 outline-none"
                    rows={1}
                  />
                  
                  <button 
                    type="submit"
                    disabled={!input.trim() || isAnalyzing}
                    className="p-3 bg-neutral-600 hover:bg-neutral-700 disabled:bg-neutral-200 dark:disabled:bg-neutral-800 disabled:text-neutral-400 text-white rounded-xl transition-colors shrink-0"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </form>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Save as PDF Modal */}
      <AnimatePresence>
        {showSaveModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
            onClick={(e) => { if (e.target === e.currentTarget) setShowSaveModal(false); }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, y: 12 }}
              transition={{ type: "spring", stiffness: 400, damping: 28 }}
              className="bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-2xl p-6 w-full max-w-sm"
            >
              {/* Icon */}
              <div className="w-12 h-12 rounded-xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center mb-4">
                <FileDown className="w-6 h-6 text-neutral-600 dark:text-neutral-300" />
              </div>

              <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-1">Save Chat?</h3>
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-6 leading-relaxed">
                {messages.length > 0
                  ? "Would you like to save this conversation as a PDF before starting a new chat?"
                  : "Start a new chat session?"}
              </p>

              <div className="flex gap-3">
                {messages.length > 0 && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={saveChatAsPDF}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-black dark:bg-white text-white dark:text-black rounded-xl text-sm font-semibold hover:bg-neutral-800 dark:hover:bg-neutral-100 transition-colors shadow-sm"
                  >
                    <FileDown className="w-4 h-4" />
                    Save as PDF
                  </motion.button>
                )}
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleNewChat}
                  className="flex-1 py-2.5 border border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-xl text-sm font-medium hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
                >
                  {messages.length > 0 ? "Skip & New Chat" : "New Chat"}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowSaveModal(false)}
                  className="px-4 py-2.5 border border-neutral-200 dark:border-neutral-700 text-neutral-500 dark:text-neutral-400 rounded-xl text-sm font-medium hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
                >
                  Cancel
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
