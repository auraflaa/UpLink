import { motion } from "motion/react";
import { Sparkles } from "lucide-react";

interface LoadingScreenProps {
  message?: string;
  subMessage?: string;
}

export default function LoadingScreen({ 
  message = "Building insights...", 
  subMessage = "Connecting to the neural network" 
}: LoadingScreenProps) {
  return (
    <div className="fixed inset-0 z-[9999] bg-void flex flex-col items-center justify-center overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-neon-purple/20 blur-[150px] rounded-full animate-pulse"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-neon-blue/10 blur-[100px] rounded-full animate-pulse delay-700"></div>
      </div>

      <div className="relative flex flex-col items-center">
        {/* Animated Loader */}
        <div className="relative w-24 h-24 mb-12">
          <motion.div
            animate={{
              rotate: 360,
              scale: [1, 1.1, 1],
            }}
            transition={{
              rotate: { duration: 2, repeat: Infinity, ease: "linear" },
              scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
            }}
            className="absolute inset-0 rounded-full border-2 border-t-neon-blue border-r-neon-purple border-b-transparent border-l-transparent shadow-[0_0_20px_rgba(0,245,255,0.3)]"
          />
          <motion.div
            animate={{
              rotate: -360,
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className="absolute inset-3 rounded-full border border-t-transparent border-r-transparent border-b-neon-purple border-l-neon-blue opacity-50"
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <Sparkles className="w-8 h-8 text-white animate-pulse" />
          </div>
        </div>

        {/* Text Area */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/50 mb-2">
            {message}
          </h2>
          <p className="text-neon-blue/60 font-medium tracking-widest text-xs uppercase">
            {subMessage}
          </p>
        </motion.div>
      </div>

      {/* Futuristic Progress Line */}
      <div className="absolute bottom-12 w-48 h-[1px] bg-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: "100%" }}
          transition={{ duration: 2, repeat: Infinity }}
          className="h-full bg-gradient-to-r from-transparent via-neon-blue to-transparent shadow-[0_0_10px_#00F5FF]"
        />
      </div>
    </div>
  );
}
