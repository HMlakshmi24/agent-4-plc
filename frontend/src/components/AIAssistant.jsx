import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { API } from '../config/api';

const AIAssistant = () => {
    const { theme } = useTheme();
    const { user } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: 'assistant', text: 'Hello Engineer. How can I assist with your PLC or HMI logic today?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    // Auto scroll down
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Only show for logged in users, or if you want it always available change this.
    if (!user) return null;

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input.trim();
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setInput('');
        setLoading(true);

        try {
            const tokenStr = localStorage.getItem("automind_token") || localStorage.getItem("token");
            const storedUser = JSON.parse(localStorage.getItem("user_details") || "{}");
            const activeEmail = user?.email || storedUser?.email;

            const headers = { "Content-Type": "application/json" };
            if (tokenStr && !tokenStr.startsWith("mock-")) {
                headers["Authorization"] = `Bearer ${tokenStr}`;
            }
            if (activeEmail) {
                headers["X-User-Email"] = activeEmail;
            }

            const res = await fetch(`${API}/api/ai-help`, {
                method: "POST",
                headers,
                body: JSON.stringify({ message: userMsg })
            });

            if (res.ok) {
                const data = await res.json();
                setMessages(prev => [...prev, { role: 'assistant', text: data.reply }]);
            } else {
                setMessages(prev => [...prev, { role: 'assistant', text: 'Sorry, I encountered an error connecting to the API.' }]);
            }
        } catch (err) {
            console.error("AI Help Error", err);
            setMessages(prev => [...prev, { role: 'assistant', text: 'Connection failed. Please check your network.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-[9999]">
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 50, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 50, scale: 0.9 }}
                        transition={{ duration: 0.2 }}
                        className="mb-4 w-[360px] h-[500px] rounded-2xl flex flex-col overflow-hidden shadow-2xl"
                        style={{
                            background: theme === 'dark' ? '#0f172a' : '#ffffff',
                            border: theme === 'dark' ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.1)',
                            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.4)'
                        }}
                    >
                        {/* Header */}
                        <div className="px-4 py-3 flex justify-between items-center" style={{
                            background: 'linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)',
                            color: 'white'
                        }}>
                            <div className="flex items-center gap-2">
                                <span className="text-xl">🤖</span>
                                <div>
                                    <h3 className="font-bold text-sm">Industrial AI Assistant</h3>
                                    <p className="text-[10px] opacity-80 uppercase tracking-wider text-green-300">Online</p>
                                </div>
                            </div>
                            <button onClick={() => setIsOpen(false)} className="text-white hover:text-red-200 transition-colors">✕</button>
                        </div>

                        {/* Chat Area */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{
                            background: theme === 'dark' ? '#1e293b' : '#f8fafc'
                        }}>
                            {messages.map((m, i) => (
                                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className="max-w-[85%] rounded-2xl px-4 py-2.5 text-sm" style={{
                                        background: m.role === 'user'
                                            ? '#3b82f6'
                                            : (theme === 'dark' ? '#0f172a' : '#ffffff'),
                                        color: m.role === 'user'
                                            ? 'white'
                                            : (theme === 'dark' ? '#e2e8f0' : '#1e293b'),
                                        border: m.role === 'assistant' && theme === 'dark' ? '1px solid rgba(255,255,255,0.05)' : (m.role === 'assistant' ? '1px solid rgba(0,0,0,0.05)' : 'none'),
                                        borderBottomRightRadius: m.role === 'user' ? '4px' : '16px',
                                        borderBottomLeftRadius: m.role === 'assistant' ? '4px' : '16px'
                                    }}>
                                        <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{m.text}</div>
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div className="flex justify-start">
                                    <div className="bg-transparent text-slate-400 text-xs italic">AI is thinking...</div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="p-3 border-t" style={{
                            borderColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                            background: theme === 'dark' ? '#0f172a' : '#ffffff'
                        }}>
                            <form
                                onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                                className="flex gap-2"
                            >
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask about PLC logic, standards..."
                                    className="flex-1 rounded-full px-4 py-2 text-sm outline-none transition-all"
                                    style={{
                                        background: theme === 'dark' ? '#1e293b' : '#f1f5f9',
                                        color: theme === 'dark' ? '#f8fafc' : '#0f172a',
                                        border: '1px solid transparent'
                                    }}
                                />
                                <button
                                    type="submit"
                                    disabled={loading || !input.trim()}
                                    className="rounded-full w-10 h-10 flex items-center justify-center bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 transition-colors shrink-0"
                                >
                                    ➤
                                </button>
                            </form>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Floating Toggle Button */}
            {!isOpen && (
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setIsOpen(true)}
                    className="w-14 h-14 rounded-full flex items-center justify-center text-2xl shadow-xl transition-all"
                    style={{
                        background: 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)',
                        color: 'white',
                        boxShadow: '0 10px 25px rgba(37, 99, 235, 0.4)'
                    }}
                >
                    🤖
                </motion.button>
            )}
        </div>
    );
};

export default AIAssistant;
