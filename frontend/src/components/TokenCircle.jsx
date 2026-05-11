import { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../context/ThemeContext';
import { API } from '../config/api';

const fmt = (n) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);

const TokenCircle = ({ user }) => {
    const { theme } = useTheme();
    const [tokens, setTokens] = useState({ used: 0, limit: 50000, remaining: 50000, blocked: false });
    const [loading, setLoading] = useState(true);

    const fetchTokens = useCallback(async () => {
        if (!user?.email) { setLoading(false); return; }
        try {
            const tokenStr = localStorage.getItem("automind_token") || localStorage.getItem("token");
            const headers = { "X-User-Email": user.email };
            if (tokenStr && !tokenStr.startsWith("mock-"))
                headers["Authorization"] = `Bearer ${tokenStr}`;

            // /api/user/usage — direct route, no redirect, headers preserved
            const res = await fetch(`${API}/api/user/usage`, { headers });
            if (res.ok) {
                const d = await res.json();
                const used    = d.used_tokens  ?? d.used  ?? 0;
                const limit   = d.token_limit  ?? d.limit ?? 50000;
                const remaining = d.remaining  ?? Math.max(0, limit - used);
                setTokens({ used, limit, remaining, blocked: d.is_blocked ?? false });
            }
        } catch (e) {
            console.warn("Token fetch error", e);
        } finally {
            setLoading(false);
        }
    }, [user]);

    useEffect(() => {
        if (!user?.email) { setLoading(false); return; }
        fetchTokens();
        const interval = setInterval(fetchTokens, 30000);
        // Refresh immediately when generation finishes
        const onDone = () => fetchTokens();
        window.addEventListener('plc:generation_done', onDone);
        return () => { clearInterval(interval); window.removeEventListener('plc:generation_done', onDone); };
    }, [user, fetchTokens]);

    if (!user || loading) return null;

    const percent = tokens.limit > 0
        ? Math.min(100, Math.max(0, (tokens.used / tokens.limit) * 100))
        : 0;

    // Color: purple (fresh) → green → orange → red (near limit)
    let color = '#a855f7';
    if (percent > 15 && percent <= 50)  color = '#22c55e';
    else if (percent > 50 && percent <= 80) color = '#f97316';
    else if (percent > 80) color = '#ef4444';

    const radius = 18;
    const dasharray = 2 * Math.PI * radius;
    const dashoffset = dasharray - (dasharray * percent) / 100;

    const isDark = theme === 'dark';

    return (
        <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full transition-all cursor-default select-none"
            title={`${tokens.used.toLocaleString()} used · ${tokens.remaining.toLocaleString()} remaining · ${tokens.limit.toLocaleString()} total`}
            style={{
                background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
                border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)',
            }}
        >
            {/* Ring */}
            <svg width="36" height="36" viewBox="0 0 40 40" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="20" cy="20" r={radius}
                    stroke={isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}
                    strokeWidth="3.5" fill="none" />
                <circle cx="20" cy="20" r={radius}
                    stroke={color} strokeWidth="3.5" fill="none"
                    strokeDasharray={dasharray}
                    strokeDashoffset={dashoffset}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1s ease-in-out, stroke 0.5s ease-in-out' }}
                />
            </svg>

            {/* Text block */}
            <div className="flex flex-col" style={{ lineHeight: 1.25 }}>
                {tokens.blocked ? (
                    <>
                        <span style={{ fontSize: 10, fontWeight: 700, color: '#ef4444', letterSpacing: '0.05em' }}>
                            LIMIT REACHED
                        </span>
                        <span style={{ fontSize: 9, color: isDark ? '#94a3b8' : '#64748b' }}>
                            Upgrade to continue
                        </span>
                    </>
                ) : (
                    <>
                        {/* e.g. "12.3k / 50.0k" */}
                        <span style={{ fontSize: 10, fontWeight: 700, color, letterSpacing: '0.03em' }}>
                            {fmt(tokens.used)} / {fmt(tokens.limit)}
                        </span>
                        {/* e.g. "37.7k left" */}
                        <span style={{ fontSize: 9, color: isDark ? '#94a3b8' : '#64748b' }}>
                            {fmt(tokens.remaining)} tokens left
                        </span>
                    </>
                )}
            </div>
        </div>
    );
};

export default TokenCircle;
