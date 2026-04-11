import React, { useState, useCallback } from "react";
import { motion } from "motion/react";
import { UploadCloud, FileText, CheckCircle, X, AlertCircle } from "lucide-react";
import { useToast } from "../components/ui/use-toast";
import { auth } from "../lib/firebase";

export default function ResumePage() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const { success, error } = useToast();

  const validateAndSetFile = (selectedFile: File) => {
    // Check file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.endsWith('.pdf') && !selectedFile.name.endsWith('.docx') && !selectedFile.name.endsWith('.txt')) {
      error("Unsupported file format. Please upload PDF, DOCX, or TXT.");
      return;
    }
    
    // Check max size (10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      error("File is too large. Maximum size is 10MB.");
      return;
    }
    
    setFile(selectedFile);
    setUploadComplete(false);
  };

  const [uploadedFiles, setUploadedFiles] = useState<{name: string, size: number, date: string}[]>([]);

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
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);

    const formData = new FormData();
    formData.append("files", file);
    formData.append("collection_name", `resume_${auth.currentUser?.uid || "anonymous"}`);
    formData.append("source_label", "resume_upload");

    try {
      const response = await fetch("/api/documents/ingest", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to parse document");
      }

      setUploadedFiles(prev => [
        { name: file.name, size: file.size, date: new Date().toLocaleDateString() },
        ...prev
      ]);
      setUploadComplete(true);
      setFile(null);
      success("Document analyzed and embedded successfully.");
    } catch (err) {
      error("Error uploading document to backend parser.");
    } finally {
      setIsUploading(false);
    }
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
                ? "border-neutral-500 bg-neutral-50 dark:bg-neutral-500/10" 
                : "border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900/50 hover:border-neutral-400 dark:hover:border-neutral-500"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="w-20 h-20 bg-neutral-100 dark:bg-neutral-500/20 text-neutral-600 dark:text-neutral-400 rounded-full flex items-center justify-center mx-auto mb-6">
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
                <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-500/10 text-neutral-600 dark:text-neutral-400 rounded-xl flex items-center justify-center">
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
                    className="p-2 text-neutral-400 hover:text-neutral-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
                
                <button
                  onClick={handleUpload}
                  disabled={isUploading || uploadComplete}
                  className={`px-6 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2 ${
                    uploadComplete 
                      ? "bg-neutral-100 dark:bg-neutral-500/20 text-neutral-700 dark:text-neutral-400 cursor-default"
                      : "bg-neutral-600 hover:bg-neutral-700 text-white disabled:opacity-50"
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
              <AlertCircle className="w-5 h-5 text-neutral-500" />
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
              {uploadedFiles.length === 0 ? (
                <p className="text-sm text-neutral-500">No documents processed yet in this session.</p>
              ) : (
                uploadedFiles.map((f, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-xl hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors cursor-pointer border border-transparent hover:border-neutral-200 dark:hover:border-neutral-700">
                    <FileText className="w-5 h-5 text-neutral-400" />
                    <div className="flex-1 overflow-hidden">
                      <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">{f.name}</p>
                      <p className="text-xs text-neutral-500">{f.date} • {(f.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    <CheckCircle className="w-4 h-4 text-neutral-500" />
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
