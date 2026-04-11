import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Github,
  Send,
  X,
  Bot,
  User,
  ArrowRight,
  LayoutDashboard,
  Plus,
  Grid3X3,
  Layers,
} from "lucide-react";
import { Component as MorphingCardStack } from "@/src/components/ui/morphing-card-stack";
import { useToast } from "@/src/components/ui/use-toast";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  analyzeWorkspace,
  chatWorkspace,
  loadUiBootstrap,
  loadVisualization,
  loadWorkspaceStatus,
  type GraphEdge,
  type GraphNode,
  type SourceKind,
  type UiBootstrapPayload,
  type VisualizationPayload,
} from "@/src/lib/mainServer";

type ProjectLink = { url: string; type: "GitHub" | "Jira" };
type AnalyzerMessage = { role: "assistant" | "user"; content: string };

const fallbackAnalyzerUi: UiBootstrapPayload["analyzer"] = {
  intro_title: "Link your workspace",
  intro_subtitle: "Paste a GitHub repository or Jira workspace link below to begin live analysis.",
  assistant_name: "Project Analyser",
  assistant_tagline: "AI Code and Task Assistant",
  visualizer_title: "Dynamic Visualiser",
  visualizer_subtitle: "Real-time project architecture flow",
  visualizer_caption: "Link a repository or board to generate a live architecture graph.",
  cards: [
    {
      id: "dynamic_visualisation",
      title: "Dynamic Visualisation",
      description: "Live architecture graphs built from indexed workspace context.",
      icon_key: "visual",
    },
    {
      id: "jira_analyse",
      title: "Jira Analyse",
      description: "Inspect projects, tickets, and linked workflow context.",
      icon_key: "jira",
    },
    {
      id: "github_analyse",
      title: "GitHub Analyse",
      description: "Review repositories, code structure, and indexed files.",
      icon_key: "github",
    },
    {
      id: "project_improvements",
      title: "Project Improvements",
      description: "Surface grounded risks, recommendations, and next actions.",
      icon_key: "layers",
    },
    {
      id: "ai_chat",
      title: "AI Chat",
      description: "Ask follow-up questions against the current workspace context.",
      icon_key: "chat",
    },
  ],
  copy: {
    default_greeting:
      "Hello! I am your project assistant. Add a GitHub repository or Jira workspace and I will help analyze it.",
    linked_prefix: "I am ready to work with",
    linked_suffix: "What would you like me to do?",
    fallback_waiting:
      "The workspace analysis is still warming up. Ask again after indexing finishes for grounded answers.",
  },
};

const USE_MAIN_SERVER_ANALYZER = import.meta.env.VITE_ENABLE_MAIN_SERVER_ANALYZER !== "false";

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function sourceKindFromLinks(links: ProjectLink[]): SourceKind | undefined {
  const hasGitHub = links.some((link) => link.type === "GitHub");
  const hasJira = links.some((link) => link.type === "Jira");
  if (hasGitHub && hasJira) return "dual";
  if (hasGitHub) return "github";
  if (hasJira) return "jira";
  return undefined;
}

function buildGreeting(links: ProjectLink[], analyzerUi: UiBootstrapPayload["analyzer"]) {
  const copy = analyzerUi.copy || {};
  if (links.length > 0) {
    const urlsInfo = links.map((link) => `\`${link.url}\` (${link.type})`).join(" and ");
    return `${copy?.linked_prefix || "I am ready to work with"} ${urlsInfo}. ${copy?.linked_suffix || "What would you like me to do?"}`;
  }

  return (
    copy?.default_greeting ||
    "Hello! I am your project assistant. Add a GitHub repository or Jira workspace and I will help analyze it."
  );
}

function buildFallbackReply(analyzerUi: UiBootstrapPayload["analyzer"], links: ProjectLink[]) {
  const copy = analyzerUi.copy || {};
  if (links.length > 0) {
    return (
      copy?.fallback_waiting ||
      "The workspace analysis is still warming up. Ask again after indexing finishes for grounded answers."
    );
  }

  return copy?.default_greeting || "Hello! I am your project assistant.";
}

