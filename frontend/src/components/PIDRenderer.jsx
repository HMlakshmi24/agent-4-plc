import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { motion } from 'framer-motion';
import useMachineState from './useMachineState';

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const toNum = (value) => (typeof value === 'number' && !Number.isNaN(value) ? value : 0);

const useCanvasSize = (ref) => {
    const [size, setSize] = useState({ width: 1200, height: 600 });
    useEffect(() => {
        if (!ref.current || typeof ResizeObserver === 'undefined') return;
        const observer = new ResizeObserver((entries) => {
            const entry = entries[0];
            if (!entry?.contentRect) return;
            setSize({
                width: Math.max(600, Math.round(entry.contentRect.width)),
                height: Math.max(400, Math.round(entry.contentRect.height))
            });
        });
        observer.observe(ref.current);
        return () => observer.disconnect();
    }, [ref]);
    return size;
};

const autoLayoutComponents = (components, canvasSize) => {
    if (!components?.length) return components || [];
    const xs = components.map((c) => toNum(c.x));
    const ys = components.map((c) => toNum(c.y));
    const rangeX = Math.max(...xs) - Math.min(...xs);
    const rangeY = Math.max(...ys) - Math.min(...ys);
    const needsAutoLayout = rangeX < 260 || rangeY < 220;
    if (!needsAutoLayout) return components;

    const width = Math.max(900, canvasSize?.width || 1200);
    const height = Math.max(600, canvasSize?.height || 600);
    const centerY = Math.round(height * 0.45);
    const topY = Math.max(70, centerY - 140);
    const leftColX = 70;
    const rightColX = width - 170;

    const flowTypes = new Set(['tank', 'pump', 'valve', 'motor', 'compressor', 'fan', 'conveyor', 'mixer']);
    const isAlarm = (c) => c.type === 'alarm';
    const isControl = (c) => c.type === 'button';
    const isInstrument = (c) => c.type === 'gauge' || (c.type || '').startsWith('sensor');
    const isFlow = (c) => flowTypes.has(c.type);

    const flow = components.filter(isFlow);
    const instruments = components.filter(isInstrument);
    const alarms = components.filter(isAlarm);
    const controls = components.filter(isControl);
    const others = components.filter((c) => !isFlow(c) && !isInstrument(c) && !isAlarm(c) && !isControl(c));

    const next = components.map((c) => ({ ...c }));
    const setPos = (component, x, y) => {
        const idx = components.indexOf(component);
        if (idx >= 0) next[idx] = { ...next[idx], x, y };
    };

    const placeRow = (items, y, spacing = 170) => {
        if (!items.length) return;
        const span = Math.max(1, items.length - 1);
        const total = span * spacing;
        const startX = Math.max(140, (width - total) / 2);
        items.forEach((item, index) => setPos(item, startX + index * spacing, y));
    };

    placeRow(flow, centerY);
    placeRow(instruments, topY, 150);
    placeRow(others, centerY + 150, 150);

    alarms.forEach((item, index) => setPos(item, leftColX, topY + index * 70));
    controls.forEach((item, index) => setPos(item, rightColX, topY + index * 70));

    return next;
};

const getButtonCommand = (label = '') => {
    const text = String(label).toLowerCase();
    if (text.includes('e-stop') || text.includes('estop') || text.includes('emergency')) return 'estop';
    if (text.includes('reset')) return 'reset';
    if (text.includes('stop') || text.includes('halt') || text.includes('off')) return 'stop';
    if (text.includes('start') || text.includes('run') || text.includes('on')) return 'start';
    return null;
};

