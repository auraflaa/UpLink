import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { BrainCircuit, Sparkles, ArrowRight, Database, Zap } from "lucide-react";
import { ThemeToggle } from "../components/theme-toggle";
import { StarsBackground } from "../components/ui/stars";

// Typewriter effect for the demo bar
const TypewriterText = ({ text, delay = 0 }: { text: string, delay?: number }) => {
  const [displayedText, setDisplayedText] = useState("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    const startTimeout = setTimeout(() => setStarted(true), delay);
    return () => clearTimeout(startTimeout);
  }, [delay]);

  useEffect(() => {
    if (!started) return;
    let i = 0;
    const interval = setInterval(() => {
      setDisplayedText(text.slice(0, i));
      i++;
      if (i > text.length) clearInterval(interval);
    }, 40);
    return () => clearInterval(interval);
  }, [text, started]);

  return (
    <span>
      {displayedText}
      <span className="animate-pulse ml-0.5 text-neutral-500">|</span>
    </span>
  );
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50 font-sans selection:bg-neutral-500/30 selection:text-neutral-900 dark:selection:bg-neutral-500/30 dark:selection:text-neutral-100 transition-colors duration-500 overflow-x-hidden relative">
      
      {/* Header */}
      <header className="fixed top-0 w-full px-6 py-5 flex items-center justify-between z-50 bg-neutral-50/90 dark:bg-neutral-950/90 backdrop-blur-md border-b border-neutral-200 dark:border-neutral-800 transition-colors">
        <div className="flex items-center gap-2">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-neutral-600 dark:text-neutral-400">
            <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="3"/>
            <circle cx="3" cy="12" r="2.5" fill="currentColor"/>
          </svg>
          <span className="font-bold text-lg tracking-tight">UpLink</span>
        </div>

        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link to="/login" className="px-6 py-2.5 text-sm font-bold bg-neutral-900 text-white dark:bg-white dark:text-neutral-900 rounded-full hover:scale-105 transition-transform shadow-sm hover:shadow-md">
            Log In
          </Link>
        </div>
      </header>

      {/* Hero Section with Stars Background */}
      <StarsBackground className="relative pt-32 pb-20 min-h-screen flex flex-col items-center justify-center z-10 px-6" starColor="#a855f7">
        
        {/* Text Section */}
        <div className="text-center z-20 w-full max-w-5xl mx-auto flex flex-col items-center">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-neutral-200 dark:border-neutral-500/20 mb-8 bg-neutral-100/50 dark:bg-neutral-500/10 backdrop-blur-sm text-neutral-700 dark:text-neutral-400"
          >
            <span className="w-2 h-2 rounded-full bg-neutral-600 dark:bg-neutral-400 animate-pulse"></span>
            <span className="text-xs font-bold tracking-[0.2em] uppercase">UpLink</span>
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-6xl md:text-8xl lg:text-[7rem] font-bold tracking-tighter leading-[0.9] mb-8"
          >
            Turn your data <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-neutral-600 to-neutral-600 dark:from-neutral-400 dark:to-neutral-600 italic font-light">into action.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-xl md:text-2xl max-w-3xl mx-auto leading-relaxed text-neutral-600 dark:text-neutral-400 mb-16"
          >
            The intelligent operating system for students. UpLink analyzes your GitHub and notes to automatically schedule your next steps.
          </motion.p>

          {/* Integrated Demo Prompt Bar */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
            className="relative p-1 rounded-full bg-gradient-to-r from-neutral-500 to-neutral-500 shadow-2xl shadow-neutral-500/20 w-full max-w-3xl mb-12"
          >
            <div className="bg-white dark:bg-neutral-950 rounded-full p-3 md:p-4 flex items-center gap-3 md:gap-4 border border-transparent">
              <div className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 md:w-5 md:h-5" />
              </div>
              <div className="text-left flex-1 overflow-hidden">
                <p className="text-sm md:text-base font-medium text-neutral-800 dark:text-neutral-200">
                  <TypewriterText text="Analyze my recent commits and block 2 hours for deep work..." delay={800} />
                </p>
              </div>
              <div className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-neutral-600 text-white flex items-center justify-center shrink-0 cursor-pointer hover:scale-110 transition-transform shadow-md shadow-neutral-500/30">
                <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.6 }}
          >
            <Link to="/login" className="inline-flex items-center justify-center gap-2 px-8 py-4 text-lg font-bold bg-neutral-600 hover:bg-neutral-500 text-white rounded-full hover:scale-105 transition-all shadow-lg shadow-neutral-500/25">
              Start Executing <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </div>
      </StarsBackground>

      {/* Simplified Features Section */}
      <section className="py-24 relative z-20 border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900/30">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tighter mb-4">
              The ultimate execution loop.
            </h2>
            <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
              We don't just show your data. We put it to work.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: Database, title: "Unify", desc: "Sync your GitHub, notes, and deadlines into one intelligent workspace.", color: "blue" },
              { icon: BrainCircuit, title: "Understand", desc: "Our AI reads the context of your code to find exactly what you need to learn next.", color: "purple" },
              { icon: Zap, title: "Execute", desc: "UpLink automatically pushes personalized tasks and focus blocks to your calendar.", color: "amber" }
            ].map((feature, idx) => (
              <div key={idx} className="group flex flex-col items-center text-center p-8 rounded-3xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 hover:border-neutral-500/50 dark:hover:border-neutral-500/50 transition-all shadow-sm hover:shadow-md dark:shadow-none">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110 ${
                  feature.color === 'blue' ? 'bg-neutral-100 dark:bg-neutral-500/10 text-neutral-600 dark:text-neutral-400' :
                  feature.color === 'purple' ? 'bg-neutral-100 dark:bg-neutral-500/10 text-neutral-600 dark:text-neutral-400' :
                  'bg-neutral-100 dark:bg-neutral-500/10 text-neutral-600 dark:text-neutral-400'
                }`}>
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-neutral-600 dark:text-neutral-400 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* High-Contrast Footer CTA */}
      <section className="relative bg-neutral-900 text-white dark:bg-neutral-950 dark:text-white py-32 overflow-hidden z-20 border-t border-neutral-800">
        {/* Decorative background elements */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-neutral-600/20 blur-[120px] rounded-full pointer-events-none"></div>

        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <h2 className="text-4xl md:text-6xl font-bold mb-6 tracking-tighter leading-[1.1]">
            Stop planning. <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-neutral-400 to-neutral-400 italic font-light">Start shipping.</span>
          </h2>
          <p className="text-lg md:text-xl text-neutral-400 leading-relaxed mb-10 max-w-xl mx-auto">
            Join the developers building unstoppable momentum with UpLink.
          </p>
          
          <Link to="/login" className="inline-flex items-center justify-center gap-3 text-lg font-bold bg-white text-neutral-900 hover:bg-neutral-200 px-8 py-4 rounded-full hover:scale-105 transition-all shadow-[0_0_40px_rgba(255,255,255,0.1)]">
            Enter UpLink <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

    </div>
  );
}
