import { motion } from "motion/react";
import { FileText, Github, Calendar, TrendingUp, Activity, CheckCircle2, ChevronRight, Clock } from "lucide-react";
import { Link } from "react-router-dom";

export default function HomePage() {
  // Mock data for graphs and stats
  const stats = [
    { label: "Growth Score", value: "842", trend: "+12%", icon: TrendingUp, color: "text-purple-500" },
    { label: "Analyzed Repos", value: "14", trend: "+3 this week", icon: Github, color: "text-emerald-500" },
    { label: "Docs Processed", value: "5", trend: "Latest: Resume_v2", icon: FileText, color: "text-blue-500" },
    { label: "Upcoming Deadlines", value: "2", trend: "Next: 3 days", icon: Calendar, color: "text-amber-500" },
  ];

  const recentProjects = [
    { name: "uplink-core", tech: "React, Node", status: "Completed", time: "2 hours ago", color: "bg-emerald-500" },
    { name: "dravix-habit-tracker", tech: "Vue, Firebase", status: "In Progress", time: "Yesterday", color: "bg-blue-500" },
    { name: "portfolio-v3", tech: "Next.js", status: "Needs Review", time: "3 days ago", color: "bg-amber-500" }
  ];

  // Week activity mock (7 items, varying height)
  const activityData = [40, 20, 50, 80, 30, 90, 60];

  return (
    <div className="pb-10">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-3 text-neutral-900 dark:text-white bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-blue-500 dark:from-purple-400 dark:to-blue-400">Welcome back, Student</h1>
        <p className="text-neutral-600 dark:text-neutral-400 text-lg">Here's a snapshot of your progress and active projects today.</p>
      </header>

      {/* Top Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ duration: 0.3, delay: i * 0.1 }}
            className="group bg-white dark:bg-neutral-900/60 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-5 hover:border-purple-500/50 dark:hover:border-purple-500/50 transition-all shadow-sm hover:shadow-xl hover:shadow-purple-500/10 cursor-pointer relative overflow-hidden"
          >
            <div className={`absolute top-0 right-0 w-24 h-24 ${stat.color.replace('text-', 'bg-')}/10 rounded-full blur-2xl -mr-10 -mt-10 opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
            <div className="flex justify-between items-start mb-3 relative z-10">
              <div className={`p-2 rounded-xl bg-neutral-100 dark:bg-neutral-800 ${stat.color} group-hover:scale-110 transition-transform duration-300`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <span className={`text-xs font-medium px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 rounded-lg group-hover:bg-opacity-20 transition-all ${stat.color.replace('text-', 'text-[')} group-hover:${stat.color} dark:group-hover:${stat.color}`}>
                {stat.trend}
              </span>
            </div>
            <h4 className="text-3xl font-bold text-neutral-900 dark:text-white mb-1 relative z-10">{stat.value}</h4>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 relative z-10 group-hover:text-neutral-700 dark:group-hover:text-neutral-300 transition-colors">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Quick Actions / Modules */}
        <div className="col-span-1 lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Resume Module */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.2 }}>
            <Link to="/resume" className="group h-full flex flex-col justify-between block bg-gradient-to-br from-white to-blue-50/30 dark:from-neutral-900/80 dark:to-blue-900/10 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 hover:border-blue-500/50 dark:hover:border-blue-500/50 transition-all shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
              <div>
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-white">Document Analysis</h3>
                <p className="text-neutral-600 dark:text-neutral-400 text-sm mb-6">Upload resumes and get AI-driven improvements for your profile.</p>
              </div>
              <div className="flex items-center text-sm font-medium text-blue-600 dark:text-blue-400 group-hover:translate-x-1 transition-transform">
                Go to Documents <ChevronRight className="w-4 h-4 ml-1" />
              </div>
            </Link>
          </motion.div>

          {/* GitHub Module */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.3 }}>
            <Link to="/github" className="group h-full flex flex-col justify-between block bg-gradient-to-br from-white to-emerald-50/30 dark:from-neutral-900/80 dark:to-emerald-900/10 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition-all shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
              <div>
                <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Github className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-white">Repo Analyzer</h3>
                <p className="text-neutral-600 dark:text-neutral-400 text-sm mb-6">Review codebases, get architectural insights, and optimize logic.</p>
              </div>
              <div className="flex items-center text-sm font-medium text-emerald-600 dark:text-emerald-400 group-hover:translate-x-1 transition-transform">
                Analyze Repo <ChevronRight className="w-4 h-4 ml-1" />
              </div>
            </Link>
          </motion.div>

          {/* Events Module */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.4 }} className="md:col-span-2">
            <Link to="/events" className="group h-full flex flex-col sm:flex-row justify-between items-start sm:items-center bg-gradient-to-r from-neutral-900 to-neutral-800 dark:from-neutral-800 dark:to-neutral-900 border border-neutral-800 rounded-3xl p-6 md:p-8 hover:border-amber-500/50 transition-all shadow-md relative overflow-hidden">
              <div className="absolute right-0 bottom-0 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl transition-transform group-hover:scale-150" />
              <div className="z-10 flex gap-4 sm:gap-6 items-center mb-4 sm:mb-0">
                <div className="w-14 h-14 bg-amber-500/20 text-amber-400 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform shrink-0">
                  <Calendar className="w-7 h-7" />
                </div>
                <div>
                   <h3 className="text-2xl font-bold text-white mb-1">Upcoming Events</h3>
                   <p className="text-neutral-400 text-sm">Don't miss out on Hackathons & Work Opportunities.</p>
                </div>
              </div>
              <div className="z-10 bg-white text-neutral-900 dark:bg-black dark:text-white px-5 py-3 rounded-full text-sm font-bold flex items-center group-hover:bg-amber-400 group-hover:text-black transition-colors">
                View Calendar <ChevronRight className="w-4 h-4 ml-1" />
              </div>
            </Link>
          </motion.div>
        </div>

        {/* Activity Feed & Heatmap Sidebar */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="col-span-1 flex flex-col gap-6"
        >
          {/* Heatmap Card */}
          <div className="bg-white dark:bg-neutral-900/60 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm hover:border-purple-500/30 transition-colors group relative overflow-hidden">
             <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-3xl -mr-10 -mt-10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="flex justify-between items-center mb-6 relative z-10">
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-white flex items-center gap-2 group-hover:text-purple-500 transition-colors">
                <Activity className="w-5 h-5 text-purple-500" />
                Activity Momentum
              </h3>
              <span className="text-xs font-medium text-neutral-500 bg-neutral-100 dark:bg-neutral-800 px-2 py-1 rounded-md">This Week</span>
            </div>
            
            <div className="flex items-end justify-between h-32 gap-2 mt-4 relative z-10">
              {activityData.map((height, i) => (
                <div key={i} className="w-full flex justify-center group/bar relative cursor-pointer">
                  <div className="absolute -top-8 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 text-xs py-1 px-2 rounded opacity-0 group-hover/bar:opacity-100 transition-opacity -translate-y-2 group-hover/bar:-translate-y-4 pointer-events-none z-10 font-medium">
                    {height}%
                  </div>
                  <div 
                    className="w-full max-w-[24px] bg-neutral-100 dark:bg-neutral-800 rounded-t-lg relative overflow-hidden transition-all duration-300 group-hover/bar:bg-purple-500/20 group-hover/bar:-translate-y-1"
                    style={{ height: "100%" }}
                  >
                    <div 
                      className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-purple-600 to-purple-400 rounded-t-sm group-hover/bar:from-purple-500 group-hover/bar:to-purple-300 transition-colors duration-300"
                      style={{ height: `${height}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-between text-xs text-neutral-500 mt-2 px-1 relative z-10">
              <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Recent Projects Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.5 }}
      >
        <div className="flex justify-between items-end mb-6">
          <div>
            <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-1">Recent Projects</h2>
            <p className="text-neutral-500 dark:text-neutral-400 text-sm">Pick up right where you left off</p>
          </div>
          <button className="text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors">
            View All
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recentProjects.map((project, i) => (
            <motion.div 
              key={i} 
              whileHover={{ y: -4, scale: 1.01 }}
              className="bg-white dark:bg-neutral-900/40 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 hover:border-purple-500/40 dark:hover:border-purple-500/40 transition-all shadow-sm hover:shadow-xl hover:shadow-purple-500/5 group cursor-pointer relative overflow-hidden"
            >
              <div className={`absolute left-0 top-0 w-1 h-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${project.color.replace('text-', 'bg-')}`} />
              <div className="flex justify-between items-start mb-4 relative z-10">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${project.color.replace('text-', 'bg-')} group-hover:scale-125 transition-transform duration-300`} />
                  <h4 className="font-semibold text-neutral-900 dark:text-white group-hover:text-purple-500 transition-colors">{project.name}</h4>
                </div>
              </div>
              <div className="flex flex-col gap-2 relative z-10">
                <div className="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-400">
                  <CheckCircle2 className="w-3.5 h-3.5 group-hover:text-neutral-900 dark:group-hover:text-neutral-300 transition-colors" />
                  <span className="group-hover:text-neutral-900 dark:group-hover:text-neutral-300 transition-colors">{project.status}</span>
                  <span className="w-1 h-1 bg-neutral-300 dark:bg-neutral-700 rounded-full mx-1"></span>
                  <span className="group-hover:text-neutral-900 dark:group-hover:text-neutral-300 transition-colors">{project.tech}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-neutral-500">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{project.time}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