// ── Individual Component Renderer ──────────────────────────────────────────────
const PIDComponent = ({ component, runtime, onUpdate, simState, machineState, onSystemCommand }) => {
    const { type, x, y, properties } = component;

    // Robust label extraction
    const formattedType = type
        ? type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
        : 'Component';
    let name = component.label || component.name || formattedType;
    if (!name || name.toLowerCase() === 'unknown') name = formattedType;

    const style = {
        position: 'absolute',
        left: `${x}px`,
        top: `${y}px`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10
    };

    const componentKey = component._key || component.id || name || `${type}-${x}-${y}`;
    const update = useCallback((patch) => { if (onUpdate) onUpdate(componentKey, patch); }, [componentKey, onUpdate]);
    const handleKey = (fn) => (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(); } };

    // ── Tank ──────────────────────────────────────────────────────────────────
    if (type === 'tank') {
        const simLevel = simState?.pumpRunning ? Math.min(100, (simState.tankLevel || 60)) : (simState?.tankLevel ?? undefined);
        const level = clamp(simLevel !== undefined ? simLevel : (runtime?.level ?? properties?.level ?? 60), 0, 100);
        const fillHeight = 110 * (level / 100);
        const fillY = 130 - fillHeight;
        const clipId = `tank-clip-${String(componentKey).replace(/\s+/g, '-')}`;
        const levelColor = level > 80 ? '#ef4444' : level < 25 ? '#f59e0b' : '#38bdf8';

        return (
            <div
                style={{ ...style, width: '110px', height: '180px' }}
                className="group pointer-events-auto flex flex-col items-center"
                role="button" tabIndex={0} title="Click to adjust level"
                onClick={() => update({ level: level < 50 ? 75 : 25 })}
                onKeyDown={handleKey(() => update({ level: level < 50 ? 75 : 25 }))}
            >
                <svg viewBox="0 0 100 150" className="w-full drop-shadow-lg" style={{ height: '150px' }}>
                    <defs>
                        <linearGradient id="tankGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#475569" />
                            <stop offset="50%" stopColor="#94a3b8" />
                            <stop offset="100%" stopColor="#475569" />
                        </linearGradient>
                        <clipPath id={clipId}>
                            <path d="M10,20 L10,130 Q10,145 50,145 Q90,145 90,130 L90,20 Q90,5 50,5 Q10,5 10,20 Z" />
                        </clipPath>
                    </defs>
                    <path d="M10,20 L10,130 Q10,145 50,145 Q90,145 90,130 L90,20 Q90,5 50,5 Q10,5 10,20 Z" fill="url(#tankGrad)" stroke="#cbd5e1" strokeWidth="2" />
                    <path d="M10,20 Q50,35 90,20" fill="none" stroke="#cbd5e1" strokeWidth="2" opacity="0.5" />
                    <motion.rect
                        x="12" y={fillY} width="76" height={fillHeight}
                        clipPath={`url(#${clipId})`} fill={levelColor} opacity="0.75"
                        initial={false}
                        animate={{ y: fillY, height: fillHeight }}
                        transition={{ duration: 0.6, ease: 'easeInOut' }}
                    />
                    <text x="50" y="90" textAnchor="middle" fontSize="18" fontWeight="bold" fill="white" fontFamily="monospace">
                        {Math.round(level)}%
                    </text>
                </svg>
                <div className="text-xs font-mono text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-600 mt-1" style={{ whiteSpace: 'nowrap' }}>{name}</div>
                {level > 80 && <div className="text-[10px] text-red-400 mt-0.5 font-bold animate-pulse">⚠ HIGH</div>}
            </div>
        );
    }

    // ── Pump ──────────────────────────────────────────────────────────────────
    if (type === 'pump') {
        const isRun = simState?.pumpRunning ?? runtime?.running ?? properties?.state === 'running';
        return (
            <div
                style={style}
                className="group pointer-events-auto flex flex-col items-center"
                role="button" tabIndex={0} title="Click to toggle pump"
                onClick={() => update({ running: !isRun })}
                onKeyDown={handleKey(() => update({ running: !isRun }))}
            >
                <svg viewBox="0 0 100 100" className="w-16 h-16 drop-shadow-md">
                    <circle cx="50" cy="50" r="40" fill="#1e293b" stroke={isRun ? '#22c55e' : '#ef4444'} strokeWidth="4" />
                    {/* Pump impeller blades */}
                    {[0, 60, 120, 180, 240, 300].map((deg, i) => (
                        <motion.line key={i}
                            x1="50" y1="50"
                            x2={50 + 28 * Math.cos((deg * Math.PI) / 180)}
                            y2={50 + 28 * Math.sin((deg * Math.PI) / 180)}
                            stroke={isRun ? '#22c55e' : '#ef4444'} strokeWidth="3" strokeLinecap="round"
                        />
                    ))}
                    <motion.circle cx="50" cy="50" r="8" fill={isRun ? '#22c55e' : '#ef4444'}
                        animate={isRun ? { scale: [1, 1.2, 1] } : { scale: 1 }}
                        transition={{ repeat: Infinity, duration: 1 }}
                    />
                    <path d="M20,90 L80,90" stroke="#cbd5e1" strokeWidth="4" />
                </svg>
                <motion.div
                    animate={isRun ? { rotate: 360 } : { rotate: 0 }}
                    transition={isRun ? { repeat: Infinity, duration: 1.5, ease: 'linear' } : {}}
                    className="absolute"
                    style={{ width: '64px', height: '64px', top: 0 }}
                />
                <div className="text-xs font-mono text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-600 mt-1">{name}</div>
                <div className={`text-[10px] font-bold mt-0.5 ${isRun ? 'text-green-400' : 'text-red-400'}`}>
                    {isRun ? 'RUNNING' : 'STOPPED'}
                </div>
            </div>
        );
    }

    // ── Valve ──────────────────────────────────────────────────────────────────
    if (type === 'valve') {
        const isOpen = simState?.valveState === 'open' ? true : (simState?.valveState === 'closed' ? false : (runtime?.open ?? properties?.state !== 'closed'));
        return (
            <div
                style={style}
                className="pointer-events-auto flex flex-col items-center cursor-pointer"
                role="button" tabIndex={0} title="Click to toggle valve"
                onClick={() => update({ open: !isOpen })}
                onKeyDown={handleKey(() => update({ open: !isOpen }))}
            >
                <svg viewBox="0 0 80 80" className="w-16 h-16 drop-shadow-sm" style={{ overflow: 'visible' }}>
                    {/* Valve body - bow-tie shape (shifted down 20px to avoid stem overflow) */}
                    <polygon points="0,20 80,20 0,80 80,80" fill={isOpen ? '#a7f3d0' : '#fecaca'} stroke="#475569" strokeWidth="2" opacity="0.9" />
                    {/* Stem */}
                    <line x1="40" y1="50" x2="40" y2="5" stroke="#cbd5e1" strokeWidth="4" />
                    {/* Handwheel */}
                    <ellipse cx="40" cy="5" rx="16" ry="6" fill="none" stroke="#cbd5e1" strokeWidth="3" />
                    <line x1="24" y1="5" x2="56" y2="5" stroke="#cbd5e1" strokeWidth="2" />
                    <line x1="40" y1="-1" x2="40" y2="11" stroke="#cbd5e1" strokeWidth="2" />
                    {/* State indicator dot */}
                    <circle cx="40" cy="50" r="5" fill={isOpen ? '#22c55e' : '#ef4444'} />
                </svg>
                <div className="text-xs font-mono text-slate-300 mt-2" style={{ whiteSpace: 'nowrap' }}>{name}</div>
                <div className={`text-[10px] font-bold ${isOpen ? 'text-green-400' : 'text-red-400'}`}>{isOpen ? 'OPEN' : 'CLOSED'}</div>
            </div>
        );
    }

    // ── Motor ──────────────────────────────────────────────────────────────────
    if (type === 'motor') {
        const isRun = simState?.pumpRunning ?? runtime?.running ?? false;
        return (
            <div style={style} className="pointer-events-auto flex flex-col items-center cursor-pointer"
                role="button" tabIndex={0} title="Click to toggle motor"
                onClick={() => update({ running: !isRun })}
                onKeyDown={handleKey(() => update({ running: !isRun }))}>
                <svg viewBox="0 0 100 80" className="w-20 h-16">
                    <rect x="10" y="20" width="80" height="40" rx="8" fill="#1e293b" stroke={isRun ? '#22c55e' : '#64748b'} strokeWidth="3" />
                    <text x="50" y="45" textAnchor="middle" fontSize="14" fontWeight="bold" fill={isRun ? '#22c55e' : '#94a3b8'} fontFamily="monospace">M</text>
                    <rect x="0" y="32" width="10" height="16" rx="2" fill="#475569" />
                    <rect x="90" y="32" width="10" height="16" rx="2" fill="#475569" />
                    {isRun && <motion.circle cx="50" cy="40" r="22" fill="none" stroke="#22c55e" strokeWidth="1" strokeDasharray="4 4"
                        animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: 'linear' }} />}
                </svg>
                <div className="text-xs font-mono text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-600 mt-1" style={{ whiteSpace: 'nowrap' }}>{name}</div>
                <div className={`text-[10px] font-bold ${isRun ? 'text-green-400' : 'text-slate-400'}`}>{isRun ? 'RUNNING' : 'STOPPED'}</div>
            </div>
        );
    }

    // ── Sensor ──────────────────────────────────────────────────────────────────
    if (type === 'sensor' || type?.startsWith('sensor_')) {
        const isActive = runtime?.active ?? properties?.active ?? true;
        const tag = name?.match(/[A-Z]{1,2}T?\d+/)?.[0] || (type?.includes('level') ? 'LT' : type?.includes('temp') ? 'TT' : type?.includes('pressure') ? 'PT' : 'XM');
        return (
            <div style={style} className="pointer-events-auto flex flex-col items-center"
                role="button" tabIndex={0} title="Click to toggle sensor"
                onClick={() => update({ active: !isActive })}
                onKeyDown={handleKey(() => update({ active: !isActive }))}>
                <svg viewBox="0 0 50 50" className="w-11 h-11 drop-shadow-md">
                    <circle cx="25" cy="25" r="23" fill={isActive ? '#1e293b' : '#f8fafc'} stroke={isActive ? '#38bdf8' : '#475569'} strokeWidth="2.5" />
                    <circle cx="25" cy="25" r="8" fill={isActive ? '#22c55e' : '#94a3b8'} opacity="0.85" />
                    <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central" fontSize="10" fontWeight="bold" fill={isActive ? '#e2e8f0' : '#0f172a'} fontFamily="monospace">{tag}</text>
                </svg>
                <div className="text-[10px] text-slate-400 mt-1 font-mono">{name}</div>
            </div>
        );
    }

