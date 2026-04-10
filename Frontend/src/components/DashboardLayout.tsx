import { Outlet, useLocation } from "react-router-dom";
import { ThemeToggle } from "./theme-toggle";
import PillNav from "./PillNav";
import UserAccount from "./UserAccount";

export default function DashboardLayout() {
  const location = useLocation();

  const navItems = [
    { href: "/home", label: "Dashboard" },
    { href: "/builder", label: "App Studio" },
    { href: "/resume", label: "Documents" },
    { href: "/github", label: "Repo Analyzer" },
    { href: "/events", label: "Events" },
  ];

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 font-sans flex flex-col transition-colors duration-300 relative">
      
      {/* Top Bar */}
      <div className="relative z-50 flex items-center justify-between w-full pt-6 md:pt-8 px-6 md:px-10 mb-12 pointer-events-none">
        {/* UpLink Logo - Top Left */}
        <a href="/" className="pointer-events-auto text-2xl font-bold tracking-tighter text-white hover:opacity-80 transition-opacity">
          UpLink
        </a>

        {/* Centered PillNav */}
        <div className="pointer-events-auto absolute left-1/2 -translate-x-1/2">
          <PillNav 
            logo="" 
            logoAlt="UpLink" 
            items={navItems} 
            activeHref={location.pathname} 
            baseColor="#09090b"
            pillColor="#27272a"
            pillTextColor="#a1a1aa"
            hoveredPillTextColor="#ffffff"
            className="!relative !top-0"
          />
        </div>

        {/* Actions - Top Right */}
        <div className="pointer-events-auto flex items-center gap-4">
          <ThemeToggle />
          <UserAccount />
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex flex-col w-full overflow-hidden">
        <div className="flex-1 overflow-y-auto px-4 md:px-8 pb-8">
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
