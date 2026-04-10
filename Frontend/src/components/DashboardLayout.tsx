import { Link, Outlet, useLocation } from "react-router-dom";
import { FileText, Github, Calendar, LayoutDashboard, Settings, LogOut, Blocks } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";

export default function DashboardLayout() {
  const location = useLocation();

  const navItems = [
    { path: "/home", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/builder", icon: Blocks, label: "App Studio" },
    { path: "/resume", icon: FileText, label: "Documents" },
    { path: "/github", icon: Github, label: "Repo Analyzer" },
    { path: "/events", icon: Calendar, label: "Events" },
  ];

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 font-sans flex transition-colors duration-300">
      {/* Sidebar */}
      <aside className="w-64 border-r border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900/30 flex flex-col transition-colors duration-300 hidden md:flex">
        <div className="p-6">
          <Link to="/" className="text-2xl font-bold tracking-tighter text-purple-600 dark:text-purple-400 mb-10 block">
            UpLink
          </Link>
          
          <nav className="space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link 
                  key={item.path}
                  to={item.path} 
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${
                    isActive 
                      ? "bg-purple-100 dark:bg-purple-500/10 text-purple-700 dark:text-purple-400" 
                      : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800/50"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        
        <div className="mt-auto p-6 space-y-2">
          <Link 
            to="/settings" 
            className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${
              location.pathname === "/settings"
                ? "bg-purple-100 dark:bg-purple-500/10 text-purple-700 dark:text-purple-400"
                : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-neutral-800/50"
            }`}
          >
            <Settings className="w-5 h-5" />
            Settings
          </Link>
          <Link to="/" className="flex items-center gap-3 px-4 py-3 text-neutral-600 dark:text-neutral-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-xl font-medium transition-colors">
            <LogOut className="w-5 h-5" />
            Sign Out
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900/30">
          <Link to="/" className="text-xl font-bold tracking-tighter text-purple-600 dark:text-purple-400">
            UpLink
          </Link>
          <ThemeToggle />
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-6xl mx-auto">
            <div className="hidden md:flex justify-end mb-8">
              <ThemeToggle />
            </div>
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