// ── Alarm ──────────────────────────────────────────────────────────────────
    if (type === 'alarm') {
        // FIXED: Only blink when alarm is ACTIVE - not constantly
        const isActive = runtime?.active ?? properties?.active ?? false;
        return (
            <div style={style} className="pointer-events-auto flex flex-col items-center"
                role="button" tabIndex={0} onClick={() => update({ active: !isActive })}
                onKeyDown={handleKey(() => update({ active: !isActive }))}>
                <motion.div
                    // Only animate briefly when active - avoid continuous blinking
                    animate={isActive ? { opacity: [1, 0.35, 1] } : { opacity: 1 }}
                    transition={isActive ? { repeat: 2, duration: 0.8 } : {}}
                >
                    <svg viewBox="0 0 60 55" className="w-12 h-11">
                        <polygon points="30,3 57,52 3,52" fill={isActive ? '#ef4444' : '#475569'} stroke="#94a3b8" strokeWidth="2" />
                        <text x="30" y="42" textAnchor="middle" fontSize="20" fontWeight="bold" fill="white">!</text>
                    </svg>
                </motion.div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">{name}</div>
                <div className={`text-[10px] font-bold ${isActive ? 'text-red-400' : 'text-slate-500'}`}>{isActive ? 'ACTIVE' : 'INACTIVE'}</div>
            </div>
        );
    }

    // ── Gauge ──────────────────────────────────────────────────────────────────
    if (type === 'gauge') {
        const val = runtime?.value ?? properties?.value ?? 50;
        const angle = -130 + (val / 100) * 260;
        const r = 28, cx2 = 35, cy2 = 38;
        const rad = (angle * Math.PI) / 180;
        const nx = cx2 + r * Math.cos(rad), ny = cy2 + r * Math.sin(rad);
        return (
            <div style={style} className="pointer-events-auto flex flex-col items-center">
                <svg viewBox="0 0 70 55" className="w-16 h-14">
                    <circle cx={cx2} cy={cy2} r={r} fill="#1e293b" stroke="#475569" strokeWidth="2.5" />
                    <path d={`M ${cx2 - r * Math.cos((50 * Math.PI) / 180)},${cy2 - r * Math.sin((50 * Math.PI) / 180)} A ${r} ${r} 0 1 1 ${cx2 + r * Math.cos((50 * Math.PI) / 180)},${cy2 - r * Math.sin((50 * Math.PI) / 180)}`}
                        fill="none" stroke="#334155" strokeWidth="6" />
                    <line x1={cx2} y1={cy2} x2={nx} y2={ny} stroke="#22d3ee" strokeWidth="2.5" strokeLinecap="round" />
                    <circle cx={cx2} cy={cy2} r="3" fill="#94a3b8" />
                    <text x={cx2} y={cy2 - 10} textAnchor="middle" fontSize="9" fill="#e2e8f0" fontFamily="monospace" fontWeight="bold">{val}</text>
                </svg>
                <div className="text-[10px] font-mono text-slate-400 mt-1">{name}</div>
            </div>
        );
    }

    // ── Mixer ──────────────────────────────────────────────────────────────────
    if (type === 'mixer') {
        return (
            <div style={{ ...style, height: '110px' }} className="pointer-events-auto flex flex-col items-center">
                <div className="w-14 h-9 bg-slate-400 rounded-t-lg border border-slate-600 flex items-center justify-center shadow-md">
                    <div className="w-9 h-1.5 bg-slate-600 rounded"></div>
                </div>
                <div className="w-2 h-20 bg-gradient-to-r from-slate-300 to-slate-500"></div>
                <motion.div animate={{ rotateY: 360 }} transition={{ repeat: Infinity, duration: 0.9, ease: 'linear' }}
                    className="w-16 h-4 bg-slate-400 rounded-full border border-slate-600 opacity-80" />
                <div className="text-xs font-mono text-slate-400 mt-1">{name}</div>
            </div>
        );
    }

    // ── Conveyor ──────────────────────────────────────────────────────────────
    if (type === 'conveyor') {
        return (
            <div style={{ ...style, width: '220px', height: '44px' }} className="pointer-events-auto">
                <div className="w-full h-full border-2 border-slate-600 bg-slate-800 relative overflow-hidden rounded flex items-center">
                    <div className="absolute inset-0 flex space-x-4 animate-[slide_2s_linear_infinite]">
                        {Array.from({ length: 10 }).map((_, i) => (
                            <div key={i} className="w-2 h-full bg-slate-700/50 transform -skew-x-12"></div>
                        ))}
                    </div>
                </div>
                <div className="text-xs text-center font-mono text-slate-500 mt-1">{name}</div>
            </div>
        );
    }

    // ── Pipe ──────────────────────────────────────────────────────────────────
    if (type === 'pipe') {
        const isVertical = properties?.orientation === 'vertical';
        return (
            <div data-interactive="true" style={{ position: 'absolute', left: `${x}px`, top: `${y}px`,
                width: isVertical ? '8px' : (properties?.length || '100px'),
                height: isVertical ? (properties?.length || '100px') : '8px',
                background: 'linear-gradient(90deg, #64748b 0%, #cbd5e1 50%, #64748b 100%)',
                border: '1px solid #475569', zIndex: 0, borderRadius: '4px',
                boxShadow: '1px 1px 2px rgba(0,0,0,0.5)'
            }} className="pointer-events-none" />
        );
    }

    // ── Button / Control ──────────────────────────────────────────────────────
    if (type === 'button') {
        const cmd = getButtonCommand(name);
        const running = !!machineState?.running && !machineState?.estop;
        const isEstop = !!machineState?.estop;
        const isStart = cmd === 'start';
        const isStop = cmd === 'stop';
        const isEStopCmd = cmd === 'estop';
        const isReset = cmd === 'reset';
        const isActive = isStart ? running : isStop ? !running : isEStopCmd ? isEstop : false;
        const btnColor = isStart ? '#22c55e' : isStop ? '#ef4444' : isEStopCmd ? '#f59e0b' : '#3b82f6';
        const disabled = isStart && isEstop;
        return (
            <div style={{ ...style, width: '90px' }} className="pointer-events-auto flex flex-col items-center">
                <button
                    onClick={() => {
                        if (disabled) return;
                        if (cmd && onSystemCommand) {
                            onSystemCommand(cmd);
                            return;
                        }
                        update({ pressed: true });
                    }}
                    style={{
                        background: isActive ? btnColor : `${btnColor}22`,
                        border: `2px solid ${btnColor}`,
                        borderRadius: '8px', padding: '8px 12px', color: isActive ? '#fff' : btnColor,
                        fontWeight: 'bold', fontSize: '10px', cursor: 'pointer',
                        textTransform: 'uppercase', letterSpacing: '1px', width: '100%',
                        opacity: disabled ? 0.5 : 1
                    }}
                >{isReset ? 'RESET' : name}</button>
            </div>
        );
    }

    // ── Default fallback ──────────────────────────────────────────────────────
    return (
        <div style={style} className="border border-dashed border-red-500 p-2 text-xs text-red-400">
            {name} ({type})
        </div>
    );
};

