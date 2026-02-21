/**
 * DashboardRenderer.jsx
 *
 * Universal HMI Symbol Engine.
 * AI returns: { title, theme, components:[{id,type,label,x,y,state,value}] }
 * This file renders each component by type — locally, no AI for rendering.
 * No domain detection. No templates. No extra files.
 * Different prompt → different JSON → different visual.
 */
import React, { useState, useEffect } from 'react';

// ─── Inject keyframe animations once ─────────────────────────────────────────
if (!document.getElementById('_hmi_kf')) {
    const s = document.createElement('style');
    s.id = '_hmi_kf';
    s.textContent = `
        @keyframes hmiSpin  { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes hmiBlink { 0%,100%{opacity:1} 50%{opacity:0.15} }
        @keyframes hmiPulse { 0%,100%{box-shadow:0 0 4px 2px #f85149aa}
                              50%{box-shadow:0 0 18px 6px #f85149} }
        @keyframes hmiFlow  { to{stroke-dashoffset:-30} }
    `;
    document.head.appendChild(s);
}

// ─── Colour helpers ───────────────────────────────────────────────────────────
const vCol = v => v > 80 ? '#e74c3c' : v < 25 ? '#f39c12' : '#2ecc71';
const sCol = s =>
    ['running', 'open', 'active'].includes(s) ? '#2ecc71' :
        ['stopped', 'closed', 'fault'].includes(s) ? '#e74c3c' :
            ['partial', 'warning', 'ack'].includes(s) ? '#f39c12' : '#7f8c8d';

// ═══════════════════════════════════════════════════════════════════════════════
// SYMBOL LIBRARY
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
            <svg width={tW} height={tH + 28} viewBox={`0 0 ${tW} ${tH + 28}`}>
                <rect x={0} y={eRY} width={tW} height={tH - 2 * eRY} fill="#0a1628" stroke="#4a90d9" strokeWidth="1.5" />
                <clipPath id={`tc_${c.id}`}><rect x={0} y={eRY} width={tW} height={tH - 2 * eRY} /></clipPath>
                <rect x={0} y={fY} width={tW} height={fH} fill={col} opacity="0.85"
                    clipPath={`url(#tc_${c.id})`} style={{ transition: 'y 0.9s,height 0.9s,fill 0.4s' }} />
                <rect x={4} y={fY + 3} width={7} height={Math.max(0, fH - 6)} rx="3" fill="rgba(255,255,255,0.12)" />
                <ellipse cx={tW / 2} cy={eRY} rx={tW / 2} ry={eRY} fill="#0d2040" stroke="#4a90d9" strokeWidth="1.5" />
                <ellipse cx={tW / 2} cy={tH - eRY} rx={tW / 2} ry={eRY} fill={col} opacity={lv > 5 ? 0.6 : 0} />
                {lv > 80 && <ellipse cx={tW / 2} cy={eRY * 2.2} rx={tW / 2 - 2} ry={eRY * 0.7}
                    fill="none" stroke="#e74c3c" strokeWidth="1.5" strokeDasharray="3,2" />}
                <text x={tW / 2} y={tH / 2 + 5} textAnchor="middle" fill="#fff"
                    fontSize="13" fontWeight="800" fontFamily="monospace">{lv.toFixed(0)}%</text>
                <text x={tW / 2} y={tH + 14} textAnchor="middle" fill="#e6edf3"
                    fontSize="10" fontWeight="700" fontFamily="monospace">{c.label}</text>
            </svg>
        </div>
    );
}

