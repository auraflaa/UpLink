import React, { useState, useRef, useEffect } from "react";
import { motion } from "motion/react";
import { Github, Send, Link as LinkIcon, X, Bot, User, ArrowRight } from "lucide-react";

export default function GithubPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [hasStarted, setHasStarted] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRepoInput, setShowRepoInput] = useState(false);
  const [tempRepoUrl, setTempRepoUrl] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
      setMessages([{ role: "assistant", content: "Hello! I'm your code analysis assistant. You haven't linked a repository yet. You can link one using the GitHub button below, or just ask me general programming questions." }]);
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
      setMessages([...newMessages, { role: "assistant", content: repoUrl ? `Based on the repository at ${repoUrl}, here is an analysis of your request... (Mock response)` : "Here is a general answer to your programming question... (Mock response)" }]);
    }, 1500);
  };

  const handleSetRepo = (e: React.FormEvent) => {
    e.preventDefault();
    if (tempRepoUrl) {
      setRepoUrl(tempRepoUrl);
      setShowRepoInput(false);
      setMessages([...messages, { role: "assistant", content: `Repository linked: \`${tempRepoUrl}\`. What would you like to know about it?` }]);
    }
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col bg-neutral-50 dark:bg-neutral-950">
      {!hasStarted ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-1 flex flex-col items-center justify-center max-w-3xl mx-auto w-full px-4"
        >
          <div className="w-20 h-20 bg-white dark:bg-neutral-900 rounded-full flex items-center justify-center mb-8 shadow-sm border border-neutral-200 dark:border-neutral-800">
            <Github className="w-10 h-10 text-neutral-900 dark:text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-neutral-900 dark:text-white mb-8 text-center tracking-tight">
            What repository do you want to analyze?
          </h1>
          
          <form onSubmit={handleStart} className="w-full relative flex items-center">
            <div className="absolute left-4 text-neutral-400">
              <LinkIcon className="w-5 h-5" />
            </div>
            <input 
              type="url"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              placeholder="Paste GitHub URL here..."
              className="w-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl py-4 pl-12 pr-40 text-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 shadow-sm text-neutral-900 dark:text-white placeholder:text-neutral-400"
            />
            <div className="absolute right-2 flex items-center gap-2">
              <button type="button" onClick={() => handleStart()} className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors">
                Skip
              </button>
              <button type="submit" className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 shadow-sm">
                Start <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
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
              <div className="w-8 h-8 bg-purple-100 dark:bg-purple-500/20 rounded-lg flex items-center justify-center">
                <Github className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h2 className="font-semibold text-neutral-900 dark:text-white leading-none mb-1">Repo Analyzer</h2>
                <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-none">AI Code Assistant</p>
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
                  <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-500/20 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-5 h-5 text-purple-600 dark:text-purple-400" />
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
                <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-500/20 flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl px-5 py-4 flex items-center gap-2 shadow-sm">
                  <div className="w-2 h-2 bg-purple-500/60 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-purple-500/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <div className="w-2 h-2 bg-purple-500/60 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
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
                <form onSubmit={handleSetRepo} className="relative flex items-center gap-2 bg-white dark:bg-neutral-900 border border-purple-500 rounded-2xl p-2 shadow-sm transition-all ring-2 ring-purple-500/20">
                  <div className="p-3 text-purple-600 dark:text-purple-400 shrink-0">
                    <Github className="w-5 h-5" />
                  </div>
                  <input 
                    autoFocus
                    type="url"
                    value={tempRepoUrl}
                    onChange={e => setTempRepoUrl(e.target.value)}
                    placeholder="Paste GitHub URL..."
                    className="flex-1 bg-transparent border-none focus:ring-0 text-base py-2 px-2 text-neutral-900 dark:text-white placeholder:text-neutral-400 outline-none"
                  />
                  <button type="button" onClick={() => setShowRepoInput(false)} className="px-4 py-2 text-sm font-medium text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors shrink-0">
                    Cancel
                  </button>
                  <button type="submit" className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-sm font-medium transition-colors shrink-0">
                    Save
                  </button>
                </form>
              ) : (
                <>
                  {repoUrl && (
                    <div className="absolute -top-10 left-0 flex items-center gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-full px-3 py-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-300 shadow-sm">
                      <Github className="w-3.5 h-3.5" />
                      <span className="truncate max-w-[200px]">{repoUrl.replace('https://github.com/', '')}</span>
                      <button onClick={() => setRepoUrl("")} className="ml-1 hover:text-red-500 transition-colors">
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                  <form onSubmit={handleSend} className="relative flex items-end gap-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-purple-500/50 focus-within:border-purple-500 transition-all">
                    <button 
                      type="button"
                      onClick={() => {
                        setTempRepoUrl(repoUrl);
                        setShowRepoInput(true);
                      }}
                      className={`p-3 rounded-xl transition-colors shrink-0 ${repoUrl ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10' : 'text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800'}`}
                      title={repoUrl ? "Change Repository" : "Link GitHub Repository"}
                    >
                      <Github className="w-5 h-5" />
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
                      placeholder={repoUrl ? "Ask about this repository..." : "Ask a general question or link a repo..."}
                      className="flex-1 max-h-32 min-h-[44px] bg-transparent border-none focus:ring-0 resize-none py-3 px-2 text-neutral-900 dark:text-white placeholder:text-neutral-400 outline-none"
                      rows={1}
                    />
                    
                    <button 
                      type="submit"
                      disabled={!input.trim() || isAnalyzing}
                      className="p-3 bg-purple-600 hover:bg-purple-700 disabled:bg-neutral-200 dark:disabled:bg-neutral-800 disabled:text-neutral-400 text-white rounded-xl transition-colors shrink-0"
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
