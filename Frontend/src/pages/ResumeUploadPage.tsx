import { useState, useRef } from 'react';
import { ArrowLeft, FileText, UploadCloud, CheckCircle2, FileJson } from 'lucide-react';
import { Link } from 'react-router-dom';

const ResumeUploadPage = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [complete, setComplete] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = () => {
    if (!file) return;
    setProcessing(true);
    // Simulate embedding generation and vector DB upload
    setTimeout(() => {
      setProcessing(false);
      setComplete(true);
    }, 2500);
  };

  return (
    <div className="flex flex-col h-screen bg-black overflow-y-auto">
      {/* Header */}
      <header className="h-16 border-b border-white/10 flex items-center px-6 bg-black/40 backdrop-blur-md sticky top-0 z-20">
        <Link to="/home" className="flex items-center gap-2 text-muted hover:text-white transition-colors mr-6">
          <ArrowLeft size={20} />
          <span>Dashboard</span>
        </Link>
        <div className="h-6 w-px bg-white/10 mr-6"></div>
        <div className="flex items-center gap-2">
          <FileText className="text-secondary" size={20} />
          <h1 className="font-semibold tracking-wide">Document Ingestion</h1>
        </div>
      </header>

      <main className="flex-1 p-8 max-w-4xl w-full mx-auto animate-fade-in flex flex-col justify-center items-center">
        
        <div className="text-center mb-10">
          <h2 className="heading-lg mb-3">Feed the Brain</h2>
          <p className="text-muted text-lg max-w-lg mx-auto">
            Upload your resume, hackathon Devpost drafts, or local notes. The User Profile Analyzer will vectorize and merge this with your semantic knowledge graph.
          </p>
        </div>

        <div className="w-full max-w-2xl glass-panel p-10 relative overflow-hidden text-center">
          
          {complete ? (
            <div className="flex flex-col items-center justify-center py-10 animate-fade-in">
              <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mb-6 border border-green-500/30">
                <CheckCircle2 size={40} className="text-green-400" />
              </div>
              <h3 className="heading-md mb-2">Vectors Successfully Embedded</h3>
              <p className="text-muted mb-8">
                "{file?.name}" has been processed through SpaCy/NLTK and stored in the Qdrant DB. Your execution layer is now smarter.
              </p>
              <button 
                onClick={() => { setFile(null); setComplete(false); }}
                className="px-6 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 font-medium transition-colors"
              >
                Upload another file
              </button>
            </div>
          ) : (
            <>
              {/* Drag & Drop Area */}
              <div 
                className={`border-2 border-dashed rounded-2xl p-12 transition-all duration-300 ${
                  isDragging 
                    ? 'border-secondary bg-secondary/10 scale-[1.02]' 
                    : file 
                      ? 'border-white/20 bg-white/5' 
                      : 'border-white/10 hover:border-white/20 hover:bg-white/[0.02]'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !file && fileInputRef.current?.click()}
                style={{ cursor: file ? 'default' : 'pointer' }}
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  className="hidden" 
                  accept=".pdf,.docx,.txt,.md"
                />
                
                {file ? (
                  <div className="flex flex-col items-center animate-fade-in">
                    <FileJson size={48} className="text-secondary mb-4" />
                    <div className="font-semibold text-lg mb-1">{file.name}</div>
                    <div className="text-sm text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); setFile(null); }}
                      className="mt-6 text-sm text-red-400 hover:text-red-300 transition-colors"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div className="w-16 h-16 bg-black/50 rounded-full flex items-center justify-center mb-4 border border-white/10">
                      <UploadCloud size={28} className="text-muted" />
                    </div>
                    <div className="font-semibold text-lg mb-2">Drag & Drop Document</div>
                    <div className="text-sm text-muted">or click to browse from your device</div>
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <button 
                onClick={handleSubmit}
                disabled={!file || processing}
                className={`w-full mt-8 py-4 rounded-xl flex items-center justify-center gap-2 font-bold text-lg transition-all shadow-lg ${
                  !file 
                    ? 'bg-white/5 text-muted cursor-not-allowed' 
                    : 'bg-secondary text-black hover:bg-secondary/90 shadow-secondary/20'
                }`}
              >
                {processing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                    Extracting & Embedding...
                  </>
                ) : (
                  'Submit Document'
                )}
              </button>
            </>
          )}

        </div>
      </main>
    </div>
  );
};

export default ResumeUploadPage;
