/**
 * DashboardRenderer.jsx
 *
 * Universal HMI Symbol Engine - INDUSTRY READY VERSION
 * Clean, professional symbols with clear labels and names
 * AI returns: { title, theme, components:[{id,type,label,x,y,state,value}] }
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import useMachineState from './useMachineState';

// ─── Inject keyframe animations once ─────────────────────────────────────────
if (!document.getElementById('_hmi_kf')) {
    const s = document.createElement('style');
    s.id = '_hmi_kf';
    s.textContent = `
        @keyframes hmiSpin  { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes hmiBlink { 0%,100%{opacity:1} 50%{opacity:0.15} }
        @keyframes hmiPulse { 0%,100%{box-shadow:0 0 4px 2px #f85149aa} 50%{box-shadow:0 0 18px 6px #f85149} }
        @keyframes hmiFlow  { to{stroke-dashoffset:-30} }
        @keyframes alarmPulse { 
            0%,100%{opacity:1;transform:scale(1)} 
            50%{opacity:0.7;transform:scale(1.05)} 
        }
    `;
    document.head.appendChild(s);
}

// ─── Colour helpers ───────────────────────────────────────────────────────────
const vCol = v => v > 80 ? '#e74c3c' : v < 25 ? '#f39c12' : '#2ecc71';
const sCol = s =>
    ['running', 'open', 'active'].includes(s) ? '#2ecc71' :
        ['stopped', 'closed', 'fault'].includes(s) ? '#e74c3c' :
            ['partial', 'warning', 'ack'].includes(s) ? '#f39c12' : '#7f8c8d';

const toNum = (value) => (typeof value === 'number' && !Number.isNaN(value) ? value : 0);

const useCanvasSize = (ref) => {
    const [size, setSize] = useState({ width: 1200, height: 700 });

    useEffect(() => {
        if (!ref.current || typeof ResizeObserver === 'undefined') return;
        const observer = new ResizeObserver((entries) => {
            const entry = entries[0];
            if (!entry?.contentRect) return;
            const next = {
                width: Math.max(600, Math.round(entry.contentRect.width)),
                height: Math.max(400, Math.round(entry.contentRect.height))
            };
            setSize(next);
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

    const sizeFor = (type) => {
        switch (type) {
            case 'tank': return { w: 110, h: 170 };
            case 'motor': return { w: 90, h: 110 };
            case 'pump': return { w: 90, h: 110 };
            case 'fan': return { w: 90, h: 110 };
            case 'compressor': return { w: 90, h: 110 };
            case 'valve': return { w: 80, h: 90 };
            case 'gauge': return { w: 110, h: 110 };
            case 'alarm': return { w: 200, h: 70 };
            case 'button': return { w: 120, h: 50 };
            case 'slider': return { w: 140, h: 80 };
            default:
                if ((type || '').startsWith('sensor')) return { w: 90, h: 90 };
                return { w: 100, h: 80 };
        }
    };

    const boxes = components.map((c) => {
        const size = sizeFor(c.type);
        return {
            x: toNum(c.x),
            y: toNum(c.y),
            w: size.w,
            h: size.h
        };
    });

    const hasOverlap = (() => {
        for (let i = 0; i < boxes.length; i++) {
            for (let j = i + 1; j < boxes.length; j++) {
                const a = boxes[i];
                const b = boxes[j];
                const overlap = a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
                if (overlap) return true;
            }
        }
        return false;
    })();

    const mean = (arr) => arr.reduce((s, v) => s + v, 0) / (arr.length || 1);
    const std = (arr) => {
        const m = mean(arr);
        return Math.sqrt(mean(arr.map((v) => (v - m) ** 2)));
    };

    const lowVariance = std(xs) < 60 || std(ys) < 60;
    const needsAutoLayout = hasOverlap || lowVariance || rangeX < 260 || rangeY < 220;
    if (!needsAutoLayout) return components;

    const width = Math.max(900, canvasSize?.width || 1200);
    const topY = 70;
    const rowGap = 170;
    const midY = topY + rowGap;
    const lowY = midY + rowGap;
    const leftColX = 70;
    const rightColX = width - 160;

    const isAlarm = (c) => c.type === 'alarm';
    const isControl = (c) => c.type === 'button' || c.type === 'slider';
    const isInstrument = (c) => c.type === 'gauge' || (c.type || '').startsWith('sensor');
    const isEquipment = (c) => !isAlarm(c) && !isControl(c) && !isInstrument(c);

    const alarms = components.filter(isAlarm);
    const controls = components.filter(isControl);
    const instruments = components.filter(isInstrument);
    const equipment = components.filter(isEquipment);

    const next = components.map((c) => ({ ...c }));
    const setPos = (component, x, y) => {
        const idx = components.indexOf(component);
        if (idx >= 0) next[idx] = { ...next[idx], x, y };
    };

    const placeRow = (items, y, spacing = 160) => {
        if (!items.length) return;
        const span = Math.max(1, items.length - 1);
        const total = span * spacing;
        const startX = Math.max(140, (width - total) / 2);
        items.forEach((item, index) => setPos(item, startX + index * spacing, y));
    };

    placeRow(instruments, topY);
    placeRow(equipment, midY);
    placeRow(components.filter((c) => !isAlarm(c) && !isControl(c) && !isInstrument(c) && !isEquipment(c)), lowY);

    alarms.forEach((item, index) => setPos(item, leftColX, topY + index * 70));
    controls.forEach((item, index) => setPos(item, rightColX, topY + index * 70));

    return next;
};

// ═══════════════════════════════════════════════════════════════════════════════
// INDUSTRY READY SYMBOL LIBRARY - Clean, Professional Design
// ═══════════════════════════════════════════════════════════════════════════════

// ── TANK ─────────────────────────────────────────────────────────────────────
function HMI_Tank({ c, running }) {
    const [lv, setLv] = useState(+(c.value ?? 65));
    useEffect(() => {
        if (!running) return;
        const id = setInterval(() =>
            setLv(v => +Math.max(5, Math.min(95, v + (Math.random() - 0.5) * 2.2)).toFixed(1)), 1800);
        return () => clearInterval(id);
    }, [running]);
    const col = vCol(lv);
    const tW = 80, tH = 130, eRY = 10;
    const fH = (tH - 2 * eRY) * Math.max(0.03, lv / 100);
    const fY = eRY + (tH - 2 * eRY) * (1 - lv / 100);
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
            <svg width={tW} height={tH + 28} viewBox={`0 0 ${tW} ${tH + 28}`}>
                {/* Tank body with professional styling */}
                <rect x={0} y={eRY} width={tW} height={tH - 2 * eRY} fill="#0a1628" stroke="#4a90d9" strokeWidth="2" rx="4" />
                {/* Liquid fill */}
                <clipPath id={`tc_${c.id}`}><rect x={0} y={eRY} width={tW} height={tH - 2 * eRY} rx="4" /></clipPath>
                <rect x={0} y={fY} width={tW} height={fH} fill={col} opacity="0.8"
                    clipPath={`url(#tc_${c.id})`} style={{ transition: 'y 0.9s,height 0.9s,fill 0.4s' }} />
                {/* Top ellipse */}
                <ellipse cx={tW / 2} cy={eRY} rx={tW / 2} ry={eRY} fill="#0d2040" stroke="#4a90d9" strokeWidth="2" />
                {/* Bottom ellipse */}
                <ellipse cx={tW / 2} cy={tH - eRY} rx={tW / 2} ry={eRY} fill={col} opacity={lv > 5 ? 0.6 : 0} />
                {/* High level indicator */}
                {lv > 80 && <ellipse cx={tW / 2} cy={eRY * 2.2} rx={tW / 2 - 2} ry={eRY * 0.7}
                    fill="none" stroke="#e74c3c" strokeWidth="2" strokeDasharray="4,2" />}
                {/* Level percentage */}
                <text x={tW / 2} y={tH / 2 + 5} textAnchor="middle" fill="#fff"
                    fontSize="14" fontWeight="800" fontFamily="monospace">{lv.toFixed(0)}%</text>
            </svg>
            {/* Clean label below - industry standard */}
            <div style={{ 
                color: '#e6edf3', 
                fontSize: 11, 
                fontWeight: 700, 
                fontFamily: 'monospace',
                marginTop: 6,
                padding: '2px 8px',
                background: 'rgba(30,58,95,0.6)',
                borderRadius: 4,
                border: '1px solid #1e3a5f'
            }}>
                {c.label}
            </div>
        </div>
    );
}

