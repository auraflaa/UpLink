import { useState, useMemo } from "react";
import { motion } from "motion/react";
import { Github, Search, BarChart3, Network, PieChart, ArrowRight, Sparkles, Clock, FolderGit2 } from "lucide-react";

export default function GithubPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [prompt, setPrompt] = useState("");
  const [vizType, setVizType] = useState("network");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResult, setShowResult] = useState(false);

  // Filters state
  const [languageFilter, setLanguageFilter] = useState("All");
  const [dateFilter, setDateFilter] = useState("All");

  // Mock Saved Repositories
  const savedRepos = useMemo(() => [
    { id: 1, name: "uplink-core", url: "https://github.com/student/uplink-core", language: "TypeScript", updated: "2026-04-08T10:00:00Z" },
    { id: 2, name: "ml-model-training", url: "https://github.com/student/ml-model", language: "Python", updated: "2026-04-05T14:30:00Z" },
    { id: 3, name: "react-portfolio", url: "https://github.com/student/react-portfolio", language: "TypeScript", updated: "2026-03-20T09:15:00Z" },
    { id: 4, name: "go-microservices", url: "https://github.com/student/go-microservices", language: "Go", updated: "2025-12-10T16:45:00Z" },
    { id: 5, name: "rust-cli-tool", url: "https://github.com/student/rust-cli", language: "Rust", updated: "2026-04-09T11:20:00Z" },
  ], []);

  // Filter Logic
  const filteredRepos = useMemo(() => {
    const now = new Date("2026-04-10T00:00:00Z").getTime(); // Using a fixed reference date for the mock
    return savedRepos.filter(repo => {
      if (languageFilter !== "All" && repo.language !== languageFilter) return false;
      
      if (dateFilter !== "All") {
        const repoDate = new Date(repo.updated).getTime();
        const diffDays = (now - repoDate) / (1000 * 3600 * 24);
        if (dateFilter === "Past week" && diffDays > 7) return false;
        if (dateFilter === "Past month" && diffDays > 30) return false;
        if (dateFilter === "Past year" && diffDays > 365) return false;
      }
      return true;
    });
  }, [savedRepos, languageFilter, dateFilter]);

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl) return;
    
    setIsAnalyzing(true);
    setShowResult(false);
    
    // Mock analysis delay
    setTimeout(() => {
      setIsAnalyzing(false);
      setShowResult(true);
    }, 2500);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="mb-10">
        <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">Repo Analyzer</h1>
        <p className="text-neutral-600 dark:text-neutral-400">Understand complex codebases instantly with AI-driven visual insights.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Input Form & Repo List */}
        <div className="lg:col-span-5 space-y-6">
          <form onSubmit={handleAnalyze} className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none">
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">GitHub Repository URL</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Github className="h-5 w-5 text-neutral-400" />
                </div>
                <input
                  type="url"
                  required
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repo"
                  className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl pl-11 pr-4 py-3 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all"
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">What do you want to know?</label>
              <textarea
                rows={3}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Show me the dependency graph, or explain the authentication flow..."
                className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-4 py-3 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all resize-none"
              />
            </div>

            <div className="mb-8">
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Visualization Type</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: "network", icon: Network, label: "Network" },
                  { id: "bar", icon: BarChart3, label: "Metrics" },
                  { id: "pie", icon: PieChart, label: "Composition" },
                ].map((type) => {
                  const Icon = type.icon;
                  return (
                    <button
                      key={type.id}
                      type="button"
                      onClick={() => setVizType(type.id)}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all ${
                        vizType === type.id
                          ? "border-purple-500 bg-purple-50 dark:bg-purple-500/10 text-purple-700 dark:text-purple-400"
                          : "border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-950 text-neutral-500 hover:border-neutral-300 dark:hover:border-neutral-700"
                      }`}
                    >
                      <Icon className="w-5 h-5 mb-1.5" />
                      <span className="text-xs font-medium">{type.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              type="submit"
              disabled={isAnalyzing || !repoUrl}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3.5 rounded-xl font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg shadow-purple-500/20"
            >
              {isAnalyzing ? (
                <><div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analyzing Repo...</>
              ) : (
                <><Search className="w-4 h-4" /> Generate Insights</>
              )}
            </button>
          </form>

          {/* Saved Repositories List with Filters */}
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none">
            <div className="flex items-center gap-2 mb-4">
              <FolderGit2 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">Saved Repositories</h3>
            </div>
            
            <div className="flex gap-3 mb-4">
              <select 
                value={languageFilter}
                onChange={(e) => setLanguageFilter(e.target.value)}
                className="flex-1 bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 appearance-none cursor-pointer"
              >
                <option value="All">All Languages</option>
                <option value="TypeScript">TypeScript</option>
                <option value="Python">Python</option>
                <option value="Go">Go</option>
                <option value="Rust">Rust</option>
              </select>
              
              <select 
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="flex-1 bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-3 py-2 text-sm text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 appearance-none cursor-pointer"
              >
                <option value="All">Any Time</option>
                <option value="Past week">Past Week</option>
                <option value="Past month">Past Month</option>
                <option value="Past year">Past Year</option>
              </select>
            </div>

            <div className="space-y-3 max-h-[280px] overflow-y-auto pr-2 custom-scrollbar">
              {filteredRepos.map(repo => (
                <div 
                  key={repo.id}
                  onClick={() => setRepoUrl(repo.url)}
                  className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 hover:border-purple-500/50 dark:hover:border-purple-500/50 cursor-pointer transition-colors group bg-neutral-50 dark:bg-neutral-950/50"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-medium text-neutral-900 dark:text-white group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors truncate pr-2">{repo.name}</span>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 shrink-0">{repo.language}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-neutral-500">
                    <Clock className="w-3.5 h-3.5" />
                    Updated {new Date(repo.updated).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                </div>
              ))}
              {filteredRepos.length === 0 && (
                <div className="text-center py-8 text-neutral-500 text-sm">
                  No repositories match your filters.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results / Visualization Area */}
        <div className="lg:col-span-7">
          <div className="h-full min-h-[500px] bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 flex flex-col shadow-sm dark:shadow-none relative overflow-hidden">
            
            {!showResult && !isAnalyzing && (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                <div className="w-16 h-16 bg-neutral-100 dark:bg-neutral-800 rounded-2xl flex items-center justify-center mb-4 text-neutral-400">
                  <Sparkles className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">Awaiting Repository</h3>
                <p className="text-neutral-500 dark:text-neutral-400 max-w-sm">
                  Paste a link and select a visualization type to uncover architectural patterns and code insights.
                </p>
              </div>
            )}

            {isAnalyzing && (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                <div className="relative w-24 h-24 mb-8">
                  <div className="absolute inset-0 border-4 border-purple-500/20 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-purple-500 rounded-full border-t-transparent animate-spin"></div>
                  <Github className="absolute inset-0 m-auto w-8 h-8 text-purple-500 animate-pulse" />
                </div>
                <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">Cloning & Analyzing...</h3>
                <p className="text-neutral-500 dark:text-neutral-400">Reading commit history and mapping dependencies.</p>
              </div>
            )}

            {showResult && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex-1 flex flex-col"
              >
                <div className="flex justify-between items-center mb-6 pb-4 border-b border-neutral-200 dark:border-neutral-800">
                  <div>
                    <h3 className="font-semibold text-neutral-900 dark:text-white text-lg">Architecture Graph</h3>
                    <p className="text-sm text-neutral-500">Based on {repoUrl.split('/').pop()}</p>
                  </div>
                  <button className="text-sm text-purple-600 dark:text-purple-400 font-medium hover:underline flex items-center gap-1">
                    Export <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
                
                {/* Mock Visualization Canvas */}
                <div className="flex-1 bg-neutral-50 dark:bg-neutral-950 rounded-2xl border border-neutral-200 dark:border-neutral-800 flex items-center justify-center relative overflow-hidden">
                  {/* Fake Network Graph Nodes */}
                  <div className="absolute top-1/4 left-1/4 w-12 h-12 bg-blue-500/20 border border-blue-500 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 text-xs font-bold z-10">Auth</div>
                  <div className="absolute top-1/2 left-1/2 w-16 h-16 bg-purple-500/20 border border-purple-500 rounded-full flex items-center justify-center text-purple-600 dark:text-purple-400 text-xs font-bold z-10 -translate-x-1/2 -translate-y-1/2">Core</div>
                  <div className="absolute bottom-1/4 right-1/4 w-14 h-14 bg-emerald-500/20 border border-emerald-500 rounded-full flex items-center justify-center text-emerald-600 dark:text-emerald-400 text-xs font-bold z-10">DB</div>
                  <div className="absolute top-1/4 right-1/3 w-10 h-10 bg-pink-500/20 border border-pink-500 rounded-full flex items-center justify-center text-pink-600 dark:text-pink-400 text-xs font-bold z-10">API</div>
                  
                  {/* Fake SVG Lines */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    <line x1="25%" y1="25%" x2="50%" y2="50%" stroke="currentColor" strokeWidth="2" className="text-neutral-300 dark:text-neutral-700" strokeDasharray="4" />
                    <line x1="50%" y1="50%" x2="75%" y2="75%" stroke="currentColor" strokeWidth="2" className="text-neutral-300 dark:text-neutral-700" />
                    <line x1="50%" y1="50%" x2="66%" y2="25%" stroke="currentColor" strokeWidth="2" className="text-neutral-300 dark:text-neutral-700" />
                  </svg>
                </div>

                <div className="mt-4 p-4 bg-purple-50 dark:bg-purple-500/10 border border-purple-100 dark:border-purple-500/20 rounded-xl">
                  <p className="text-sm text-purple-900 dark:text-purple-200 leading-relaxed">
                    <span className="font-semibold">AI Insight:</span> The core module is heavily coupled with the authentication service. Consider extracting the auth middleware to reduce dependency cycles and improve testability.
                  </p>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
