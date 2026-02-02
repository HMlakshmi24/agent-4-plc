import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./hmi_generator_v2.css";
import { API } from '../config/api';

const HmiGeneratorV2 = () => {
  const [showModal, setShowModal] = useState(false);
  const [requirement, setRequirement] = useState("");
  const [loading, setLoading] = useState(false);
  const [generatedHmi, setGeneratedHmi] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [hmiHistory, setHmiHistory] = useState([]);

  const handleGenerate = async () => {
    if (!requirement.trim()) return alert("Please enter a requirement!");

    setLoading(true);
    try {
      const response = await fetch(`${API}/plc/generate-hmi`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirement: requirement.trim() }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error generating HMI");
      }

      const data = await response.json();
      console.log("Generated HMI:", data);
      
      setGeneratedHmi(data);
      setShowPreview(true);
      
      // Add to history
      setHmiHistory([...hmiHistory, {
        id: Date.now(),
        requirement: requirement,
        hmi_code: data.hmi_code,
        timestamp: new Date().toLocaleTimeString()
      }]);

    } catch (err) {
      alert(`Failed to generate HMI: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!generatedHmi) return;
    
    const filename = `hmi_interface_${Date.now()}.html`;
    const element = document.createElement("a");
    const file = new Blob([generatedHmi.hmi_code], { type: "text/html" });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handlePreviewInBrowser = () => {
    if (!generatedHmi) return;
    const preview = window.open();
    preview.document.write(generatedHmi.hmi_code);
  };

  const handleClearHistory = () => {
    setHmiHistory([]);
    setGeneratedHmi(null);
    setShowPreview(false);
    setRequirement("");
  };

  const handleTryNow = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please login first!");
      return;
    }
    setShowModal(true);
  };

  return (
    <div className="hmi-section-v2">
      <div className="hmi-header">
        <div className="hmi-text">
          <h2>🎨 AI HMI Interface Designer</h2>
          <p>
            Generate industrial-grade Human-Machine Interface (HMI) panels instantly.
            Follows ISA-101 standards and best practices for operator interaction.
          </p>
        </div>

        <div className="hmi-action">
          <motion.button
            className="hmi-generate-btn"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleTryNow}
          >
            Design HMI →
          </motion.button>
        </div>
      </div>

      {/* Results Container */}
      <div className="hmi-results-container">
        {/* History Panel (Left) */}
        {hmiHistory.length > 0 && (
          <div className="hmi-history-panel">
            <div className="hmi-history-header">
              <h3>📋 HMI History</h3>
              <button className="hmi-clear-btn" onClick={handleClearHistory}>Clear All</button>
            </div>
            <div className="hmi-history-list">
              {hmiHistory.map((item) => (
                <div key={item.id} className="hmi-history-item">
                  <div className="hmi-history-meta">
                    <span className="hmi-time-badge">{item.timestamp}</span>
                  </div>
                  <p className="hmi-history-requirement">{item.requirement.substring(0, 50)}...</p>
                  <div className="hmi-preview-mini">
                    <pre>{item.hmi_code.substring(0, 150)}...</pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Preview Panel (Right) */}
        {showPreview && generatedHmi && (
          <div className="hmi-preview-panel">
            <div className="hmi-preview-header">
              <h3>✅ HMI Preview</h3>
              <span className="hmi-validated-badge">✓ Generated</span>
            </div>

            {/* Live preview */}
            <div className="hmi-live-preview">
              <h4>Live Preview:</h4>
              <div className="hmi-frame">
                <iframe
                  srcDoc={generatedHmi.hmi_code}
                  title="HMI Preview"
                  frameBorder="0"
                  style={{ width: '100%', height: '300px', border: 'none', borderRadius: '6px' }}
                />
              </div>
            </div>

            {/* Code display */}
            <div className="hmi-code-preview">
              <h4>HTML Code ({generatedHmi.hmi_code.split('\n').length} lines):</h4>
              <pre><code>{generatedHmi.hmi_code}</code></pre>
            </div>

            {/* Action buttons */}
            <div className="hmi-preview-actions">
              <button 
                className="hmi-download-btn"
                onClick={handleDownload}
              >
                💾 Download HMI
              </button>
              <button 
                className="hmi-open-btn"
                onClick={handlePreviewInBrowser}
              >
                🌐 Open in Browser
              </button>
              <button 
                className="hmi-regenerate-btn"
                onClick={() => setShowPreview(false)}
              >
                🔄 Regenerate
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            className="hmi-modal-overlay-v2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowModal(false)}
          >
            <motion.div
              className="hmi-modal-v2"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.3 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3>Design HMI Panel</h3>
              
              {/* HMI description */}
              <div className="hmi-input-group">
                <label>Describe Your HMI Panel (Plain English):</label>
                <textarea
                  value={requirement}
                  onChange={(e) => setRequirement(e.target.value)}
                  placeholder="Example: Create an HMI panel for a pump system. Show: 1) Current pressure (analog gauge 0-100 bar), 2) Pump status (Running/Stopped indicator), 3) Temperature display (numeric 0-80°C), 4) Start/Stop buttons, 5) Alarm lights for High Pressure and Overtemperature. Use industrial colors: green for normal, yellow for caution, red for alarm."
                  rows="8"
                />
                <div className="hmi-char-count">{requirement.length} characters</div>
              </div>

              {/* Buttons */}
              <div className="hmi-modal-buttons">
                <button
                  className="hmi-cancel-btn"
                  onClick={() => {
                    setShowModal(false);
                    setRequirement("");
                  }}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  className="hmi-generate-modal-btn"
                  onClick={handleGenerate}
                  disabled={loading || !requirement.trim()}
                >
                  {loading ? (
                    <>
                      <span className="hmi-spinner"></span> Generating...
                    </>
                  ) : (
                    "Design HMI"
                  )}
                </button>
              </div>

              {/* Guidelines */}
              <div className="hmi-guidelines">
                <p>📋 HMI Design Guidelines:</p>
                <ul>
                  <li>Describe all displays (gauges, indicators, numeric values)</li>
                  <li>List all interactive elements (buttons, switches, sliders)</li>
                  <li>Specify alarm conditions and visual states</li>
                  <li>Include color preferences for different states</li>
                  <li>Mention any special requirements (responsive, dark mode, etc.)</li>
                </ul>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default HmiGeneratorV2;
