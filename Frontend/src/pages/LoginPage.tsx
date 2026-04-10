import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, Github, Mail, Sparkles } from "lucide-react";
import { ThemeToggle } from "../components/theme-toggle";

export default function LoginPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [focusedInput, setFocusedInput] = useState<string | null>(null);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Mock login delay
    setTimeout(() => {
      navigate("/home");
    }, 1500);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 flex w-full font-sans overflow-hidden transition-colors duration-300">
      
      {/* Left Side - Visual Presentation */}
      <div className="hidden lg:flex relative w-1/2 bg-white dark:bg-neutral-900 items-center justify-center overflow-hidden border-r border-neutral-200 dark:border-neutral-800 transition-colors duration-300">
        {/* Animated Grid Background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        
        {/* Animated Glowing Orbs */}
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-400/30 dark:bg-purple-600/30 rounded-full blur-[100px]"
        />
        <motion.div
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-400/20 dark:bg-blue-600/20 rounded-full blur-[100px]"
        />

        {/* Content */}
        <div className="relative z-10 p-12 max-w-xl">
          <Link to="/" className="text-4xl font-bold tracking-tighter text-purple-600 dark:text-purple-400 mb-12 block hover:opacity-80 transition-opacity">
            UpLink
          </Link>
          
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-500/10 text-purple-700 dark:text-purple-400 text-sm font-medium mb-6 border border-purple-200 dark:border-purple-500/20">
              <Sparkles className="w-4 h-4" />
              <span>The future of student productivity</span>
            </div>
            <h2 className="text-5xl font-bold text-neutral-900 dark:text-white mb-6 leading-tight">
              Connect your <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600 dark:from-purple-400 dark:to-pink-600">
                fragmented progress.
              </span>
            </h2>
            <p className="text-xl text-neutral-600 dark:text-neutral-400 leading-relaxed">
              Turn scattered GitHub repos, lost notes, and missed deadlines into a unified system of momentum.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative bg-neutral-50 dark:bg-neutral-950 transition-colors duration-300">
        {/* Mobile Logo */}
        <Link to="/" className="lg:hidden absolute top-8 left-8 text-2xl font-bold tracking-tighter text-purple-600 dark:text-purple-400">
          UpLink
        </Link>

        <div className="absolute top-8 right-8">
          <ThemeToggle />
        </div>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="w-full max-w-md"
        >
          <motion.div variants={itemVariants} className="text-center mb-10">
            <h2 className="text-3xl font-bold text-neutral-900 dark:text-white mb-3">Welcome back</h2>
            <p className="text-neutral-600 dark:text-neutral-400">Enter your details to access your workspace.</p>
          </motion.div>

          <motion.div variants={itemVariants} className="space-y-4 mb-8">
            <motion.button 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleLogin}
              className="w-full flex items-center justify-center gap-3 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white py-3.5 rounded-xl transition-all font-medium border border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 shadow-sm hover:shadow-md dark:shadow-none dark:hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]"
            >
              <Github className="w-5 h-5" />
              Continue with GitHub
            </motion.button>
            <motion.button 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleLogin}
              className="w-full flex items-center justify-center gap-3 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white py-3.5 rounded-xl transition-all font-medium border border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 shadow-sm hover:shadow-md dark:shadow-none dark:hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]"
            >
              <Mail className="w-5 h-5" />
              Continue with Google
            </motion.button>
          </motion.div>

          <motion.div variants={itemVariants} className="relative flex items-center py-4 mb-6">
            <div className="flex-grow border-t border-neutral-200 dark:border-neutral-800"></div>
            <span className="flex-shrink-0 mx-4 text-neutral-500 text-sm font-medium uppercase tracking-wider">Or continue with email</span>
            <div className="flex-grow border-t border-neutral-200 dark:border-neutral-800"></div>
          </motion.div>

          <form onSubmit={handleLogin} className="space-y-5">
            <motion.div variants={itemVariants}>
              <label className="block text-sm font-medium text-neutral-600 dark:text-neutral-400 mb-2 transition-colors" style={{ color: focusedInput === 'email' ? '#c084fc' : undefined }}>
                Email address
              </label>
              <div className="relative">
                <input 
                  type="email" 
                  required
                  onFocus={() => setFocusedInput('email')}
                  onBlur={() => setFocusedInput(null)}
                  className="w-full bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-xl px-4 py-3.5 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all shadow-sm dark:shadow-none"
                  placeholder="you@example.com"
                />
              </div>
            </motion.div>
            
            <motion.div variants={itemVariants}>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-neutral-600 dark:text-neutral-400 transition-colors" style={{ color: focusedInput === 'password' ? '#c084fc' : undefined }}>
                  Password
                </label>
                <a href="#" className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-500 dark:hover:text-purple-300 transition-colors">Forgot password?</a>
              </div>
              <div className="relative">
                <input 
                  type="password" 
                  required
                  onFocus={() => setFocusedInput('password')}
                  onBlur={() => setFocusedInput(null)}
                  className="w-full bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-xl px-4 py-3.5 text-neutral-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all shadow-sm dark:shadow-none"
                  placeholder="••••••••"
                />
              </div>
            </motion.div>
            
            <motion.div variants={itemVariants} className="pt-4">
              <motion.button 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isLoading}
                className="relative w-full bg-purple-600 hover:bg-purple-500 text-white py-4 rounded-xl font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-70 overflow-hidden group shadow-lg shadow-purple-500/20"
              >
                {/* Button Hover Effect Background */}
                <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
                
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>Sign In <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" /></>
                )}
              </motion.button>
            </motion.div>
          </form>
          
          <motion.p variants={itemVariants} className="text-center mt-8 text-neutral-500 text-sm">
            Don't have an account? <a href="#" className="text-purple-600 dark:text-purple-400 hover:text-purple-500 dark:hover:text-purple-300 transition-colors font-medium">Sign up for free</a>
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}
