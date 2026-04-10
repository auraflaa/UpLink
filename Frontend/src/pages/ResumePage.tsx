import { useState } from "react";
import { motion } from "motion/react";
import { UploadCloud, FileText, CheckCircle, X, AlertCircle } from "lucide-react";

export default function ResumePage() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setUploadComplete(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setUploadComplete(false);
    }
  };

  const handleUpload = () => {
    if (!file) return;
    setIsUploading(true);
    // Mock upload delay
    setTimeout(() => {
      setIsUploading(false);
      setUploadComplete(true);
    }, 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="mb-10">
        <h1 className="text-3xl font-bold mb-2 text-neutral-900 dark:text-white">Document Upload</h1>
        <p className="text-neutral-600 dark:text-neutral-400">Upload your resume or project documents for AI analysis.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Area */}
          <div 
            className={`border-2 border-dashed rounded-3xl p-12 text-center transition-all ${
              isDragging 
                ? "border-purple-500 bg-purple-50 dark:bg-purple-500/10" 
                : "border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900/50 hover:border-purple-400 dark:hover:border-purple-500"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="w-20 h-20 bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded-full flex items-center justify-center mx-auto mb-6">
              <UploadCloud className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">Drag & drop your document here</h3>
            <p className="text-neutral-500 dark:text-neutral-400 mb-8">Supports PDF, DOCX, TXT up to 10MB</p>
            
            <input 
              type="file" 
              id="file-upload" 
              className="hidden" 
              accept=".pdf,.docx,.txt"
              onChange={handleFileChange}
            />
            <label 
              htmlFor="file-upload"
              className="cursor-pointer px-6 py-3 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 rounded-xl font-medium hover:bg-neutral-800 dark:hover:bg-neutral-200 transition-colors inline-flex items-center gap-2"
            >
              Browse Files
            </label>
          </div>

          {/* Selected File & Action */}
          {file && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 flex items-center justify-between shadow-sm dark:shadow-none"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <p className="font-medium text-neutral-900 dark:text-white">{file.name}</p>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                {!isUploading && !uploadComplete && (
                  <button 
                    onClick={() => setFile(null)}
                    className="p-2 text-neutral-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
                
                <button
                  onClick={handleUpload}
                  disabled={isUploading || uploadComplete}
                  className={`px-6 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2 ${
                    uploadComplete 
                      ? "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 cursor-default"
                      : "bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-50"
                  }`}
                >
                  {isUploading ? (
                    <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Uploading...</>
                  ) : uploadComplete ? (
                    <><CheckCircle className="w-4 h-4" /> Analyzed</>
                  ) : (
                    "Analyze Document"
                  )}
                </button>
              </div>
            </motion.div>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-white flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-purple-500" />
              How it works
            </h3>
            <ul className="space-y-4 text-neutral-600 dark:text-neutral-400 text-sm">
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center shrink-0 font-medium text-neutral-900 dark:text-white">1</span>
                <p>Upload your latest resume or project documentation.</p>
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center shrink-0 font-medium text-neutral-900 dark:text-white">2</span>
                <p>Our AI extracts key skills, experiences, and gaps.</p>
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center shrink-0 font-medium text-neutral-900 dark:text-white">3</span>
                <p>Get actionable feedback to align with your target roles.</p>
              </li>
            </ul>
          </div>

          {/* Previous Uploads */}
          <div className="bg-white dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 rounded-3xl p-6 shadow-sm dark:shadow-none">
            <h3 className="text-lg font-semibold mb-4 text-neutral-900 dark:text-white">Recent Documents</h3>
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors cursor-pointer border border-transparent hover:border-neutral-200 dark:hover:border-neutral-700">
                  <FileText className="w-5 h-5 text-neutral-400" />
                  <div className="flex-1 overflow-hidden">
                    <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">Software_Engineer_Resume_v{i}.pdf</p>
                    <p className="text-xs text-neutral-500">Oct {12 + i}, 2025</p>
                  </div>
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
