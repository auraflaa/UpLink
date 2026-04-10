import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, BrainCircuit } from 'lucide-react';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate auth
    setTimeout(() => {
      setLoading(false);
      navigate('/home');
    }, 1000);
  };

  return (
    <div className="flex flex-col h-screen relative">
      <div className="p-6">
        <Link to="/" className="inline-flex items-center gap-2 text-muted hover:text-white transition-colors">
          <ArrowLeft size={20} />
          <span>Back to Demo</span>
        </Link>
      </div>

      <div className="flex-1 flex items-center justify-center p-4 animate-fade-in">
        <div className="glass-panel w-full max-w-md p-8 relative overflow-hidden">
          {/* Subtle inner glow */}
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-primary/20 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
              <BrainCircuit className="text-secondary" size={32} />
            </div>
          </div>
          
          <div className="text-center mb-8">
            <h2 className="heading-lg mb-2">Welcome Back</h2>
            <p className="text-muted">Enter your cognitive space to continue</p>
          </div>

          <form onSubmit={handleLogin} className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <label className="text-sm text-muted font-medium ml-1">Email Address</label>
              <input 
                type="email" 
                required
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                placeholder="student@uplink.ai"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
            </div>
            
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center ml-1">
                <label className="text-sm text-muted font-medium">Password</label>
                <a href="#" className="text-xs text-primary hover:text-primary-hover">Forgot?</a>
              </div>
              <input 
                type="password" 
                required
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full mt-4 bg-white text-black font-bold py-3 rounded-xl hover:bg-gray-200 active:scale-95 transition-all flex justify-center items-center h-12"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
              ) : (
                "Authenticate & Sync"
              )}
            </button>
          </form>
          
          <div className="mt-8 text-center text-sm text-muted">
            Don't have an UpLink instance? <a href="#" className="text-white font-medium hover:underline">Request access</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
