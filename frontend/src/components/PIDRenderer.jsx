import React, { useState } from 'react';
import { motion } from 'framer-motion';

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const PIDComponent = ({ component, runtime, onUpdate }) => {
    const { type, name, x, y, properties } = component;

    const style = {
        position: 'absolute',
        left: `${x}px`,
        top: `${y}px`,
        width: '70px',
        height: '70px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10
    };

    const componentKey = component._key || component.id || name || `${type}-${x}-${y}`;
    const update = (patch) => onUpdate(componentKey, patch);
    const handleKey = (fn) => (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fn();
        }
    };

    switch (type) {
        case 'tank': {
            const level = clamp(runtime?.level ?? properties?.level ?? 60, 0, 100);
            const nextLevel = level < 40 ? 60 : level < 75 ? 90 : 20;
            const fillHeight = 110 * (level / 100);
            const fillY = 130 - fillHeight;
            const clipId = `tank-clip-${String(componentKey || 'tank').replace(/\s+/g, '-')}`;

            return (
                <div
                    style={{ ...style, width: '110px', height: '160px' }}
                    className="group pointer-events-auto flex flex-col items-center"
                    data-interactive="true"
                    role="button"
                    tabIndex={0}
                    title="Click to change tank level"
                    onClick={() => update({ level: nextLevel })}
                    onKeyDown={handleKey(() => update({ level: nextLevel }))}
                >
                    <svg viewBox="0 0 100 150" className="w-full h-full drop-shadow-lg">
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
                            x="12"
                            y={fillY}
                            width="76"
                            height={fillHeight}
                            clipPath={`url(#${clipId})`}
                            fill="#38bdf8"
                            opacity="0.7"
                            initial={false}
                            animate={{ y: fillY, height: fillHeight }}
                            transition={{ duration: 0.4, ease: 'easeInOut' }}
                        />
                    </svg>
                    <div className="text-xs font-mono text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-600 -mt-2">
                        {name}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">{level}%</div>
                </div>
            );
        }

        case 'pump': {
            const isRun = runtime?.running ?? properties?.state === 'running';
            return (
                <div
                    style={style}
                    className="group pointer-events-auto flex flex-col items-center"
                    data-interactive="true"
                    role="button"
                    tabIndex={0}
                    title="Click to toggle pump"
                    onClick={() => update({ running: !isRun })}
                    onKeyDown={handleKey(() => update({ running: !isRun }))}
                >
                    <svg viewBox="0 0 100 100" className="w-16 h-16 drop-shadow-md">
                        <circle cx="50" cy="50" r="40" fill="#cbd5e1" stroke="#475569" strokeWidth="3" />
                        <path d="M50,10 L50,90 M10,50 L90,50" stroke="#475569" strokeWidth="1" />
                        <path d="M20,90 L80,90" stroke="#475569" strokeWidth="4" />
                        <motion.circle
                            cx="50"
                            cy="50"
                            r="15"
                            fill={isRun ? "#22c55e" : "#ef4444"}
                            animate={{ opacity: isRun ? 0.9 : 0.6 }}
                        />
                    </svg>
                    <div className="absolute -bottom-4 text-xs font-mono text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-600">{name}</div>
                </div>
            );
        }

        case 'valve': {
            const isOpen = runtime?.open ?? properties?.state !== 'closed';
            return (
                <div
                    style={style}
                    className="pointer-events-auto flex flex-col items-center cursor-pointer"
                    data-interactive="true"
                    role="button"
                    tabIndex={0}
                    title="Click to toggle valve"
                    onClick={() => update({ open: !isOpen })}
                    onKeyDown={handleKey(() => update({ open: !isOpen }))}
                >
                    <svg viewBox="0 0 100 60" className="w-16 h-12 drop-shadow-sm">
                        <path d="M0,0 L100,0 L0,60 L100,60 Z" fill={isOpen ? "#a7f3d0" : "#fecaca"} stroke="#475569" strokeWidth="2" opacity="0.9" />
                        <line x1="50" y1="30" x2="50" y2="-20" stroke="#cbd5e1" strokeWidth="4" />
                        <path d="M20,-20 Q50,-35 80,-20 L20,-20 Z" fill="#cbd5e1" stroke="#475569" strokeWidth="2" />
                    </svg>
                    <div className="text-xs font-mono text-slate-300 mt-1">{name}</div>
                </div>
            );
        }

        case 'sensor': {
            const isActive = runtime?.active ?? properties?.active ?? false;
            return (
                <div
                    style={style}
                    className="pointer-events-auto flex flex-col items-center"
                    data-interactive="true"
                    role="button"
                    tabIndex={0}
                    title="Click to toggle sensor"
                    onClick={() => update({ active: !isActive })}
                    onKeyDown={handleKey(() => update({ active: !isActive }))}
                >
                    <svg viewBox="0 0 50 50" className="w-11 h-11 drop-shadow-md">
                        <circle cx="25" cy="25" r="23" fill={isActive ? "#e2e8f0" : "#f8fafc"} stroke="#475569" strokeWidth="2" />
                        <circle cx="25" cy="25" r="8" fill={isActive ? "#22c55e" : "#94a3b8"} opacity="0.85" />
                        <text x="50%" y="55%" textAnchor="middle" fontSize="12" fontWeight="bold" fill="#0f172a" fontFamily="monospace">
                            {name?.includes('LT') ? 'LT' : name?.includes('PT') ? 'PT' : name?.includes('TT') ? 'TT' : 'XM'}
                        </text>
                    </svg>
                    <div className="absolute -top-4 text-[10px] text-slate-400 bg-slate-900/60 px-1.5 rounded">{name}</div>
                </div>
            );
        }

        case 'mixer':
            return (
                <div style={{ ...style, height: '110px' }} className="pointer-events-auto flex flex-col items-center">
                    <div className="w-14 h-9 bg-slate-400 rounded-t-lg border border-slate-600 flex items-center justify-center shadow-md">
                        <div className="w-9 h-1.5 bg-slate-600 rounded"></div>
                    </div>
                    <div className="w-2 h-20 bg-gradient-to-r from-slate-300 to-slate-500"></div>
                    <motion.div
                        animate={{ rotateY: 360 }}
                        transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
                        className="w-16 h-4 bg-slate-400 rounded-full border border-slate-600 opacity-80"
                    />
                    <div className="text-xs font-mono text-slate-400 mt-1">{name}</div>
                </div>
            );

        case 'conveyor':
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

        case 'pipe': {
            const isVertical = properties?.orientation === 'vertical';
            return (
                <div
                    style={{
                        position: 'absolute',
                        left: `${x}px`,
                        top: `${y}px`,
                        width: isVertical ? '8px' : (properties?.length || '100px'),
                        height: isVertical ? (properties?.length || '100px') : '8px',
                        background: 'linear-gradient(90deg, #64748b 0%, #cbd5e1 50%, #64748b 100%)',
                        border: '1px solid #475569',
                        zIndex: 0,
                        borderRadius: '4px',
                        boxShadow: '1px 1px 2px rgba(0,0,0,0.5)'
                    }}
                    className="pointer-events-none"
                />
            );
        }

        default:
            return (
                <div style={style} className="border border-dashed border-red-500 p-2 text-xs text-red-400">
                    Unknown: {type}
                </div>
            );
    }
};

export default function PIDRenderer({ layout }) {
    const [runtimeState, setRuntimeState] = useState({});

    if (!layout || !layout.components) return null;

    const updateComponent = (id, patch) => {
        if (!id) return;
        setRuntimeState((prev) => ({
            ...prev,
            [id]: { ...(prev[id] || {}), ...patch }
        }));
    };

    return (
        <div style={{ width: '1200px', height: '800px' }} className="relative bg-[#0b1120] overflow-hidden border-2 border-slate-800 rounded-3xl shadow-2xl">
            <div className="absolute inset-0 opacity-30 pointer-events-none"
                style={{ backgroundImage: 'linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)', backgroundSize: '50px 50px' }}
            />

            {layout.components.map((comp, index) => {
                const componentKey = comp.id || comp.name || `${comp.type}-${index}`;
                return (
                    <PIDComponent
                        key={componentKey}
                        component={{ ...comp, _key: componentKey }}
                        runtime={runtimeState[componentKey]}
                        onUpdate={updateComponent}
                    />
                );
            })}
        </div>
    );
}
