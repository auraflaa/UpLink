import { useState, useEffect, FormEvent } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Calendar, MapPin, Clock, ExternalLink, Trophy, Search, X, Loader2 } from "lucide-react";
import { loadEventSummary, type EventSummaryPayload } from "@/src/lib/mainServer";

const colorClasses: Record<string, { badge: string; icon: string }> = {
  purple: {
    badge: "bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-300",
    icon: "bg-purple-100 dark:bg-purple-500/10 text-purple-600 dark:text-purple-400",
  },
  blue: {
    badge: "bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300",
    icon: "bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400",
  },
  emerald: {
    badge: "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300",
    icon: "bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  },
  amber: {
    badge: "bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-300",
    icon: "bg-amber-100 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400",
  },
  slate: {
    badge: "bg-slate-100 dark:bg-slate-500/20 text-slate-700 dark:text-slate-300",
    icon: "bg-slate-100 dark:bg-slate-500/10 text-slate-600 dark:text-slate-400",
  },
};

export default function EventsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [summary, setSummary] = useState<EventSummaryPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState("Hackathon");
  const [newDate, setNewDate] = useState("");
  const [newLocation, setNewLocation] = useState("");

  const fetchEvents = async () => {
    try {
      const response = await loadEventSummary({
        uiSurface: "events.dashboard",
        sourceKind: "event",
      });
      if (response.data) {
        setSummary(response.data);
      }
    } catch (err) {
      console.error("Failed to load event summary:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void fetchEvents();
  }, []);

  const handleAddEvent = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    const payload = {
      title: newTitle,
      kind: "event",
      execute_at: new Date(newDate).toISOString(),
      metadata: {
        location: newLocation,
        type: newType,
        color: newType === "Hackathon" ? "purple" : newType === "Deadline" ? "amber" : "emerald",
      },
    };

    try {
      await fetch("/api/scheduler/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      await fetchEvents();
      setShowAddModal(false);
      setNewTitle("");
      setNewDate("");
      setNewLocation("");
    } catch (error) {
      console.error("Failed to schedule:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || !summary) {
    return (
      <div className="flex justify-center items-center h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neutral-900 dark:border-white"></div>
      </div>
    );
  }

  const filteredEvents = summary.events.filter(
    (event) =>
      event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.type.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <header className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">{summary.header?.title || "Events"}</h1>
          <p className="text-neutral-600 dark:text-neutral-400">{summary.header?.subtitle}</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-5 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-xl font-medium hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors whitespace-nowrap"
        >
          + {summary.header?.add_button_label || "Add Event"}
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-neutral-400" />
            </div>
            <input
              type="text"
              placeholder="Search events by name or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl pl-11 pr-4 py-3.5 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50 focus:border-neutral-500 transition-all shadow-sm dark:shadow-none"
            />
          </div>

          {isLoading ? (
            <div className="flex justify-center py-20 text-neutral-400">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : filteredEvents.length > 0 ? (
            filteredEvents.map((event) => {
              const classes = colorClasses[event.color] || colorClasses.slate;
              return (
                <div
                  key={event.id}
                  className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none hover:border-neutral-500/50 transition-colors group"
                >
                  <div className="flex flex-col sm:flex-row justify-between gap-4 mb-4">
                    <div className="flex items-start gap-4">
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${classes.icon}`}>
                        {event.type === "Hackathon" ? <Trophy className="w-6 h-6" /> : <Calendar className="w-6 h-6" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-1 flex-wrap">
                          <h3 className="text-xl font-semibold text-neutral-900 dark:text-white">{event.title}</h3>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${classes.badge}`}>
                            {event.type}
                          </span>
                        </div>
                        <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">{event.status}</p>
                      </div>
                    </div>
                    {event.url ? (
                      <a
                        href={event.url}
                        target="_blank"
                        rel="noreferrer"
                        className="w-10 h-10 rounded-full border border-neutral-200 dark:border-neutral-700 flex items-center justify-center text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors shrink-0"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    ) : (
                      <div className="w-10 h-10 rounded-full border border-neutral-200 dark:border-neutral-700 flex items-center justify-center text-neutral-300 shrink-0">
                        <ExternalLink className="w-4 h-4" />
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-neutral-100 dark:border-neutral-800/50">
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
              );
            })
          ) : (
            <div className="text-center py-12 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl shadow-sm dark:shadow-none">
              <div className="w-16 h-16 bg-neutral-100 dark:bg-neutral-800 rounded-full flex items-center justify-center mx-auto mb-4 text-neutral-400">
                <Search className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">{summary.empty_state?.title || "No scheduled events"}</h3>
              <p className="text-neutral-500 dark:text-neutral-400">
                {searchQuery ? `We could not find any events matching "${searchQuery}".` : summary.empty_state?.body}
              </p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-neutral-600 rounded-3xl p-6 text-white shadow-lg shadow-neutral-500/20 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2" />
            <h3 className="text-xl font-bold mb-2 relative z-10">{summary.momentum?.title || "Momentum Score"}</h3>
            <div className="flex items-end gap-2 mb-4 relative z-10">
              <span className="text-5xl font-black tracking-tighter">{summary.momentum?.score || 0}</span>
              <span className="text-neutral-200 mb-1 font-medium">/ {summary.momentum?.max_score || 100}</span>
            </div>
            <p className="text-neutral-100 text-sm relative z-10">{summary.momentum?.body}</p>
            <p className="text-neutral-200/80 text-xs mt-3 relative z-10">
              {summary.summary?.upcoming || 0} upcoming reminder(s) · next due {summary.summary?.next_due || "never"}
            </p>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white dark:bg-neutral-900 rounded-3xl p-6 shadow-2xl w-full max-w-md border border-neutral-200 dark:border-neutral-800"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold dark:text-white">Schedule Event</h2>
                <button onClick={() => setShowAddModal(false)} className="text-neutral-500 hover:text-neutral-800 dark:hover:text-white">
                  <X />
                </button>
              </div>

              <form onSubmit={handleAddEvent} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Event Title</label>
                  <input
                    required
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className="w-full bg-neutral-50 dark:bg-neutral-800 border-none rounded-xl px-4 py-3 dark:text-white focus:ring-2 focus:ring-neutral-500 outline-none"
                    placeholder="e.g. SF AI Hackathon"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full bg-neutral-50 dark:bg-neutral-800 border-none rounded-xl px-4 py-3 dark:text-white focus:ring-2 focus:ring-neutral-500 outline-none"
                  >
                    <option value="Hackathon">Hackathon</option>
                    <option value="Conference">Conference</option>
                    <option value="Deadline">Deadline</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Date and Time</label>
                  <input
                    required
                    type="datetime-local"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full bg-neutral-50 dark:bg-neutral-800 border-none rounded-xl px-4 py-3 dark:text-white focus:ring-2 focus:ring-neutral-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 dark:text-neutral-300">Location</label>
                  <input
                    required
                    type="text"
                    value={newLocation}
                    onChange={(e) => setNewLocation(e.target.value)}
                    className="w-full bg-neutral-50 dark:bg-neutral-800 border-none rounded-xl px-4 py-3 dark:text-white focus:ring-2 focus:ring-neutral-500 outline-none"
                    placeholder="Online or City"
                  />
                </div>

                <div className="pt-4 pt-2">
                  <button
                    disabled={isSubmitting}
                    type="submit"
                    className="w-full bg-neutral-600 hover:bg-neutral-700 text-white rounded-xl py-3 font-medium transition-colors disabled:opacity-50 flex justify-center items-center"
                  >
                    {isSubmitting ? <Loader2 className="animate-spin" /> : "Schedule and Sync"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
