import React from 'react';
import { motion } from 'framer-motion';
import { FiMail, FiMapPin, FiGlobe } from 'react-icons/fi';
import Navbar from './Navbar';
import Footer from './Footer';

const LandingPage = ({ onLogin, onRegister }) => {
    return (
        <div className="min-h-screen bg-white dark:bg-slate-950 font-sans">
            {/* 
        1. HERO SECTION 
        Dark Gradient Background as requested
      */}
            <section className="relative w-full py-32 lg:py-48 flex flex-col items-center justify-center text-center overflow-hidden">
                {/* Background */}
                <div className="absolute inset-0 z-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
                    <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
                    {/* Animated Glows */}
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-[120px] animate-pulse-slow"></div>
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-[120px] animate-pulse-slow"></div>
                </div>

                <div className="relative z-10 max-w-5xl mx-auto px-6">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 tracking-tight leading-tight">
                            Build Compliant IEC 61131-3 Logic <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">
                                In Minutes
                            </span>
                        </h1>

                        <p className="text-xl text-slate-300 mb-12 max-w-2xl mx-auto font-light">
                            Automind AI — AI-Powered PLC & HMI Automation Platform.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
                            <button
                                onClick={onRegister}
                                className="group relative px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white text-lg font-bold rounded-full shadow-[0_10px_20px_rgba(37,99,235,0.3)] hover:shadow-[0_15px_30px_rgba(37,99,235,0.4)] transition-all transform hover:-translate-y-1"
                            >
                                Register Now
                            </button>

                            <button
                                onClick={onLogin}
                                className="px-8 py-4 text-white text-lg font-medium hover:text-blue-300 transition-colors"
                                title="Already have an account?"
                            >
                                Login
                            </button>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* 
        2. CONTACT INFO STRIP (White Section)
        High Contrast for visibility
      */}
            <section className="bg-white border-b border-slate-200 py-16 text-slate-900">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 justify-items-center text-center divide-y md:divide-y-0 md:divide-x divide-slate-200">

                        {/* Column 1: Write to Us */}
                        <div className="w-full px-4 pt-8 md:pt-0">
                            <div className="flex justify-center mb-3 text-slate-800">
                                <FiMail size={28} />
                            </div>
                            <h3 className="text-xl font-extrabold text-slate-900 mb-2">Write to Us</h3>
                            <a href="mailto:hm.lakshmi@parijat.com" className="text-blue-700 hover:text-blue-900 font-bold text-lg">
                                hm.lakshmi@parijat.com
                            </a>
                        </div>

                        {/* Column 2: Address */}
                        <div className="w-full px-4 pt-8 md:pt-0">
                            <div className="flex justify-center mb-3 text-slate-800">
                                <FiMapPin size={28} />
                            </div>
                            <h3 className="text-xl font-extrabold text-slate-900 mb-2">Address</h3>
                            <p className="text-slate-800 font-bold text-lg leading-relaxed">
                                9603 Neuens Rd.<br />Houston, TX. 77080
                            </p>
                        </div>

                        {/* Column 3: Visit */}
                        <div className="w-full px-4 pt-8 md:pt-0">
                            <div className="flex justify-center mb-3 text-slate-800">
                                <FiGlobe size={28} />
                            </div>
                            <h3 className="text-xl font-extrabold text-slate-900 mb-2">For More Visit</h3>
                            <a href="https://www.parijat.com" target="_blank" rel="noreferrer" className="text-blue-700 hover:text-blue-900 font-bold text-lg">
                                www.parijat.com
                            </a>
                        </div>

                    </div>
                </div>
            </section>

            {/* 
        3. BRANDING & FEATURES SECTION
      */}
            <section className="bg-slate-50 py-20 text-center">
                <div className="max-w-5xl mx-auto px-6">

                    {/* Parijat Branding */}
                    <div className="mb-20">
                        <div className="text-3xl font-black text-slate-900 flex justify-center items-center gap-2 mb-2">
                            <span className="text-4xl text-blue-600">⚙️</span>
                            Parijat Controlware, Inc.
                        </div>
                        <p className="text-sm font-bold text-slate-600 uppercase tracking-widest mb-6">
                            Automation & Controls Solution
                        </p>
                        <p className="text-lg text-slate-700 font-medium leading-relaxed max-w-3xl mx-auto">
                            Since 1989, Our Team Has Succeeded In Understanding The Needs Of The Industry And Creating Reliable Products To Serve Them All.
                        </p>
                    </div>

                    {/* Features (Automind AI) */}
                    <h2 className="text-4xl font-extrabold text-slate-900 mb-12">Why Automind AI?</h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
                        {/* Feature 1 */}
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-blue-700 mb-3">AI-Powered IEC Code Generation</h3>
                            <p className="text-slate-700 font-medium leading-relaxed">
                                Generate IEC 61131-3 Structured Text (ST), Ladder (LD), and Function Block (FBD) logic instantly using natural language prompts.
                            </p>
                        </div>
                        {/* Feature 2 */}
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-blue-700 mb-3">Deterministic Industrial Logic Engine</h3>
                            <p className="text-slate-700 font-medium leading-relaxed">
                                Our engine converts structured intent into clean, standards-compliant PLC code without random AI formatting errors.
                            </p>
                        </div>
                        {/* Feature 3 */}
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-blue-700 mb-3">IEC 61131-3 Compliant Templates</h3>
                            <p className="text-slate-700 font-medium leading-relaxed">
                                Pre-validated logic structures for Timers, Counters, State machines, Batch control, Alarm logic, and Safety overrides.
                            </p>
                        </div>
                        {/* Feature 4 */}
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-blue-700 mb-3">AI Debug Assistant</h3>
                            <p className="text-slate-700 font-medium leading-relaxed">
                                Built-in AI assistant helps explain compiler errors, suggest structured corrections, and optimize logic clarity.
                            </p>
                        </div>
                        {/* Feature 5 */}
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-blue-700 mb-3">Clean Industrial Output</h3>
                            <p className="text-slate-700 font-medium leading-relaxed">
                                No unnecessary variables. No random comments. No broken logic. Just clear, industry-standard variable declarations.
                            </p>
                        </div>
                        {/* Feature 6 */}
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-blue-700 mb-3">Secure & Structured</h3>
                            <p className="text-slate-700 font-medium leading-relaxed">
                                Each user workspace is isolated. AI never directly writes raw code but uses a structured model to ensure reliability.
                            </p>
                        </div>
                    </div>

                    {/* AI Disclaimer */}
                    <div className="mt-16 bg-yellow-50 border border-yellow-200 p-6 rounded-xl max-w-3xl mx-auto">
                        <h4 className="flex items-center justify-center gap-2 font-bold text-yellow-800 mb-2">
                            ⚠️ AI Disclaimer
                        </h4>
                        <p className="text-yellow-900 text-sm leading-relaxed">
                            Automind AI assists in generating IEC 61131-3 compliant code. However, all generated logic must be reviewed, tested, and validated by qualified engineers before deployment. The platform does not assume responsibility for unverified implementation in live systems.
                        </p>
                    </div>

                    <div className="mt-10 py-4 opacity-70">
                        <p className="text-sm font-semibold text-slate-500 tracking-wider">
                            BUILT WITH ENGINEERING DISCIPLINE. POWERED BY AI. VERIFIED BY HUMANS.
                        </p>
                    </div>

                </div>
            </section>
        </div>
    );
};

export default LandingPage;
