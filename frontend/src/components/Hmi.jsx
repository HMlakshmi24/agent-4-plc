import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./hmi.css";
import "./unified-modal.css";
import { API } from "../config/api";

const Hmi = () => {
  const [showModal, setShowModal] = useState(false);
  const [requirement, setRequirement] = useState("");
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [hmiCode, setHmiCode] = useState("");
  const [previewMode, setPreviewMode] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState("");
  const [style, setStyle] = useState("industrial");
  const [importedFile, setImportedFile] = useState(null);
  const [importedFileName, setImportedFileName] = useState("");
  const [temperature, setTemperature] = useState(0.3);
  const [exportFormat, setExportFormat] = useState("html");
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const fileInputRef = useRef(null);

  // ✅ NEW: Load history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("hmiHistory");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to load HMI history:", e);
      }
    }
  }, []);

  // ✅ NEW: Save to history after successful generation
  const addToHistory = (req, st, exp) => {
    const user = JSON.parse(localStorage.getItem("automind_user") || "{}");

    const newEntry = {
      id: Date.now(),
      requirement: req.substring(0, 50),
      style: st,
      exportFormat: exp,
      timestamp: new Date().toLocaleString(),
      code: hmiCode
    };
    const updated = [newEntry, ...history].slice(0, 10);
    setHistory(updated);
    localStorage.setItem("hmiHistory", JSON.stringify(updated));
  };

  const handleGenerate = async () => {
    if (!requirement.trim()) {
      setError("Please enter a requirement!");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const sendStyle = style === "p_and_id" ? "pid" : "modern";

      const response = await fetch(`${API}/plc/generate-hmi`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requirement: requirement,
          style: sendStyle,
          current_hmi_code: importedFile,
          temperature: temperature,
          export_format: exportFormat
        }),
      });
      if (!response.ok) {
        let errText = await response.text();
        try {
          const j = JSON.parse(errText);
          errText = j.detail || j.message || errText;
        } catch (e) { }
        setError(`Generation failed: ${errText}`);
        setLoading(false);
        return;
      }

      const data = await response.json();
      console.log("Backend HMI response:", data);

      const sanitizeHmi = (html) => {
        try {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");

          const metas = Array.from(doc.querySelectorAll('meta[name]'));
          const seen = new Set();
          metas.forEach((m) => {
            const n = m.getAttribute('name');
            if (seen.has(n)) m.remove();
            else seen.add(n);
          });

          const nameEls = Array.from(doc.getElementsByTagName('name'));
          nameEls.forEach((el) => el.parentNode && el.parentNode.removeChild(el));

          return doc.documentElement.outerHTML;
        } catch (e) {
          return html
            .replace(/<name[^>]*>[\s\S]*?<\/name>/gi, "")
            .replace(/(<meta[^>]*name=\"([^\"]+)\"[^>]*>)([\s\S]*?)/gi, (m) => m);
        }
      };

      const cleaned = sanitizeHmi(data.hmi_code || "");
      setHmiCode(cleaned);
      setGenerated(true);
      setPreviewMode(true);
      setShowModal(true);
      setLoading(false);

      // ✅ NEW: Add to history
      addToHistory(requirement, sendStyle, exportFormat);
    } catch (err) {
      console.error(err);
      setError(err?.message || "Failed to generate HMI code. Please try again.");
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!requirement.trim()) {
      setError("No previous requirement found!");
      return;
    }
    setError("");
    setShowModal(true);
    setRegenerating(true);
    // Don't clear hmiCode here to prevent blank screen, just show loading state
    try {
      await handleGenerate();
    } finally {
      setRegenerating(false);
    }
  };

  const handleDownload = () => {
    if (!hmiCode) {
      alert("No HMI code generated yet!");
      return;
    }

    const blob = new Blob([hmiCode], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hmi_${style}_${Date.now()}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImportFile = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      setImportedFile(text);
      setImportedFileName(file.name);
      setError("");
    } catch (err) {
      setError("Failed to read file. Please ensure it's a valid HTML file.");
    }
  };

  const handleTryNow = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Please login first!");
      return;
    }
    setError("");
    setShowModal(true);
  };

  const handleClose = () => {
    setShowModal(false);
    setGenerated(false);
    setPreviewMode(false);
    setRequirement("");
    setImportedFile(null);
    setImportedFileName("");
    setError("");
    setShowHistory(false);
  };

  const loadFromHistory = (entry) => {
    setHmiCode(entry.code);
    setRequirement(entry.requirement);
    setStyle(entry.style);
    setExportFormat(entry.exportFormat);
    setGenerated(true);
    setPreviewMode(true);
    setShowHistory(false);
  };

  return (
    <div className="hmi-section">
      <div className="hmi-text">
        <h2>AI WebHMI Interface Designer</h2>
        <p>
          Generate professional Human-Machine Interface (HMI) HTML designs from natural language.
          Supports Industrial ISA-101 standards, P&ID style diagrams, and modern dashboards.
          Import existing HMIs for AI-powered modifications.
        </p>
        <div className="hmi-features">
          <span className="feature-badge">✓ ISA-101 Compliant</span>
          <span className="feature-badge">✓ P&ID Style</span>
          <span className="feature-badge">✓ FactoryTalk Compatible</span>
          <span className="feature-badge">✓ Import & Modify</span>
        </div>
      </div>

      <div className="hmi-action">
        <motion.button
          className="hmi-generate-btn"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleTryNow}
        >
          Design HMI
        </motion.button>
      </div>

      <AnimatePresence>
        {showModal && (
          <motion.div
            className="hmi-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="hmi-modal enhanced"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {!generated ? (
                <>
                  <h3>🎨 Design Your HMI Interface</h3>

                  <div className="style-selector">
                    <label>HMI Style:</label>
                    <div className="style-options">
                      <button
                        className={`style-btn ${style === "industrial" ? "active" : ""}`}
                        onClick={() => setStyle("industrial")}
                      >
                        🏭 Industrial (ISA-101)
                      </button>
                      <button
                        className={`style-btn ${style === "p_and_id" ? "active" : ""}`}
                        onClick={() => setStyle("p_and_id")}
                      >
                        📊 P&ID Diagram
                      </button>
                      <button
                        className={`style-btn ${style === "modern" ? "active" : ""}`}
                        onClick={() => setStyle("modern")}
                      >
                        ✨ Modern Dashboard
                      </button>
                    </div>
                  </div>

                  <div className="export-format-selector">
                    <label>Export Format:</label>
                    <div className="format-options">
                      <button
                        className={`format-btn ${exportFormat === "html" ? "active" : ""}`}
                        onClick={() => setExportFormat("html")}
                      >
                        📄 Standard HTML
                      </button>
                      <button
                        className={`format-btn ${exportFormat === "factorytalk" ? "active" : ""}`}
                        onClick={() => setExportFormat("factorytalk")}
                      >
                        🏢 FactoryTalk View
                      </button>
                      <button
                        className={`format-btn ${exportFormat === "webforms" ? "active" : ""}`}
                        onClick={() => setExportFormat("webforms")}
                      >
                        🌐 ASP.NET WebForms
                      </button>
                    </div>
                  </div>

                  {error && <div className="error-message">⚠️ {error}</div>}

                  {history.length > 0 && (
                    <div className="history-section">
                      <button
                        className={`history-toggle ${showHistory ? "active" : ""}`}
                        onClick={() => setShowHistory(!showHistory)}
                      >
                        ⏱️ Recent HMIs ({history.length})
                      </button>
                      {showHistory && (
                        <div className="history-list">
                          {history.map((entry) => (
                            <div key={entry.id} className="history-item">
                              <div className="history-info">
                                <strong>{entry.requirement}</strong>
                                <small>{entry.timestamp}</small>
                              </div>
                              <button
                                className="history-load-btn"
                                onClick={() => loadFromHistory(entry)}
                              >
                                Load
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="create-new-section">
                    <h4>Create New HMI</h4>
                  </div>

                  <div className="import-section">
                    <label>Import Existing HMI (Optional):</label>
                    <div className="import-controls">
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImportFile}
                        accept=".html,.htm"
                        style={{ display: "none" }}
                      />
                      <button
                        className="import-btn"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        📁 Import HTML
                      </button>
                      {importedFile && (
                        <div className="import-status-box">
                          <span className="import-status-icon">✓</span>
                          <span className="import-status-text">
                            {importedFileName} ({Math.round(importedFile.length / 1024)}KB)
                          </span>
                          <button
                            className="import-clear-btn"
                            onClick={() => {
                              setImportedFile(null);
                              setImportedFileName("");
                            }}
                            title="Remove imported file"
                          >
                            ✕
                          </button>
                        </div>
                      )}
                    </div>
                    <small className="help-text">
                      Upload previous HMI to modify or extend with AI
                    </small>
                  </div>

                  <div className="requirement-section">
                    <label>
                      {importedFile ? "Describe modifications:" : "Describe your HMI:"}
                    </label>
                    <textarea
                      value={requirement}
                      onChange={(e) => setRequirement(e.target.value)}
                      placeholder={
                        importedFile
                          ? "e.g., Add a temperature gauge and change the start button to green..."
                          : "e.g., Create a tank control HMI with start/stop buttons, level indicator, and temperature gauge..."
                      }
                      rows={4}
                    />
                  </div>

                  <div className="consistency-section">
                    <label>
                      Generation Mode:
                      <span className="temp-value">
                        {temperature === 0 ? "Deterministic" : temperature < 0.5 ? "Consistent" : "Creative"}
                      </span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="temp-slider"
                    />
                    <small className="help-text">
                      {temperature === 0
                        ? "Same input = same output (recommended for iterations)"
                        : temperature < 0.5
                          ? "Minor variations on regeneration"
                          : "More creative variations each time"}
                    </small>
                  </div>

                  <div className="hmi-modal-buttons">
                    <button className="cancel-btn" onClick={handleClose}>
                      Cancel
                    </button>
                    <button
                      className="generate-btn"
                      onClick={handleGenerate}
                      disabled={loading}
                    >
                      {loading ? "🔄 Generating..." : "🚀 Generate HMI"}
                    </button>
                  </div>
                </>
              ) : (
                <div className="hmi-result">
                  {error && <div className="error-message">⚠️ {error}</div>}
                  <h3>✅ HMI Generated Successfully!</h3>

                  <div className="result-actions">
                    <button
                      className="preview-btn"
                      onClick={() => setPreviewMode(!previewMode)}
                    >
                      {previewMode ? "📝 Show Code" : "👁️ Preview"}
                    </button>
                    <button className="download-btn" onClick={handleDownload}>
                      💾 Download HTML
                    </button>
                    <button
                      className="regenerate-btn"
                      onClick={handleRegenerate}
                      disabled={loading || regenerating}
                    >
                      {regenerating || loading ? "🔄 Regenerating..." : "🔄 Re-generate"}
                    </button>
                  </div>

                  <div className="result-display" style={{ position: 'relative' }}>
                    {(loading || regenerating) && (
                      <div style={{
                        position: 'absolute',
                        inset: 0,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'rgba(0,0,0,0.5)',
                        zIndex: 10,
                        borderRadius: '8px'
                      }}>
                        <div className="loading-spinner" style={{ color: 'white', fontWeight: 'bold' }}>
                          🔄 Updating Layout...
                        </div>
                      </div>
                    )}
                    {previewMode ? (
                      <iframe
                        srcDoc={hmiCode}
                        title="HMI Preview"
                        className="hmi-preview"
                        sandbox="allow-scripts"
                      />
                    ) : (
                      <pre className="code-preview">
                        <code>{hmiCode}</code>
                      </pre>
                    )}
                  </div>

                  <div className="generation-info">
                    <small>
                      Style: <strong>{style}</strong> | Mode:{" "}
                      <strong>
                        {temperature === 0 ? "Deterministic" : "Creative"}
                      </strong>
                    </small>
                  </div>

                  <button className="close-btn" onClick={handleClose}>
                    Close
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Hmi;
