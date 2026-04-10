import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  toast: (options: Omit<Toast, "id">) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const TOAST_TIMEOUT = 4000;

let toastCounter = 0;

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback((options: Omit<Toast, "id">) => {
    const id = `toast-${++toastCounter}`;
    setToasts((prev) => [...prev, { ...options, id }]);
    
    setTimeout(() => {
      removeToast(id);
    }, TOAST_TIMEOUT);
  }, [removeToast]);

  const success = useCallback((message: string) => toast({ message, type: "success" }), [toast]);
  const error = useCallback((message: string) => toast({ message, type: "error" }), [toast]);
  const info = useCallback((message: string) => toast({ message, type: "info" }), [toast]);

  return (
    <ToastContext.Provider value={{ toast, success, error, info, removeToast }}>
      {children}
      <div className="fixed bottom-0 right-0 z-[100] p-4 space-y-4 w-full flex flex-col items-center sm:items-end pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 50, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className={`
                pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl border shadow-lg max-w-sm w-full sm:w-auto
                ${
                  t.type === "success" 
                    ? "bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white"
                    : t.type === "error"
                    ? "bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/50 text-red-900 dark:text-red-200"
                    : "bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800 text-neutral-900 dark:text-white"
                }
              `}
            >
              <div className="shrink-0 flex items-center justify-center">
                {t.type === "success" && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                {t.type === "error" && <AlertCircle className="w-5 h-5 text-red-500" />}
                {t.type === "info" && <Info className="w-5 h-5 text-blue-500" />}
              </div>
              
              <p className="flex-1 text-sm font-medium pr-2">
                {t.message}
              </p>
              
              <button
                onClick={() => removeToast(t.id)}
                className="shrink-0 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
