import { motion } from "motion/react";
import { User, Bell, Shield, Palette } from "lucide-react";

export default function SettingsPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-4xl"
    >
      <header className="mb-10">
        <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">Settings</h1>
        <p className="text-neutral-600 dark:text-neutral-400">Manage your account preferences and integrations.</p>
      </header>

      <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-3xl overflow-hidden shadow-sm dark:shadow-none">
        
        {/* Profile Section */}
        <div className="p-8 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-10 h-10 bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 rounded-full flex items-center justify-center">
              <User className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">Profile Information</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Full Name</label>
              <input type="text" defaultValue="Student Developer" className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-4 py-2.5 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50" />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Email Address</label>
              <input type="email" defaultValue="student@university.edu" className="w-full bg-neutral-50 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-xl px-4 py-2.5 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-neutral-500/50" />
            </div>
          </div>
        </div>

        {/* Integrations Section */}
        <div className="p-8 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-10 h-10 bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 rounded-full flex items-center justify-center">
              <Shield className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">Connected Accounts</h2>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-800 rounded-xl bg-neutral-50 dark:bg-neutral-950/50">
              <div>
                <p className="font-medium text-neutral-900 dark:text-white">GitHub</p>
                <p className="text-sm text-neutral-500">Connected as @studentdev</p>
              </div>
              <button className="px-4 py-2 text-sm font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-500 transition-colors">Disconnect</button>
            </div>
          </div>
        </div>

        {/* Preferences Section */}
        <div className="p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-10 h-10 bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 rounded-full flex items-center justify-center">
              <Bell className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">Notifications</h2>
          </div>
          
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="font-medium text-neutral-900 dark:text-white">Event Reminders</p>
                <p className="text-sm text-neutral-500">Get notified 24h before hackathons start.</p>
              </div>
              <div className="relative">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-neutral-200 dark:bg-neutral-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neutral-600"></div>
              </div>
            </label>
            
            <label className="flex items-center justify-between cursor-pointer pt-4 border-t border-neutral-100 dark:border-neutral-800/50">
              <div>
                <p className="font-medium text-neutral-900 dark:text-white">Weekly Digest</p>
                <p className="text-sm text-neutral-500">Summary of your progress and momentum.</p>
              </div>
              <div className="relative">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-neutral-200 dark:bg-neutral-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-neutral-600"></div>
              </div>
            </label>
          </div>
        </div>

        <div className="p-8 bg-neutral-50 dark:bg-neutral-900/50 border-t border-neutral-200 dark:border-neutral-800 flex justify-end">
          <button className="px-6 py-2.5 bg-neutral-600 hover:bg-neutral-700 text-white rounded-xl font-medium transition-colors">
            Save Changes
          </button>
        </div>
      </div>
    </motion.div>
  );
}
