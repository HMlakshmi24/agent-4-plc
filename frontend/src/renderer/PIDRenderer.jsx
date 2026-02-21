
import React from 'react';

export default function PIDRenderer({ layout }) {

    return (
        <div className="pid-container" style={{
            backgroundColor: "#0f172a",
            minHeight: '600px',
            border: '1px solid #334155',
            borderRadius: '8px',
            overflow: 'hidden'
        }}>
            <h2 style={{ position: 'absolute', top: 10, left: 20, color: '#64748b', zIndex: 10 }}>{layout.system_name} (P&ID)</h2>

            <svg width="100%" height="600" style={{ background: "#0f172a" }}>
                <defs>
                    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                        <path d="M0,0 L0,6 L9,3 z" fill="#64748b" />
                    </marker>
                </defs>

                {layout.components.map(comp => {

                    if (comp.type === "tank") {
                        return (
                            <g key={comp.id}>
                                <rect x={comp.x} y={comp.y} width="100" height="150" rx="5"
                                    stroke="#0ea5e9" fill="#1e293b" strokeWidth="2" />
                                <text x={comp.x + 50} y={comp.y + 75} textAnchor="middle" fill="#0ea5e9" fontSize="14">{comp.name}</text>
                                {/* Fluid Level Mock */}
                                <rect x={comp.x + 10} y={comp.y + 50} width="80" height="90" fill="#0ea5e9" opacity="0.3" />
                            </g>
                        );
                    }

                    if (comp.type === "pump") {
                        return (
                            <g key={comp.id}>
                                <circle cx={comp.x + 25} cy={comp.y + 25} r="25"
                                    stroke="#22c55e" fill="#1e293b" strokeWidth="2" />
                                <path d={`M${comp.x + 25},${comp.y} L${comp.x + 50},${comp.y + 25} L${comp.x + 25},${comp.y + 50} Z`} fill="#22c55e" opacity="0.8" />
                                <text x={comp.x + 25} y={comp.y + 65} textAnchor="middle" fill="#22c55e" fontSize="12">{comp.name}</text>
                            </g>
                        );
                    }

                    if (comp.type === "valve") {
                        return (
                            <g key={comp.id}>
                                <path d={`M${comp.x},${comp.y} L${comp.x + 40},${comp.y + 20} L${comp.x},${comp.y + 20} L${comp.x + 40},${comp.y} Z`}
                                    stroke="#eab308" fill="#1e293b" strokeWidth="2" />
                                <circle cx={comp.x + 20} cy={comp.y - 10} r="10" stroke="#eab308" fill="none" strokeWidth="2" />
                                <line x1={comp.x + 20} y1={comp.y} x2={comp.x + 20} y2={comp.y - 10} stroke="#eab308" strokeWidth="2" />
                                <text x={comp.x + 20} y={comp.y + 35} textAnchor="middle" fill="#eab308" fontSize="12">{comp.name}</text>
                            </g>
                        )
                    }

                    if (comp.type === "pipe") {
                        // Simple horizontal pipe representation for now
                        return (
                            <line key={comp.id} x1={comp.x} y1={comp.y} x2={comp.x + 100} y2={comp.y}
                                stroke="#64748b" strokeWidth="4" />
                        )
                    }

                    if (comp.type === "sensor" || comp.type === "transmitter") {
                        return (
                            <g key={comp.id}>
                                <circle cx={comp.x + 15} cy={comp.y + 15} r="15" stroke="#a855f7" fill="#1e293b" strokeWidth="2" />
                                <text x={comp.x + 15} y={comp.y + 20} textAnchor="middle" fill="#a855f7" fontSize="10">{comp.name}</text>
                            </g>
                        )
                    }

                    // Default generic box
                    return (
                        <g key={comp.id}>
                            <rect x={comp.x} y={comp.y} width="60" height="40" stroke="#ccc" fill="transparent" strokeDasharray="4" />
                            <text x={comp.x} y={comp.y + 20} fill="#ccc" fontSize="10">{comp.name}</text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
}
