import React, { useState, useEffect, useContext, createContext, useCallback } from 'react';
import { motion } from 'framer-motion';

// ─── Shared Plant Context ────────────────────────────────────────────────────
// Start/Stop buttons broadcast state to all widgets on the same dashboard
const PlantContext = createContext({ running: false, setRunning: () => { } });

// ─── Styles ──────────────────────────────────────────────────────────────────
const cardStyle =
    'bg-slate-900/70 backdrop-blur-md border border-slate-700/60 rounded-3xl shadow-2xl ' +
    'hover:border-teal-400/60 transition-all duration-300 group';
const glassTitle =
    'text-sm md:text-base font-semibold text-teal-300 uppercase tracking-[0.18em] mb-4 ' +
    'flex items-center gap-2 font-display';

// ─── SVG Gauge Arc ───────────────────────────────────────────────────────────
function GaugeArc({ value = 0, max = 100, color = '#06b6d4' }) {
    const radius = 54;
    const cx = 70;
    const cy = 70;
    const startAngle = 220;
    const endAngle = -40;
    const totalArc = startAngle - endAngle;
    const pct = Math.max(0, Math.min(1, value / max));
    const angle = startAngle - pct * totalArc;

    const toRad = (deg) => (deg * Math.PI) / 180;
    const polarX = (cx, r, deg) => cx + r * Math.cos(toRad(deg));
    const polarY = (cy, r, deg) => cy + r * Math.sin(toRad(deg));

    // Track path
    const trackD = `M ${polarX(cx, radius, startAngle)} ${polarY(cy, radius, startAngle)}
        A ${radius} ${radius} 0 1 1 ${polarX(cx, radius, endAngle)} ${polarY(cy, radius, endAngle)}`;

    // Fill path
    const largeArc = totalArc * pct > 180 ? 1 : 0;
    const fillD =
        pct > 0
            ? `M ${polarX(cx, radius, startAngle)} ${polarY(cy, radius, startAngle)}
           A ${radius} ${radius} 0 ${largeArc} 1 ${polarX(cx, radius, angle)} ${polarY(cy, radius, angle)}`
            : '';

    return (
        <svg width="140" height="120" viewBox="0 0 140 130" className="overflow-visible">
            {/* Track */}
            <path d={trackD} fill="none" stroke="#1e293b" strokeWidth="10" strokeLinecap="round" />
            {/* Fill */}
            {fillD && (
                <path
                    d={fillD}
                    fill="none"
                    stroke={color}
                    strokeWidth="10"
                    strokeLinecap="round"
                    style={{
                        filter: `drop-shadow(0 0 6px ${color}99)`,
                        transition: 'stroke-dashoffset 0.6s ease'
                    }}
                />
            )}
            {/* Needle dot */}
            <circle
                cx={polarX(cx, radius, angle)}
                cy={polarY(cy, radius, angle)}
                r="5"
                fill={color}
                style={{ filter: `drop-shadow(0 0 4px ${color})`, transition: 'all 0.6s ease' }}
            />
        </svg>
    );
}

