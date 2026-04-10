import { useState } from "react";
import { motion } from "motion/react";
import { Database, Bot, Layout, Play, Share, Settings2, Plus, ArrowRight, FileText, Github, MessageSquare, Sparkles, CheckCircle2 } from "lucide-react";

export default function BuilderPage() {
  const [selectedNode, setSelectedNode] = useState<string | null>("ai-node");
  const [isPublishing, setIsPublishing] = useState(false);
  const [published, setPublished] = useState(false);

  const handlePublish = () => {
    setIsPublishing(true);
    setTimeout(() => {
      setIsPublishing(false);
      setPublished(true);
    }, 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="h-[calc(100vh-8rem)] flex flex-col"
    >
      <header className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">AI App Studio</h1>
          <p className="text-neutral-600 dark:text-neutral-400">Build custom AI workflows by connecting data sources to AI functions.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-xl font-medium hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors flex items-center gap-2">
            <Play className="w-4 h-4" /> Test Run
          </button>
          <button 
            onClick={handlePublish}
            disabled={isPublishing || published}
            className={`px-5 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
              published 
                ? "bg-emerald-500 text-white" 
                : "bg-purple-600 hover:bg-purple-700 text-white"
            }`}
          >
            {isPublishing ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Publishing...</>
            ) : published ? (
              <><CheckCircle2 className="w-4 h-4" /> Published</>
            ) : (
              <><Share className="w-4 h-4" /> Publish App</>
            )}
          </button>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        
        {/* Left Sidebar: Blocks Palette */}
        <div className="lg:col-span-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-5 flex flex-col overflow-y-auto custom-scrollbar shadow-sm dark:shadow-none">
          <h3 className="font-semibold text-neutral-900 dark:text-white mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-purple-500" /> Add Blocks
          </h3>
          
          <div className="space-y-6">
            {/* Data Sources */}
            <div>
              <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider mb-3">Data Sources</h4>
              <div className="space-y-2">
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-purple-400 dark:hover:border-purple-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0"><FileText className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Resume PDF</span>
                </div>
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-purple-400 dark:hover:border-purple-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0"><Github className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">GitHub Repo</span>
                </div>
              </div>
            </div>

            {/* AI Functions */}
            <div>
              <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider mb-3">AI Functions</h4>
              <div className="space-y-2">
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-purple-400 dark:hover:border-purple-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0"><Bot className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Gap Analyzer</span>
                </div>
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-purple-400 dark:hover:border-purple-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0"><Sparkles className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Custom Prompt</span>
                </div>
              </div>
            </div>

            {/* UI Components */}
            <div>
              <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider mb-3">Outputs & UI</h4>
              <div className="space-y-2">
                <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl flex items-center gap-3 cursor-grab hover:border-purple-400 dark:hover:border-purple-500 transition-colors bg-neutral-50 dark:bg-neutral-950/50">
                  <div className="w-8 h-8 rounded-lg bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400 flex items-center justify-center shrink-0"><MessageSquare className="w-4 h-4" /></div>
                  <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Chat Interface</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Middle: Canvas */}
        <div className="lg:col-span-6 bg-neutral-100 dark:bg-neutral-950/50 border border-neutral-200 dark:border-neutral-800 rounded-3xl relative overflow-hidden flex items-center justify-center shadow-inner">
          {/* Dotted Background */}
          <div className="absolute inset-0 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] dark:bg-[radial-gradient(#404040_1px,transparent_1px)] [background-size:24px_24px] opacity-50"></div>
          
          {/* Mock Pipeline */}
          <div className="relative z-10 flex flex-col items-center gap-6 w-full max-w-md px-6">
            
            {/* Input Layer */}
            <div className="flex gap-4 w-full justify-center">
              <div 
                onClick={() => setSelectedNode("data-1")}
                className={`p-4 rounded-2xl border-2 bg-white dark:bg-neutral-900 shadow-sm cursor-pointer transition-all ${selectedNode === "data-1" ? "border-blue-500 ring-4 ring-blue-500/20" : "border-neutral-200 dark:border-neutral-700 hover:border-blue-400"}`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center"><FileText className="w-5 h-5" /></div>
                  <div>
                    <p className="text-sm font-bold text-neutral-900 dark:text-white">Resume</p>
                    <p className="text-xs text-neutral-500">PDF Document</p>
                  </div>
                </div>
              </div>

              <div 
                onClick={() => setSelectedNode("data-2")}
                className={`p-4 rounded-2xl border-2 bg-white dark:bg-neutral-900 shadow-sm cursor-pointer transition-all ${selectedNode === "data-2" ? "border-emerald-500 ring-4 ring-emerald-500/20" : "border-neutral-200 dark:border-neutral-700 hover:border-emerald-400"}`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center"><Github className="w-5 h-5" /></div>
                  <div>
                    <p className="text-sm font-bold text-neutral-900 dark:text-white">GitHub</p>
                    <p className="text-xs text-neutral-500">API Source</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Arrow Down */}
            <div className="flex gap-16 text-neutral-300 dark:text-neutral-600">
              <div className="w-px h-8 bg-current"></div>
              <div className="w-px h-8 bg-current"></div>
            </div>

            {/* AI Layer */}
            <div 
              onClick={() => setSelectedNode("ai-node")}
              className={`w-full p-5 rounded-2xl border-2 bg-white dark:bg-neutral-900 shadow-md cursor-pointer transition-all ${selectedNode === "ai-node" ? "border-purple-500 ring-4 ring-purple-500/20" : "border-neutral-200 dark:border-neutral-700 hover:border-purple-400"}`}
            >
              <div className="flex items-center gap-4 mb-3">
                <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 flex items-center justify-center"><Bot className="w-6 h-6" /></div>
                <div>
                  <p className="text-base font-bold text-neutral-900 dark:text-white">Career Gap Analyzer</p>
                  <p className="text-sm text-neutral-500">AI Function</p>
                </div>
              </div>
              <div className="bg-neutral-50 dark:bg-neutral-950 rounded-xl p-3 border border-neutral-100 dark:border-neutral-800">
                <p className="text-xs text-neutral-600 dark:text-neutral-400 font-mono line-clamp-2">
                  "Compare my resume and GitHub repos against entry-level React developer roles. Highlight missing skills."
                </p>
              </div>
            </div>

            {/* Arrow Down */}
            <div className="w-px h-8 bg-neutral-300 dark:bg-neutral-600"></div>

            {/* Output Layer */}
            <div 
              onClick={() => setSelectedNode("output-node")}
              className={`w-full p-4 rounded-2xl border-2 bg-white dark:bg-neutral-900 shadow-sm cursor-pointer transition-all ${selectedNode === "output-node" ? "border-pink-500 ring-4 ring-pink-500/20" : "border-neutral-200 dark:border-neutral-700 hover:border-pink-400"}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400 flex items-center justify-center"><MessageSquare className="w-5 h-5" /></div>
                  <div>
                    <p className="text-sm font-bold text-neutral-900 dark:text-white">Recruiter Chatbot</p>
                    <p className="text-xs text-neutral-500">Interactive UI</p>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-neutral-400" />
              </div>
            </div>

          </div>
        </div>

        {/* Right Sidebar: Configuration */}
        <div className="lg:col-span-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-5 flex flex-col overflow-y-auto custom-scrollbar shadow-sm dark:shadow-none">
          <h3 className="font-semibold text-neutral-900 dark:text-white mb-6 flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-purple-500" /> Configuration
          </h3>

          {selectedNode === "ai-node" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Block Name</label>
                <input type="text" defaultValue="Career Gap Analyzer" className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50" />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">System Prompt (Plain English)</label>
                <textarea 
                  rows={6} 
                  defaultValue="Compare my resume and GitHub repos against entry-level React developer roles. Highlight missing skills. Always cite which project or resume section you are referencing."
                  className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none" 
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Model Selection</label>
                <select className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50">
                  <option>Gemini 1.5 Flash (Fast)</option>
                  <option>Gemini 1.5 Pro (Advanced)</option>
                </select>
              </div>
            </motion.div>
          )}

          {selectedNode === "data-1" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Source Name</label>
                <input type="text" defaultValue="Resume" className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50" />
              </div>
              <div className="p-4 border border-neutral-200 dark:border-neutral-800 rounded-xl bg-neutral-50 dark:bg-neutral-950 flex items-center justify-between">
                <span className="text-sm font-medium text-neutral-900 dark:text-white">johndoe_resume.pdf</span>
                <button className="text-xs text-red-500 font-medium">Replace</button>
              </div>
            </motion.div>
          )}

          {selectedNode === "data-2" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Connection</label>
                <div className="p-3 border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50 dark:bg-emerald-500/10 rounded-xl flex items-center gap-2 text-emerald-700 dark:text-emerald-400 text-sm font-medium">
                  <CheckCircle2 className="w-4 h-4" /> Authenticated as @johndoe
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Included Repositories</label>
                <select className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50">
                  <option>All Public Repos</option>
                  <option>Selected Repos Only...</option>
                </select>
              </div>
            </motion.div>
          )}

          {selectedNode === "output-node" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Interface Type</label>
                <select className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50">
                  <option>Conversational Chatbot</option>
                  <option>Static Dashboard</option>
                  <option>API Endpoint</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Welcome Message</label>
                <textarea 
                  rows={3} 
                  defaultValue="Hi! I'm John's AI assistant. Ask me anything about his experience, projects, or skills."
                  className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none" 
                />
              </div>
            </motion.div>
          )}

        </div>
      </div>
    </motion.div>
  );
}
