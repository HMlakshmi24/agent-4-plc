import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { API } from '../config/api';

const TokenCircle = ({ user }) => {
    const { theme } = useTheme();
    const [tokens, setTokens] = useState({ used: 0, limit: 50000, blocked: false });
    const [loading, setLoading] = useState(true);

    // Poll for token update every 15s or when user changes
    useEffect(() => {
        if (!user || window.location.pathname.startsWith('/auth')) {
            setLoading(false);
            return;
        }

        const fetchTokens = async () => {
            try {
                const tokenStr = localStorage.getItem("automind_token") || localStorage.getItem("token");
                const headers = {};
                if (tokenStr && !tokenStr.startsWith("mock-")) headers["Authorization"] = `Bearer ${tokenStr}`;
                if (user.email) headers["X-User-Email"] = user.email;

                const res = await fetch(`${API}/api/tokens`, { headers });
                if (res.ok) {
                    const data = await res.json();
                    setTokens(data);
                }
            } catch (e) {
                console.warn("Token fetch error", e);
            } finally {
                setLoading(false);
            }
        };

        fetchTokens();
        const interval = setInterval(fetchTokens, 15000); // 15s polling to catch active gens
        return () => clearInterval(interval);
    }, [user]);

    if (!user || loading) return null;

    const percent = Math.min(100, Math.max(0, (tokens.used / tokens.limit) * 100));

    // Logic: <15%: purple, <50%: green, <75%: orange, >75%: red
    let color = '#a855f7'; // purple
    if (percent > 15 && percent <= 50) color = '#22c55e'; // green
    else if (percent > 50 && percent <= 75) color = '#f97316'; // orange
    else if (percent > 75) color = '#ef4444'; // red

    const radius = 18;
    const dasharray = 2 * Math.PI * radius; // ~113.1
    const dashoffset = dasharray - (dasharray * percent) / 100;

    return (
        <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full transition-all cursor-crosshair"
            title={`${tokens.used.toLocaleString()} / ${tokens.limit.toLocaleString()} Tokens Used`}
            style={{
                background: theme === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
                border: theme === 'dark' ? '1px solid rgba(255,255,255,0.05)' : '1px solid rgba(0,0,0,0.05)'
            }}
        >
            <svg width="38" height="38" viewBox="0 0 40 40" className="transform -rotate-90">
                <circle
                    cx="20" cy="20" r={radius}
                    stroke={theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}
                    strokeWidth="3.5"
                    fill="none"
                />
                <circle
                    cx="20" cy="20" r={radius}
                    stroke={color}
                    strokeWidth="3.5"
                    fill="none"
                    strokeDasharray={dasharray}
                    strokeDashoffset={dashoffset}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1s ease-in-out, stroke 0.5s ease-in-out' }}
                />
            </svg>
            <div className="flex flex-col text-[10px] font-bold tracking-widest uppercase" style={{ lineHeight: '1.2' }}>
                <span style={{ color }}>{percent.toFixed(0)}%</span>
                <span className={theme === 'dark' ? 'text-slate-500' : 'text-slate-400'}>LIMIT</span>
            </div>
        </div>
    );
};

export default TokenCircle;
