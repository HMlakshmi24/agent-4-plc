/**
 * WaterHMI.jsx
 * Full SCADA-style HMI for Water/Wastewater Treatment matching reference images.
 * Domain: "tank" / water treatment.
 */
import React, { useState, useEffect, useContext, createContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const PlantCtx = createContext({ running: false, setRunning: () => { } });

// ─── colour helpers ───────────────────────────────────────────────────────────
const lcol = pct => pct > 80 ? '#e74c3c' : pct < 25 ? '#e67e22' : '#2196f3';

// ─── Mini SVG Tank (top summary row) ─────────────────────────────────────────
function MiniTank({ pct, color }) {
    const h = Math.max(2, pct * 0.3);
    return (
        <svg width="36" height="34" viewBox="0 0 36 34">
            <rect x="2" y="2" width="32" height="30" rx="3" fill="#0a1628" stroke={color} strokeWidth="1.5" />
            <rect x="2" y={32 - h} width="32" height={h} fill={color} opacity="0.85" rx="2" />
            <line x1="2" y1="8" x2="34" y2="8" stroke="rgba(248,81,73,0.4)" strokeWidth="0.8" strokeDasharray="2,1" />
        </svg>
    );
}

// ─── Cylindrical SVG vessel (process flow) ──────────────────────────────────
function CylTank({ label, tag, pct, x, y, w = 56, h = 90, accentColor }) {
    const fill = pct / 100;
    const lqH = h * 0.8 * fill;
    const lqY = y + h * 0.1 + h * 0.8 * (1 - fill);
    const col = lcol(pct);
    const ellipseRY = w * 0.2;
    return (
        <g>
            {/* Body */}
            <rect x={x} y={y + ellipseRY} width={w} height={h - 2 * ellipseRY} fill="#0a1628" stroke={accentColor || '#4a90d9'} strokeWidth="1.5" />
            {/* Liquid */}
            <clipPath id={`cyl-${tag}`}>
                <rect x={x} y={y + ellipseRY} width={w} height={h - 2 * ellipseRY} />
            </clipPath>
            <rect x={x} y={lqY} width={w} height={lqH} fill={col} opacity="0.85"
                clipPath={`url(#cyl-${tag})`} style={{ transition: 'y 1s, height 1s' }} />
            {/* Top ellipse */}
            <ellipse cx={x + w / 2} cy={y + ellipseRY} rx={w / 2} ry={ellipseRY}
                fill="#0d2040" stroke={accentColor || '#4a90d9'} strokeWidth="1.5" />
            {/* Bottom ellipse */}
            <ellipse cx={x + w / 2} cy={y + h - ellipseRY} rx={w / 2} ry={ellipseRY}
                fill={col} opacity={fill > 0 ? 0.6 : 0} style={{ transition: 'opacity 0.5s' }} />
            {/* Level % */}
            <text x={x + w / 2} y={y + h / 2 + 4} textAnchor="middle"
                fill="#fff" fontSize="13" fontWeight="800" fontFamily="monospace">{pct}%</text>
            {/* Tag */}
            <text x={x + w / 2} y={y + h + 14} textAnchor="middle"
                fill="#e6edf3" fontSize="9" fontWeight="700" fontFamily="monospace">{tag}</text>
            {/* Label */}
            <text x={x + w / 2} y={y + h + 24} textAnchor="middle"
                fill="#8b949e" fontSize="8" fontFamily="monospace">{label}</text>
        </g>
    );
}

// ─── Pump circle ────────────────────────────────────────────────────────────
function PumpSym({ cx, cy, r = 16, running, label, onClick }) {
    return (
        <g onClick={onClick} style={{ cursor: 'pointer' }}>
            <circle cx={cx} cy={cy} r={r}
                fill={running ? '#0c3020' : '#1c2030'}
                stroke={running ? '#3fb950' : '#e67e22'} strokeWidth="2" />
            {[0, 60, 120, 180, 240, 300].map(a => (
                <line key={a}
                    x1={cx} y1={cy}
                    x2={cx + (r - 4) * Math.cos(a * Math.PI / 180)}
                    y2={cy + (r - 4) * Math.sin(a * Math.PI / 180)}
                    stroke={running ? '#3fb950' : '#e67e22'} strokeWidth="1.5"
                    style={{ transformOrigin: `${cx}px ${cy}px`, animation: running ? 'pidSpin 1.2s linear infinite' : 'none' }} />
            ))}
            <circle cx={cx} cy={cy} r={4}
                fill={running ? '#3fb950' : '#c0392b'}
                style={{ filter: running ? 'drop-shadow(0 0 4px #3fb950)' : 'none' }} />
            <text x={cx} y={cy + r + 10} textAnchor="middle"
                fill={running ? '#3fb950' : '#e67e22'} fontSize="8" fontWeight="700" fontFamily="monospace">
                {running ? 'Running' : 'Standby'}
            </text>
            {label && <text x={cx} y={cy - r - 4} textAnchor="middle"
                fill="#e6edf3" fontSize="8" fontFamily="monospace">{label}</text>}
        </g>
    );
}

// ─── Valve symbol ───────────────────────────────────────────────────────────
function ValveSym({ cx, cy, open, label, onClick, size = 12 }) {
    const col = open ? '#3fb950' : '#e3b341';
    return (
        <g onClick={onClick} style={{ cursor: 'pointer' }}>
            <polygon points={`${cx - size},${cy - size} ${cx},${cy} ${cx - size},${cy + size}`}
                fill="none" stroke={col} strokeWidth="1.5" />
            <polygon points={`${cx + size},${cy - size} ${cx},${cy} ${cx + size},${cy + size}`}
                fill="none" stroke={col} strokeWidth="1.5" />
            <line x1={cx} y1={cy - size} x2={cx} y2={cy - size - 8} stroke={col} strokeWidth="1.5" />
            <rect x={cx - 5} y={cy - size - 14} width={10} height={6} rx={1}
                fill={open ? '#0c3020' : '#2a1e00'} stroke={col} strokeWidth="1" />
            {label && <text x={cx} y={cy + size + 10} textAnchor="middle"
                fill={col} fontSize="8" fontFamily="monospace">{label}</text>}
        </g>
    );
}

// ─── Instrument bubble ───────────────────────────────────────────────────────
function InstrBubble({ cx, cy, tag, value, unit, pipey, alarm }) {
    const fn = tag.replace(/-.*/, '');
    const col = fn === 'LT' ? '#8e44ad' : fn === 'PT' ? '#4a90d9' : fn === 'FT' ? '#2f8f83' : '#8b949e';
    return (
        <g>
            <line x1={cx} y1={cy + 18} x2={cx} y2={pipey}
                stroke={col} strokeWidth="1" strokeDasharray="3,2" />
            <circle cx={cx} cy={cy} r={18} fill="#0d1117" stroke={alarm ? '#f85149' : col} strokeWidth={alarm ? 2 : 1.5} />
            {alarm && <circle cx={cx} cy={cy} r={18} fill="rgba(248,81,73,0.1)" />}
            <text x={cx} y={cy - 3} textAnchor="middle" fill={col} fontSize="8" fontWeight="700" fontFamily="monospace">{fn}</text>
            <text x={cx} y={cy + 6} textAnchor="middle" fill="#e6edf3" fontSize="7" fontFamily="monospace">{value}</text>
            <text x={cx} y={cy + 26} textAnchor="middle" fill={col} fontSize="8" fontFamily="monospace">{tag}</text>
        </g>
    );
}

// ─── Trend sparkline ─────────────────────────────────────────────────────────
function SparkLine({ data, color, yMin = 30, yMax = 90, h = 60, w = 280 }) {
    if (!data || !data.length) return null;
    const pts = data.map((v, i) => {
        const x = (i / (data.length - 1)) * w;
        const y = h - ((v - yMin) / (yMax - yMin)) * h;
        return `${x},${y}`;
    }).join(' ');
    return (
        <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"
            style={{ filter: `drop-shadow(0 0 3px ${color}66)` }} />
    );
}

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════
export default function WaterHMI({ layout }) {
    const { running, setRunning } = useContext(PlantCtx);

    // ── Fixed plant structure (from layout or defaults) ────────
    const tanks = [
        { tag: 'ET-101', label: 'Influent Tank', base: 75, accentColor: '#2196f3' },
        { tag: 'AT-102', label: 'Aeration Tank', base: 62, accentColor: '#2f8f83' },
        { tag: 'CT-103', label: 'Clarifier Tank', base: 45, accentColor: '#9b59b6' },
        { tag: 'ET-104', label: 'Effluent Tank', base: 88, accentColor: '#27ae60' },
    ];

    // ── State ──────────────────────────────────────────────────
    const [tab, setTab] = useState('home');
    const [levels, setLevels] = useState(tanks.map(t => t.base));
    const [pumps, setPumps] = useState([true, false, false, false]); // P-101, B-101, P-104, PP-105
    const [valves, setValves] = useState([true, true, false, true, true, false]);
    const [clock, setClock] = useState('');
    const [trendData, setTrendData] = useState({
        influent: Array.from({ length: 20 }, () => 60 + Math.random() * 20),
        effluent: Array.from({ length: 20 }, () => 50 + Math.random() * 20),
        ph: Array.from({ length: 20 }, () => 65 + Math.random() * 15),
    });
    const [alarmAcked, setAlarmAcked] = useState({});
    const [eStopActive, setEStopActive] = useState(false);

    const alarmItems = [
        { id: 'a1', tag: 'HH-101', msg: 'High Level', sev: 'CRITICAL' },
        { id: 'a2', tag: 'P-103', msg: 'Pump Fault', sev: 'WARNING' },
        { id: 'a3', tag: 'CT-103', msg: 'Sludge High', sev: 'WARNING' },
    ];

    const procParams = [
        { tag: 'LT-101', val: `${levels[0].toFixed(0)} %`, status: levels[0] > 80 ? 'High' : levels[0] < 25 ? 'Low' : 'Normal' },
        { tag: 'LT-102', val: `${levels[1].toFixed(0)} %`, status: 'Normal' },
        { tag: 'LT-103', val: `${levels[2].toFixed(0)} %`, status: levels[2] < 30 ? 'Low' : 'Normal' },
        { tag: 'LT-104', val: `${levels[3].toFixed(0)} %`, status: levels[3] > 85 ? 'High' : 'Normal' },
        { tag: 'Flow', val: '125 m³/h', status: 'Normal' },
        { tag: 'pH', val: '7.2', status: 'Normal' },
    ];
    const statCol = s => s === 'High' ? '#f85149' : s === 'Low' ? '#e3b341' : '#3fb950';

    // ── Live clock ──────────────────────────────────────────────
    useEffect(() => {
        const tick = () => {
            const d = new Date();
            const hm = d.toLocaleTimeString('en-GB');
            const dt = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
            setClock(`${hm}  ${dt}`);
        };
        tick();
        const id = setInterval(tick, 1000);
        return () => clearInterval(id);
    }, []);

    // ── Live level & trend updates ──────────────────────────────
    useEffect(() => {
        if (!running || eStopActive) return;
        const id = setInterval(() => {
            setLevels(prev => prev.map((l, i) => {
                let d = (Math.random() - 0.5) * 1.5;
                if (pumps[0] && i === 0) d -= 0.8;
                if (pumps[0] && i === 1) d += 0.6;
                if (pumps[1] && i === 2) d += 0.4;
                if (pumps[2] && i === 3) d += 0.3;
                return +Math.max(5, Math.min(95, l + d)).toFixed(1);
            }));
            setTrendData(prev => ({
                influent: [...prev.influent.slice(1), levels[0] + (Math.random() - 0.5) * 5],
                effluent: [...prev.effluent.slice(1), levels[3] + (Math.random() - 0.5) * 5],
                ph: [...prev.ph.slice(1), 65 + Math.random() * 15],
            }));
        }, 1500);
        return () => clearInterval(id);
    }, [running, eStopActive, pumps]);

    const togglePump = i => setPumps(p => { const n = [...p]; n[i] = !n[i]; return n; });
    const toggleValve = i => setValves(v => { const n = [...v]; n[i] = !n[i]; return n; });

    const runningPumps = pumps.filter(Boolean).length;
    const openValves = valves.filter(Boolean).length;
    const activeAlarms = alarmItems.filter(a => !alarmAcked[a.id]).length;

    // ═══════════════════════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════════════════════
    return (
        <div style={{
            width: '100%', height: '100%', display: 'flex', flexDirection: 'column',
            background: '#0d1117', overflow: 'hidden', fontFamily: 'Inter, sans-serif'
        }}>

            <style>{`
                @keyframes pidSpin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
                @keyframes pulse   { 0%,100%{opacity:1} 50%{opacity:0.3} }
            `}</style>

            {/* ── TOP HEADER ─────────────────────────────────── */}
            <div style={{
                display: 'flex', alignItems: 'center', padding: '8px 16px',
                background: '#111827', borderBottom: '1px solid #30363d', flexShrink: 0, gap: 12
            }}>
                <span style={{
                    fontSize: 11, color: '#58a6ff', fontWeight: 600, border: '1px solid #30363d',
                    padding: '3px 8px', borderRadius: 4, cursor: 'pointer'
                }}>Plant Overview ▹</span>
                <span style={{
                    flex: 1, textAlign: 'center', fontWeight: 800, fontSize: 14,
                    color: '#e6edf3', letterSpacing: '0.1em', textTransform: 'uppercase'
                }}>
                    {layout?.system_name || 'Water / Wastewater Treatment Plant'}
                </span>
                <button onClick={() => setRunning(r => !r)} style={{
                    padding: '4px 12px', borderRadius: 4,
                    border: 'none', fontWeight: 700, fontSize: 11, cursor: 'pointer',
                    background: running ? '#1f6f6a' : '#2ea043', color: '#fff'
                }}>
                    {running ? 'Auto Mode' : 'Start Plant'}
                </button>
                <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#8b949e' }}>{clock}</span>
                <span style={{ fontSize: 16, cursor: 'pointer', position: 'relative' }}>
                    🔔
                    {activeAlarms > 0 && (
                        <span style={{
                            position: 'absolute', top: -4, right: -4, width: 14, height: 14,
                            background: '#f85149', borderRadius: '50%', fontSize: 8, display: 'flex',
                            alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700
                        }}>
                            {activeAlarms}
                        </span>
                    )}
                </span>
                <span style={{ fontSize: 16, cursor: 'pointer' }}>⚙️</span>
            </div>

            {/* ── TANK SUMMARY ROW ────────────────────────────── */}
            <div style={{
                display: 'flex', gap: 8, padding: '8px 16px',
                background: '#111827', borderBottom: '1px solid #30363d', flexShrink: 0
            }}>
                {tanks.map((t, i) => (
                    <motion.div key={t.tag} whileHover={{ scale: 1.03 }}
                        style={{
                            display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px',
                            background: '#1c2333', borderRadius: 8, border: '1px solid #30363d', flex: 1
                        }}>
                        <MiniTank pct={levels[i]} color={lcol(levels[i])} />
                        <div>
                            <div style={{ fontSize: 10, color: '#8b949e', fontWeight: 600 }}>{t.tag}</div>
                            <div style={{
                                fontWeight: 800, fontSize: 16, color: lcol(levels[i]),
                                fontFamily: 'monospace'
                            }}>{levels[i].toFixed(0)}<span style={{ fontSize: 10 }}> %</span></div>
                            <div style={{ fontSize: 9, color: '#8b949e' }}>Level</div>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* ── MAIN BODY ────────────────────────────────────── */}
            <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>

                {/* ── LEFT: Process Flow SVG ─── */}
                <div style={{
                    flex: '0 0 58%', background: '#0f172a',
                    borderRight: '1px solid #30363d', overflow: 'hidden', position: 'relative'
                }}>

                    <svg width="100%" height="100%" viewBox="0 0 620 340"
                        style={{ display: 'block' }}>
                        <defs>
                            <pattern id="wGrid" width="25" height="25" patternUnits="userSpaceOnUse">
                                <path d="M25 0L0 0 0 25" fill="none" stroke="#1e2228" strokeWidth="0.4" />
                            </pattern>
                        </defs>
                        <rect width="620" height="340" fill="url(#wGrid)" />

                        {/* ── Main process pipe (top line) */}
                        <rect x="30" y="138" width="560" height="12" rx="3" fill="#1e3a5f" stroke="#4a90d9" strokeWidth="1" />
                        {/* animated flow when running */}
                        {running && pumps[0] && [60, 100, 140, 180].map((x, i) => (
                            <polygon key={i} points={`${x},141 ${x + 7},144 ${x},147`}
                                fill="#3fb950" opacity="0.9"
                                style={{ animation: `pulse ${0.8 + i * 0.2}s ease-in-out infinite alternate` }} />
                        ))}

                        {/* ── Sludge pipe (bottom return) */}
                        <rect x="220" y="240" width="200" height="8" rx="2" fill="#1a1a2e" stroke="#6e40c9" strokeWidth="1" />

                        {/* ── INFLUENT arrow */}
                        <polygon points="18,140 30,145 18,150" fill="#3fb950" />
                        <text x="4" y="136" fill="#3fb950" fontSize="7" fontWeight="700" fontFamily="monospace">INFLUENT</text>

                        {/* ── Tanks along top pipe */}
                        <CylTank label="IT-101" tag="Influent" pct={Math.round(levels[0])} x={50} y={45} w={60} h={92} accentColor="#2196f3" />
                        <CylTank label="AT-102" tag="Aeration" pct={Math.round(levels[1])} x={185} y={45} w={60} h={92} accentColor="#2f8f83" />
                        <CylTank label="CT-103" tag="Clarifier" pct={Math.round(levels[2])} x={328} y={45} w={55} h={88} accentColor="#9b59b6" />
                        <CylTank label="ET-104" tag="Effluent" pct={Math.round(levels[3])} x={475} y={48} w={58} h={88} accentColor="#27ae60" />

                        {/* Pipes from tanks down to main pipe */}
                        {[80, 215, 355, 504].map((x, i) => (
                            <line key={i} x1={x} y1={137} x2={x} y2={i === 1 ? 145 : 138}
                                stroke="#4a90d9" strokeWidth="2" />
                        ))}

                        {/* ── Pumps */}
                        <PumpSym cx={153} cy={144} r={15} running={pumps[0] && running} label="P-101"
                            onClick={() => togglePump(0)} />
                        <PumpSym cx={295} cy={144} r={15} running={pumps[1] && running} label="B-101"
                            onClick={() => togglePump(1)} />
                        <PumpSym cx={450} cy={144} r={15} running={pumps[2] && running} label="P-104"
                            onClick={() => togglePump(2)} />

                        {/* ── Valves */}
                        <ValveSym cx={115} cy={144} open={valves[0]} label="FV-101" onClick={() => toggleValve(0)} size={11} />
                        <ValveSym cx={255} cy={144} open={valves[1]} label="FV-102" onClick={() => toggleValve(1)} size={11} />
                        <ValveSym cx={410} cy={144} open={valves[2]} label="FV-103" onClick={() => toggleValve(2)} size={11} />

                        {/* ── SUMP tank */}
                        <CylTank label="SUMP-105" tag="Sump" pct={90} x={295} y={220} w={44} h={70} accentColor="#e67e22" />
                        {/* sump pump */}
                        <PumpSym cx={384} cy={255} r={13} running={false} label="PP-103" onClick={() => { }} />
                        <line x1={339} y1={255} x2={371} y2={255} stroke="#6e40c9" strokeWidth="1.5" />

                        {/* ── EFFLUENT arrow */}
                        <polygon points={`590,140 604,144 590,148`} fill="#27ae60" />
                        <text x="592" y="136" fill="#27ae60" fontSize="7" fontWeight="700" fontFamily="monospace">EFFLUENT</text>

                        {/* ── Instrument bubbles - top */}
                        <InstrBubble cx={80} cy={22} tag="LT-101" value={`${levels[0].toFixed(0)}%`} unit="%" pipey={45} alarm={levels[0] > 80} />
                        <InstrBubble cx={215} cy={22} tag="LT-102" value={`${levels[1].toFixed(0)}%`} unit="%" pipey={45} alarm={false} />
                        <InstrBubble cx={355} cy={22} tag="LT-103" value={`${levels[2].toFixed(0)}%`} unit="%" pipey={45} alarm={levels[2] < 25} />
                        <InstrBubble cx={504} cy={22} tag="LT-104" value={`${levels[3].toFixed(0)}%`} unit="%" pipey={48} alarm={levels[3] > 85} />

                        {/* ── HH alarm badge for high tanks */}
                        {levels[0] > 80 && (
                            <g>
                                <circle cx={310} cy={105} r={18} fill="#e3b341" stroke="#e3b341" strokeWidth="1" />
                                <text x={310} y={101} textAnchor="middle" fill="#000" fontSize="8" fontWeight="800">HH</text>
                                <text x={310} y={115} textAnchor="middle" fill="#000" fontSize="9" fontWeight="800">{levels[0].toFixed(0)}%</text>
                            </g>
                        )}

                        {/* Interactive hint */}
                        <text x="310" y="336" textAnchor="middle" fill="#30363d" fontSize="8" fontFamily="monospace">
                            Click pumps/valves to toggle
                        </text>
                    </svg>
                </div>

                {/* ── RIGHT: Status + Alarms ─── */}
                <div style={{
                    flex: 1, display: 'flex', flexDirection: 'column', background: '#111827',
                    padding: '12px', gap: 10, overflowY: 'auto'
                }}>

                    {/* System Status card */}
                    <div style={{
                        background: '#1c2333', borderRadius: 8, padding: '10px 14px',
                        border: '1px solid #30363d'
                    }}>
                        <div style={{
                            fontWeight: 800, fontSize: 12, color: '#e6edf3',
                            marginBottom: 8, letterSpacing: '0.08em'
                        }}>SYSTEM STATUS</div>
                        {[
                            { label: 'Pumps', val: `Running ${runningPumps}/4`, ok: runningPumps > 0 },
                            { label: 'Valves', val: `Open ${openValves}/6`, ok: openValves >= 4 },
                            { label: 'Power', val: 'Normal', ok: true },
                        ].map(r => (
                            <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                <div style={{
                                    width: 8, height: 8, borderRadius: '50%',
                                    background: r.ok ? '#3fb950' : '#f85149',
                                    boxShadow: r.ok ? '0 0 6px #3fb950' : '0 0 6px #f85149'
                                }} />
                                <span style={{ fontSize: 11, color: '#8b949e', flex: 1 }}>{r.label}</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color: r.ok ? '#3fb950' : '#f85149' }}>{r.val}</span>
                            </div>
                        ))}
                    </div>

                    {/* Alarms card */}
                    <div style={{
                        background: '#1c1010', borderRadius: 8, padding: '10px 14px',
                        border: '1px solid #6e2020', flex: 1
                    }}>
                        <div style={{
                            fontWeight: 800, fontSize: 12, color: '#f85149',
                            marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6
                        }}>
                            <span style={{
                                width: 7, height: 7, borderRadius: '50%', background: '#f85149', display: 'inline-block',
                                animation: activeAlarms > 0 ? 'pulse 1s step-end infinite' : 'none'
                            }} />
                            ALARMS
                        </div>
                        {alarmItems.map(a => {
                            const acked = alarmAcked[a.id];
                            const col = a.sev === 'CRITICAL' ? '#f85149' : '#e3b341';
                            return (
                                <div key={a.id} style={{
                                    display: 'flex', alignItems: 'center', gap: 6,
                                    padding: '5px 6px', marginBottom: 3, borderRadius: 4,
                                    background: acked ? 'rgba(0,0,0,0.2)' : `${col}14`,
                                    borderLeft: `3px solid ${acked ? '#30363d' : col}`,
                                    opacity: acked ? 0.5 : 1
                                }}>
                                    <span style={{ fontSize: 11 }}>{a.sev === 'CRITICAL' ? '🔺' : '⚠️'}</span>
                                    <span style={{ flex: 1, fontSize: 11, color: acked ? '#8b949e' : col, fontWeight: 600 }}>
                                        {a.tag} {a.msg}
                                    </span>
                                </div>
                            );
                        })}
                        <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                            <button style={{
                                flex: 1, padding: '5px', borderRadius: 4, border: '1px solid #30363d',
                                background: '#1c2333', color: '#8b949e', fontSize: 10, cursor: 'pointer', fontWeight: 600
                            }}
                                onClick={() => {
                                    const obj = {};
                                    alarmItems.forEach(a => { obj[a.id] = true; });
                                    setAlarmAcked(obj);
                                }}>Acknowledge</button>
                            <button style={{
                                flex: 1, padding: '5px', borderRadius: 4, border: '1px solid #30363d',
                                background: '#1c2333', color: '#8b949e', fontSize: 10, cursor: 'pointer', fontWeight: 600
                            }}>
                                Silence
                            </button>
                        </div>
                    </div>

                    {/* E-Stop */}
                    <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
                        onClick={() => { setEStopActive(e => !e); if (!eStopActive) setRunning(false); }}
                        style={{
                            padding: '10px', borderRadius: 8, border: 'none', cursor: 'pointer',
                            background: eStopActive ? '#6e0c0c' : '#da3633', color: '#fff',
                            fontWeight: 900, fontSize: 13, letterSpacing: '0.08em',
                            boxShadow: eStopActive ? '0 0 20px rgba(218,54,51,0.8)' : '0 0 10px rgba(218,54,51,0.4)'
                        }}>
                        {eStopActive ? '⚠ E-STOP ACTIVE — RESET' : '🔴 E-STOP'}
                    </motion.button>
                </div>
            </div>

            {/* ── BOTTOM: Params + Trend ────────────────────────── */}
            <div style={{
                display: 'flex', borderTop: '1px solid #30363d', background: '#111827',
                flexShrink: 0, maxHeight: 180
            }}>

                {/* Process Parameters table */}
                <div style={{
                    flex: '0 0 220px', borderRight: '1px solid #30363d', padding: '8px 12px',
                    overflowY: 'auto'
                }}>
                    <div style={{
                        fontWeight: 700, fontSize: 10, color: '#8b949e', letterSpacing: '0.12em',
                        marginBottom: 6, textTransform: 'uppercase'
                    }}>Process Parameters</div>
                    <div style={{
                        display: 'grid', gridTemplateColumns: '80px 60px 60px',
                        gap: 1, fontSize: 10
                    }}>
                        {['Tag', 'Value', 'Status'].map(h => (
                            <div key={h} style={{
                                color: '#8b949e', fontWeight: 700, padding: '3px 4px',
                                borderBottom: '1px solid #30363d'
                            }}>{h}</div>
                        ))}
                        {procParams.map(p => (
                            <React.Fragment key={p.tag}>
                                <div style={{ color: '#58a6ff', padding: '3px 4px', fontFamily: 'monospace' }}>{p.tag}</div>
                                <div style={{ color: '#e6edf3', padding: '3px 4px', fontWeight: 700, fontFamily: 'monospace' }}>{p.val}</div>
                                <div style={{ color: statCol(p.status), padding: '3px 4px', fontWeight: 600 }}>
                                    ● {p.status}
                                </div>
                            </React.Fragment>
                        ))}
                    </div>
                </div>

                {/* Trend chart */}
                <div style={{ flex: 1, padding: '8px 14px', minWidth: 0 }}>
                    <div style={{
                        fontWeight: 700, fontSize: 10, color: '#8b949e', letterSpacing: '0.12em',
                        marginBottom: 4, textTransform: 'uppercase', display: 'flex', gap: 14
                    }}>
                        <span>Trends</span>
                        {[['Influent', '#2196f3'], ['Effluent', '#27ae60'], ['pH', '#e3b341']].map(([l, c]) => (
                            <span key={l} style={{ color: c, fontWeight: 600 }}>● {l}</span>
                        ))}
                    </div>
                    <svg width="100%" height="100" viewBox="0 0 400 100" preserveAspectRatio="none">
                        {/* Y-axis gridlines */}
                        {[0, 25, 50, 75, 100].map(y => (
                            <React.Fragment key={y}>
                                <line x1="0" y1={y} x2="400" y2={y} stroke="#1e2228" strokeWidth="0.5" />
                                <text x="2" y={y - 2} fill="#484f58" fontSize="6" fontFamily="monospace">{100 - y}</text>
                            </React.Fragment>
                        ))}
                        <SparkLine data={trendData.influent} color="#2196f3" h={100} w={400} />
                        <SparkLine data={trendData.effluent} color="#27ae60" h={100} w={400} />
                        <SparkLine data={trendData.ph} color="#e3b341" h={100} w={400} yMin={60} yMax={80} />
                    </svg>
                </div>
            </div>

            {/* ── BOTTOM TABS ───────────────────────────────────── */}
            <div style={{ display: 'flex', background: '#0d1117', borderTop: '1px solid #30363d', flexShrink: 0 }}>
                {['Home', 'Process', 'Alarms', 'Trends', 'Reports'].map(t => (
                    <button key={t} onClick={() => setTab(t.toLowerCase())} style={{
                        flex: 1, padding: '10px', border: 'none', cursor: 'pointer',
                        fontWeight: 700, fontSize: 11, letterSpacing: '0.06em',
                        background: tab === t.toLowerCase() ? '#2f8f83' : 'transparent',
                        color: tab === t.toLowerCase() ? '#fff' : '#8b949e',
                        borderTop: tab === t.toLowerCase() ? '2px solid #3fb950' : '2px solid transparent',
                        transition: 'all 0.2s',
                    }}>{t}</button>
                ))}
            </div>
        </div>
    );
}