function renderAnalyzerCardIcon(iconKey: string) {
  switch (iconKey) {
    case "visual":
      return <Grid3X3 className="h-5 w-5" />;
    case "jira":
      return <LayoutDashboard className="h-5 w-5" />;
    case "github":
      return <Github className="h-5 w-5" />;
    case "layers":
      return <Layers className="h-5 w-5" />;
    case "chat":
      return <Bot className="h-5 w-5" />;
    default:
      return <Grid3X3 className="h-5 w-5" />;
  }
}

function GraphPreview({
  nodes,
  edges,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
}) {
  const visibleNodes = nodes.slice(0, 8);
  const [dragPositions, setDragPositions] = useState<Record<string, { x: number; y: number }>>({});

  const positionedNodes = useMemo(() => {
    return visibleNodes.map((node, index) => {
      const row = Math.floor(index / 4);
      const column = index % 4;
      const initialX = 90 + column * 170;
      const initialY = 70 + row * 150;
      const pos = dragPositions[node.id] || { x: initialX, y: initialY };
      return { ...node, x: pos.x, y: pos.y };
    });
  }, [visibleNodes, dragPositions]);

  const positionMap = useMemo(
    () => Object.fromEntries(positionedNodes.map((node) => [node.id, node])),
    [positionedNodes],
  );

  const handleDrag = (id: string, info: any) => {
    setDragPositions((prev) => {
      const current = prev[id] || positionedNodes.find((n) => n.id === id) || { x: 0, y: 0 };
      return {
        ...prev,
        [id]: { x: current.x + info.delta.x, y: current.y + info.delta.y },
      };
    });
  };

  if (!positionedNodes.length) {
    return (
      <div className="relative w-full aspect-video bg-neutral-50 dark:bg-neutral-950 rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: "radial-gradient(circle, rgba(128,128,128,0.15) 1px, transparent 1px)",
            backgroundSize: "20px 20px",
          }}
        />

        <motion.div
          animate={{ y: [0, -4, 0] }}
          transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
          className="absolute top-[20%] left-[15%] w-20 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm"
        >
          Frontend
        </motion.div>
        <motion.div
          animate={{ y: [0, -4, 0] }}
          transition={{ repeat: Infinity, duration: 2.5, delay: 0.3, ease: "easeInOut" }}
          className="absolute top-[20%] right-[15%] w-20 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm"
        >
          Backend
        </motion.div>
        <motion.div
          animate={{ y: [0, -4, 0] }}
          transition={{ repeat: Infinity, duration: 2.5, delay: 0.6, ease: "easeInOut" }}
          className="absolute top-[55%] left-[35%] w-24 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm"
        >
          Database
        </motion.div>
        <motion.div
          animate={{ y: [0, -4, 0] }}
          transition={{ repeat: Infinity, duration: 2.5, delay: 0.9, ease: "easeInOut" }}
          className="absolute bottom-[12%] left-[20%] w-16 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm"
        >
          Auth
        </motion.div>
        <motion.div
          animate={{ y: [0, -4, 0] }}
          transition={{ repeat: Infinity, duration: 2.5, delay: 1.2, ease: "easeInOut" }}
          className="absolute bottom-[12%] right-[20%] w-16 h-10 bg-white dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded-lg flex items-center justify-center text-xs font-semibold text-neutral-700 dark:text-neutral-300 shadow-sm"
        >
          API
        </motion.div>

        <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
          <line
            x1="25%"
            y1="35%"
            x2="47%"
            y2="60%"
            stroke="currentColor"
            className="text-neutral-300 dark:text-neutral-700"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
          <line
            x1="75%"
            y1="35%"
            x2="53%"
            y2="60%"
            stroke="currentColor"
            className="text-neutral-300 dark:text-neutral-700"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
          <line
            x1="47%"
            y1="72%"
            x2="28%"
            y2="85%"
            stroke="currentColor"
            className="text-neutral-300 dark:text-neutral-700"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
          <line
            x1="53%"
            y1="72%"
            x2="72%"
            y2="85%"
            stroke="currentColor"
            className="text-neutral-300 dark:text-neutral-700"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
        </svg>
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-video bg-neutral-50 dark:bg-neutral-950 rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(circle, rgba(128,128,128,0.15) 1px, transparent 1px)",
          backgroundSize: "20px 20px",
        }}
      />
      <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
        {edges.slice(0, 12).map((edge) => {
          const source = positionMap[edge.source];
          const target = positionMap[edge.target];
          if (!source || !target) return null;
          return (
            <g key={edge.id}>
              <line
                x1={source.x + 55}
                y1={source.y + 26}
                x2={target.x + 55}
                y2={target.y + 26}
                stroke="currentColor"
                className="text-neutral-300 dark:text-neutral-700"
                strokeWidth="1.5"
                strokeDasharray="5 5"
              />
              {edge.label ? (
                <text
                  x={(source.x + target.x) / 2 + 55}
                  y={(source.y + target.y) / 2 + 18}
                  textAnchor="middle"
                  className="fill-neutral-500 text-[10px]"
                >
                  {edge.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      {positionedNodes.map((node, index) => (
        <motion.div
          key={node.id}
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.04 }}
          drag
          dragMomentum={false}
          onDrag={(_, info) => handleDrag(node.id, info)}
          whileDrag={{ scale: 1.05, cursor: "grabbing" }}
          className="absolute w-[110px] min-h-[54px] rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 shadow-xl shadow-neutral-500/10 px-3 py-2 flex flex-col justify-center cursor-grab"
          style={{ x: node.x, y: node.y }}
        >
          <span className="text-[10px] uppercase tracking-wide text-neutral-400">{node.group}</span>
          <span className="text-xs font-semibold text-neutral-800 dark:text-neutral-100 leading-tight">
            {node.label}
          </span>
        </motion.div>
      ))}
    </div>
  );
}

export default function GithubPage() {
  const { error } = useToast();

  const JIRA_LOGO =
    "https://assets.streamlinehq.com/image/private/w_300,h_300,ar_1/f_auto/v1/icons/professional-tools/jira-software-2-tfcc3k607k9mwgzab3lul.png/jira-software-2-wcevcgjziue4ibno342wv.png?_a=DATAiZAAZAA0";

  const [links, setLinks] = useState<ProjectLink[]>([]);
  const [tempRepoUrl, setTempRepoUrl] = useState("");
  const [hasStarted, setHasStarted] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<AnalyzerMessage[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRepoInput, setShowRepoInput] = useState(false);
  const [visualMode, setVisualMode] = useState(false);
  const [platform, setPlatform] = useState<"GitHub" | "Jira">("GitHub");
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState("idle");
  const [visualization, setVisualization] = useState<VisualizationPayload | null>(null);
  const [analyzerUi, setAnalyzerUi] = useState<UiBootstrapPayload["analyzer"] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const analyzerCards = (analyzerUi?.cards || []).map((card) => ({
    id: card.id,
    title: card.title,
    description: card.description,
    icon: renderAnalyzerCardIcon(card.icon_key),
  }));

  useEffect(() => {
    const interval = setInterval(() => {
      setPlatform((previous) => (previous === "GitHub" ? "Jira" : "GitHub"));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let active = true;

    const hydrateUi = async () => {
      try {
        const response = await loadUiBootstrap({
          uiSurface: "repo_analyzer.bootstrap",
        });
        if (!active) return;
        if (response.data?.analyzer) {
          setAnalyzerUi(response.data.analyzer);
        }
      } catch (bootstrapError) {
        console.error("Failed to load analyzer UI bootstrap:", bootstrapError);
      } finally {
        if (active) setIsLoading(false);
      }
    };

    void hydrateUi();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAnalyzing]);

  const currentSourceKind = sourceKindFromLinks(links);

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
    if (links.some((link) => link.type === type)) {
      error(`You can only link one ${type} workspace at a time.`);
      return false;
    }
    setLinks((previous) => [...previous, { url: newUrl, type }]);
    setTempRepoUrl("");
    return true;
  };

  const appendAssistantMessage = (content: string) => {
    setMessages((previous) => [...previous, { role: "assistant", content }]);
  };

  const loadWorkspaceVisualization = async (
    nextWorkspaceId: string,
    nextSourceKind: SourceKind | undefined,
  ) => {
    const response = await loadVisualization({
      workspaceId: nextWorkspaceId,
      sourceKind: nextSourceKind,
      uiSurface: "repo_analyzer.visual_mode",
    });

    setVisualization(response.data);
    setAnalysisStatus(response.meta.status);
  };

  const pollWorkspace = async (
    nextWorkspaceId: string,
    nextSourceKind: SourceKind | undefined,
  ) => {
    for (let attempt = 0; attempt < 10; attempt += 1) {
      const response = await loadWorkspaceStatus({
        workspaceId: nextWorkspaceId,
        sourceKind: nextSourceKind,
        uiSurface: "repo_analyzer.status_poll",
      });
      setAnalysisStatus(response.meta.status);

      if (response.meta.status === "ready" || response.meta.status === "partial") {
        await loadWorkspaceVisualization(nextWorkspaceId, nextSourceKind);
        return;
      }
      if (response.meta.status === "failed") {
        return;
      }

      await delay(2000);
    }

    await loadWorkspaceVisualization(nextWorkspaceId, nextSourceKind);
  };

  const syncWorkspaceAnalysis = async (currentLinks: ProjectLink[]) => {
    if (!currentLinks.length || !USE_MAIN_SERVER_ANALYZER) {
      setWorkspaceId(null);
      setVisualization(null);
      setAnalysisStatus("idle");
      return;
    }

    const githubUrl = currentLinks.find((link) => link.type === "GitHub")?.url;
    const jiraUrl = currentLinks.find((link) => link.type === "Jira")?.url;
    const sourceKind = sourceKindFromLinks(currentLinks);

    setAnalysisStatus("accepted");
    setVisualization(null);

    try {
      const response = await analyzeWorkspace({
        githubUrl,
        jiraUrl,
        uiSurface: "repo_analyzer.link_submit",
      });
      const nextWorkspaceId =
        String(response.data?.workspace_id || response.meta.workspace_id || "").trim();

      if (!nextWorkspaceId || response.meta.status === "failed") {
        setWorkspaceId(null);
        setVisualization(null);
        setAnalysisStatus("idle");
        return;
      }

      setWorkspaceId(nextWorkspaceId);
      setAnalysisStatus(response.meta.status);
      await pollWorkspace(nextWorkspaceId, sourceKind);
    } catch (analysisError) {
      console.error("Main Server analyzer failed, falling back:", analysisError);
      setWorkspaceId(null);
      setVisualization(null);
      setAnalysisStatus("idle");
    }
  };

  const handleRemoveLink = (index: number) => {
    const updatedLinks = links.filter((_, currentIndex) => currentIndex !== index);
    setLinks(updatedLinks);
    setWorkspaceId(null);
    setVisualization(null);
    setAnalysisStatus("idle");

    if (hasStarted) {
      void syncWorkspaceAnalysis(updatedLinks);
    }
  };

  const handleStart = (event?: React.FormEvent) => {
    event?.preventDefault();
    let currentLinks = [...links];

    if (tempRepoUrl.trim() && currentLinks.length < 2) {
      const type = detectPlatform(tempRepoUrl);
      if (!type) {
        error("Invalid link. Please provide a valid GitHub or Jira URL.");
        return;
      }
      if (currentLinks.some((link) => link.type === type)) {
        error(`You can only link one ${type} workspace at a time.`);
        return;
      }
      currentLinks.push({ url: tempRepoUrl, type });
      setLinks(currentLinks);
      setTempRepoUrl("");
    }

    setHasStarted(true);
    setMessages([{ role: "assistant", content: buildGreeting(currentLinks, analyzerUi || {}) }]);
    void syncWorkspaceAnalysis(currentLinks);
  };

  const handleStartLinkless = () => {
    setWorkspaceId("default_chat");
    setHasStarted(true);
    setMessages([{ role: "assistant", content: "I am ready. What would you like to discuss?" }]);
  };

  const handleSend = async (event?: React.FormEvent) => {
    event?.preventDefault();
    if (!input.trim()) return;

    const query = input;
    const nextMessages = [...messages, { role: "user" as const, content: query }];
    setMessages(nextMessages);
    setInput("");
    setIsAnalyzing(true);

    try {
      if (USE_MAIN_SERVER_ANALYZER) {
        const activeWorkspaceId = workspaceId || (links.length > 0 ? "active_workspace" : "default_chat");
        const response = await chatWorkspace({
          workspaceId: activeWorkspaceId,
          query,
          sourceKind: currentSourceKind,
          uiSurface: "repo_analyzer.chat_panel",
        });

        const answer =
          String(response.data?.answer || "").trim() || buildFallbackReply(analyzerUi || {}, links);
        setMessages([...nextMessages, { role: "assistant", content: answer }]);
      } else {
        setMessages([...nextMessages, { role: "assistant", content: buildFallbackReply(analyzerUi || {}, links) }]);
      }
    } catch (chatError) {
      console.error("Chat failed, using fallback:", chatError);
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: buildFallbackReply(analyzerUi || {}, links),
        },
      ]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSetRepoInside = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!tempRepoUrl.trim() || links.length >= 2) return;

    const newType = detectPlatform(tempRepoUrl);
    if (!newType) {
      error("Invalid link. Please provide a valid GitHub or Jira URL.");
      return;
    }
    if (links.some((link) => link.type === newType)) {
      error(`You can only link one ${newType} workspace at a time.`);
      return;
    }

    const anchoredUrl = tempRepoUrl;
    const updatedLinks = [...links, { url: anchoredUrl, type: newType }];
    setLinks(updatedLinks);
    setTempRepoUrl("");
    setShowRepoInput(false);

    if (hasStarted) {
      appendAssistantMessage(`I have anchored a new project: \`${anchoredUrl}\`.`);
      void syncWorkspaceAnalysis(updatedLinks);
    }
  };

  const JiraIcon = ({ className = "w-5 h-5" }: { className?: string }) => (
    <img src={JIRA_LOGO} alt="Jira" className={className} />
  );

  const graphNodes = visualization?.graph?.nodes || [];
  const graphEdges = visualization?.graph?.edges || [];

  if (isLoading || !analyzerUi) {
    return (
      <div className="flex justify-center items-center h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900 dark:border-white"></div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col bg-neutral-50 dark:bg-neutral-950">
      {!hasStarted ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-1 flex flex-col items-center justify-center max-w-3xl mx-auto w-full px-4 gap-0"
        >
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
            <p className="text-neutral-500 dark:text-neutral-400 text-sm">
              {analyzerUi.intro_subtitle || "Paste a GitHub repository or Jira workspace link below to begin live analysis."}
            </p>
          </div>

          {links.length > 0 && (
            <div className="flex gap-2 mb-4 flex-wrap justify-center">
              <AnimatePresence>
                {links.map((link, index) => (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    key={link.url}
                    className="flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full px-4 py-2 text-sm font-medium text-neutral-600 dark:text-neutral-300 shadow-sm"
                  >
                    {link.type === "GitHub" ? <Github className="w-4 h-4" /> : <JiraIcon className="w-4 h-4" />}
                    <span className="truncate max-w-[200px]">{link.url.replace(/^https?:\/\/(www\.)?/, "")}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveLink(index)}
                      className="ml-1 hover:text-neutral-500 transition-colors p-1"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

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
                onChange={(event) => setTempRepoUrl(event.target.value)}
                disabled={links.length >= 2}
                placeholder={links.length >= 2 ? "Maximum links added" : `Paste ${platform} URL here...`}
                className="w-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl py-4 pl-12 pr-44 text-lg focus:outline-none focus:ring-2 focus:ring-neutral-500/50 shadow-sm text-neutral-900 dark:text-white placeholder:text-neutral-400 transition-all disabled:opacity-50"
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
                  <button
                    type="button"
                    onClick={() => handleStart()}
                    className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors"
                  >
                    Skip
                  </button>
                )}
                <button
                  disabled={
                    (!tempRepoUrl.trim() && links.length === 0) ||
                    (links.length >= 2 && tempRepoUrl.trim().length > 0)
                  }
                  type="submit"
                  className="bg-neutral-600 hover:bg-neutral-700 disabled:bg-neutral-300 dark:disabled:bg-neutral-800 disabled:text-neutral-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 shadow-sm"
                >
                  Start <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
            <div className="flex justify-center mt-6">
              <button
                onClick={handleStartLinkless}
                className="text-sm font-medium text-neutral-500 hover:text-neutral-900 dark:hover:text-white transition-colors underline decoration-neutral-300 dark:decoration-neutral-700 underline-offset-4"
              >
                Or, chat without linking a workspace
              </button>
            </div>
          </div>
        </motion.div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full">
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
                    {platform === "GitHub" ? (
                      <Github className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
                    ) : (
                      <JiraIcon className="w-4 h-4" />
                    )}
                  </motion.div>
                </AnimatePresence>
              </div>
              <div>
                <h2 className="font-semibold text-neutral-900 dark:text-white leading-none mb-1">
                  {analyzerUi.assistant_name || "Project Analyser"}
                </h2>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-none">
                  {analyzerUi.assistant_tagline || "AI Code and Task Assistant"}
                </p>
              </div>
            </div>
          </header>
          {visualMode ? (
            <div className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar flex flex-col items-center justify-center">
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-2xl">
                <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-xl bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center">
                      <Grid3X3 className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                    </div>
                    <div>
                      <h3 className="font-bold text-neutral-900 dark:text-white">
                        {analyzerUi.visualizer_title || "Dynamic Visualiser"}
                      </h3>
                      <p className="text-xs text-neutral-500">
                        {analyzerUi.visualizer_subtitle || "Real-time project architecture flow"}
                      </p>
                    </div>
                  </div>

                  <GraphPreview nodes={graphNodes} edges={graphEdges} />
                  <p className="text-xs text-neutral-400 text-center mt-4">
                    {analyzerUi.visualizer_caption || "Link a repository or board to generate a live architecture graph."}
                  </p>
                </div>
              </motion.div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 custom-scrollbar">
              {messages.map((message, index) => (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={`${message.role}-${index}`}
                  className={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {message.role === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-500/20 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 ${
                      message.role === "user"
                        ? "bg-neutral-900 dark:bg-white text-white dark:text-neutral-900"
                        : "bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-800 dark:text-neutral-200 shadow-sm"
                    }`}
                  >
                    <div className="leading-relaxed text-[15px] space-y-3 break-words text-neutral-800 dark:text-neutral-200">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-2 space-y-1" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-2 space-y-1" {...props} />,
                          li: ({node, ...props}) => <li className="pl-1" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-semibold text-neutral-900 dark:text-white" {...props} />,
                          a: ({node, ...props}) => <a className="text-pink-500 hover:text-pink-400 underline underline-offset-2" {...props} />,
                          code: ({node, inline, className, children, ...props}: any) => {
                            const match = /language-(\w+)/.exec(className || '')
                            return !inline ? (
                              <div className="my-3 bg-[#1e1e1e] border border-neutral-800 overflow-x-auto rounded-xl p-4 shadow-inner">
                                <code className="text-sm font-mono text-neutral-200 whitespace-pre" {...props}>
                                  {children}
                                </code>
                              </div>
                            ) : (
                              <code className="px-1.5 py-0.5 mx-0.5 rounded-md bg-neutral-100 dark:bg-neutral-800 text-pink-600 dark:text-pink-400 font-mono text-[13px] border border-neutral-200 dark:border-neutral-700" {...props}>
                                {children}
                              </code>
                            )
                          }
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                  {message.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center shrink-0 mt-1">
                      <User className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                    </div>
                  )}
                </motion.div>
              ))}
              {isAnalyzing && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 justify-start">
                  <div className="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-500/20 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                  </div>
                  <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl px-5 py-4 flex items-center gap-2 shadow-sm">
                    <div className="w-2 h-2 bg-neutral-500/60 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-neutral-500/60 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                    <div
                      className="w-2 h-2 bg-neutral-500/60 rounded-full animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    />
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          <div className="p-4 bg-neutral-50 dark:bg-neutral-950 shrink-0">
            <div className="max-w-3xl mx-auto relative pt-8">
              {links.length > 0 && !showRepoInput && (
                <div className="absolute top-0 left-0 flex items-center gap-2 flex-wrap">
                  <AnimatePresence>
                    {links.map((link, index) => (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        key={link.url}
                        className="flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full px-3 py-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-300 shadow-sm"
                      >
                        {link.type === "GitHub" ? <Github className="w-3.5 h-3.5" /> : <JiraIcon className="w-3.5 h-3.5" />}
                        <span className="truncate max-w-[150px]">{link.url.replace(/^https?:\/\/(www\.)?/, "")}</span>
                        <button onClick={() => handleRemoveLink(index)} className="ml-1 hover:text-neutral-500 transition-colors">
                          <X className="w-3 h-3" />
                        </button>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}

              {showRepoInput ? (
                <form onSubmit={handleSetRepoInside} className="relative flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-500 rounded-2xl p-2 shadow-sm transition-all ring-2 ring-neutral-500/20">
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
                    onChange={(event) => setTempRepoUrl(event.target.value)}
                    disabled={links.length >= 2}
                    placeholder={links.length >= 2 ? "Maximum 2 links attached..." : `Link another ${platform} URL...`}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-base py-2 px-2 text-neutral-900 dark:text-white placeholder:text-neutral-400 outline-none disabled:opacity-50"
                  />
                  <button
                    type="button"
                    onClick={() => setShowRepoInput(false)}
                    className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors shrink-0"
                  >
                    Cancel
                  </button>
                  <button
                    disabled={!tempRepoUrl.trim() || links.length >= 2}
                    type="submit"
                    className="px-4 py-2 bg-neutral-600 disabled:bg-neutral-300 dark:disabled:bg-neutral-800 disabled:text-neutral-500 hover:bg-neutral-700 text-white rounded-xl text-sm font-medium transition-colors shrink-0"
                  >
                    Add
                  </button>
                </form>
              ) : (
                <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-neutral-500/50 focus-within:border-neutral-500 transition-all">
                  <button
                    type="button"
                    onClick={() => setShowRepoInput(true)}
                    className={`relative w-11 h-11 rounded-xl transition-colors shrink-0 flex items-center justify-center ${
                      links.length > 0
                        ? "text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-500/10"
                        : "text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                    }`}
                    title="Manage References"
                  >
                    <Plus className="w-5 h-5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => setVisualMode((previous) => !previous)}
                    className={`relative w-11 h-11 rounded-xl transition-colors shrink-0 flex items-center justify-center ${
                      visualMode
                        ? "text-white bg-neutral-700 dark:bg-white dark:text-neutral-900"
                        : "text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                    }`}
                    title="Dynamic Visualiser"
                  >
                    <Grid3X3 className="w-5 h-5" />
                  </button>

                  <textarea
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder={
                      links.length > 0
                        ? "Ask about your attached projects..."
                        : `Ask a general question or attach a ${platform} repo...`
                    }
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
    </div>
  );
}
