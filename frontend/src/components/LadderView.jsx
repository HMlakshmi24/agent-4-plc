import React from "react";

export default function LadderView({ rungs }) {
    if (!rungs || rungs.length === 0) {
        return <div className="text-gray-500 italic p-4">No ladder logic generated yet.</div>;
    }

    return (
        <div style={{ padding: "20px", color: 'inherit' }}>
            <h2 className="text-xl font-bold mb-6 border-b border-slate-700 pb-2">LD (Ladder Diagram) Logic</h2>

            {rungs.map((rung, index) => (
                <div key={index} style={{ marginBottom: "30px" }}>
                    <h3 className="font-semibold text-lg mb-2 text-blue-400">{rung.title}</h3>

                    <div
                        className="ladder-rung-container"
                        style={{
                            background: "#1e293b", // Dark slate background matches theme
                            color: "#e2e8f0",      // Light text
                            padding: "15px",
                            borderRadius: "10px",
                            fontFamily: "'Fira Code', 'Courier New', monospace",
                            whiteSpace: "pre",
                            border: "1px solid #334155",
                            boxShadow: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.2)",
                            overflowX: "auto"
                        }}
                    >
                        {rung.ascii}
                    </div>
                    {rung.notes && <div className="text-sm text-gray-500 mt-1 italic">{rung.notes}</div>}
                </div>
            ))}
        </div>
    );
}
