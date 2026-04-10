import { motion } from "motion/react";
import { FileText, Github, Calendar } from "lucide-react";
import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <>
      <header className="mb-10">
        <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">Welcome back, Student</h1>
        <p className="text-neutral-600 dark:text-neutral-400">Here's what's happening with your projects today.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions / Modules */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="col-span-1 lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {/* Resume Module */}
          <Link to="/resume" className="group block bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 hover:border-purple-500/50 dark:hover:border-purple-500/50 transition-all shadow-sm hover:shadow-md dark:shadow-none">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-white">Document Upload</h3>
            <p className="text-neutral-600 dark:text-neutral-400 text-sm">Upload resumes and documents for analysis and tracking.</p>
          </Link>

          {/* GitHub Module */}
          <Link to="/github" className="group block bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 hover:border-purple-500/50 dark:hover:border-purple-500/50 transition-all shadow-sm hover:shadow-md dark:shadow-none">
            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Github className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-white">Repo Analyzer</h3>
            <p className="text-neutral-600 dark:text-neutral-400 text-sm">Paste a GitHub link, prompt for insights, and visualize your code.</p>
          </Link>

          {/* Events Module */}
          <Link to="/events" className="group block bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 hover:border-purple-500/50 dark:hover:border-purple-500/50 transition-all md:col-span-2 shadow-sm hover:shadow-md dark:shadow-none">
            <div className="w-12 h-12 bg-amber-100 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Calendar className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-white">Upcoming Events</h3>
            <p className="text-neutral-600 dark:text-neutral-400 text-sm">Don't miss momentum. Track hackathons and submission windows.</p>
          </Link>
        </motion.div>

        {/* Activity Feed / Sidebar */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="col-span-1 bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none"
        >
          <h3 className="text-lg font-semibold mb-6 text-neutral-900 dark:text-white">Recent Activity</h3>
          <div className="space-y-6">
            <div className="flex gap-4">
              <div className="w-2 h-2 mt-2 rounded-full bg-emerald-500 dark:bg-emerald-400 shrink-0" />
              <div>
                <p className="text-sm text-neutral-800 dark:text-neutral-200">Analyzed <span className="font-medium text-emerald-600 dark:text-emerald-400">uplink-core</span> repository</p>
                <p className="text-xs text-neutral-500 mt-1">2 hours ago</p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-2 h-2 mt-2 rounded-full bg-blue-500 dark:bg-blue-400 shrink-0" />
              <div>
                <p className="text-sm text-neutral-800 dark:text-neutral-200">Uploaded new resume draft</p>
                <p className="text-xs text-neutral-500 mt-1">Yesterday</p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-2 h-2 mt-2 rounded-full bg-amber-500 dark:bg-amber-400 shrink-0" />
              <div>
                <p className="text-sm text-neutral-800 dark:text-neutral-200">Registered for <span className="font-medium text-amber-600 dark:text-amber-400">Global Hackathon 2026</span></p>
                <p className="text-xs text-neutral-500 mt-1">3 days ago</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </>
  );
}