// ── PUMP ─────────────────────────────────────────────────────────────────────
function HMI_Pump({ c, running }) {
    const [on, setOn] = useState(c.state === 'running');
    useEffect(() => { if (!running) setOn(false); }, [running]);
    const col = on && running ? '#2ecc71' : '#e74c3c';
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
            onClick={() => running && setOn(p => !p)}>
            <svg width="64" height="64" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r="28" fill={on ? '#0c3020' : '#1c2030'} stroke={col} strokeWidth="2"
                    style={{ filter: on && running ? `drop-shadow(0 0 6px ${col}88)` : 'none' }} />
                {[0, 60, 120, 180, 240, 300].map(a => (
                    <line key={a} x1="32" y1="32"
                        x2={32 + 20 * Math.cos(a * Math.PI / 180)}
                        y2={32 + 20 * Math.sin(a * Math.PI / 180)}
                        stroke={col} strokeWidth="2"
                        style={{
                            transformOrigin: '32px 32px',
                            animation: on && running ? 'hmiSpin 1.1s linear infinite' : 'none'
                        }} />
                ))}
                <circle cx="32" cy="32" r="5" fill={col} />
            </svg>
            <div style={{ color: '#e6edf3', fontSize: 10, fontWeight: 700, fontFamily: 'monospace' }}>{c.label}</div>
            <div style={{
                fontSize: 9, fontWeight: 700, color: col, fontFamily: 'monospace',
                animation: on && running ? 'none' : 'none'
            }}>
                {on && running ? 'RUNNING' : 'STOPPED'}
            </div>
        </div>
    );
}

