import { GitBranch, FileText, Upload, Brain, Activity, Settings, Bell, Search, ChartPie } from 'lucide-react';

const HomePage = () => {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-black/50 backdrop-blur-3xl">
      {/* Top Navigation */}
      <header className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-black/20 backdrop-blur-md z-10">
        <div className="flex items-center gap-2">
          <Brain className="text-secondary" size={24} />
          <span className="font-semibold tracking-wide">UpLink</span>
        </div>
        
        <div className="flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
            <input 
              type="text" 
              placeholder="Search your repos, notes, and tasks..." 
              className="w-full bg-white/5 border border-white/10 rounded-full pl-10 pr-4 py-1.5 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button className="text-muted hover:text-white transition-colors relative">
            <Bell size={20} />
            <span className="absolute top-0 right-0 w-2 h-2 bg-primary rounded-full"></span>
          </button>
          <button className="text-muted hover:text-white transition-colors">
            <Settings size={20} />
          </button>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary p-[2px]">
            <div className="w-full h-full bg-black rounded-full flex items-center justify-center">
              <span className="text-xs font-bold">JD</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 border-r border-white/10 bg-black/20 p-4 flex flex-col gap-2 z-10 hidden md:flex">
          <div className="text-xs text-muted font-semibold tracking-wider mb-2 ml-2">OVERVIEW</div>
          <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10 text-primary font-medium">
            <Activity size={18} /> Dashboard
          </a>
          <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-muted hover:bg-white/5 hover:text-white transition-colors">
            <ChartPie size={18} /> Analytics Context
          </a>
          
          <div className="text-xs text-muted font-semibold tracking-wider mt-6 mb-2 ml-2">DATA SOURCES</div>
          <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-muted hover:bg-white/5 hover:text-white transition-colors">
            <GitBranch size={18} /> GitHub Synced
          </a>
          <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-muted hover:bg-white/5 hover:text-white transition-colors">
            <FileText size={18} /> Resumes & Notes
          </a>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-8 relative">
          <div className="animate-fade-in">
            <div className="mb-10">
              <h1 className="heading-lg mb-2">Welcome back, John.</h1>
              <p className="text-muted text-lg">Your cognitive loop is active. Here's what needs attention today.</p>
            </div>
            
            {/* Core Modules Grid exactly as per the system architecture diagram */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
              
              {/* GitHub Repo Analyzer Path */}
              <div className="glass-panel p-8 text-left group cursor-pointer relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-bl-full -z-10 group-hover:bg-primary/20 transition-colors"></div>
                <div className="w-14 h-14 rounded-xl bg-[#24292e]/80 border border-white/10 flex items-center justify-center mb-6 shadow-lg shadow-black/50">
                  <GitBranch size={28} className="text-white" />
                </div>
                <h3 className="heading-md mb-3">GitHub Repo Analyzer</h3>
                <p className="text-muted mb-6">
                  Extract repo data, generate embeddings, and process them through the RAG brain to uncover specific insights and next actions.
                </p>
                <div className="flex items-center justify-between mt-auto">
                  <div className="text-sm font-medium text-primary">Ready to parse</div>
                  <button className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-sm font-medium transition-colors">
                    Analyze Link
                  </button>
                </div>
              </div>

              {/* Resume / Document Uploading Path */}
              <div className="glass-panel p-8 text-left group cursor-pointer relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-secondary/10 rounded-bl-full -z-10 group-hover:bg-secondary/20 transition-colors"></div>
                <div className="w-14 h-14 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center mb-6 shadow-lg shadow-black/50 text-blue-400">
                  <Upload size={28} />
                </div>
                <h3 className="heading-md mb-3">Document Processing</h3>
                <p className="text-muted mb-6">
                  Upload your resume or hackathon notes. Our User Profile Analyzer uses SpaCy & NLTK to build your personal knowledge vector.
                </p>
                <div className="flex items-center justify-between mt-auto">
                  <div className="text-sm font-medium text-secondary">PDF, DOCX, MD supported</div>
                  <button className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-sm font-medium transition-colors">
                    Upload File
                  </button>
                </div>
              </div>
              
            </div>

            {/* AI Action Execution Layer Section */}
            <div className="mt-8">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-3">
                <div className="w-2 h-6 bg-primary rounded-full"></div>
                Execution Layer Activity
              </h3>
              
              <div className="glass-panel overflow-hidden">
                <table className="w-full text-left">
                  <thead className="bg-white/5 border-b border-white/10">
                    <tr>
                      <th className="px-6 py-4 text-xs font-semibold text-muted tracking-wider uppercase">Source</th>
                      <th className="px-6 py-4 text-xs font-semibold text-muted tracking-wider uppercase">Insight / Action</th>
                      <th className="px-6 py-4 text-xs font-semibold text-muted tracking-wider uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    <tr className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-6 py-4 flex items-center gap-3">
                    <GitBranch size={16} className="text-muted" /> <span className="font-medium">React-Dash</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-300">
                        Incomplete 'Authentication' module detected. Scheduled Telegram reminder for Friday.
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-green-500/10 text-green-400 text-xs font-medium border border-green-500/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span> Synced to Calendar
                        </span>
                      </td>
                    </tr>
                    <tr className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-6 py-4 flex items-center gap-3">
                        <FileText size={16} className="text-muted" /> <span className="font-medium">Resume_2024.pdf</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-300">
                        Skill gap identified: You lack 'Next.js' experience for targeted internships. Added learning node.
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-yellow-500/10 text-yellow-500 text-xs font-medium border border-yellow-500/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span> Processing Vectors
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
};

export default HomePage;
