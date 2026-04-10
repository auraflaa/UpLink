import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Github, Send, Link as LinkIcon, X, Bot, User, ArrowRight, LayoutDashboard } from "lucide-react";

export default function GithubPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [hasStarted, setHasStarted] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRepoInput, setShowRepoInput] = useState(false);
  const [tempRepoUrl, setTempRepoUrl] = useState("");
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

  const handleStart = (e?: React.FormEvent) => {
    e?.preventDefault();
    setHasStarted(true);
    if (repoUrl) {
      setMessages([{ role: "assistant", content: `I'm ready to analyze \`${repoUrl}\`. What would you like to know?` }]);
    } else {
      setMessages([{ role: "assistant", content: "Hello! I'm your code analysis assistant. You haven't linked a project yet. You can link one using the button below, or just ask me general programming questions." }]);
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
      setMessages([...newMessages, { role: "assistant", content: repoUrl ? `Based on the project at ${repoUrl}, here is an analysis of your request... (Mock response)` : "Here is a general answer to your programming question... (Mock response)" }]);
    }, 1500);
  };

  const handleSetRepo = (e: React.FormEvent) => {
    e.preventDefault();
    if (tempRepoUrl) {
      setRepoUrl(tempRepoUrl);
      setShowRepoInput(false);
      setMessages([...messages, { role: "assistant", content: `Project linked: \`${tempRepoUrl}\`. What would you like to know about it?` }]);
    }
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col bg-neutral-50 dark:bg-neutral-950">
      {!hasStarted ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-1 flex flex-col items-center justify-end max-w-4xl mx-auto w-full px-4 pb-32"
        >
          {/* Top Section: Logos & Titles - Now clustered with the input */}
          <div className="flex flex-col items-center mb-10">
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
                    transition={{ 
                      duration: 0.4, 
                      ease: [0.23, 1, 0.32, 1] 
                    }}
                    className={`absolute font-extrabold ${platform === "GitHub" ? "text-neutral-900 dark:text-white" : "text-neutral-900 dark:text-white"}`}
                  >
                    {platform}
                  </motion.div>
                </AnimatePresence>
              </motion.div>
               workspace
            </h1>
            <p className="text-neutral-500 dark:text-neutral-400 text-sm">Paste a repository or project link below to begin analysis</p>
          </div>
          
          {/* Bottom Section: URL Input */}
          <div className="w-full max-w-3xl animate-in fade-in slide-in-from-bottom-4 duration-1000">
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
                    {platform === "GitHub" ? <Github className="w-5 h-5" /> : <img src={JIRA_LOGO} alt="Jira" className="w-5 h-5" />}
                  </motion.div>
                </AnimatePresence>
              </div>
              <input 
                type="url"
                value={repoUrl}
                onChange={e => setRepoUrl(e.target.value)}
                placeholder={`Paste ${platform} URL here...`}
                className="w-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl py-4 pl-12 pr-40 text-lg focus:outline-none focus:ring-2 focus:ring-neutral-500/50 shadow-sm text-neutral-900 dark:text-white placeholder:text-neutral-400 transition-all"
              />
              <div className="absolute right-2 flex items-center gap-2">
                <button type="button" onClick={() => handleStart()} className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors">
                  Skip
                </button>
                <button type="submit" className="bg-neutral-600 hover:bg-neutral-700 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 shadow-sm">
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
                      {platform === "GitHub" ? <Github className="w-4 h-4 text-neutral-600 dark:text-neutral-400" /> : <img src={JIRA_LOGO} alt="Jira" className="w-4 h-4" />}
                    </motion.div>
                  </AnimatePresence>
              </div>
              <div>
                <h2 className="font-semibold text-neutral-900 dark:text-white leading-none mb-1">Project Analyser</h2>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-none">AI Code & Task Assistant</p>
              </div>
            </div>
          </header>

          {/* Messages Area */}
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

          {/* Input Area */}
          <div className="p-4 bg-neutral-50 dark:bg-neutral-950 shrink-0">
            <div className="max-w-3xl mx-auto relative">
              {/* Repo Badge / Input */}
              {showRepoInput ? (
                <form onSubmit={handleSetRepo} className="relative flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-500 rounded-2xl p-2 shadow-sm transition-all ring-2 ring-neutral-500/20">
                  <div className="p-3 text-neutral-600 dark:text-neutral-400 shrink-0 relative w-11 h-11 flex items-center justify-center">
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={platform}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="absolute"
                      >
                        {platform === "GitHub" ? <Github className="w-5 h-5" /> : <img src={JIRA_LOGO} alt="Jira" className="w-5 h-5" />}
                      </motion.div>
                    </AnimatePresence>
                  </div>
                  <input 
                    autoFocus
                    type="url"
                    value={tempRepoUrl}
                    onChange={e => setTempRepoUrl(e.target.value)}
                    placeholder={`Paste ${platform} URL...`}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-base py-2 px-2 text-neutral-900 dark:text-white placeholder:text-neutral-400 outline-none"
                  />
                  <button type="button" onClick={() => setShowRepoInput(false)} className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors shrink-0">
                    Cancel
                  </button>
                  <button type="submit" className="px-4 py-2 bg-neutral-600 hover:bg-neutral-700 text-white rounded-xl text-sm font-medium transition-colors shrink-0">
                    Save
                  </button>
                </form>
              ) : (
                <>
                  {repoUrl && (
                    <div className="absolute -top-10 left-0 flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full px-3 py-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-300 shadow-sm">
                      <LayoutDashboard className="w-3.5 h-3.5" />
                      <span className="truncate max-w-[200px]">{repoUrl.replace('https://github.com/', '').replace('https://', '')}</span>
                      <button onClick={() => setRepoUrl("")} className="ml-1 hover:text-neutral-500 transition-colors">
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                  <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-neutral-500/50 focus-within:border-neutral-500 transition-all">
                    <button 
                      type="button"
                      onClick={() => {
                        setTempRepoUrl(repoUrl);
                        setShowRepoInput(true);
                       }}
                      className={`relative w-11 h-11 rounded-xl transition-colors shrink-0 flex items-center justify-center ${repoUrl ? 'text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-500/10' : 'text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800'}`}
                      title={repoUrl ? "Change Project" : "Link Project Repository"}
                    >
                      <AnimatePresence mode="wait">
                        <motion.div
                           key={platform}
                           initial={{ opacity: 0, scale: 0.8 }}
                           animate={{ opacity: 1, scale: 1 }}
                           exit={{ opacity: 0, scale: 0.8 }}
                           className="absolute"
                        >
                           {platform === "GitHub" ? <Github className="w-5 h-5" /> : <img src={JIRA_LOGO} alt="Jira" className="w-5 h-5" />}
                        </motion.div>
                      </AnimatePresence>
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
                      placeholder={repoUrl ? "Ask about this project..." : `Ask a general question or link a ${platform} repo...`}
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
                </>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