// ── Main PIDRenderer with START/STOP ─────────────────────────────────────────
export default function PIDRenderer({ layout }) {
    const [machineState, setMachineState] = useMachineState();
    const [runtimeState, setRuntimeState] = useState({});
    const [simState, setSimState] = useState({
        isRunning: false,
        pumpRunning: false,
        valveState: 'closed',
        tankLevel: 60,
        temperature: 25,
        pressure: 1.0
    });
    const canvasRef = useRef(null);
    const canvasSize = useCanvasSize(canvasRef);

    if (!layout || !layout.components) return null;

    const arrangedComponents = useMemo(
        () => autoLayoutComponents(layout.components, canvasSize),
        [layout, canvasSize]
    );

    const hasPump = layout.components.some(c => c.type === 'pump');
    const hasTank = layout.components.some(c => c.type === 'tank');
    const hasValve = layout.components.some(c => c.type === 'valve');

    const running = !!machineState?.running && !machineState?.estop;
    const isEstop = !!machineState?.estop;

    useEffect(() => {
        if (isEstop) {
            setSimState(prev => ({
                ...prev,
                isRunning: false,
                pumpRunning: false,
                valveState: 'closed'
            }));
            return;
        }
        if (running) {
            setSimState(prev => ({
                ...prev,
                isRunning: true,
                pumpRunning: true,
                valveState: 'open'
            }));
        } else {
            setSimState(prev => ({
                ...prev,
                isRunning: false,
                pumpRunning: false,
                valveState: 'closed'
            }));
        }
    }, [running, isEstop]);

    // Simulate tank filling when pump runs
    useEffect(() => {
        if (!simState.pumpRunning) return;
        const interval = setInterval(() => {
            setSimState(prev => {
                const newLevel = Math.min(100, prev.tankLevel + 0.5);
                const alarm = newLevel >= 90;
                return { ...prev, tankLevel: newLevel, alarm };
            });
        }, 500);
        return () => clearInterval(interval);
    }, [simState.pumpRunning]);

const updateComponent = useCallback((id, patch) => {
        if (!id) return;
        setRuntimeState(prev => ({ ...prev, [id]: { ...(prev[id] || {}), ...patch } }));
        
        // Sync component state back to simState - FIXED: Properly control machines
        const compType = id.toLowerCase();
        
        if (patch.running !== undefined) {
            // This is a pump or motor
            setSimState(prev => ({ ...prev, pumpRunning: patch.running, isRunning: patch.running }));
        }
        if (patch.open !== undefined) {
            // This is a valve
            setSimState(prev => ({ ...prev, valveState: patch.open ? 'open' : 'closed' }));
        }
        if (patch.level !== undefined) {
            // Tank level changed
            setSimState(prev => ({ ...prev, tankLevel: patch.level }));
        }
    }, []);

    const handleStart = () => {
        setMachineState({ running: true, estop: false });
        setSimState(prev => ({
            ...prev, isRunning: true, pumpRunning: true, valveState: 'open'
        }));
    };

    const handleStop = () => {
        setMachineState({ running: false });
        setSimState(prev => ({
            ...prev, isRunning: false, pumpRunning: false, valveState: 'closed'
        }));
    };

    const handleEstop = () => {
        setMachineState({ running: false, estop: true });
        setSimState(prev => ({
            ...prev, isRunning: false, pumpRunning: false, valveState: 'closed'
        }));
    };

    const handleReset = () => {
        setMachineState({ estop: false });
    };

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative', display: 'flex', flexDirection: 'column' }}>
            {/* ── Status Bar ─────────────────────────────────────────────── */}
            <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '6px 16px', background: 'rgba(15,23,42,0.95)',
                borderBottom: '1px solid #1e3a5f', flexShrink: 0, gap: '12px', flexWrap: 'wrap'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {/* START */}
                    <button onClick={isEstop ? handleReset : handleStart} disabled={isEstop} style={{
                        padding: '5px 14px', background: running ? '#16a34a' : '#15803d',
                        color: '#fff', border: `1px solid ${running ? '#4ade80' : '#22c55e'}`,
                        borderRadius: '6px', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer',
                        letterSpacing: '1px', boxShadow: running ? '0 0 8px #22c55e88' : 'none',
                        transition: 'all 0.2s', opacity: isEstop ? 0.5 : 1
                    }}>▶ START</button>

                    {/* STOP */}
                    <button onClick={handleStop} style={{
                        padding: '5px 14px', background: !running ? '#991b1b' : '#7f1d1d',
                        color: '#fff', border: `1px solid ${!running ? '#f87171' : '#ef4444'}`,
                        borderRadius: '6px', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer',
                        letterSpacing: '1px', transition: 'all 0.2s'
                    }}>■ STOP</button>

                    <button onClick={isEstop ? handleReset : handleEstop} style={{
                        padding: '5px 14px', background: isEstop ? '#b45309' : '#9a3412',
                        color: '#fff', border: `1px solid ${isEstop ? '#f59e0b' : '#fb923c'}`,
                        borderRadius: '6px', fontWeight: 'bold', fontSize: '11px', cursor: 'pointer',
                        letterSpacing: '1px', transition: 'all 0.2s'
                    }}>{isEstop ? 'RESET' : 'E-STOP'}</button>


                    <span style={{ fontSize: '11px', color: running ? '#4ade80' : '#64748b', marginLeft: '4px' }}>
                        ● {running ? 'RUNNING' : 'STOPPED'}
                    </span>
                    {simState.alarm && (
                        <motion.span animate={{ opacity: [1, 0.3, 1] }} transition={{ repeat: 2, duration: 0.6 }}
                            style={{ fontSize: '11px', color: '#ef4444', fontWeight: 'bold' }}>
                            ⚠ HIGH LEVEL ALARM
                        </motion.span>
                    )}
                </div>
                <div style={{ display: 'flex', gap: '14px', fontSize: '11px', color: '#94a3b8' }}>
                    {hasTank && <span>Tank: <b style={{ color: simState.tankLevel > 80 ? '#ef4444' : '#38bdf8' }}>{Math.round(simState.tankLevel)}%</b></span>}
                    {hasPump && <span>Pump: <b style={{ color: simState.pumpRunning ? '#22c55e' : '#ef4444' }}>{simState.pumpRunning ? 'ON' : 'OFF'}</b></span>}
                    {hasValve && <span>Valve: <b style={{ color: simState.valveState === 'open' ? '#22c55e' : '#ef4444' }}>{simState.valveState.toUpperCase()}</b></span>}
                </div>
            </div>

            {/* ── Canvas ─────────────────────────────────────────────────── */}
            <div ref={canvasRef} style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#0b1120' }}>
                {/* Grid background */}
                <div className="absolute inset-0 opacity-30 pointer-events-none"
                    style={{ backgroundImage: 'linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)', backgroundSize: '50px 50px' }} />

                {arrangedComponents.map((comp, index) => {
                    const componentKey = comp.id || comp.label || comp.name || `${comp.type}-${index}`;
                    return (
                        <PIDComponent
                            key={componentKey}
                            component={{ ...comp, _key: componentKey }}
                            runtime={runtimeState[componentKey]}
                            simState={simState}
                            onUpdate={updateComponent}
                            machineState={machineState}
                            onSystemCommand={(cmd) => {
                                if (cmd === 'start') handleStart();
                                if (cmd === 'stop') handleStop();
                                if (cmd === 'estop') handleEstop();
                                if (cmd === 'reset') handleReset();
                            }}
                        />
                    );
                })}
            </div>

            {/* ── Instructions ───────────────────────────────────────────── */}
            <div data-interactive="true" style={{ position: 'absolute', bottom: '8px', left: '8px',
                fontSize: '10px', color: '#475569',
                background: 'rgba(15,23,42,0.8)', padding: '3px 8px', borderRadius: '4px'
            }}>
                Click components to interact • Use START / STOP to control system
            </div>
        </div>
    );
}

