import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Github, Send, Link as LinkIcon, X, Bot, User, ArrowRight, LayoutDashboard, Plus, Grid3X3, Layers, Sparkles } from "lucide-react";
import { Component as MorphingCardStack } from "@/src/components/ui/morphing-card-stack";
import { useToast } from "@/src/components/ui/use-toast";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const JIRA_LOGO = "https://assets.streamlinehq.com/image/private/w_300,h_300,ar_1/f_auto/v1/icons/professional-tools/jira-software-2-tfcc3k607k9mwgzab3lul.png/jira-software-2-wcevcgjziue4ibno342wv.png?_a=DATAiZAAZAA0";

  const [platform, setPlatform] = useState<"GitHub" | "Jira">("GitHub");

  useEffect(() => {
    const interval = setInterval(() => {
      setPlatform(prev => prev === "GitHub" ? "Jira" : "GitHub");
    }, 5000);
    return () => clearInterval(interval);
  }, []);

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

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;
    
    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setInput("");
    setIsAnalyzing(true);
    
    setTimeout(() => {
      setIsAnalyzing(false);
      const contextualContent = links.length > 0 
        ? `Based on your linked projects (${links.map(l => l.type).join(' & ')}), here is your response... (Mock)`
        : "Here is a general answer to your request... (Mock)";
      setMessages([...newMessages, { role: "assistant", content: contextualContent }]);
    }, 1500);
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
    <div className="h-[calc(100vh-6rem)] flex flex-col bg-neutral-50 dark:bg-neutral-950">
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
                    className="flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full px-4 py-2 text-sm font-medium text-neutral-600 dark:text-neutral-300 shadow-sm"
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
          </header>

          {/* Messages / Visualiser Area */}
          {visualMode ? (
            <div className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar flex flex-col items-center justify-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-2xl"
              >
                <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 shadow-sm">
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
                  <div className="relative w-full aspect-video bg-neutral-50 dark:bg-neutral-950 rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden">
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
                    <div className="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-500/20 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
                    </div>
                  )}
                  <div className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 ${msg.role === 'user' ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900' : 'bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-800 dark:text-neutral-200 shadow-sm'}`}>
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  {msg.role === 'user' && (
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
                    <div className="w-2 h-2 bg-neutral-500/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-neutral-500/60 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 bg-neutral-50 dark:bg-neutral-950 shrink-0">
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
                         className="flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full px-3 py-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-300 shadow-sm"
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
                    onChange={e => setTempRepoUrl(e.target.value)}
                    disabled={links.length >= 2}
                    placeholder={links.length >= 2 ? "Maximum 2 links attached..." : `Link another ${platform} URL...`}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-base py-2 px-2 text-neutral-900 dark:text-white placeholder:text-neutral-400 outline-none disabled:opacity-50"
                  />
                  <button type="button" onClick={() => setShowRepoInput(false)} className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors shrink-0">
                    Cancel
                  </button>
                  <button disabled={!tempRepoUrl.trim() || links.length >= 2} type="submit" className="px-4 py-2 bg-neutral-600 disabled:bg-neutral-300 dark:disabled:bg-neutral-800 disabled:text-neutral-500 hover:bg-neutral-700 text-white rounded-xl text-sm font-medium transition-colors shrink-0">
                    Add
                  </button>
                </form>
              ) : (
                <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-neutral-500/50 focus-within:border-neutral-500 transition-all">
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
    </div>
  );
}
