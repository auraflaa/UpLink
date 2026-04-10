import { ArrowRight, BrainCircuit, Activity, LineChart } from 'lucide-react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="container relative">
      <nav className="flex items-center justify-between py-6 animate-fade-in">
        <div className="flex items-center gap-2">
          <BrainCircuit className="text-secondary" size={32} />
          <span className="heading-md">UpLink</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login" className="text-muted hover:text-white transition-colors">
            Login
          </Link>
          <Link 
            to="/login" 
            className="px-6 py-2 rounded-full font-semibold bg-white text-black hover:bg-gray-200 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      <main className="flex flex-col items-center justify-center text-center mt-24 mb-32 animate-fade-in delay-100">
        <div className="inline-block mb-6 px-4 py-1 rounded-full border border-white/10 bg-white/5 text-sm font-medium backdrop-blur-md">
          <span className="text-gradient">Student Growth & Project Assistant</span>
        </div>
        
        <h1 className="heading-xl mb-6 max-w-4xl">
          The Data Exists. <br/> The Clarity Doesn't.
        </h1>
        
        <p className="text-muted text-lg max-w-2xl mb-10">
          Transform your fragmented GitHub commits, hackathon projects, and notes 
          into a <span className="text-white font-medium">closed-loop cognitive system</span>. 
          We don't just analyze — we understand, track, and act on your data.
        </p>

        <div className="flex items-center gap-4">
          <Link 
            to="/login"
            className="group flex items-center gap-2 px-8 py-4 rounded-full bg-primary hover:bg-primary-hover text-white font-bold text-lg transition-all"
          >
            Enter the Loop 
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </main>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in delay-200 mb-20">
        {/* Feature 1 */}
        <div className="glass-panel p-8 text-left">
          <div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center mb-6 text-primary">
            <Activity size={24} />
          </div>
          <h3 className="heading-md mb-2">Fragmented Progress</h3>
          <p className="text-muted">
            Projects live on GitHub. Ideas die in notes. Deadlines hide in chats. Unify them into a single trackable system.
          </p>
        </div>

        {/* Feature 2 */}
        <div className="glass-panel p-8 text-left">
          <div className="w-12 h-12 rounded-lg bg-secondary/20 flex items-center justify-center mb-6 text-secondary">
            <BrainCircuit size={24} />
          </div>
          <h3 className="heading-md mb-2">Cognitive Overload</h3>
          <p className="text-muted">
            Stop spending energy managing tools. Our intelligent embedding system processes your data automatically.
          </p>
        </div>

        {/* Feature 3 */}
        <div className="glass-panel p-8 text-left">
          <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center mb-6 text-white">
            <LineChart size={24} />
          </div>
          <h3 className="heading-md mb-2">Missed Momentum</h3>
          <p className="text-muted">
            Automated execution and reminders ensure hackathons and deadlines never pass unnoticed again.
          </p>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
