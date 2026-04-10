import { useState } from "react";
import { motion } from "motion/react";
import { Calendar, MapPin, Clock, ExternalLink, Trophy, Search } from "lucide-react";

export default function EventsPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const events = [
    {
      id: 1,
      title: "Global AI Hackathon 2026",
      date: "Oct 15 - Oct 17, 2026",
      time: "48 Hours",
      location: "Online",
      type: "Hackathon",
      status: "Upcoming",
      color: "purple"
    },
    {
      id: 2,
      title: "Web3 Builders Summit",
      date: "Nov 02, 2026",
      time: "10:00 AM EST",
      location: "San Francisco, CA",
      type: "Conference",
      status: "Registration Open",
      color: "blue"
    },
    {
      id: 3,
      title: "Open Source Contribution Month",
      date: "Ends Nov 30, 2026",
      time: "Ongoing",
      location: "GitHub",
      type: "Challenge",
      status: "In Progress",
      color: "emerald"
    }
  ];

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
          <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">Events & Momentum</h1>
          <p className="text-neutral-600 dark:text-neutral-400">Track hackathons, submission windows, and never miss an opportunity.</p>
        </div>
        <button className="px-5 py-2.5 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-xl font-medium hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors whitespace-nowrap">
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
              placeholder="Search events by name or type (e.g., Hackathon)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-xl pl-11 pr-4 py-3.5 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all shadow-sm dark:shadow-none"
            />
          </div>

          {/* Events List */}
          {filteredEvents.length > 0 ? (
            filteredEvents.map((event) => (
              <div key={event.id} className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none hover:border-purple-500/50 transition-colors group">
                <div className="flex flex-col sm:flex-row justify-between gap-4 mb-4">
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 bg-${event.color}-100 dark:bg-${event.color}-500/10 text-${event.color}-600 dark:text-${event.color}-400`}>
                      {event.type === 'Hackathon' ? <Trophy className="w-6 h-6" /> : <Calendar className="w-6 h-6" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="text-xl font-semibold text-neutral-900 dark:text-white">{event.title}</h3>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium bg-${event.color}-100 dark:bg-${event.color}-500/20 text-${event.color}-700 dark:text-${event.color}-300`}>
                          {event.type}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-purple-600 dark:text-purple-400">{event.status}</p>
                    </div>
                  </div>
                  <button className="w-10 h-10 rounded-full border border-neutral-200 dark:border-neutral-700 flex items-center justify-center text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors shrink-0">
                    <ExternalLink className="w-4 h-4" />
                  </button>
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
            ))
          ) : (
            <div className="text-center py-12 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl shadow-sm dark:shadow-none">
              <div className="w-16 h-16 bg-neutral-100 dark:bg-neutral-800 rounded-full flex items-center justify-center mx-auto mb-4 text-neutral-400">
                <Search className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-white mb-2">No events found</h3>
              <p className="text-neutral-500 dark:text-neutral-400">
                We couldn't find any events matching "{searchQuery}".
              </p>
              <button 
                onClick={() => setSearchQuery("")}
                className="mt-4 px-4 py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-500/10 rounded-lg transition-colors"
              >
                Clear search
              </button>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-purple-600 rounded-3xl p-6 text-white shadow-lg shadow-purple-500/20 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2"></div>
            <h3 className="text-xl font-bold mb-2 relative z-10">Momentum Score</h3>
            <div className="flex items-end gap-2 mb-4 relative z-10">
              <span className="text-5xl font-black tracking-tighter">84</span>
              <span className="text-purple-200 mb-1 font-medium">/ 100</span>
            </div>
            <p className="text-purple-100 text-sm relative z-10">You're in the top 15% of active builders this month. Keep it up!</p>
          </div>

          <div className="bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-white">Calendar Integration</h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-6">Sync your UpLink events directly with your primary calendar to avoid cognitive overload.</p>
            <button className="w-full py-2.5 border border-neutral-300 dark:border-neutral-700 rounded-xl text-sm font-medium hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors text-neutral-900 dark:text-white">
              Connect Google Calendar
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