// ── FAN ──────────────────────────────────────────────────────────────────────
function HMI_Fan({ c, running }) {
    const [on, setOn] = useState(c.state === 'running');
    useEffect(() => { if (!running) setOn(false); }, [running]);
    const col = on && running ? '#2ecc71' : '#7f8c8d';
    const spd = (c.value ?? 60) > 70 ? 0.7 : 1.2;
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
            onClick={() => running && setOn(p => !p)}>
            <svg width="72" height="72" viewBox="0 0 72 72">
                <circle cx="36" cy="36" r="32" fill="#0a1628" stroke="#4a90d9" strokeWidth="1.5" />
                {[0, 90, 180, 270].map(a => (
                    <ellipse key={a} cx="36" cy="16" rx="9" ry="16" fill={col} opacity="0.88"
                        style={{
                            transformOrigin: '36px 36px', transform: `rotate(${a}deg)`,
                            animation: on && running ? `hmiSpin ${spd}s linear infinite` : 'none'
                        }} />
                ))}
                <circle cx="36" cy="36" r="7" fill="#0d1117" stroke={col} strokeWidth="2" />
                <circle cx="36" cy="36" r="3" fill={col} />
            </svg>
            <div style={{ color: '#e6edf3', fontSize: 10, fontWeight: 700, fontFamily: 'monospace' }}>{c.label}</div>
            <div style={{ fontSize: 9, fontWeight: 700, color: col, fontFamily: 'monospace' }}>
                {on && running ? `${c.value ?? 50} Hz` : 'OFF'}
            </div>
        </div>
    );
}

// ── MOTOR ────────────────────────────────────────────────────────────────────
function HMI_Motor({ c, running }) {
    const [on, setOn] = useState(c.state === 'running');
    const [rpm, setRpm] = useState(+(c.value ?? 1450));
    useEffect(() => { if (!running) { setOn(false); setRpm(0); } }, [running]);
    useEffect(() => {
        if (!on || !running) return;
        const base = +(c.value ?? 1450);
        const id = setInterval(() => setRpm(+(base * (0.92 + Math.random() * 0.1)).toFixed(0)), 1500);
        return () => clearInterval(id);
    }, [on, running]);
    const col = on && running ? '#2ecc71' : '#e74c3c';
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
            onClick={() => running && setOn(p => !p)}>
            <div style={{
                width: 72, height: 62, background: '#0d2040', border: `2px solid ${col}`, borderRadius: 8,
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
                boxShadow: on && running ? `0 0 14px ${col}55` : 'none', transition: 'all 0.3s'
            }}>
                <span style={{
                    fontSize: 16, fontWeight: 900, color: col, fontFamily: 'monospace',
                    display: 'inline-block',
                    animation: on && running ? 'hmiSpin 2.5s linear infinite' : 'none'
                }}>M</span>
                <span style={{ fontSize: 9, color: '#e6edf3', fontFamily: 'monospace' }}>
                    {on && running ? `${Math.round(rpm)} RPM` : '0 RPM'}
                </span>
            </div>
            <div style={{ color: '#e6edf3', fontSize: 10, fontWeight: 700, fontFamily: 'monospace', marginTop: 4 }}>{c.label}</div>
            <div style={{ fontSize: 9, fontWeight: 700, color: col, fontFamily: 'monospace' }}>
                {on && running ? 'RUNNING' : 'STOPPED'}
            </div>
        </div>
    );
}