// ── PUMP ─────────────────────────────────────────────────────────────────────
function HMI_Pump({ c, running }) {
    const [on, setOn] = useState(c.state === 'running');
    useEffect(() => { if (!running) setOn(false); }, [running]);
    const col = on && running ? '#2ecc71' : '#e74c3c';
    return (
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center', cursor: 'pointer' }}
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
    const col = c.state === 'active' ? '#e74c3c' : c.state === 'warning' ? '#f39c12' : '#2ecc71';
    return (
        <div style={{
            position: 'absolute', left: c.x, top: c.y, display: 'flex', alignItems: 'center',
            gap: 8, padding: '7px 14px', background: `${col}18`,
            border: `1.5px solid ${acked ? '#333' : col}`, borderRadius: 6,
            cursor: 'pointer', opacity: acked ? 0.45 : 1, minWidth: 180,
            animation: !acked && c.state === 'active' ? 'hmiPulse 1.5s ease-in-out infinite' : 'none'
        }}
            onClick={() => setAcked(p => !p)}>
            <span style={{ fontSize: 14 }}>
                {c.state === 'active' ? '🔺' : c.state === 'warning' ? '⚠️' : '✅'}
            </span>
            <div style={{ flex: 1 }}>
                <div style={{
                    color: acked ? '#555' : col, fontWeight: 700, fontSize: 11,
                    fontFamily: 'monospace', letterSpacing: '0.04em'
                }}>{c.label}</div>
                {!acked && <div style={{ color: acked ? '#555' : col, fontSize: 9, fontFamily: 'monospace' }}>
                    {c.state?.toUpperCase()} — Click to ACK
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
            <svg width="90" height="84" viewBox="0 0 90 84">
                <path d={d(sA + sweep)} fill="none" stroke="#1e2228" strokeWidth="8" strokeLinecap="round" />
                <path d={d(eA)} fill="none" stroke={col} strokeWidth="8" strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 3px ${col}88)`, transition: 'all 0.5s' }} />
                <line x1={cx} y1={cy}
                    x2={cx + 26 * Math.cos(eA * Math.PI / 180)}
                    y2={cy + 26 * Math.sin(eA * Math.PI / 180)}
                    stroke="#e6edf3" strokeWidth="1.5" strokeLinecap="round" />
                <circle cx={cx} cy={cy} r="4" fill="#e6edf3" />
                <text x={cx} y={cy + 22} textAnchor="middle" fill={col}
                    fontSize="13" fontWeight="800" fontFamily="monospace">{val.toFixed(0)}</text>
            </svg>
            <div style={{
                color: '#8b949e', fontSize: 9, fontFamily: 'monospace',
                marginTop: -4
            }}>{c.label} {c.unit || ''}</div>
        </div>
    );
}

// ── SLIDER ───────────────────────────────────────────────────────────────────
function HMI_Slider({ c }) {
    const [val, setVal] = useState(+(c.value ?? 50));
    const col = '#2f8f83';
    return (
        <div style={{ position: 'absolute', left: c.x, top: c.y, minWidth: 130 }}>
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
function HMI_Button({ c }) {
    const [active, setActive] = useState(c.state === 'active');
    const lbl = c.label.toLowerCase();
    const col = ['start', 'run', 'on'].some(k => lbl.includes(k)) ? '#238636'
        : ['stop', 'off', 'e-stop', 'estop'].some(k => lbl.includes(k)) ? '#da3633'
            : '#1f6feb';
    return (
        <div style={{ position: 'absolute', left: c.x, top: c.y }}>
            <button onClick={() => setActive(p => !p)} style={{
                padding: '9px 18px', borderRadius: 6,
                border: `1px solid ${active ? col : '#30363d'}`, cursor: 'pointer',
                fontWeight: 700, fontSize: 11, letterSpacing: '0.06em',
                background: active ? col : '#1c2333', color: active ? '#fff' : '#8b949e',
                boxShadow: active ? `0 0 12px ${col}77` : 'none', transition: 'all 0.2s'
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
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
        <div style={{ position: 'absolute', left: c.x, top: c.y, textAlign: 'center' }}>
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
function HMISymbol({ c, running }) {
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
        case 'button': return <HMI_Button c={c} />;
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
function StatusBar({ layout, running, setRunning }) {
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
    return (
        <div style={{
            display: 'flex', alignItems: 'center', gap: 12, padding: '9px 18px',
            background: '#111827', borderBottom: '1px solid #30363d', flexShrink: 0
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
                    animation: 'hmiBlink 1.2s step-end infinite'
                }}>
                    🔔 {activeAlarms} ALARM{activeAlarms > 1 ? 'S' : ''}
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
            <button onClick={() => setRunning(r => !r)}
                style={{
                    padding: '5px 16px', borderRadius: 4, border: 'none', fontWeight: 700,
                    fontSize: 11, cursor: 'pointer', letterSpacing: '0.05em',
                    background: running ? '#da3633' : '#238636', color: '#fff',
                    transition: 'all 0.2s'
                }}>
                {running ? '■ STOP ALL' : '▶ START ALL'}
            </button>
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN EXPORT
// ═══════════════════════════════════════════════════════════════════════════════
export default function DashboardRenderer({ layout }) {
    const [running, setRunning] = useState(false);
    const hasLayout = !!(layout?.components?.length);

    useEffect(() => { if (!hasLayout) setRunning(false); }, [hasLayout]);

    return (
        <div style={{
            position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
            background: '#0d1117', overflow: 'hidden'
        }}>
            <StatusBar layout={layout} running={running} setRunning={setRunning} />
            <div style={{ flex: 1, position: 'relative', overflow: 'auto' }}>
                {!hasLayout
                    ? <DefaultHMI />
                    : (layout.components || []).map(c =>
                        <HMISymbol key={c.id || c.label} c={c} running={running} />
                    )
                }
            </div>
        </div>
    );
}
