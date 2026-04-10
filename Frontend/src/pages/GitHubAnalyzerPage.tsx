import { useState } from 'react';
import { ArrowLeft, GitBranch, Terminal, Play, LayoutGrid } from 'lucide-react';
import { Link } from 'react-router-dom';

const GitHubAnalyzerPage = () => {
  const [url, setUrl] = useState('');
  const [prompt, setPrompt] = useState('');
  const [vizType, setVizType] = useState('Dependency Node Graph');
  const [analyzing, setAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    setAnalyzing(true);
    // Simulate API delay
    setTimeout(() => {
      setAnalyzing(false);
      setShowResults(true);
    }, 2000);
  };

  return (
    <div className="flex flex-col h-screen bg-black overflow-y-auto">
      {/* Header */}
      <header className="h-16 border-b border-white/10 flex items-center px-6 bg-black/40 backdrop-blur-md sticky top-0 z-20">
        <Link to="/home" className="flex items-center gap-2 text-muted hover:text-white transition-colors mr-6">
          <ArrowLeft size={20} />
          <span>Dashboard</span>
        </Link>
        <div className="h-6 w-px bg-white/10 mr-6"></div>
        <div className="flex items-center gap-2">
          <GitBranch className="text-primary" size={20} />
          <h1 className="font-semibold tracking-wide">GitHub Repo Analyzer</h1>
        </div>
      </header>

      <main className="flex-1 p-8 max-w-6xl w-full mx-auto animate-fade-in">
        
        {/* Input Configuration Area */}
        <div className="glass-panel p-8 mb-8">
          <form onSubmit={handleAnalyze} className="flex flex-col gap-6">
            
            {/* Link Paste Area */}
            <div>
              <label className="text-sm text-muted font-medium ml-1 flex items-center gap-2 mb-2">
                <GitBranch size={16} /> Repository Link Paste Area
              </label>
              <input 
                type="url" 
                required
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all font-mono text-sm"
                placeholder="https://github.com/username/repository"
                value={url}
                onChange={e => setUrl(e.target.value)}
              />
            </div>

            {/* Prompt Area */}
            <div>
              <label className="text-sm text-muted font-medium ml-1 flex items-center gap-2 mb-2">
                <Terminal size={16} /> Analysis Prompt
              </label>
              <textarea 
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all min-h-[120px] resize-y"
                placeholder="What specific insights are you looking for? (e.g. 'Identify unoptimized React re-renders', 'Map the authentication flow', or leave blank for a general architecture overview)"
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
              />
            </div>

            {/* Visualization Dropdown & Submit */}
            <div className="flex flex-col md:flex-row items-end gap-4 mt-2">
              <div className="flex-1 w-full relative">
                <label className="text-sm text-muted font-medium ml-1 flex items-center gap-2 mb-2">
                  <LayoutGrid size={16} /> Viz Choosing Dropbox
                </label>
                <select 
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white appearance-none focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                  value={vizType}
                  onChange={e => setVizType(e.target.value)}
                >
                  <option>Dependency Node Graph</option>
                  <option>Component Hierarchy Tree</option>
                  <option>PR Velocity Timeline</option>
                  <option>Knowledge Gap Matrix</option>
                </select>
                <div className="absolute right-4 top-10 pointer-events-none text-muted">▼</div>
              </div>
              
              <button 
                type="submit" 
                disabled={analyzing}
                className="w-full md:w-auto px-8 py-3 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold flex items-center justify-center gap-2 transition-all h-[50px] shadow-lg shadow-primary/20"
              >
                {analyzing ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <>
                    <Play size={18} fill="currentColor" /> Run Analysis
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results Area (Simulated) */}
        {showResults && (
          <div className="glass-panel p-8 animate-fade-in border-primary/30">
            <h2 className="heading-md mb-6 flex items-center gap-3">
              <div className="w-2 h-6 bg-secondary rounded-full"></div>
              Semantic Intelligence Output
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 relative bg-black/60 rounded-xl border border-white/5 h-[400px] flex items-center justify-center overflow-hidden">
                {/* Simulated Graph Background */}
                <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#4b5563 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
                <div className="text-center relative z-10">
                  <div className="text-secondary font-mono text-sm mb-2">{vizType} rendered</div>
                  <p className="text-muted">Interactive vector visualization will render here.</p>
                </div>
              </div>
              
              <div className="flex flex-col gap-4">
                <div className="bg-black/40 border border-white/5 rounded-xl p-5 border-l-4 border-l-primary">
                  <h4 className="font-semibold text-white mb-2 text-sm uppercase tracking-wider">Key Finding</h4>
                  <p className="text-sm text-gray-400">The `AuthService` module has a high cyclomatic complexity and is tightly coupled with local storage. Refactoring recommended.</p>
                </div>
                
                <div className="bg-black/40 border border-white/5 rounded-xl p-5 border-l-4 border-l-secondary">
                  <h4 className="font-semibold text-white mb-2 text-sm uppercase tracking-wider">Next Action Generation</h4>
                  <p className="text-sm text-gray-400">Scheduled a "Review Auth Pattern" reminder for your next deep-work block in Telegram.</p>
                  <button className="mt-3 text-xs font-semibold text-secondary hover:text-white transition-colors uppercase tracking-wider">Execute Action →</button>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

export default GitHubAnalyzerPage;
