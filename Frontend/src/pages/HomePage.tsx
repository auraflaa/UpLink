import { useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  FileText,
  Github,
  Calendar,
  TrendingUp,
  Activity,
  CheckCircle2,
  ChevronRight,
  Clock,
} from "lucide-react";
import { Link } from "react-router-dom";
import { loadUiBootstrap, type HomeStat, type UiBootstrapPayload } from "@/src/lib/mainServer";
export default function HomePage() {
  const [homeData, setHomeData] = useState<UiBootstrapPayload["home"] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const hydrate = async () => {
      try {
        const response = await loadUiBootstrap({
          uiSurface: "home.dashboard",
        });
        if (!active) return;
        if (response.data?.home) {
          setHomeData(response.data.home);
        }
      } catch (error) {
        console.error("Failed to load home dashboard bootstrap:", error);
      } finally {
        if (active) setIsLoading(false);
      }
    };

    void hydrate();
    return () => {
      active = false;
    };
  }, []);

  if (isLoading && !homeData) {
    return (
      <div className="flex justify-center items-center h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900 dark:border-white"></div>
      </div>
    );
  }

  const fallbackHome = {
    welcome: { title: "Welcome back", subtitle: "Here is a live snapshot of your workspace activity." },
    stats: [
      { label: "Workspaces", value: "—", trend: "—", icon_key: "github" },
      { label: "Documents", value: "—", trend: "—", icon_key: "file_text" },
      { label: "Events", value: "—", trend: "—", icon_key: "calendar" },
      { label: "Activity", value: "—", trend: "—", icon_key: "trending_up" },
    ],
    activity: [
      { day: "Mon", value: 0, count: 0 }, { day: "Tue", value: 0, count: 0 },
      { day: "Wed", value: 0, count: 0 }, { day: "Thu", value: 0, count: 0 },
      { day: "Fri", value: 0, count: 0 }, { day: "Sat", value: 0, count: 0 },
      { day: "Sun", value: 0, count: 0 },
    ],
    recent_projects: [],
    modules: {
      documents: { title: "Document Analysis", description: "Upload resumes and get AI-driven improvements for your profile." },
      analyzer: { title: "Repo Analyzer", description: "Review codebases, get architectural insights, and optimize logic." },
      events: { title: "Upcoming Events", description: "Do not miss out on hackathons and work opportunities." },
    },
    empty_state: { title: "No recent workspaces yet", body: "Connect a GitHub repo or Jira board to begin.", button_label: "Refresh" },
  };

  const data = homeData || fallbackHome;

  const statIconMap: Record<string, any> = {
    trending_up: TrendingUp,
    github: Github,
    file_text: FileText,
    calendar: Calendar,
  };

  const stats = data.stats;
  const activityData = data.activity;
  const recentProjects = data.recent_projects;

  return (
    <div className="pb-10">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-3 text-neutral-900 dark:text-white bg-clip-text text-transparent bg-gradient-to-r from-neutral-600 to-neutral-500 dark:from-neutral-400 dark:to-neutral-400">
          {data.welcome.title}
        </h1>
        <p className="text-neutral-600 dark:text-neutral-400 text-lg">{data.welcome.subtitle}</p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat, i) => {
          const StatIcon = statIconMap[stat.icon_key as keyof typeof statIconMap] || Activity;
          return (
            <motion.div
              key={`${stat.label}-${i}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ scale: 1.02, y: -4 }}
              transition={{ duration: 0.3, delay: i * 0.1 }}
              className="group bg-white dark:bg-neutral-900/60 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-5 hover:border-neutral-500/50 dark:hover:border-neutral-500/50 transition-all shadow-sm hover:shadow-xl hover:shadow-neutral-500/10 cursor-pointer relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-neutral-500/10 rounded-full blur-2xl -mr-10 -mt-10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="flex justify-between items-start mb-3 relative z-10">
                <div className="p-2 rounded-xl bg-neutral-100 dark:bg-neutral-800 text-neutral-500 group-hover:text-neutral-900 dark:group-hover:text-white group-hover:scale-110 transition-all duration-300">
                  <StatIcon className="w-5 h-5" />
                </div>
                <span className="text-xs font-medium px-2 py-1 bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 rounded-lg group-hover:bg-neutral-200 dark:group-hover:bg-neutral-700 group-hover:text-neutral-900 dark:group-hover:text-white transition-all">
                  {stat.trend}
                </span>
              </div>
              <h4 className="text-3xl font-bold text-neutral-900 dark:text-white mb-1 relative z-10">{stat.value}</h4>
              <p className="text-sm text-neutral-500 dark:text-neutral-400 relative z-10 group-hover:text-neutral-700 dark:group-hover:text-neutral-300 transition-colors">
                {stat.label}
              </p>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="col-span-1 lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.2 }}>
            <Link
              to="/resume"
              className="group h-full flex flex-col justify-between block bg-gradient-to-br from-white to-neutral-50/30 dark:from-neutral-900/80 dark:to-neutral-900/10 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 hover:border-neutral-500/50 dark:hover:border-neutral-500/50 transition-all shadow-sm relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-neutral-500/5 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
              <div>
                <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-white">
                  {data.modules?.documents?.title || "Document Analysis"}
                </h3>
                <p className="text-neutral-600 dark:text-neutral-400 text-sm mb-6">
                  {data.modules?.documents?.description || "Upload resumes and get AI-driven improvements for your profile."}
                </p>
              </div>
              <div className="flex items-center text-sm font-medium text-neutral-600 dark:text-neutral-400 group-hover:translate-x-1 transition-transform">
                Go to Documents <ChevronRight className="w-4 h-4 ml-1" />
              </div>
            </Link>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4, delay: 0.3 }}>
            <Link
              to="/github"
              className="group h-full flex flex-col justify-between block bg-gradient-to-br from-white to-neutral-50/30 dark:from-neutral-900/80 dark:to-neutral-900/10 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 hover:border-neutral-500/50 dark:hover:border-neutral-500/50 transition-all shadow-sm relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-neutral-500/5 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
              <div>
                <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Github className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-white">
                  {data.modules?.analyzer?.title || "Repo Analyzer"}
                </h3>
                <p className="text-neutral-600 dark:text-neutral-400 text-sm mb-6">
                  {data.modules?.analyzer?.description || "Review codebases, get architectural insights, and optimize logic."}
                </p>
              </div>
              <div className="flex items-center text-sm font-medium text-neutral-600 dark:text-neutral-400 group-hover:translate-x-1 transition-transform">
                Analyze Repo <ChevronRight className="w-4 h-4 ml-1" />
              </div>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
            className="md:col-span-2"
          >
            <Link
              to="/events"
              className="group h-full flex flex-col sm:flex-row justify-between items-start sm:items-center bg-gradient-to-r from-neutral-900 to-neutral-800 dark:from-neutral-800 dark:to-neutral-900 border border-neutral-800 rounded-3xl p-6 md:p-8 hover:border-neutral-500/50 transition-all shadow-md relative overflow-hidden"
            >
              <div className="absolute right-0 bottom-0 w-48 h-48 bg-neutral-500/10 rounded-full blur-3xl transition-transform group-hover:scale-150" />
              <div className="z-10 flex gap-4 sm:gap-6 items-center mb-4 sm:mb-0">
                <div className="w-14 h-14 bg-neutral-500/20 text-neutral-400 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform shrink-0">
                  <Calendar className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white mb-1">
                    {data.modules?.events?.title || "Upcoming Events"}
                  </h3>
                  <p className="text-neutral-400 text-sm">
                    {data.modules?.events?.description || "Do not miss out on hackathons and work opportunities."}
                  </p>
                </div>
              </div>
              <div className="z-10 bg-white text-neutral-900 dark:bg-black dark:text-white px-5 py-3 rounded-full text-sm font-bold flex items-center group-hover:bg-neutral-400 group-hover:text-black transition-colors">
                View Calendar <ChevronRight className="w-4 h-4 ml-1" />
              </div>
            </Link>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="col-span-1 flex flex-col gap-6"
        >
          <div className="bg-white dark:bg-neutral-900/60 backdrop-blur-xl border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm hover:border-neutral-500/30 transition-colors group relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-neutral-500/5 rounded-full blur-3xl -mr-10 -mt-10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="flex justify-between items-center mb-6 relative z-10">
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-white flex items-center gap-2 group-hover:text-neutral-500 transition-colors">
                <Activity className="w-5 h-5 text-neutral-500" />
                Activity Momentum
              </h3>
              <span className="text-xs font-medium text-neutral-500 bg-neutral-100 dark:bg-neutral-800 px-2 py-1 rounded-md">This Week</span>
            </div>

            <div className="flex items-end justify-between h-32 gap-2 mt-4 relative z-10">
              {activityData.map((point, i) => (
                <div key={`${point.day}-${i}`} className="w-full flex justify-center group/bar relative cursor-pointer">
                  <div className="absolute -top-8 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 text-xs py-1 px-2 rounded opacity-0 group-hover/bar:opacity-100 transition-opacity -translate-y-2 group-hover/bar:-translate-y-4 pointer-events-none z-10 font-medium">
                    {point.count} item(s)
                  </div>
                  <div
                    className="w-full max-w-[24px] bg-neutral-100 dark:bg-neutral-800 rounded-t-lg relative overflow-hidden transition-all duration-300 group-hover/bar:bg-neutral-500/20 group-hover/bar:-translate-y-1"
                    style={{ height: "100%" }}
                  >
                    <div
                      className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-neutral-600 to-neutral-400 rounded-t-sm group-hover/bar:from-neutral-500 group-hover/bar:to-neutral-300 transition-colors duration-300"
                      style={{ height: `${point.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-between text-xs text-neutral-500 mt-2 px-1 relative z-10">
              {activityData.map((point) => (
                <span key={point.day}>{point.day}</span>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.5 }}>
        <div className="flex justify-between items-end mb-6">
          <div>
            <h2 className="text-2xl font-bold text-neutral-900 dark:text-white mb-1">Recent Projects</h2>
            <p className="text-neutral-500 dark:text-neutral-400 text-sm">Pick up right where you left off</p>
          </div>
          <button className="text-sm font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors">
            {data.empty_state.button_label}
          </button>
        </div>

        {recentProjects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recentProjects.map((project, i) => (
              <motion.div
                key={`${project.name}-${i}`}
                whileHover={{ y: -4, scale: 1.01 }}
                className="bg-white dark:bg-neutral-900/40 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-5 hover:border-neutral-500/40 dark:hover:border-neutral-500/40 transition-all shadow-sm hover:shadow-xl hover:shadow-neutral-500/5 group cursor-pointer relative overflow-hidden"
              >
                <div className="absolute left-0 top-0 w-1 h-full bg-neutral-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="flex justify-between items-start mb-4 relative z-10">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-neutral-500 group-hover:bg-neutral-900 dark:group-hover:bg-white group-hover:scale-125 transition-all duration-300" />
                    <h4 className="font-semibold text-neutral-900 dark:text-white group-hover:text-black dark:group-hover:text-white transition-colors">
                      {project.name}
                    </h4>
                  </div>
                </div>
                <div className="flex flex-col gap-2 relative z-10">
                  <div className="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-400">
                    <CheckCircle2 className="w-3.5 h-3.5 group-hover:text-neutral-900 dark:group-hover:text-neutral-300 transition-colors" />
                    <span className="group-hover:text-neutral-900 dark:group-hover:text-neutral-300 transition-colors">
                      {project.status}
                    </span>
                    <span className="w-1 h-1 bg-neutral-300 dark:bg-neutral-700 rounded-full mx-1" />
                    <span className="group-hover:text-neutral-900 dark:group-hover:text-neutral-300 transition-colors">
                      {project.tech}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-neutral-500">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{project.time}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="bg-white dark:bg-neutral-900/40 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">{data.empty_state.title}</h3>
            <p className="text-neutral-500 dark:text-neutral-400 text-sm">{data.empty_state.body}</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
