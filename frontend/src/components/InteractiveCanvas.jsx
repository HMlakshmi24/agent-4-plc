import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

const InteractiveCanvas = ({ children, initialScale = 0.95 }) => {
    const containerRef = useRef(null);
    const [scale, setScale] = useState(initialScale);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });

    // Center content on mount
    useEffect(() => {
        if (containerRef.current) {
            const { clientWidth, clientHeight } = containerRef.current;
            const contentW = 1200;
            const contentH = 800;

            const scaleX = (clientWidth - 140) / contentW;
            const scaleY = (clientHeight - 140) / contentH;
            const fitScale = Math.min(scaleX, scaleY, 1);

            setScale(fitScale);
            setPosition({
                x: (clientWidth - contentW * fitScale) / 2,
                y: (clientHeight - contentH * fitScale) / 2
            });
        }
    }, []);

    const handleWheel = (e) => {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            const zoomSensitivity = 0.001;
            const newScale = Math.min(Math.max(0.1, scale - e.deltaY * zoomSensitivity), 4);

            // Zoom towards mouse pointer logic would go here, 
            // but for simplicity/stability we'll zoom center or just scale
            setScale(newScale);
        } else {
            // Pan if not zooming? Or just standard scroll? 
            // Let's allow standard scroll if not capturing, but we want a canvas feel.
            // Actually, let's map wheel to pan if logic dictates, but standard is Zoom on Ctrl+Wheel.
        }
    };

    // Custom Drag Logic (Space + Drag or Middle Click)
    const handleMouseDown = (e) => {
        const isInteractive = e.target.closest('[data-interactive="true"]');
        if (isInteractive && e.button === 0) return;
        if (e.button === 1 || e.button === 0) {
            setIsDragging(true);
            setLastMousePos({ x: e.clientX, y: e.clientY });
            e.preventDefault();
        }
    };

    const handleMouseMove = (e) => {
        if (isDragging) {
            const dx = e.clientX - lastMousePos.x;
            const dy = e.clientY - lastMousePos.y;
            setPosition(prev => ({ x: prev.x + dx, y: prev.y + dy }));
            setLastMousePos({ x: e.clientX, y: e.clientY });
        }
    };

    const handleMouseUp = () => {
        setIsDragging(false);
    };

    const handleZoomIn = () => setScale(s => Math.min(s * 1.2, 4));
    const handleZoomOut = () => setScale(s => Math.max(s / 1.2, 0.1));
    const handleFit = () => {
        if (containerRef.current) {
            const { clientWidth, clientHeight } = containerRef.current;
            const fitScale = Math.min((clientWidth - 120) / 1200, (clientHeight - 120) / 800, 1);
            setScale(fitScale);
            setPosition({
                x: (clientWidth - 1200 * fitScale) / 2,
                y: (clientHeight - 800 * fitScale) / 2
            });
        }
    };

    return (
        <div
            ref={containerRef}
            className="w-full h-full relative overflow-hidden bg-[#0b1120] select-none"
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
            {/* Grid Background */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.05]"
                style={{
                    backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
                    backgroundSize: `${48 * scale}px ${48 * scale}px`,
                    backgroundPosition: `${position.x}px ${position.y}px`
                }}
            />

            {/* Content Container */}
            <motion.div
                style={{
                    width: 1200,
                    height: 800,
                    x: position.x,
                    y: position.y,
                    scale: scale,
                    originX: 0,
                    originY: 0
                }}
                className="absolute shadow-2xl bg-slate-900/60 backdrop-blur-sm border border-slate-700 rounded-3xl overflow-hidden"
            >
                {children}
            </motion.div>

            {/* Controls */}
            <div className="absolute bottom-6 right-6 flex gap-2 z-50">
                <div className="bg-slate-800/90 backdrop-blur border border-slate-700 rounded-2xl p-1.5 flex shadow-xl">
                    <button onClick={handleZoomOut} className="w-9 h-9 flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-700 rounded-xl transition">-</button>
                    <span className="w-14 flex items-center justify-center text-sm font-mono text-slate-300">{Math.round(scale * 100)}%</span>
                    <button onClick={handleZoomIn} className="w-9 h-9 flex items-center justify-center text-slate-300 hover:text-white hover:bg-slate-700 rounded-xl transition">+</button>
                </div>
                <button onClick={handleFit} className="px-4 bg-slate-800/90 backdrop-blur border border-slate-700 rounded-2xl text-sm font-semibold text-slate-200 hover:text-white hover:bg-slate-700 shadow-xl transition">
                    FIT
                </button>
            </div>

            {/* Hint */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-slate-900/60 text-xs text-slate-400 px-4 py-1.5 rounded-full border border-slate-800/60 pointer-events-none">
                Drag to pan. Ctrl+Scroll to zoom. Click elements to toggle.
            </div>
        </div>
    );
};

export default InteractiveCanvas;
