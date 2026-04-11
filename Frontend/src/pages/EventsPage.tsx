import { useState, useEffect, FormEvent } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Calendar, MapPin, Clock, ExternalLink, Trophy, Search, X, Loader2, CheckCircle2, Send } from "lucide-react";
import { auth } from "../lib/firebase";
import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { useToast } from "../components/ui/use-toast";

// Telegram bot link — replace with your actual bot username
const TELEGRAM_BOT_LINK = "https://t.me/UpLinkNotifyBot";

export default function EventsPage() {
  const { error: toastError, success: toastSuccess } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [events, setEvents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Integration flow state
  const [showIntegrationModal, setShowIntegrationModal] = useState(false);
  const [lastAddedEventTitle, setLastAddedEventTitle] = useState("");
  const [googleConnected, setGoogleConnected] = useState(false);
  const [telegramConnected, setTelegramConnected] = useState(false);
  const [isConnectingGoogle, setIsConnectingGoogle] = useState(false);

  // Form State
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState("Hackathon");
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [newLocation, setNewLocation] = useState("");

  const fetchEvents = async () => {
    try {
      const response = await fetch("/api/scheduler/jobs");
      if (response.ok) {
        const data = await response.json();
        const formattedEvents = data.jobs.map((job: any) => ({
          id: job.job_id,
          title: job.title,
          date: new Date(job.execute_at).toLocaleDateString(undefined, {
             year: 'numeric', month: 'short', day: 'numeric'
          }),
          time: new Date(job.execute_at).toLocaleTimeString(undefined, {
             hour: '2-digit', minute: '2-digit'
          }),
          location: job.metadata?.location || "Unknown",
          type: job.metadata?.type || "Event",
          status: job.status === "scheduled" ? "Upcoming" : job.status,
          color: job.metadata?.color || "purple",
        }));
        if (formattedEvents.length === 0) {
            setEvents(defaultEvents);
        } else {
            setEvents(formattedEvents);
        }
      } else {
        setEvents(defaultEvents);
      }
    } catch (err) {
      console.error("Backend offline, using fallback data.");
      setEvents(defaultEvents);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const defaultEvents = [
    {
      id: "1", title: "Global AI Hackathon 2026", date: "Oct 15, 2026", time: "09:00 AM", location: "Online", type: "Hackathon", status: "Upcoming", color: "purple"
    },
    {
      id: "2", title: "Web3 Builders Summit", date: "Nov 02, 2026", time: "10:00 AM", location: "San Francisco, CA", type: "Conference", status: "Registration Open", color: "blue"
    }
  ];

  const handleAddEvent = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Build ISO string manually from separate date/time inputs — no Date() parsing needed.
    // newDate = "YYYY-MM-DD", newTime = "HH:MM"
    // Get local offset string e.g. "+05:30"
    const offsetMins = -(new Date().getTimezoneOffset());
    const sign = offsetMins >= 0 ? '+' : '-';
    const absMin = Math.abs(offsetMins);
    const tzStr = `${sign}${String(Math.floor(absMin / 60)).padStart(2, '0')}:${String(absMin % 60).padStart(2, '0')}`;
    const execute_at = `${newDate}T${newTime}:00${tzStr}`;

    const payload = {
        title: newTitle,
        kind: "event",
        execute_at,
        metadata: {
            location: newLocation,
            type: newType,
            color: newType === "Hackathon" ? "purple" : "emerald"
        }
    };

    try {
        await fetch("/api/scheduler/schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        await fetchEvents();
        
        // Store the title and show integration modal
        setLastAddedEventTitle(newTitle);
        setShowAddModal(false);
        setShowIntegrationModal(true);
        
        // Reset form
        setNewTitle("");
        setNewDate("");
        setNewTime("");
        setNewLocation("");
    } catch (e) {
        console.error("Failed to schedule:", e);
        toastError("Failed to schedule event. Backend may be offline.");
    } finally {
        setIsSubmitting(false);
    }
  };

  const handleGoogleCalendarConnect = async () => {
    setIsConnectingGoogle(true);
    try {
      const provider = new GoogleAuthProvider();
      provider.addScope("https://www.googleapis.com/auth/calendar.events");
      await signInWithPopup(auth, provider);
      setGoogleConnected(true);
      toastSuccess("Google Calendar connected!");
    } catch (err) {
      console.error("Google Calendar auth failed:", err);
      toastError("Google Calendar connection failed. Please try again.");
    } finally {
      setIsConnectingGoogle(false);
    }
  };

  const handleCloseIntegration = () => {
    setShowIntegrationModal(false);
    setGoogleConnected(false);
    setTelegramConnected(false);
  };

  const filteredEvents = events.filter(event => 
    event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    event.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-[#f5f0e8]">Events & Momentum</h1>
          <p className="text-neutral-600 dark:text-neutral-400">Track hackathons, submission windows, and never miss an opportunity.</p>
        </div>
        <button 
          onClick={() => setShowAddModal(true)}
          className="px-5 py-2.5 bg-black dark:bg-[#f5f0e8] text-white dark:text-black rounded-xl font-medium hover:opacity-90 transition-all whitespace-nowrap"
        >
          + Add Custom Event
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Search Bar */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-neutral-400" />
            </div>
            <input
              type="text"
              placeholder="Search events by name or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white dark:bg-black border border-neutral-200 dark:border-[#f5f0e8]/[0.08] rounded-xl pl-11 pr-4 py-3.5 text-neutral-900 dark:text-[#f5f0e8] focus:outline-none focus:ring-2 focus:ring-neutral-500/50 focus:border-neutral-500 transition-all"
            />
          </div>

          {/* Events List */}
          {isLoading ? (
             <div className="flex justify-center py-20 text-neutral-400">
               <Loader2 className="w-8 h-8 animate-spin" />
             </div>
          ) : filteredEvents.length > 0 ? (
            filteredEvents.map((event) => (
              <div key={event.id} className="bg-white dark:bg-black border border-neutral-200 dark:border-[#f5f0e8]/[0.06] rounded-3xl p-6 hover:border-neutral-400 dark:hover:border-[#f5f0e8]/[0.15] transition-colors group">
                <div className="flex flex-col sm:flex-row justify-between gap-4 mb-4">
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 bg-${event.color}-100 dark:bg-${event.color}-500/10 text-${event.color}-600 dark:text-${event.color}-400`}>
                      {event.type === 'Hackathon' ? <Trophy className="w-6 h-6" /> : <Calendar className="w-6 h-6" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-xl font-semibold text-neutral-900 dark:text-[#f5f0e8]">{event.title}</h3>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium bg-${event.color}-100 dark:bg-${event.color}-500/20 text-${event.color}-700 dark:text-${event.color}-300`}>
                          {event.type}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">{event.status}</p>
                    </div>
                  </div>
                  <button className="w-10 h-10 rounded-full border border-neutral-200 dark:border-[#f5f0e8]/[0.08] flex items-center justify-center text-neutral-500 hover:text-neutral-900 dark:hover:text-[#f5f0e8] hover:bg-neutral-100 dark:hover:bg-[#f5f0e8]/[0.04] transition-colors shrink-0">
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-neutral-100 dark:border-[#f5f0e8]/[0.04]">
                  <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                    <Calendar className="w-4 h-4" />
                    {event.date}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                    <Clock className="w-4 h-4" />
                    {event.time}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                    <MapPin className="w-4 h-4" />
                    {event.location}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 bg-white dark:bg-black border border-neutral-200 dark:border-[#f5f0e8]/[0.06] rounded-3xl">
              <div className="w-16 h-16 bg-neutral-100 dark:bg-[#f5f0e8]/[0.04] rounded-full flex items-center justify-center mx-auto mb-4 text-neutral-400">
                <Search className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-[#f5f0e8] mb-2">No events found</h3>
              <p className="text-neutral-500 dark:text-neutral-400">
                We couldn't find any events matching "{searchQuery}".
              </p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-black dark:bg-[#f5f0e8]/[0.04] rounded-3xl p-6 text-[#f5f0e8] border border-transparent dark:border-[#f5f0e8]/[0.06] relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#f5f0e8]/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2"></div>
            <h3 className="text-xl font-bold mb-2 relative z-10">Momentum Score</h3>
            <div className="flex items-end gap-2 mb-4 relative z-10">
              <span className="text-5xl font-black tracking-tighter">84</span>
              <span className="text-[#f5f0e8]/60 mb-1 font-medium">/ 100</span>
            </div>
            <p className="text-[#f5f0e8]/60 text-sm relative z-10">You're in the top 15% of active builders this month. Keep it up!</p>
          </div>
        </div>
      </div>

      {/* ─── Add Event Modal ─── */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white dark:bg-black rounded-3xl p-6 shadow-2xl w-full max-w-md border border-neutral-200 dark:border-[#f5f0e8]/[0.08]"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold dark:text-[#f5f0e8]">Schedule Event</h2>
                <button onClick={() => setShowAddModal(false)} className="text-neutral-500 hover:text-neutral-800 dark:hover:text-[#f5f0e8]">
                  <X />
                </button>
              </div>
              
              <form onSubmit={handleAddEvent} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Event Title</label>
                  <input required type="text" value={newTitle} onChange={e => setNewTitle(e.target.value)} className="w-full bg-neutral-50 dark:bg-[#f5f0e8]/[0.04] border border-neutral-200 dark:border-[#f5f0e8]/[0.08] rounded-xl px-4 py-3 dark:text-[#f5f0e8] focus:ring-2 focus:ring-neutral-500 outline-none transition-all" placeholder="e.g. SF AI Hackathon" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Type</label>
                  <select value={newType} onChange={e => setNewType(e.target.value)} className="w-full bg-neutral-50 dark:bg-[#f5f0e8]/[0.04] border border-neutral-200 dark:border-[#f5f0e8]/[0.08] rounded-xl px-4 py-3 dark:text-[#f5f0e8] focus:ring-2 focus:ring-neutral-500 outline-none transition-all">
                    <option value="Hackathon">Hackathon</option>
                    <option value="Conference">Conference</option>
                    <option value="Deadline">Deadline</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Date</label>
                  <input 
                    required 
                    type="date"
                    value={newDate}
                    min={new Date().toISOString().slice(0, 10)}
                    onChange={e => setNewDate(e.target.value)}
                    className="w-full bg-neutral-50 dark:bg-[#f5f0e8]/[0.04] border border-neutral-200 dark:border-[#f5f0e8]/[0.08] rounded-xl px-4 py-3 dark:text-[#f5f0e8] focus:ring-2 focus:ring-neutral-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Time</label>
                  <input 
                    required 
                    type="time"
                    value={newTime}
                    onChange={e => setNewTime(e.target.value)}
                    className="w-full bg-neutral-50 dark:bg-[#f5f0e8]/[0.04] border border-neutral-200 dark:border-[#f5f0e8]/[0.08] rounded-xl px-4 py-3 dark:text-[#f5f0e8] focus:ring-2 focus:ring-neutral-500 outline-none transition-all"
                  />
                </div>
                <div>
                   <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Location</label>
                   <input required type="text" value={newLocation} onChange={e => setNewLocation(e.target.value)} className="w-full bg-neutral-50 dark:bg-[#f5f0e8]/[0.04] border border-neutral-200 dark:border-[#f5f0e8]/[0.08] rounded-xl px-4 py-3 dark:text-[#f5f0e8] focus:ring-2 focus:ring-neutral-500 outline-none transition-all" placeholder="Online or City" />
                </div>

                <div className="pt-2">
                   <button disabled={isSubmitting} type="submit" className="w-full bg-black dark:bg-[#f5f0e8] text-white dark:text-black hover:opacity-90 rounded-xl py-3 font-medium transition-all disabled:opacity-50 flex justify-center items-center">
                     {isSubmitting ? <Loader2 className="animate-spin" /> : "Schedule & Sync"}
                   </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ─── Integration Prompt Modal ─── */}
      <AnimatePresence>
        {showIntegrationModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="bg-white dark:bg-black rounded-3xl p-7 shadow-2xl w-full max-w-md border border-neutral-200 dark:border-[#f5f0e8]/[0.08]"
            >
              {/* Success header */}
              <div className="text-center mb-6">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 400, damping: 15, delay: 0.1 }}
                  className="w-14 h-14 bg-emerald-100 dark:bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <CheckCircle2 className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
                </motion.div>
                <h2 className="text-xl font-bold dark:text-[#f5f0e8] mb-1">Event Scheduled!</h2>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                  <span className="font-medium text-neutral-700 dark:text-[#f5f0e8]/70">"{lastAddedEventTitle}"</span> has been added to your events.
                </p>
              </div>

              {/* Divider */}
              <div className="flex items-center gap-3 mb-5">
                <div className="flex-1 h-px bg-neutral-200 dark:bg-[#f5f0e8]/[0.06]" />
                <span className="text-[11px] text-neutral-400 uppercase tracking-widest font-medium">Stay synced</span>
                <div className="flex-1 h-px bg-neutral-200 dark:bg-[#f5f0e8]/[0.06]" />
              </div>

              <div className="space-y-3">
                {/* Google Calendar Integration */}
                <div className={`rounded-2xl border p-4 transition-all ${
                  googleConnected 
                    ? 'border-emerald-300 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/[0.06]' 
                    : 'border-neutral-200 dark:border-[#f5f0e8]/[0.08] bg-neutral-50 dark:bg-[#f5f0e8]/[0.02]'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {/* Google Calendar icon */}
                      <div className="w-10 h-10 rounded-xl bg-white dark:bg-black border border-neutral-200 dark:border-[#f5f0e8]/[0.08] flex items-center justify-center shrink-0">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <rect x="3" y="4" width="18" height="18" rx="3" stroke="#4285F4" strokeWidth="1.5"/>
                          <path d="M3 9h18" stroke="#4285F4" strokeWidth="1.5"/>
                          <rect x="7" y="12" width="3" height="3" rx="0.5" fill="#EA4335"/>
                          <rect x="14" y="12" width="3" height="3" rx="0.5" fill="#34A853"/>
                          <rect x="7" y="16.5" width="3" height="3" rx="0.5" fill="#FBBC05"/>
                          <rect x="14" y="16.5" width="3" height="3" rx="0.5" fill="#4285F4"/>
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-semibold dark:text-[#f5f0e8]">Google Calendar</p>
                        <p className="text-xs text-neutral-400">
                          {googleConnected ? "Connected & synced" : "Auto-sync events to your calendar"}
                        </p>
                      </div>
                    </div>
                    {googleConnected ? (
                      <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
                        <CheckCircle2 className="w-4 h-4 text-white" />
                      </div>
                    ) : (
                      <button
                        onClick={handleGoogleCalendarConnect}
                        disabled={isConnectingGoogle}
                        className="px-4 py-2 text-xs font-semibold bg-black dark:bg-[#f5f0e8] text-white dark:text-black rounded-full hover:opacity-90 transition-all disabled:opacity-50 shrink-0"
                      >
                        {isConnectingGoogle ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          "Connect"
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* Telegram Notifications */}
                <div className={`rounded-2xl border p-4 transition-all ${
                  telegramConnected 
                    ? 'border-emerald-300 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/[0.06]' 
                    : 'border-neutral-200 dark:border-[#f5f0e8]/[0.08] bg-neutral-50 dark:bg-[#f5f0e8]/[0.02]'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {/* Telegram icon */}
                      <div className="w-10 h-10 rounded-xl bg-white dark:bg-black border border-neutral-200 dark:border-[#f5f0e8]/[0.08] flex items-center justify-center shrink-0">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <path d="M22 3L9.218 10.083M22 3L15 22L9.218 10.083M22 3L2 9.5L9.218 10.083" stroke="#229ED9" strokeWidth="1.5" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-semibold dark:text-[#f5f0e8]">Telegram Notifications</p>
                        <p className="text-xs text-neutral-400">
                          {telegramConnected ? "Bot connected — notifications enabled" : "Get reminders via Telegram bot"}
                        </p>
                      </div>
                    </div>
                    {telegramConnected ? (
                      <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
                        <CheckCircle2 className="w-4 h-4 text-white" />
                      </div>
                    ) : (
                      <a
                        href={TELEGRAM_BOT_LINK}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => setTelegramConnected(true)}
                        className="px-4 py-2 text-xs font-semibold bg-[#229ED9] text-white rounded-full hover:bg-[#1a8ac2] transition-all shrink-0 flex items-center gap-1.5"
                      >
                        <Send className="w-3 h-3" /> Send Hi
                      </a>
                    )}
                  </div>

                  {/* Telegram instructions */}
                  {!telegramConnected && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="mt-3 pt-3 border-t border-neutral-200 dark:border-[#f5f0e8]/[0.06]"
                    >
                      <div className="flex items-start gap-2">
                        <div className="w-5 h-5 rounded-full bg-[#229ED9]/10 flex items-center justify-center shrink-0 mt-0.5">
                          <span className="text-[10px] font-bold text-[#229ED9]">1</span>
                        </div>
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">
                          Click <span className="font-medium text-[#229ED9]">"Send Hi"</span> to open our Telegram bot
                        </p>
                      </div>
                      <div className="flex items-start gap-2 mt-1.5">
                        <div className="w-5 h-5 rounded-full bg-[#229ED9]/10 flex items-center justify-center shrink-0 mt-0.5">
                          <span className="text-[10px] font-bold text-[#229ED9]">2</span>
                        </div>
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">
                          Press <span className="font-medium">Start</span> and send <span className="font-mono bg-neutral-100 dark:bg-[#f5f0e8]/[0.06] px-1.5 py-0.5 rounded text-[11px]">hi</span> to activate notifications
                        </p>
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>

              {/* Done button */}
              <button
                onClick={handleCloseIntegration}
                className="w-full mt-5 py-3 text-sm font-medium text-neutral-500 dark:text-neutral-400 hover:text-neutral-800 dark:hover:text-[#f5f0e8] transition-colors rounded-xl border border-neutral-200 dark:border-[#f5f0e8]/[0.08] hover:bg-neutral-50 dark:hover:bg-[#f5f0e8]/[0.02]"
              >
                {googleConnected || telegramConnected ? "Done — I'm all set!" : "Skip for now"}
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
