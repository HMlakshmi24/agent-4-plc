import React, { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { API } from '../config/api';
import DashboardRenderer from './DashboardRenderer';
import PIDRenderer from './PIDRenderer';
import InteractiveCanvas from './InteractiveCanvas';
import './hmi_generator_v3.css';

export default function HmiGeneratorV3() {
    const themeContext = useTheme();
    const theme = themeContext?.theme || 'dark';

    const [showModal, setShowModal] = useState(false);
    const [prompt, setPrompt] = useState("");
    const [systemName, setSystemName] = useState("MyHMISystem");
    const [designStyle, setDesignStyle] = useState("dashboard"); // "dashboard" or "pid"
    const [layout, setLayout] = useState(null);
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState([]);
    const [quotaExceeded, setQuotaExceeded] = useState(false);

    React.useEffect(() => {
        const fetchHistory = async () => {
            const token = localStorage.getItem("automind_token") || localStorage.getItem("token");
            const user = JSON.parse(localStorage.getItem("automind_user") || localStorage.getItem("user_details") || "{}");
            if (!token) return;

            const headers = { Authorization: `Bearer ${token}` };
            if (user.email) headers["X-User-Email"] = user.email;

            try {
                const res = await fetch(`${API}/history/`, { headers });
                if (res.ok) {
                    const data = await res.json();
                    const formatted = data.map(item => ({
                        ...JSON.parse(item.code || "{}"),
                        system_name: item.program_name
                    })).filter(l => l.style).reverse();
                    setHistory(formatted);
                }
            } catch (e) {
                console.error("Failed to fetch HMI history", e);
            }
        };
        fetchHistory();
    }, []);

    const handleGenerate = async () => {
        if (!prompt.trim()) return;
        setLoading(true);

        try {
            let enrichedPrompt = prompt;
            if (designStyle === "dashboard") {
                enrichedPrompt += "\n\n[STYLE REQUIREMENT]: Create a Modern HMI Dashboard. Use charts, gauges, indicators, and value cards.";
            } else {
                enrichedPrompt += "\n\n[STYLE REQUIREMENT]: Create a P&ID Schematic. Use tanks, pumps, valves, pipes, and sensors.";
            }

            const res = await axios.post(`${API}/api/hmi/generate`, {
                prompt: enrichedPrompt
            });

            if (res.data) {
                const newLayout = { ...res.data, system_name: systemName };
                setLayout(newLayout);
                setHistory(prev => [newLayout, ...prev]);
                setShowModal(false);

                // Save to Global History Backend
                const token = localStorage.getItem("automind_token") || localStorage.getItem("token");
                const user = JSON.parse(localStorage.getItem("automind_user") || "{}");
                if (token) {
                    const headers = { "Content-Type": "application/json" };
                    if (!token.startsWith("mock-")) headers["Authorization"] = `Bearer ${token}`;

                    if (user.email) headers["X-User-Email"] = user.email;

                    fetch(`${API}/history/`, {
                        method: "POST",
                        headers: headers,
                        body: JSON.stringify({
                            program_name: systemName,
                            description: prompt,
                            code: JSON.stringify(newLayout),
                            language: "JSON",
                            brand: "Automind HMI",
                            type: "hmi"
                        })
                    }).catch(e => console.error("Failed to save HMI history", e));
                }
            }
        } catch (err) {
            console.error(err);
            if (err.response?.status === 429 || (err.response?.status === 403 && (err.response?.data?.detail || "").toLowerCase().includes("quota"))) {
                setQuotaExceeded(true);
                setShowModal(false);
            } else {
                alert("Failed to generate HMI. Please try again. " + (err.response?.data?.detail || err.message));
            }
        } finally {
            setLoading(false);
        }
    };

    const handleStartProject = () => {
        setShowModal(true);
    };

    const handleBackToLanding = () => {
        setLayout(null);
        setPrompt("");
    };

    const handleExport = async (format) => {
        if (!layout) return;
        try {
            const res = await axios.post(`${API}/api/hmi/export`, {
                layout: layout,
                format: format
            }, { responseType: 'blob' });

            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${layout.system_name || 'project'}.${format === 'html' ? 'html' : 'json'}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.setTimeout(() => window.URL.revokeObjectURL(url), 0);
        } catch (err) {
            console.error(err);
            alert("Export failed: " + (err.response?.statusText || "Unknown error"));
        }
    };

    const renderWorkspace = () => (
        <div className={`flex h-screen overflow-hidden ${theme === 'dark' ? 'bg-[#0b0f17] text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
            <div className={`w-[360px] border-r flex flex-col backdrop-blur-xl z-20 transition-colors hmi-panel-glow
                ${theme === 'dark'
                    ? 'border-slate-800 bg-[#0f172a]/90'
                    : 'border-slate-200 bg-white/90'}`}>

                <div className={`px-7 py-6 border-b flex items-center justify-between transition-colors
                    ${theme === 'dark'
                        ? 'border-slate-800/70'
                        : 'border-slate-200'}`}>
                    <div>
                        <h2 className={`text-xl font-display font-semibold tracking-tight ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>AI WebHMI Interface Designer</h2>
                        <p className="text-[11px] text-sky-300 uppercase tracking-[0.3em]">V3 Layout Engine</p>
                    </div>
                    <span className="hmi-chip">Live</span>
                </div>

                <div className="p-6 flex-1 overflow-y-auto space-y-6 hmi-scrollbar">
                    <div className={`p-5 rounded-2xl border transition-colors ${theme === 'dark' ? 'bg-[#101a2c] border-slate-700/60' : 'bg-slate-100 border-slate-200'}`}>
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-[0.24em] block mb-2">Current Project</label>
                        <p className={`text-lg font-display font-semibold ${theme === 'dark' ? 'text-slate-100' : 'text-slate-900'}`}>{layout?.system_name || "Untitled"}</p>
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                            <span className={`hmi-chip ${layout?.style === 'pid' ? 'hmi-chip-amber' : ''}`}>
                                {layout?.style === 'pid' ? 'P&ID' : 'Dashboard'}
                            </span>
                            <span className="text-xs text-slate-500">Auto layout</span>
                        </div>
                    </div>

                    <button
                        onClick={handleStartProject}
                        className={`w-full py-3.5 rounded-2xl border transition-all flex items-center justify-center gap-2 text-base font-semibold
                            ${theme === 'dark'
                                ? 'border-slate-600 text-slate-200 hover:border-blue-400 hover:text-blue-200 bg-[#0f172a]'
                                : 'border-slate-300 text-slate-700 hover:border-blue-500 hover:text-blue-700 bg-white'}`}
                    >
                        <span className="text-lg">+</span> New Generation
                    </button>

                    <button
                        onClick={handleBackToLanding}
                        className="w-full py-2 text-sm text-slate-500 hover:text-slate-300 transition-colors"
                    >
                        Back to Home
                    </button>

                    <div className="hmi-divider" />

                    <div className="space-y-3">
                        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Export</p>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                onClick={() => handleExport('json')}
                                disabled={!layout}
                                className={`py-3 rounded-xl text-sm font-semibold transition-colors ${theme === 'dark' ? 'bg-slate-800 hover:bg-slate-700 text-slate-200' : 'bg-white border border-slate-200 hover:bg-slate-50 text-slate-700'}`}
                            >
                                Download JSON
                            </button>
                            <button
                                onClick={() => handleExport('html')}
                                disabled={!layout}
                                className={`py-3 rounded-xl text-sm font-semibold transition-colors ${theme === 'dark' ? 'bg-slate-800 hover:bg-slate-700 text-slate-200' : 'bg-white border border-slate-200 hover:bg-slate-50 text-slate-700'}`}
                            >
                                View HTML
                            </button>
                        </div>
                        <p className="text-xs text-slate-500">JSON export keeps full component metadata.</p>
                    </div>
                </div>
            </div>

            <div className={`flex-1 relative overflow-hidden flex flex-col transition-colors ${theme === 'dark' ? 'bg-[#0b0f17]' : 'bg-slate-100'}`}>
                <div className="h-16 flex items-center justify-between px-8 z-10 absolute top-0 w-full pointer-events-none">
                    <div className={`flex items-center gap-3 px-5 py-2.5 rounded-full border mt-6 pointer-events-auto shadow-xl
                        ${theme === 'dark' ? 'bg-slate-900/80 border-slate-700/60 text-slate-200' : 'bg-white/80 border-slate-300/60 text-slate-700'}`}>
                        <div className="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.6)] animate-pulse"></div>
                        <span className="text-sm font-semibold tracking-wide">Status: Ready</span>
                    </div>
                    <div className={`hidden md:flex items-center gap-3 px-5 py-2.5 rounded-full border mt-6 pointer-events-auto shadow-xl
                        ${theme === 'dark' ? 'bg-slate-900/70 border-slate-700/50 text-slate-300' : 'bg-white/80 border-slate-300/60 text-slate-700'}`}>
                        <span className="text-xs uppercase tracking-[0.2em] text-slate-400">System</span>
                        <span className="text-sm font-semibold">{layout?.system_name || "Untitled"}</span>
                        <span className="hmi-chip">{layout?.style === 'pid' ? 'P&ID' : 'Dashboard'}</span>
                    </div>
                </div>

                <div className="flex-1 w-full h-full relative">
                    <InteractiveCanvas>
                        {layout?.style === 'pid' ? (
                            <PIDRenderer layout={layout} />
                        ) : (
                            <DashboardRenderer layout={layout} />
                        )}
                    </InteractiveCanvas>
                </div>
            </div>
        </div>
    );

    const renderLandingPage = () => (
        <div className="relative flex flex-col items-center justify-center p-8 py-20"> {/* Removed min-h-[80vh] for compact layout */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="relative z-10 text-center max-w-4xl w-full rounded-[24px]"
                style={{
                    background: theme === 'dark' ? 'rgba(30, 41, 59, 0.7)' : 'rgba(255, 255, 255, 0.75)',
                    backdropFilter: 'blur(10px)',
                    padding: '40px', // Reduced padding
                    border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(255, 255, 255, 0.6)',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.2)',
                    color: theme === 'dark' ? 'white' : '#1e293b'
                }}
            >

                <h1 className="mb-4 font-display text-4xl md:text-5xl font-extrabold tracking-tight leading-tight"
                    style={{
                        background: 'linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)', // PLC Style
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        fontSize: '2.5rem',
                        fontWeight: '800',
                        marginBottom: '1rem'
                    }}>
                    AI WebHMI Interface Designer
                </h1>

                <p className={`text-lg mb-8 max-w-2xl mx-auto leading-relaxed ${theme === 'dark' ? 'text-slate-400' : 'text-slate-600'}`}>
                    Create production-ready HMI layouts.
                    <br />
                    Supports Dashboards and P&ID Schematics for Industrial Automation.
                </p>

                <motion.button
                    whileHover={{ scale: 1.05, boxShadow: '0 20px 30px -10px rgba(14, 165, 233, 0.4)' }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleStartProject}
                    style={{
                        padding: '16px 40px', // Slightly smaller button
                        background: 'linear-gradient(to right, #0ea5e9, #2563eb)', // PLC Style
                        color: 'white',
                        border: 'none',
                        borderRadius: '100px',
                        fontSize: '1.15em',
                        fontWeight: '600',
                        cursor: 'pointer',
                        boxShadow: '0 10px 20px -5px rgba(14, 165, 233, 0.3)',
                        letterSpacing: '0.02em'
                    }}
                >
                    Start Project →
                </motion.button>

                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'center', gap: '20px', fontSize: '0.85em', color: '#64748b' }}>
                    <span>HMI V3</span> • <span>Dashboard</span> • <span>P&ID</span> • <span>JSON Export</span>
                </div>
            </motion.div>
        </div>
    );

    return (
        <div className="hmi-section-v3 hmi-v3 relative w-full overflow-hidden" style={{ // Removed h-full to fit content naturally if needed, but preserved w-full
            minHeight: '600px', // Enforce minimum but allow it to be shorter than screen if embedded
            color: theme === 'dark' ? 'white' : '#1e293b',
            background: theme === 'dark'
                ? 'radial-gradient(circle at 50% 10%, #1e293b 0%, #020617 100%)' // PLC Style Dark
                : 'linear-gradient(to bottom, #f8fafc, #e2e8f0)', // PLC Style Light
            fontFamily: 'Inter, sans-serif',
            transition: 'background 0.3s, color 0.3s'
        }}>

            {/* Background Grid Effect - Dynamic Opacity */}
            <div style={{
                position: 'absolute', inset: 0,
                backgroundImage: theme === 'dark'
                    ? 'linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px)'
                    : 'linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px)',
                backgroundSize: '48px 48px',
                pointerEvents: 'none',
                zIndex: 0
            }} />

            <div className="pointer-events-none absolute -top-40 right-10 h-80 w-80 rounded-full"
                style={{
                    background: theme === 'dark'
                        ? 'radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, rgba(14, 165, 233, 0) 70%)'
                        : 'radial-gradient(circle, rgba(14, 165, 233, 0.1) 0%, rgba(14, 165, 233, 0) 70%)',
                    filter: 'blur(40px)'
                }}
            />

            {/* Content Container */}
            <div className={`relative z-10 w-full h-full ${theme === 'light' ? 'text-slate-900' : 'text-white'}`}>
                {quotaExceeded ? (
                    <div className="flex flex-col items-center justify-center h-full min-h-[60vh] p-8">
                        <div style={{ textAlign: 'center', padding: '80px', background: theme === 'dark' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(239, 68, 68, 0.05)', border: '1px solid #ef4444', borderRadius: '24px', maxWidth: '600px', backdropFilter: 'blur(10px)' }}>
                            <h2 style={{ fontSize: '2.5rem', color: '#ef4444', marginBottom: '20px', fontWeight: 'bold' }}>⚠ Quota Reached</h2>
                            <p style={{ fontSize: '1.2rem', marginBottom: '40px' }}>You have reached the 50K token quota per account. To continue generating, please renew your subscription.</p>
                            <button onClick={() => window.location.href = "mailto:contact@parijat.com?subject=Renew Automind Subscription"} style={{ padding: '16px 40px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '100px', fontSize: '1.2rem', cursor: 'pointer', fontWeight: 'bold', boxShadow: '0 10px 20px -5px rgba(239, 68, 68, 0.4)' }}>Renew Subscription</button>
                            <div style={{ marginTop: '20px' }}>
                                <button onClick={() => setQuotaExceeded(false)} style={{ background: 'transparent', border: 'none', color: '#64748b', textDecoration: 'underline', cursor: 'pointer' }}>Go Back</button>
                            </div>
                        </div>
                    </div>
                ) : layout ? renderWorkspace() : renderLandingPage()}
            </div>

            <AnimatePresence>
                {showModal && (
                    <motion.div className="plc-modal-overlay-v2" onClick={() => setShowModal(false)}
                        style={{
                            position: 'fixed',
                            inset: 0,
                            zIndex: 1000,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backdropFilter: 'blur(8px)',
                            background: 'rgba(0,0,0,0.6)'
                        }}
                    >
                        <motion.div
                            className="plc-modal-v2"
                            onClick={(e) => e.stopPropagation()}
                            style={{
                                background: theme === 'dark' ? '#1e293b' : 'white',
                                color: theme === 'dark' ? 'white' : '#1e293b',
                                width: '95%',
                                maxWidth: '720px', // PLC Style (max-width)
                                maxHeight: '95vh',
                                display: 'flex',
                                flexDirection: 'column',
                                borderRadius: '12px', // PLC Style
                                border: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.05)',
                                boxShadow: '0 24px 60px rgba(0, 0, 0, 0.45)' // PLC Style
                            }}
                        >
                            <div className="modal-header flex justify-between items-center p-6" style={{
                                borderBottom: '1px solid rgba(255, 255, 255, 0.1)', // PLC Style
                                background: 'rgba(6, 182, 212, 0.04)', // PLC Style
                                padding: '24px 28px' // PLC Style
                            }}>
                                <div>
                                    <h3 className="text-2xl font-extrabold tracking-tight">New HMI Project</h3> {/* PLC Font Style */}
                                </div>
                                <button className="close-btn text-xl leading-none text-slate-400 hover:text-white" onClick={() => setShowModal(false)}>✕</button>
                            </div>

                            <div className="modal-content p-7 space-y-7">
                                {/* System Name Input */}
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-[0.24em]">System Name</label>
                                    <input
                                        type="text"
                                        value={systemName}
                                        onChange={(e) => setSystemName(e.target.value)}
                                        placeholder="e.g. WaterTreatmentPlant, MainDashboard"
                                        className={`w-full rounded-xl p-4 text-base outline-none transition-all
                                        ${theme === 'dark'
                                                ? 'bg-slate-900 border border-slate-700 text-white focus:ring-2 focus:ring-blue-500'
                                                : 'bg-slate-50 border border-slate-300 text-slate-900 focus:ring-2 focus:ring-blue-600'}`}
                                    />
                                </div>

                                {/* Style Selector */}
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-[0.24em]">Design Style</label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <button
                                            className={`p-4 rounded-2xl border flex flex-col items-start justify-center gap-2 transition-all text-left ${designStyle === 'dashboard'
                                                ? 'bg-blue-900/30 border-blue-400/50 text-blue-200 shadow-[0_0_18px_rgba(59,130,246,0.25)]'
                                                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'}`}
                                            onClick={() => setDesignStyle('dashboard')}
                                        >
                                            <div className="text-sm font-semibold">Dashboard</div>
                                            <div className="text-xs text-slate-400">KPIs, cards, charts</div>
                                        </button>
                                        <button
                                            className={`p-4 rounded-2xl border flex flex-col items-start justify-center gap-2 transition-all text-left ${designStyle === 'pid'
                                                ? 'bg-amber-900/30 border-amber-400/50 text-amber-200 shadow-[0_0_18px_rgba(245,158,11,0.25)]'
                                                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'}`}
                                            onClick={() => setDesignStyle('pid')}
                                        >
                                            <div className="text-sm font-semibold">P&ID Schematic</div>
                                            <div className="text-xs text-slate-400">Tanks, valves, piping</div>
                                        </button>
                                    </div>
                                </div>

                                {/* Prompt Input */}
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-[0.24em]">System Requirements</label>
                                    <div className="relative">
                                        <textarea
                                            value={prompt}
                                            onChange={(e) => setPrompt(e.target.value)}
                                            placeholder="Describe your system (e.g. 'Bottling line with 3 conveyors, 2 fillers, and a reject station...')"
                                            className={`w-full rounded-xl p-4 outline-none transition-all min-h-[200px] resize-none border text-base
                                            ${theme === 'dark'
                                                    ? 'bg-slate-900 border-slate-700 text-white focus:ring-2 focus:ring-blue-500'
                                                    : 'bg-slate-50 border-slate-300 text-slate-900 focus:ring-2 focus:ring-blue-600'}`}
                                        />
                                        <div className="absolute bottom-3 right-3 text-xs text-slate-500">{prompt.length} chars</div>
                                    </div>
                                </div>

                                {/* Modal Actions */}
                                <div className="flex justify-end gap-4 p-6 border-t border-slate-700/40" style={{
                                    background: theme === 'dark' ? '#1e293b' : '#f8fafc',
                                    borderRadius: '0 0 12px 12px',
                                    borderTop: theme === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.05)'
                                }}>
                                    <button
                                        className={`px-6 py-3 rounded-lg font-semibold transition-colors border ${theme === 'dark'
                                            ? 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800 hover:border-slate-600'
                                            : 'border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                                            }`}
                                        onClick={() => setShowModal(false)}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        className="px-8 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                        style={{
                                            background: '#2563eb', // PLC Accent Primary
                                            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
                                        }}
                                        onClick={handleGenerate}
                                        disabled={loading || !prompt.trim()}
                                    >
                                        {loading ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                                Generating...
                                            </>
                                        ) : (
                                            <>Generate Interface</>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div >
    );
}
