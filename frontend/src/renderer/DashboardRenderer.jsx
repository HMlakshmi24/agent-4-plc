
import React from 'react';

export default function DashboardRenderer({ layout }) {

    return (
        <div className="dashboard-container" style={{
            backgroundColor: '#0f172a',
            color: 'white',
            minHeight: '600px',
            position: 'relative',
            padding: '20px',
            border: '1px solid #334155',
            borderRadius: '8px'
        }}>
            <h1 className="text-3xl text-cyan-400 mb-4" style={{ borderBottom: '1px solid #333', paddingBottom: '10px' }}>
                {layout.system_name}
            </h1>

            {layout.components.map(comp => (
                <div key={comp.id}
                    style={{
                        position: 'absolute',
                        left: comp.x,
                        top: comp.y,
                        border: '1px solid #475569',
                        backgroundColor: '#1e293b',
                        padding: '10px',
                        borderRadius: '4px',
                        width: comp.type === 'tank' ? '100px' : 'auto',
                        height: comp.type === 'tank' ? '150px' : 'auto',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                >
                    <div style={{ fontWeight: 'bold', color: '#38bdf8', marginBottom: '5px' }}>{comp.name}</div>
                    <div style={{ fontSize: '0.8em', color: '#94a3b8', textTransform: 'uppercase' }}>{comp.type}</div>

                    {/* Mock Value Display */}
                    <div style={{ marginTop: '5px', fontSize: '1.2em', color: '#a5f3fc' }}>
                        {comp.type === 'pump' ? (Math.random() > 0.5 ? 'ON' : 'OFF') :
                            comp.type === 'valve' ? (Math.random() > 0.5 ? 'OPEN' : 'CLOSED') :
                                (Math.random() * 100).toFixed(1)}
                    </div>
                </div>
            ))}
        </div>
    );
}