// ── COMPRESSOR ───────────────────────────────────────────────────────────────
function HMI_Compressor({ c, running }) {
    const [on, setOn] = useState(c.state === 'running');
    useEffect(() => { if (!running) setOn(false); }, [running]);
    const col = on && running ? '#2ecc71' : '#e74c3c';
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
            onClick={() => running && setOn(p => !p)}>
            <svg width="70" height="70" viewBox="0 0 70 70">
                <rect x="5" y="5" width="60" height="60" rx="6" fill="#0d2040" stroke={col} strokeWidth="2" />
                <ellipse cx="35" cy="35" rx="20" ry="20" fill="none" stroke={col} strokeWidth="1.5"
                    strokeDasharray="5,3"
                    style={{
                        transformOrigin: '35px 35px',
                        animation: on && running ? 'hmiSpin 2s linear infinite' : 'none'
                    }} />
                <text x="35" y="40" textAnchor="middle" fill={col}
                    fontSize="18" fontWeight="900" fontFamily="monospace">C</text>
            </svg>
            <div style={{ color: '#e6edf3', fontSize: 10, fontWeight: 700, fontFamily: 'monospace' }}>{c.label}</div>
            <div style={{ fontSize: 9, fontWeight: 700, color: col, fontFamily: 'monospace' }}>
                {on && running ? `${c.value ?? 8} bar` : 'STOPPED'}
            </div>
        </div>
    );
}

// ── VALVE ────────────────────────────────────────────────────────────────────
function HMI_Valve({ c, running }) {
    const [st, setSt] = useState(c.state || 'closed');
    const col = sCol(st);
    const sz = 13;
    const cycle = ['open', 'partial', 'closed'];
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
            onClick={() => running && setSt(s => cycle[(cycle.indexOf(s) + 1) % cycle.length])}>
            <svg width={sz * 3.2} height={sz * 3.2 + 20} viewBox={`0 0 ${sz * 3.2} ${sz * 3.2 + 20}`}>
                <polygon points={`${sz * 0.3},${sz} ${sz * 1.6},${sz * 1.6} ${sz * 0.3},${sz * 2.2}`}
                    fill="none" stroke={col} strokeWidth="2" />
                <polygon points={`${sz * 2.9},${sz} ${sz * 1.6},${sz * 1.6} ${sz * 2.9},${sz * 2.2}`}
                    fill="none" stroke={col} strokeWidth="2" />
                <line x1={sz * 1.6} y1={sz} x2={sz * 1.6} y2={sz * 0.2} stroke={col} strokeWidth="2" />
                <rect x={sz * 1.1} y={0} width={sz * 1} height={sz * 0.25} rx="2"
                    fill={col} opacity="0.5" />
                <text x={sz * 1.6} y={sz * 3.2 + 14} textAnchor="middle"
                    fill={col} fontSize="9" fontFamily="monospace" fontWeight="700">{c.label}</text>
                <text x={sz * 1.6} y={sz * 3.2 + 4} textAnchor="middle"
                    fill={col} fontSize="8" fontFamily="monospace">{st.toUpperCase()}</text>
            </svg>
        </div>
    );
}

// ── ALARM ────────────────────────────────────────────────────────────────────
function HMI_Alarm({ c }) {
    const [acked, setAcked] = useState(false);
    // Only blink when alarm is ACTIVE - fixed issue with constant blinking
    const alarmState = c.state || 'inactive';
    const col = alarmState === 'active' ? '#e74c3c' : alarmState === 'warning' ? '#f39c12' : '#2ecc71';
    return (
        <div style={{
            position: 'absolute', left: c.x, top: c.y, display: 'flex', alignItems: 'center',
            gap: 8, padding: '7px 14px', background: `${col}22`,
            border: `1.5px solid ${acked ? '#333' : col}`, borderRadius: 6,
            cursor: 'pointer', opacity: acked ? 0.45 : 1, minWidth: 180,
            zIndex: 50,
            // FIXED: Only apply animation when alarm is active and not acknowledged
            animation: !acked && alarmState === 'active' ? 'alarmPulse 1.5s ease-in-out 2' : 'none'
        }}
            onClick={() => setAcked(p => !p)}>
            <span style={{ fontSize: 14 }}>
                {alarmState === 'active' ? '🔺' : alarmState === 'warning' ? '⚠️' : '✅'}
            </span>
            <div style={{ flex: 1 }}>
                <div style={{
                    color: acked ? '#555' : col, fontWeight: 700, fontSize: 11,
                    fontFamily: 'monospace', letterSpacing: '0.04em'
                }}>{c.label}</div>
                {!acked && <div style={{ color: acked ? '#555' : col, fontSize: 9, fontFamily: 'monospace' }}>
                    {alarmState.toUpperCase()} — Click to ACK
                </div>}
            </div>
        </div>
    );
}

