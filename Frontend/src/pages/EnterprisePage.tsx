import React, { useState } from "react";
import { motion } from "motion/react";
import { Search, Play, ArrowRight, Globe, Shield, Zap, Code2 } from "lucide-react";
import { Link } from "react-router-dom";
import { useToast } from "../components/ui/use-toast";

/* ------------------------------------------------------------------ */
/*  TypeScript Interfaces                                              */
/* ------------------------------------------------------------------ */

interface InputFieldProps {
  label: string;
  placeholder: string;
  type?: string;
  value: string;
  onChange: (val: string) => void;
}

interface NavLinkProps {
  label: string;
  isHighlighted?: boolean;
}

interface PillButtonProps {
  children: React.ReactNode;
  variant?: "solid" | "glass";
  className?: string;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
}

/* ------------------------------------------------------------------ */
/*  Sub-Components                                                     */
/* ------------------------------------------------------------------ */

const NavLink = ({ label, isHighlighted }: NavLinkProps) => (
  <a
    href="#"
    className={`text-sm font-medium transition-colors ${
      isHighlighted
        ? "text-white"
        : "text-neutral-500 hover:text-neutral-300"
    }`}
  >
    {label}
  </a>
);

const PillButton = ({ children, variant = "solid", className = "", onClick, type = "button", disabled = false }: PillButtonProps) => (
  <button
    type={type}
    onClick={onClick}
    disabled={disabled}
    className={`
      rounded-full font-semibold text-sm transition-all duration-200 cursor-pointer
      ${variant === "solid"
        ? "bg-white text-black hover:bg-neutral-200 active:bg-neutral-300 shadow-[0_0_20px_rgba(255,255,255,0.05)]"
        : "bg-white/5 text-neutral-300 border border-white/10 hover:bg-white/10 hover:border-white/20 backdrop-blur-md"
      }
      ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      ${className}
    `}
  >
    {children}
  </button>
);

