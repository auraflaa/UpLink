import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, Mail, Sparkles } from "lucide-react";
import { ThemeToggle } from "../components/theme-toggle";
import { auth, googleProvider } from "../lib/firebase";
import { signInWithPopup, GoogleAuthProvider } from "firebase/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [focusedInput, setFocusedInput] = useState<string | null>(null);

  const handleEmailLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Mock email login delay
    setTimeout(() => {
      navigate("/home");
    }, 1500);
  };

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      navigate("/home");
    } catch (error) {
      console.error("Google login failed:", error);
      setIsLoading(false);
    }
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
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white py-3.5 rounded-xl transition-all font-medium border border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 shadow-sm hover:shadow-md dark:shadow-none dark:hover:shadow-[0_0_20px_rgba(255,255,255,0.05)] disabled:opacity-70"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </motion.button>
          </motion.div>

          <motion.div variants={itemVariants} className="relative flex items-center py-4 mb-6">
            <div className="flex-grow border-t border-neutral-200 dark:border-neutral-800"></div>
            <span className="flex-shrink-0 mx-4 text-neutral-500 text-sm font-medium uppercase tracking-wider">Or continue with email</span>
            <div className="flex-grow border-t border-neutral-200 dark:border-neutral-800"></div>
          </motion.div>

          <form onSubmit={handleEmailLogin} className="space-y-5">
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