// ── GAUGE (SVG arc) ──────────────────────────────────────────────────────────
function HMI_Gauge({ c, running }) {
    const [val, setVal] = useState(+(c.value ?? 50));
    useEffect(() => {
        if (!running) return;
        const base = +(c.value ?? 50);
        const id = setInterval(() =>
            setVal(+(base * (0.88 + Math.random() * 0.24)).toFixed(1)), 2000);
        return () => clearInterval(id);
    }, [running]);
    const mx = c.max ?? 100;
    const col = vCol(val / mx * 100);
    const R = 34, cx = 45, cy = 48;
    const sA = -220, sweep = 260;
    const pct = Math.min(1, Math.max(0, val / mx));
    const eA = sA + pct * sweep;
    const arc = (a) => ({ x: cx + R * Math.cos(a * Math.PI / 180), y: cy + R * Math.sin(a * Math.PI / 180) });
    const d = (end) => {
        const s = arc(sA), e = arc(end);
        return `M ${s.x} ${s.y} A ${R} ${R} 0 ${pct * sweep > 180 ? 1 : 0} 1 ${e.x} ${e.y}`;
    };
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <svg width="90" height="84" viewBox="0 0 90 84">
                <path d={d(sA + sweep)} fill="none" stroke="#1e2228" strokeWidth="8" strokeLinecap="round" />
                <path d={d(eA)} fill="none" stroke={col} strokeWidth="8" strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 3px ${col}88)`, transition: 'all 0.5s' }} />
                <line x1={cx} y1={cy}
                    x2={cx + 26 * Math.cos(eA * Math.PI / 180)}
                    y2={cy + 26 * Math.sin(eA * Math.PI / 180)}
                    stroke="#e6edf3" strokeWidth="1.5" strokeLinecap="round" />
                <circle cx={cx} cy={cy} r="4" fill="#e6edf3" />
                <text x={cx} y={cy + 14} textAnchor="middle" fill={col}
                    fontSize="13" fontWeight="800" fontFamily="monospace">{val.toFixed(0)}</text>
                {c.unit && <text x={cx} y={cy + 26} textAnchor="middle" fill="#8b949e"
                    fontSize="8" fontFamily="monospace">{c.unit}</text>}
            </svg>
            <div style={{
                color: '#8b949e', fontSize: 9, fontFamily: 'monospace',
                marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.08em',
                whiteSpace: 'nowrap'
            }}>{c.label}</div>
        </div>
    );
}

// ── SLIDER ───────────────────────────────────────────────────────────────────
function HMI_Slider({ c }) {
    const [val, setVal] = useState(+(c.value ?? 50));
    const col = '#2f8f83';
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, minWidth: 130 }}>
            <div style={{ color: '#8b949e', fontSize: 9, fontFamily: 'monospace', marginBottom: 3 }}>{c.label}</div>
            <input type="range" min={c.min ?? 0} max={c.max ?? 100} value={val}
                onChange={e => setVal(+e.target.value)}
                style={{ width: '100%', accentColor: col }} />
            <div style={{
                color: col, fontSize: 14, fontWeight: 800, fontFamily: 'monospace',
                textAlign: 'right'
            }}>{val} {c.unit || '%'}</div>
        </div>
    );
}

// ── BUTTON ───────────────────────────────────────────────────────────────────
const getButtonCommand = (label = '') => {
    const text = String(label).toLowerCase();
    if (text.includes('e-stop') || text.includes('estop') || text.includes('emergency')) return 'estop';
    if (text.includes('reset')) return 'reset';
    if (text.includes('stop') || text.includes('halt') || text.includes('off')) return 'stop';
    if (text.includes('start') || text.includes('run') || text.includes('on')) return 'start';
    return null;
};

function HMI_Button({ c, machineState, onCommand }) {
    const [active, setActive] = useState(c.state === 'active');
    const cmd = getButtonCommand(c.label);
    const isStart = cmd === 'start';
    const isStop = cmd === 'stop';
    const isEstop = cmd === 'estop';
    const isReset = cmd === 'reset';

    const derivedActive = isStart ? !!machineState?.running
        : isStop ? !machineState?.running
            : isEstop ? !!machineState?.estop
                : isReset ? false
                    : active;

    const col = isStart ? '#238636'
        : isStop ? '#da3633'
            : isEstop ? '#f59e0b'
                : '#1f6feb';

    const disabled = isStart && machineState?.estop;

    const handleClick = () => {
        if (disabled) return;
        if (cmd && onCommand) {
            onCommand(cmd);
            return;
        }
        setActive((prev) => !prev);
    };

    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y }}>
            <button onClick={handleClick} disabled={disabled} style={{
                padding: '9px 18px', borderRadius: 6,
                border: `1px solid ${derivedActive ? col : '#30363d'}`, cursor: disabled ? 'not-allowed' : 'pointer',
                fontWeight: 700, fontSize: 11, letterSpacing: '0.06em',
                background: derivedActive ? col : '#1c2333', color: derivedActive ? '#fff' : '#8b949e',
                boxShadow: derivedActive ? `0 0 12px ${col}77` : 'none', transition: 'all 0.2s',
                opacity: disabled ? 0.5 : 1
            }}>
                {c.label}
            </button>
        </div>
    );
}

// ── SENSOR_LEVEL (vertical bar) ───────────────────────────────────────────────
function HMI_SensorLevel({ c, running }) {
    const [val, setVal] = useState(+(c.value ?? 60));
    useEffect(() => {
        if (!running) return;
        const id = setInterval(() =>
            setVal(v => +Math.max(0, Math.min(100, v + (Math.random() - 0.5) * 3)).toFixed(1)), 1800);
        return () => clearInterval(id);
    }, [running]);
    const col = vCol(val);
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
            <div style={{
                fontSize: 9, color: '#8b949e', fontFamily: 'monospace',
                letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 3
            }}>{c.label}</div>
            <div style={{
                position: 'relative', width: 22, height: 80, background: '#1e2228',
                borderRadius: 4, margin: '0 auto', overflow: 'hidden', border: '1px solid #30363d'
            }}>
                <div style={{
                    position: 'absolute', bottom: 0, left: 0, right: 0,
                    height: `${val}%`, background: col, transition: 'height 0.8s,background 0.4s'
                }} />
            </div>
            <div style={{
                color: col, fontSize: 11, fontWeight: 800,
                fontFamily: 'monospace', marginTop: 3
            }}>{val.toFixed(0)}%</div>
        </div>
    );
}

// ── SENSOR_PRESSURE ───────────────────────────────────────────────────────────
function HMI_SensorPressure({ c, running }) {
    const [val, setVal] = useState(+(c.value ?? 4));
    useEffect(() => {
        if (!running) return;
        const base = +(c.value ?? 4);
        const id = setInterval(() =>
            setVal(+(base * (0.88 + Math.random() * 0.24)).toFixed(2)), 2000);
        return () => clearInterval(id);
    }, [running]);
    const col = val > (c.max ?? 10) * 0.8 ? '#e74c3c' : '#4a90d9';
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
            <svg width="60" height="60" viewBox="0 0 60 60">
                <circle cx="30" cy="30" r="27" fill="#0d2040" stroke={col} strokeWidth="1.5"
                    style={{ filter: `drop-shadow(0 0 4px ${col}66)` }} />
                <text x="30" y="27" textAnchor="middle" fill={col}
                    fontSize="12" fontWeight="800" fontFamily="monospace">{val.toFixed(1)}</text>
                <text x="30" y="38" textAnchor="middle" fill="#8b949e"
                    fontSize="8" fontFamily="monospace">{c.unit || 'bar'}</text>
            </svg>
            <div style={{
                color: '#8b949e', fontSize: 8, fontFamily: 'monospace',
                textTransform: 'uppercase', marginTop: 2
            }}>{c.label}</div>
        </div>
    );
}

// ── SENSOR_TEMP ───────────────────────────────────────────────────────────────
function HMI_SensorTemp({ c, running }) {
    const [val, setVal] = useState(+(c.value ?? 25));
    useEffect(() => {
        if (!running) return;
        const base = +(c.value ?? 25);
        const id = setInterval(() =>
            setVal(+(base + (Math.random() - 0.5) * 3).toFixed(1)), 2000);
        return () => clearInterval(id);
    }, [running]);
    const col = val > 80 ? '#e74c3c' : val > 50 ? '#f39c12' : '#4a90d9';
    return (
        <div data-interactive="true" style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
            <div style={{
                width: 44, background: '#0d2040', border: `2px solid ${col}`, borderRadius: 8,
                padding: '6px 4px', boxShadow: val > 80 ? `0 0 12px ${col}66` : 'none'
            }}>
                <div style={{ color: col, fontSize: 13, fontWeight: 900, fontFamily: 'monospace' }}>{val.toFixed(0)}</div>
                <div style={{ color: '#8b949e', fontSize: 8, fontFamily: 'monospace' }}>°C</div>
            </div>
            <div style={{
                color: '#8b949e', fontSize: 8, fontFamily: 'monospace',
                marginTop: 3, textTransform: 'uppercase'
            }}>{c.label}</div>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SYMBOL ROUTER — AI decides type, this renders it
// ═══════════════════════════════════════════════════════════════════════════════
function HMISymbol({ c, running, machineState, onCommand }) {
    const p = { c, running };
    switch (c.type) {
        case 'tank': return <HMI_Tank            {...p} />;
        case 'pump': return <HMI_Pump            {...p} />;
        case 'fan': return <HMI_Fan             {...p} />;
        case 'motor': return <HMI_Motor           {...p} />;
        case 'compressor': return <HMI_Compressor      {...p} />;
        case 'valve': return <HMI_Valve           {...p} />;
        case 'alarm': return <HMI_Alarm c={c} />;
        case 'gauge': return <HMI_Gauge           {...p} />;
        case 'slider': return <HMI_Slider c={c} />;
        case 'button': return <HMI_Button c={c} machineState={machineState} onCommand={onCommand} />;
        case 'sensor_level': return <HMI_SensorLevel     {...p} />;
        case 'sensor_pressure': return <HMI_SensorPressure  {...p} />;
        case 'sensor_temp': return <HMI_SensorTemp      {...p} />;
        default:
            return (
                <div style={{
                    position: 'absolute', left: c.x, top: c.y, padding: '5px 10px',
                    background: '#1c2333', border: '1px solid #30363d', borderRadius: 4,
                    color: '#8b949e', fontSize: 9, fontFamily: 'monospace'
                }}>
                    [{c.type}] {c.label}
                </div>
            );
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DEFAULT VIEW (shown before first generation)
// ═══════════════════════════════════════════════════════════════════════════════
function DefaultHMI() {
    const syms = [
        { x: 120, type: 'tank', ic: '💧', label: 'Tank' },
        { x: 260, type: 'pump', ic: '⚙️', label: 'Pump' },
        { x: 400, type: 'fan', ic: '🌀', label: 'Fan' },
        { x: 540, type: 'alarm', ic: '🔺', label: 'Alarm' },
        { x: 680, type: 'gauge', ic: '📊', label: 'Gauge' },
    ];
    return (
        <div style={{
            width: '100%', height: '100%', display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: 28, background: '#0d1117'
        }}>
            <div style={{ display: 'flex', gap: 0 }}>
                {syms.map((s, i) => (
                    <div key={i} style={{
                        textAlign: 'center', padding: '0 20px',
                        borderRight: i < syms.length - 1 ? '1px solid #30363d' : 'none'
                    }}>
                        <div style={{ fontSize: 32, marginBottom: 6 }}>{s.ic}</div>
                        <div style={{
                            fontSize: 9, color: '#8b949e', fontFamily: 'monospace',
                            letterSpacing: '0.1em', textTransform: 'uppercase'
                        }}>{s.label}</div>
                    </div>
                ))}
            </div>
            <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#e6edf3', fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
                    HMI Canvas Ready
                </div>
                <div style={{ color: '#8b949e', fontSize: 12, maxWidth: 340, lineHeight: 1.6 }}>
                    Type any process description and click Generate.<br />
                    The AI picks the right equipment — different prompt, different visual.
                </div>
            </div>
            <div style={{
                display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center',
                maxWidth: 500
            }}>
                {['Water Treatment Plant', 'Fan & HVAC System', 'Motor Drive Control',
                    'Alarm & Event Logs', 'Compressor Station'].map(ex => (
                        <div key={ex} style={{
                            padding: '5px 12px', background: '#1c2333',
                            border: '1px solid #30363d', borderRadius: 20, color: '#8b949e',
                            fontSize: 10, fontFamily: 'monospace', cursor: 'default'
                        }}>
                            {ex}
                        </div>
                    ))}
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// STATUS BAR
// ═══════════════════════════════════════════════════════════════════════════════
function StatusBar({ layout, machineState, setMachineState }) {
    const [clock, setClock] = useState('');
    useEffect(() => {
        const tick = () => setClock(new Date().toLocaleTimeString('en-GB', { hour12: false }));
        tick();
        const id = setInterval(tick, 1000);
        return () => clearInterval(id);
    }, []);
    const activeAlarms = (layout?.components || []).filter(
        c => c.type === 'alarm' && c.state === 'active'
    ).length;
    const running = !!machineState?.running && !machineState?.estop;
    const isEstop = !!machineState?.estop;
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 18px',
            background: 'linear-gradient(90deg, #0f1b2c 0%, #0a1524 60%, #0b1626 100%)',
            borderBottom: '1px solid #1f2a3a',
            boxShadow: '0 8px 20px rgba(0,0,0,0.45)',
            flexShrink: 0
        }}>
            <div style={{
                flex: 1, fontWeight: 800, fontSize: 14, color: '#e6edf3',
                letterSpacing: '0.06em', textTransform: 'uppercase'
            }}>
                {layout?.title || layout?.system_name || 'HMI Dashboard'}
            </div>
            {activeAlarms > 0 && (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: 5, padding: '3px 10px',
                    background: 'rgba(248,81,73,0.15)', border: '1px solid #f85149',
                    borderRadius: 4, color: '#f85149', fontSize: 11, fontWeight: 700,
                    animation: 'alarmPulse 1.6s ease-in-out 2'
                }}>
                    🔔 {activeAlarms} ALARM{activeAlarms > 1 ? 'S' : ''}
                </div>
            )}
            {isEstop && (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: 6, padding: '3px 10px',
                    background: 'rgba(245,158,11,0.15)', border: '1px solid #f59e0b',
                    borderRadius: 4, color: '#f59e0b', fontSize: 11, fontWeight: 800,
                    letterSpacing: '0.06em'
                }}>
                    E-STOP ACTIVE
                </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: running ? '#2ecc71' : '#6e7681',
                    boxShadow: running ? '0 0 8px #2ecc71' : 'none', transition: 'all 0.3s'
                }} />
                <span style={{
                    fontSize: 11, fontWeight: 700, letterSpacing: '0.08em',
                    color: running ? '#2ecc71' : '#6e7681'
                }}>
                    {running ? 'ONLINE' : 'STANDBY'}
                </span>
            </div>
            <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#8b949e' }}>{clock}</span>
            <button onClick={() => {
                if (isEstop) {
                    setMachineState({ estop: false });
                    return;
                }
                setMachineState({ running: !running, estop: false });
            }}
                style={{
                    padding: '6px 18px',
                    borderRadius: 6,
                    border: `1px solid ${running ? '#f87171' : '#4ade80'}`,
                    fontWeight: 800,
                    fontSize: 11,
                    cursor: 'pointer',
                    letterSpacing: '0.07em',
                    background: running ? 'linear-gradient(180deg,#ef4444,#b91c1c)' : 'linear-gradient(180deg,#22c55e,#15803d)',
                    color: '#fff',
                    transition: 'all 0.2s',
                    boxShadow: running ? '0 0 14px rgba(239,68,68,0.45)' : '0 0 14px rgba(34,197,94,0.35)'
                }}>
                {isEstop ? 'RESET E-STOP' : (running ? 'STOP ALL' : 'START ALL')}
            </button>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN EXPORT
// ═══════════════════════════════════════════════════════════════════════════════
export default function DashboardRenderer({ layout }) {
    const [machineState, setMachineState] = useMachineState();
    const hasLayout = !!(layout?.components?.length);
    const canvasRef = useRef(null);
    const canvasSize = useCanvasSize(canvasRef);

    useEffect(() => {
        if (!hasLayout) setMachineState({ running: false, estop: false });
    }, [hasLayout, setMachineState]);

    const running = !!machineState?.running && !machineState?.estop;
    const arrangedComponents = useMemo(
        () => autoLayoutComponents(layout?.components || [], canvasSize),
        [layout, canvasSize]
    );

    const handleCommand = (cmd) => {
        if (cmd === 'start') setMachineState({ running: true, estop: false });
        if (cmd === 'stop') setMachineState({ running: false });
        if (cmd === 'estop') setMachineState({ running: false, estop: true });
        if (cmd === 'reset') setMachineState({ estop: false });
    };

    return (
        <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            background: 'radial-gradient(circle at 20% 10%, #132238 0%, #0b1320 40%, #070d16 100%)',
            overflow: 'hidden'
        }}>
            <StatusBar layout={layout} machineState={machineState} setMachineState={setMachineState} />
            <div ref={canvasRef} style={{ flex: 1, position: 'relative', overflow: 'auto' }}>
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    pointerEvents: 'none',
                    opacity: 0.08,
                    backgroundImage:
                        'linear-gradient(#7dd3fc 1px, transparent 1px), linear-gradient(90deg, #7dd3fc 1px, transparent 1px)',
                    backgroundSize: '56px 56px'
                }} />
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    pointerEvents: 'none',
                    opacity: 0.12,
                    background:
                        'radial-gradient(circle at 70% 20%, rgba(14,165,233,0.35), transparent 45%), radial-gradient(circle at 15% 80%, rgba(34,197,94,0.25), transparent 50%)'
                }} />
                {!hasLayout
                    ? <DefaultHMI />
                    : arrangedComponents.map(c =>
                        <HMISymbol
                            key={c.id || c.label}
                            c={c}
                            running={running}
                            machineState={machineState}
                            onCommand={handleCommand}
                        />
                    )
                }
            </div>
        </div>
    );
}