const InputField = ({ label, placeholder, type = "text", value, onChange }: InputFieldProps) => (
  <div className="flex flex-col gap-1.5">
    <label className="text-xs font-medium text-neutral-400 tracking-wide">{label}</label>
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-4 py-3 text-sm text-white placeholder:text-neutral-600 focus:outline-none focus:border-white/20 focus:bg-white/[0.06] transition-all"
    />
  </div>
);

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function EnterprisePage() {
  const [form, setForm] = useState({ name: "", email: "", company: "", country: "", message: "" });
  const [domainSearch, setDomainSearch] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { success } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      success("Request received. Our enterprise team will contact you shortly.");
      setForm({ name: "", email: "", company: "", country: "", message: "" });
    }, 1500);
  };

  const navLinks: NavLinkProps[] = [
    { label: "Product" },
    { label: "Teams" },
    { label: "Resources" },
    { label: "Community" },
    { label: "Support" },
    { label: "Enterprise", isHighlighted: true },
    { label: "Pricing" },
  ];

  return (
    <div className="min-h-screen bg-black text-white font-sans antialiased selection:bg-white/20 overflow-x-hidden" style={{ fontFamily: "'Inter', system-ui, -apple-system, sans-serif" }}>
      
      {/* Ambient radial gradient for depth */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 right-0 w-[900px] h-[900px] bg-[radial-gradient(ellipse_at_center,_rgba(40,40,40,0.4)_0%,_transparent_70%)] translate-x-1/3 -translate-y-1/4" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-[radial-gradient(ellipse_at_center,_rgba(30,30,30,0.3)_0%,_transparent_70%)] -translate-x-1/4 translate-y-1/4" />
      </div>

      {/* ---- Navigation ---- */}
      <nav className="fixed top-0 w-full z-50 bg-black/60 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
              <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="3"/>
              <circle cx="3" cy="12" r="2.5" fill="currentColor"/>
            </svg>
            <span className="font-bold text-base tracking-tight">UpLink</span>
          </Link>

          {/* Center Links */}
          <div className="hidden lg:flex items-center gap-7">
            {navLinks.map((link, i) => (
              <NavLink key={i} {...link} />
            ))}
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm font-medium text-neutral-400 hover:text-white transition-colors">
              Log in
            </Link>
            <Link to="/login" className="bg-white text-black text-sm font-semibold px-5 py-2 rounded-full hover:bg-neutral-200 transition-colors">
              Sign up
            </Link>
          </div>
        </div>
      </nav>

      {/* ================================================================== */}
      {/*  SECTION 1: Hero + Enterprise Form                                  */}
      {/* ================================================================== */}
      <section className="relative z-10 pt-32 pb-28 min-h-screen flex items-center">
        <div className="max-w-7xl mx-auto px-6 w-full">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-20 items-center">
            
            {/* Left: Hero Copy */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
              className="lg:col-span-5"
            >
              <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 mb-8">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-medium text-neutral-400 tracking-widest uppercase">Enterprise Ready</span>
              </div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-[-0.04em] leading-[0.95] mb-7">
                Ship faster.
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-neutral-300 to-neutral-500">
                  Build smarter.
                </span>
              </h1>

              <p className="text-lg text-neutral-400 leading-relaxed mb-10 max-w-md">
                The collaborative platform for teams that need enterprise-grade security, 
                advanced permissions, and the flexibility to ship at scale.
              </p>

              <div className="flex items-center gap-3 flex-wrap">
                <PillButton variant="solid" className="px-7 py-3.5 text-sm">
                  Explore
                </PillButton>
                <PillButton variant="glass" className="px-7 py-3.5 text-sm flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  Watch video
                </PillButton>
              </div>

              {/* Trust Badges */}
              <div className="flex items-center gap-6 mt-14">
                {[
                  { icon: Shield, label: "SOC 2 Compliant" },
                  { icon: Zap, label: "99.9% Uptime" },
                  { icon: Globe, label: "Global CDN" },
                ].map((badge, i) => (
                  <div key={i} className="flex items-center gap-2 text-neutral-500">
                    <badge.icon className="w-4 h-4" />
                    <span className="text-xs font-medium">{badge.label}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Right: Enterprise Contact Form */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.15, ease: [0.23, 1, 0.32, 1] }}
              className="lg:col-span-7 flex justify-center lg:justify-end"
            >
              <div className="w-full max-w-lg bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8 backdrop-blur-2xl shadow-[0_8px_64px_rgba(0,0,0,0.4)]">
                <h2 className="text-2xl font-bold tracking-tight mb-1">Talk to sales</h2>
                <p className="text-sm text-neutral-500 mb-7">Let's help your team build better.</p>

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <InputField label="Name" placeholder="Jane Doe" value={form.name} onChange={v => setForm({...form, name: v})} />
                    <InputField label="Email" placeholder="jane@company.com" type="email" value={form.email} onChange={v => setForm({...form, email: v})} />
                    <InputField label="Company" placeholder="Acme Inc." value={form.company} onChange={v => setForm({...form, company: v})} />
                    <InputField label="Country" placeholder="United States" value={form.country} onChange={v => setForm({...form, country: v})} />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-medium text-neutral-400 tracking-wide">How can we help?</label>
                    <textarea
                      value={form.message}
                      onChange={e => setForm({...form, message: e.target.value})}
                      placeholder="Tell us about your use case..."
                      rows={4}
                      className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-4 py-3 text-sm text-white placeholder:text-neutral-600 focus:outline-none focus:border-white/20 focus:bg-white/[0.06] transition-all resize-none"
                    />
                  </div>

                  <PillButton variant="solid" type="submit" disabled={isSubmitting} className="w-full py-3.5 text-sm mt-2 flex justify-center items-center gap-2">
                    {isSubmitting ? (
                      <><div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> Sending...</>
                    ) : (
                      "Get in touch"
                    )}
                  </PillButton>
                </form>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/*  SECTION 2: Domain Search                                           */}
      {/* ================================================================== */}
      <section className="relative z-10 py-32 border-t border-white/[0.06]">
        {/* Subtle ambient glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-[radial-gradient(ellipse_at_center,_rgba(50,50,50,0.25)_0%,_transparent_70%)] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
            
            {/* Left: Domain Search Content */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
              className="lg:col-span-6"
            >
              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-[-0.04em] leading-[0.95] mb-4">
                Start with
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-neutral-300 to-neutral-500">
                  a free domain.
                </span>
              </h2>
              <p className="text-neutral-500 text-lg mb-10 max-w-md">
                Free for the first year with any yearly Framer plan. Build, launch, and grow 
                your online presence — on your own terms.
              </p>

              {/* Domain Search Bar */}
              <div className="relative max-w-md">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-600" />
                <input
                  type="text"
                  value={domainSearch}
                  onChange={e => setDomainSearch(e.target.value)}
                  placeholder="Search for a domain..."
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-full pl-12 pr-5 py-4 text-sm text-white placeholder:text-neutral-600 focus:outline-none focus:border-white/20 focus:bg-white/[0.06] transition-all"
                />
              </div>

              <div className="flex items-center gap-4 mt-8 text-neutral-600 text-xs font-medium">
                <span>.com</span>
                <span>.design</span>
                <span>.app</span>
                <span>.io</span>
                <span>.dev</span>
                <span className="text-neutral-500">+50 more</span>
              </div>
            </motion.div>

            {/* Right: 3D Visual Placeholder */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1, delay: 0.2, ease: [0.23, 1, 0.32, 1] }}
              className="lg:col-span-6 flex items-center justify-center"
            >
              <div className="relative w-72 h-72 sm:w-80 sm:h-80">
                {/* Outer glow */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-white/[0.06] to-transparent blur-3xl scale-125" />
                
                {/* Glass orb */}
                <div className="relative w-full h-full rounded-[2rem] bg-gradient-to-br from-white/[0.08] to-white/[0.02] border border-white/[0.1] backdrop-blur-xl flex items-center justify-center overflow-hidden shadow-[0_0_80px_rgba(255,255,255,0.03)]">
                  
                  {/* Caustic refraction lines */}
                  <div className="absolute inset-0 opacity-20">
                    <div className="absolute top-[20%] left-[10%] w-[80%] h-[1px] bg-gradient-to-r from-transparent via-white/40 to-transparent rotate-[25deg]" />
                    <div className="absolute top-[40%] left-[5%] w-[90%] h-[1px] bg-gradient-to-r from-transparent via-white/30 to-transparent rotate-[-15deg]" />
                    <div className="absolute top-[65%] left-[15%] w-[70%] h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent rotate-[10deg]" />
                  </div>

                  {/* Rainbow light refraction */}
                  <div className="absolute top-[30%] right-[10%] w-32 h-16 bg-gradient-to-r from-red-500/10 via-yellow-500/10 to-blue-500/10 blur-2xl rotate-[-20deg]" />
                  <div className="absolute bottom-[25%] left-[15%] w-24 h-12 bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-cyan-500/10 blur-2xl rotate-[15deg]" />
                  
                  {/* The "M" letterform */}
                  <span className="relative z-10 text-8xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white/80 to-white/20 select-none" style={{ letterSpacing: "-0.05em" }}>
                    M
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ================================================================== */}
      {/*  SECTION 3: Feature Grid (bonus)                                    */}
      {/* ================================================================== */}
      <section className="relative z-10 py-28 border-t border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl sm:text-5xl font-extrabold tracking-[-0.04em] mb-4">
              Built for teams that ship
            </h2>
            <p className="text-neutral-500 text-lg max-w-xl mx-auto">
              Everything you need to go from concept to production, faster.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              { icon: Code2, title: "Code-First", desc: "Build with React components, export clean production code." },
              { icon: Shield, title: "Enterprise Auth", desc: "SSO, SAML, and granular role-based access control." },
              { icon: Zap, title: "Edge Rendering", desc: "Deploy to 250+ global edge nodes with zero config." },
              { icon: Globe, title: "Localization", desc: "Built-in i18n support for 40+ languages out of the box." },
              { icon: Search, title: "SEO Optimized", desc: "Server-rendered pages with automatic meta tag generation." },
              { icon: ArrowRight, title: "CI/CD Pipelines", desc: "Push to deploy with automated preview environments." },
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="group p-6 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.04] transition-all cursor-default"
              >
                <div className="w-10 h-10 rounded-lg bg-white/[0.06] flex items-center justify-center mb-4 group-hover:bg-white/[0.1] transition-colors">
                  <feature.icon className="w-5 h-5 text-neutral-400 group-hover:text-white transition-colors" />
                </div>
                <h3 className="font-semibold text-white mb-1.5">{feature.title}</h3>
                <p className="text-sm text-neutral-500 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- Footer ---- */}
      <footer className="relative z-10 border-t border-white/[0.06] py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-neutral-600">
              <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="3"/>
              <circle cx="3" cy="12" r="2.5" fill="currentColor"/>
            </svg>
            <span className="text-sm font-semibold text-neutral-600">UpLink</span>
          </div>
          <p className="text-xs text-neutral-700">© 2026 UpLink Inc. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