// ─── Individual Widget Renderer ───────────────────────────────────────────────
const ComponentRenderer = ({ component, onRunningChange }) => {
    const { type, name, properties } = component;
    const { running, setRunning } = useContext(PlantContext);

    const [value, setValue] = useState(
        properties?.value != null ? Number(properties.value) : Math.floor(Math.random() * 60 + 30)
    );
    const [isActive, setIsActive] = useState(properties?.active !== false);
    const [setpoint, setSetpoint] = useState(properties?.setpoint ?? 70);

    // Live simulation — only when plant is running
    useEffect(() => {
        if (!running) return;
        if (type !== 'gauge' && type !== 'value_card') return;
        const id = setInterval(() => {
            setValue((prev) => {
                const noise = (Math.random() - 0.5) * 4;
                const nudge = (setpoint - prev) * 0.05; // Pull toward setpoint
                let next = prev + noise + nudge;
                const lo = properties?.min ?? 0;
                const hi = properties?.max ?? 100;
                return Math.round(Math.max(lo, Math.min(hi, next)) * 10) / 10;
            });
        }, 2000 + Math.random() * 1500);
        return () => clearInterval(id);
    }, [running, type, setpoint, properties]);

    // Base positioning
    const style = {
        position: 'absolute',
        left: `${component.x ?? 0}px`,
        top: `${component.y ?? 0}px`,
        width: properties?.width || undefined,
        height: properties?.height || undefined,
    };

    const unit = properties?.unit || (type === 'gauge' ? '%' : '');
    const maxVal = properties?.max ?? 100;

    switch (type) {

        // ── Chart ──────────────────────────────────────────────────────────
        case 'chart': {
            const bars = running
                ? Array.from({ length: 9 }, () => Math.floor(Math.random() * 90 + 10))
                : [40, 70, 50, 90, 60, 80, 45, 65, 85];
            return (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                    style={{ ...style, width: properties?.width || '280px', height: '180px' }}
                    className={`${cardStyle} p-5 flex flex-col`}
                >
                    <div className={glassTitle}>
                        <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.6)]" />
                        {name}
                    </div>
                    <div className="flex-1 flex items-end gap-1 pb-1 border-b border-slate-700/50">
                        {bars.map((h, i) => (
                            <div key={i} className="flex-1 relative group/bar">
                                <div
                                    className="absolute bottom-0 w-full bg-gradient-to-t from-cyan-500/20 to-cyan-400/60 rounded-t-sm transition-all duration-700"
                                    style={{ height: `${h}%` }}
                                />
                            </div>
                        ))}
                    </div>
                    <div className="mt-2 flex justify-between text-xs font-mono text-slate-500">
                        <span>T-0</span><span>Now</span>
                    </div>
                </motion.div>
            );
        }

        // ── Gauge ──────────────────────────────────────────────────────────
        case 'gauge': {
            const danger = value > maxVal * 0.85;
            const color = danger ? '#ef4444' : '#06b6d4';
            return (
                <motion.div
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    style={{ ...style, width: '220px', height: 'auto' }}
                    className={`${cardStyle} flex flex-col items-center p-4`}
                >
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-1">{name}</div>
                    <GaugeArc value={value} max={maxVal} color={color} />
                    <div className="text-4xl font-mono font-bold text-white -mt-6 tracking-tight">
                        {value}<span className="text-base text-slate-400 ml-1">{unit}</span>
                    </div>
                    {/* Setpoint slider */}
                    <div className="w-full mt-3 px-2">
                        <div className="flex justify-between text-xs text-slate-500 mb-1">
                            <span>Setpoint</span><span className="text-cyan-400 font-mono">{setpoint}{unit}</span>
                        </div>
                        <input
                            type="range" min={0} max={maxVal} value={setpoint}
                            onChange={(e) => setSetpoint(Number(e.target.value))}
                            className="w-full accent-cyan-500 cursor-pointer"
                        />
                    </div>
                    {danger && (
                        <div className="mt-2 text-xs text-red-400 font-semibold animate-pulse">⚠ HIGH ALERT</div>
                    )}
                </motion.div>
            );
        }

        // ── Value Card ─────────────────────────────────────────────────────
        case 'value_card':
            return (
                <motion.div
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    style={{ ...style, height: 'auto', minHeight: '90px' }}
                    className={`${cardStyle} p-5 flex flex-col justify-between`}
                >
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest">{name}</div>
                    <div className="mt-2 text-4xl font-mono text-white font-bold tracking-tight">
                        {value}
                        <span className="text-sm text-slate-400 ml-1">{unit}</span>
                    </div>
                    <div className="mt-1 text-xs text-emerald-400 font-mono">
                        {running ? '● LIVE' : '○ STOPPED'}
                    </div>
                </motion.div>
            );

        // ── Status Indicator ───────────────────────────────────────────────
        case 'status_indicator': {
            const isOn = properties?.follows_plant ? running : isActive;
            return (
                <motion.div
                    initial={{ scale: 0.8 }} animate={{ scale: 1 }}
                    style={{ ...style, width: '160px', height: 'auto' }}
                    onClick={() => !properties?.follows_plant && setIsActive((p) => !p)}
                    className={`flex flex-col items-center gap-3 p-4 bg-slate-900/60 rounded-2xl border transition-all cursor-pointer ${isOn ? 'border-emerald-500/50' : 'border-red-500/40'}`}
                >
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${isOn ? 'bg-emerald-500/10 shadow-[0_0_20px_rgba(16,185,129,0.3)]' : 'bg-red-500/10'}`}>
                        <div className={`w-5 h-5 rounded-full transition-all ${isOn ? 'bg-emerald-400 shadow-[0_0_12px_#34d399]' : 'bg-red-500'}`} />
                    </div>
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest text-center">{name}</span>
                    <span className={`text-xs font-bold ${isOn ? 'text-emerald-400' : 'text-red-400'}`}>{isOn ? 'RUNNING' : 'STOPPED'}</span>
                </motion.div>
            );
        }

        // ── Button / Start / Stop ──────────────────────────────────────────
        case 'button': {
            const isStart = name?.toLowerCase().includes('start');
            const isStop = name?.toLowerCase().includes('stop');
            const handleClick = () => {
                if (isStart) { setRunning(true); setIsActive(true); }
                else if (isStop) { setRunning(false); setIsActive(false); }
                else setIsActive((p) => !p);
            };
            const lit = isStart ? running : isStop ? !running : isActive;
            return (
                <motion.button
                    whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
                    onClick={handleClick}
                    style={{ ...style, width: properties?.width || '160px', height: '56px' }}
                    className={`font-bold rounded-2xl shadow-lg border text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-all ${isStart
                            ? lit ? 'bg-emerald-600 border-emerald-400/40 text-white shadow-emerald-900/40' : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-emerald-900/30'
                            : isStop
                                ? 'bg-red-700/80 border-red-400/40 text-white hover:bg-red-600 shadow-red-900/40'
                                : lit ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-slate-900 border-teal-200/20' : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                        }`}
                >
                    <span className={`w-2.5 h-2.5 rounded-full ${isStart ? (lit ? 'bg-white animate-pulse' : 'bg-slate-500')
                            : isStop ? 'bg-red-300'
                                : lit ? 'bg-slate-900/60' : 'bg-slate-500'
                        }`} />
                    {name}
                </motion.button>
            );
        }

        // ── Alarm List ─────────────────────────────────────────────────────
        case 'alarm_list':
            return (
                <motion.div
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    style={{ ...style, width: '420px', height: '220px' }}
                    className="bg-slate-950/80 backdrop-blur-md border border-red-500/30 rounded-2xl overflow-hidden shadow-2xl flex flex-col"
                >
                    <div className="bg-red-500/10 p-3 border-b border-red-500/20 flex justify-between items-center">
                        <span className="text-sm font-semibold text-red-300 uppercase tracking-widest flex items-center gap-2">
                            <span className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
                            Active Alarms
                        </span>
                        <span className="text-xs bg-red-500/20 text-red-200 px-2 py-0.5 rounded border border-red-500/30 font-semibold">{running ? 'LIVE' : 'IDLE'}</span>
                    </div>
                    <div className="p-2 space-y-1.5 overflow-y-auto flex-1">
                        {(properties?.mock_data || [
                            { Time: '10:23', Message: 'High Pressure - Tank A', Severity: 'CRITICAL' },
                            { Time: '10:15', Message: 'Pump 2 Vibration', Severity: 'WARNING' },
                            { Time: '09:42', Message: 'Flow Rate Anomaly', Severity: 'INFO' },
                        ]).map((a, i) => (
                            <div key={i} className={`flex items-center gap-2 text-xs p-2 rounded ${a.Severity === 'CRITICAL' ? 'bg-red-500/10 border-l-2 border-red-500 text-red-200'
                                    : a.Severity === 'WARNING' ? 'bg-orange-500/10 border-l-2 border-orange-500 text-orange-200'
                                        : 'bg-slate-800/50 border-l-2 border-slate-500 text-slate-300'
                                }`}>
                                <span className="font-mono opacity-60">{a.Time}</span>
                                <span className="flex-1 font-semibold">{a.Message}</span>
                                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-black/30">{a.Severity}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>
            );

        // ── Fallback ───────────────────────────────────────────────────────
        default:
            return (
                <div style={style} className={`${cardStyle} flex items-center justify-center p-3`}>
                    <div className="text-xs text-slate-500 font-mono">{name || type}</div>
                </div>
            );
    }
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function DashboardRenderer({ layout }) {
    const [running, setRunning] = useState(false);

    if (!layout || !layout.components) return (
        <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            No HMI layout generated yet. Click "New Generation" to start.
        </div>
    );

    return (
        <PlantContext.Provider value={{ running, setRunning }}>
            {/* Plant status bar */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-3 px-5 py-2 rounded-full bg-slate-900/80 border border-slate-700 shadow-xl backdrop-blur-md">
                <div className={`w-2.5 h-2.5 rounded-full transition-all ${running ? 'bg-emerald-400 shadow-[0_0_10px_#4ade80] animate-pulse' : 'bg-slate-600'}`} />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
                    Plant: {running ? 'RUNNING' : 'STOPPED'}
                </span>
                <button
                    onClick={() => setRunning((r) => !r)}
                    className={`ml-2 px-4 py-1 rounded-full text-xs font-bold transition-all ${running ? 'bg-red-600 hover:bg-red-500 text-white' : 'bg-emerald-600 hover:bg-emerald-500 text-white'}`}
                >
                    {running ? 'STOP ALL' : 'START ALL'}
                </button>
            </div>

            {/* Components canvas */}
            <div style={{ width: '1200px', height: '800px', position: 'relative', marginTop: '48px' }}>
                {layout.components.map((comp) => (
                    <ComponentRenderer key={comp.id} component={comp} />
                ))}
            </div>
        </PlantContext.Provider>
    );
}
