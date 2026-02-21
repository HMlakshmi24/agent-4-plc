import React, { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./hmi_generator_v2.css";
import { API } from "../config/api";

const HmiGeneratorV2 = () => {
  /* Simplified State - Removed Export/Import Logic */
  const [showModal, setShowModal] = useState(false);
  const [requirement, setRequirement] = useState("");
  const [designStyle, setDesignStyle] = useState("pid_web");
  const [loading, setLoading] = useState(false);
  const [generatedHmi, setGeneratedHmi] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [history, setHistory] = useState([]);
  /* Simplified Styles - Only P&ID and Industrial */
  const styles = [
    { value: "pid_web", label: "P&ID Schematic", desc: "Dark P&ID blocks and tags" },
    { value: "industrial_std", label: "Standard HMI", desc: "High contrast panel view" }
  ];

  const buildPrompt = () => {
    const base = [
      "Create a professional WebHMI interface as a single HTML fragment with matching CSS.",
      "Use a dark industrial background (#1e1e1e to #222) unless the style says otherwise.",
      "Use clean typographic hierarchy, consistent spacing, and a grid-aligned layout.",
      "Keep layout deterministic: if the requirement is unchanged, keep the same structure and placement.",
      "Use instrument tags (e.g., P-101, TK-101, LT-101, CV-101) where appropriate.",
      "Prefer card-like control blocks with status + action buttons.",
      "Ensure readable contrast and clear affordances for buttons and controls."
    ];

    const styleRules = {
      pid_web: [
        "Primary style: P&ID schematic for web.",
        "Layout: left column for equipment blocks, center for tank/vessel, right for valve/control block.",
        "Use simple line work for pipes and connectors when logical.",
        "Use consistent panel shapes with subtle inner shadows and borders.",
        "Use muted cyan/teal for active elements and warm amber for valve block."
      ],
      industrial_std: [
        "Industrial standard look with neutral grays and sharp borders.",
        "Use restrained accent colors for status and alarms.",
        "Focus on high-contrast numeric displays and clear state indicators."
      ]
    };

    const styleGuide = styleRules[designStyle] || [];

    return [
      ...base,
      ...styleGuide,
      `System: ${requirement.trim()}`
    ].join("\n");
  };

  const handleGenerate = async () => {
    if (!requirement.trim()) return alert("Please enter a requirement!");

    setLoading(true);
    try {
      const response = await fetch(`${API}/hmi/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requirement: buildPrompt(),
          style: designStyle
        })
      });

      if (!response.ok) {
        let errorMsg = "Unknown error";
        try {
          const error = await response.json();
          errorMsg = error.detail || error.message || errorMsg;
        } catch {
          errorMsg = `HTTP ${response.status}`;
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();

      const newHmi = {
        id: Date.now(),
        requirement: requirement,
        style: designStyle,
        html: data.html,
        css: data.css,
        explanation: data.explanation || "Generated based on requirements.",
        timestamp: new Date().toLocaleTimeString()
      };

      setGeneratedHmi(newHmi);
      setShowPreview(true);

      if (showModal) {
        setTimeout(() => setShowModal(false), 100);
      }

      setHistory([...history, newHmi]);
    } catch (err) {
      console.error("HMI Generation error:", err);
      alert(`Failed to generate HMI: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
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
          <h2>AI WebHMI Interface Designer</h2>
          <p>
            Generate professional WebHMI screens as HTML/CSS from text.
            Describe your interface (buttons, gauges, charts) and we will build it.
          </p>
        </div>

        <div className="hmi-action">
          <motion.button
            className="hmi-generate-btn"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleTryNow}
          >
            Start Designing -&gt;
          </motion.button>
        </div>
      </div>

      <div className="hmi-results-container">
        {history.length > 0 && (
          <div className="hmi-history-panel">
            <div className="history-header">
              <h3>Design History</h3>
              <button className="clear-btn" onClick={handleClearHistory}>
                Clear All
              </button>
            </div>
            <div className="history-list">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="history-item"
                  onClick={() => {
                    setGeneratedHmi(item);
                    setShowPreview(true);
                  }}
                >
                  <div className="history-meta">
                    <span className="style-badge">
                      {styles.find((s) => s.value === item.style)?.label || item.style}
                    </span>
                    <span className="time-badge">{item.timestamp}</span>
                  </div>
                  <p className="history-req">{item.requirement.substring(0, 50)}...</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {showPreview && generatedHmi && (
          <div className="hmi-preview-panel">
            <div className="preview-header">
              <h3>Interface Generated</h3>
              <div className="preview-controls">
                <button
                  className={`view-btn ${viewMode === "preview" ? "active" : ""}`}
                  onClick={() => setViewMode("preview")}
                >
                  Preview
                </button>
                <button
                  className={`view-btn ${viewMode === "code" ? "active" : ""}`}
                  onClick={() => setViewMode("code")}
                >
                  HTML/CSS
                </button>
              </div>
            </div>

            <div className="preview-content-area">
              {loading && (
                <div className="preview-loading">
                  <div className="preview-spinner"></div>
                  <span>Generating...</span>
                </div>
              )}
              {viewMode === "preview" ? (
                <div className="live-preview-frame">
                  <style>{generatedHmi.css}</style>
                  <div dangerouslySetInnerHTML={{ __html: generatedHmi.html }} />
                </div>
              ) : (
                <div className="code-frame">
                  <h4>HTML</h4>
                  <pre>{generatedHmi.html}</pre>
                  <h4>CSS</h4>
                  <pre>{generatedHmi.css}</pre>
                </div>
              )}
            </div>

            <div className="preview-footer">
              <button
                className="close-preview-btn"
                onClick={handleGenerate}
                disabled={loading}
              >
                Regenerate
              </button>
              <button className="close-preview-btn" onClick={() => setShowModal(true)}>
                Edit Inputs
              </button>
              <button className="close-preview-btn" onClick={() => setShowPreview(false)}>
                Close Preview
              </button>
            </div>
          </div>
        )}
      </div>

      <AnimatePresence>
        {showModal && (
          <motion.div
            className="hmi-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowModal(false)}
          >
            <motion.div
              className="hmi-modal"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3>AI WebHMI Interface Designer</h3>
                <button className="close-btn" onClick={() => setShowModal(false)}>
                  x
                </button>
              </div>

              <div className="modal-content">
                <div className="input-group">
                  <label>Design Style</label>
                  <div className="style-options">
                    {styles.map((s) => (
                      <button
                        key={s.value}
                        className={`style-btn ${designStyle === s.value ? "active" : ""}`}
                        onClick={() => setDesignStyle(s.value)}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="input-group">
                  <label>Requirements</label>
                  <textarea
                    value={requirement}
                    onChange={(e) => setRequirement(e.target.value)}
                    placeholder="E.g. Create a water tank level control screen with a pump start/stop button and a gauge..."
                  />
                </div>

                <div className="modal-actions">
                  <button className="btn-cancel" onClick={() => setShowModal(false)}>
                    Cancel
                  </button>
                  <button className="btn-generate" onClick={handleGenerate} disabled={loading}>
                    {loading ? "Generating..." : "Generate HMI"}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default HmiGeneratorV2;
