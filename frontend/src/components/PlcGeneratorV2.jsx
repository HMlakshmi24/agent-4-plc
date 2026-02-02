import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./plc_generator_v2.css";
import { API } from '../config/api';

const PlcGeneratorV2 = () => {
  const [showModal, setShowModal] = useState(false);
  const [requirement, setRequirement] = useState("");
  const [language, setLanguage] = useState("ST"); // Default language
  const [plcBrand, setPlcBrand] = useState("generic"); // PLC brand selection
  const [loading, setLoading] = useState(false);
  const [generatedCode, setGeneratedCode] = useState(null);
  const [editedCode, setEditedCode] = useState(""); // User can edit code
  const [isEditing, setIsEditing] = useState(false); // Toggle edit mode
  const [showPreview, setShowPreview] = useState(false);
  const [codeHistory, setCodeHistory] = useState([]); // Keep history visible

  const languages = [
    { value: "ST", label: "Structured Text (ST)", desc: "Text-based, most popular" },
    { value: "LD", label: "Ladder Diagram (LD)", desc: "Graphical relay logic" },
    { value: "FBD", label: "Function Block Diagram (FBD)", desc: "Data flow diagram" },
    { value: "SFC", label: "Sequential Function Chart (SFC)", desc: "State machine" },
    { value: "IL", label: "Instruction List (IL)", desc: "Assembly-like format" }
  ];

  const brands = [
    { value: "generic", label: "Generic IEC 61131-3", logo: "🏭" },
    { value: "siemens", label: "Siemens SIMATIC", logo: "🔷" },
    { value: "mitsubishi", label: "Mitsubishi MELSEC", logo: "🔶" },
    { value: "ab", label: "Allen-Bradley", logo: "🟨" },
    { value: "schneider", label: "Schneider Electric", logo: "🟩" }
  ];

  const handleGenerate = async () => {
    if (!requirement.trim()) return alert("Please enter a requirement!");

    setLoading(true);
    try {
      const response = await fetch(`${API}/plc-v2/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requirement: requirement.trim(),
          language: language,
          plc_brand: plcBrand
        }),
      });

      if (!response.ok) {
        let errorMsg = "Unknown error";
        try {
          const error = await response.json();
          errorMsg = error.detail || error.message || errorMsg;
        } catch {
          errorMsg = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      console.log("Generated code:", data);

      setGeneratedCode(data);
      setEditedCode(data.code); // Initialize edited code with generated code
      setIsEditing(false); // Start in view mode
      setShowPreview(true);
      setShowModal(false); // Auto-close modal as requested

      // Add to history but keep old requests visible
      setCodeHistory([...codeHistory, {
        id: Date.now(),
        requirement: requirement,
        language: language,
        code: data.code,
        timestamp: new Date().toLocaleTimeString()
      }]);

    } catch (err) {
      console.error("Generation error:", err);
      const errorMsg = err.message || "Failed to fetch";
      alert(`❌ Failed to generate code:\n\n${errorMsg}\n\nMake sure:\n1. Backend is running at ${API}\n2. API key is configured\n3. Network is connected`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!generatedCode) return;

    const extension = language === "ST" ? "st" : language === "IL" ? "il" : "txt";
    const filename = `plc_code_${language}_${Date.now()}.${extension}`;

    // Use edited code if user made changes, otherwise use generated code
    const codeToDownload = isEditing ? editedCode : generatedCode.code;

    const element = document.createElement("a");
    const file = new Blob([codeToDownload], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleClearHistory = () => {
    setCodeHistory([]);
    setGeneratedCode(null);
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
    <div className="plc-section-v2">
      <div className="plc-header">
        <div className="plc-text">
          <h2>🤖 AI PLC Code Generator</h2>
          <p>
            Generate IEC 61131-3 compliant PLC code instantly. Supports ST, LD, FBD, SFC, and IL.
            Write requirements in plain English—we handle the rest.
          </p>
        </div>

        <div className="plc-action">
          <motion.button
            className="plc-generate-btn"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleTryNow}
          >
            Start Generating →
          </motion.button>
        </div>
      </div>

      {/* Show generated code and history side by side */}
      <div className="plc-results-container">
        {/* Previous generated codes (left side - scrollable history) */}
        {codeHistory.length > 0 && (
          <div className="plc-history-panel">
            <div className="history-header">
              <h3>📋 Generation History</h3>
              <button className="clear-btn" onClick={handleClearHistory}>Clear All</button>
            </div>
            <div className="history-list">
              {codeHistory.map((item) => (
                <div key={item.id} className="history-item">
                  <div className="history-meta">
                    <span className="lang-badge">{item.language}</span>
                    <span className="time-badge">{item.timestamp}</span>
                  </div>
                  <p className="history-requirement">{item.requirement.substring(0, 50)}...</p>
                  <pre className="history-code">{item.code.substring(0, 200)}...</pre>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Current preview (right side - full code preview) */}
        {showPreview && generatedCode && (
          <div className="plc-preview-panel">
            <div className="preview-header">
              <h3>✅ Code Generated & Validated</h3>
              <div className="preview-meta">
                <span className="language-tag">{generatedCode.language}</span>
                {generatedCode.validated ? (
                  <span className="validated-badge">✓ All Validations Passed</span>
                ) : (
                  <span className="warning-badge">⚠ Review Issues Below</span>
                )}
              </div>
            </div>

            {/* Timestamp */}
            <div className="timestamp-section">
              <small>Generated: {new Date(generatedCode.timestamp).toLocaleString()}</small>
            </div>

            {/* Validation Status & Issues */}
            {generatedCode.warnings && generatedCode.warnings.length > 0 && (
              <div className="validation-section">
                <h4>📋 Validation Report ({generatedCode.warnings.length} items):</h4>
                <div className="validation-list">
                  {generatedCode.warnings.map((warning, idx) => {
                    const isError = warning.startsWith('❌');
                    const isWarning = warning.startsWith('⚠️');
                    const isTip = warning.startsWith('💡');
                    return (
                      <div key={idx} className={`validation-item ${isError ? 'error' : isWarning ? 'warning' : 'tip'}`}>
                        {warning}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Explanation */}
            <div className="explanation-section">
              <h4>📝 Code Explanation & Validation Summary:</h4>
              <div className="explanation-text">
                {generatedCode.explanation.split('\n').map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
              </div>
            </div>

            {/* Code display & editing */}
            <div className="code-preview">
              <div className="code-header">
                <h4>Source Code ({(isEditing ? editedCode : generatedCode.code).split('\n').length} lines)</h4>
                <div className="code-actions">
                  <button
                    className={`edit-btn ${isEditing ? 'editing' : ''}`}
                    onClick={() => setIsEditing(!isEditing)}
                    title={isEditing ? "Save changes" : "Edit code"}
                  >
                    {isEditing ? "✅ Done Editing" : "✏️ Edit Code"}
                  </button>
                  <button
                    className="copy-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(isEditing ? editedCode : generatedCode.code);
                      alert("Code copied to clipboard!");
                    }}
                    title="Copy code"
                  >
                    📋 Copy
                  </button>
                </div>
              </div>

              {isEditing ? (
                <textarea
                  className="code-editor"
                  value={editedCode}
                  onChange={(e) => setEditedCode(e.target.value)}
                  placeholder="Edit your PLC code here..."
                  spellCheck="false"
                />
              ) : (
                <pre><code>{editedCode}</code></pre>
              )}
            </div>

            {/* Action buttons */}
            <div className="preview-actions">
              <button
                className="download-btn"
                onClick={handleDownload}
                title={generatedCode.validated ? "Download this code" : "Fix issues before downloading"}
              >
                💾 Download Code
              </button>
              <button
                className="regenerate-btn"
                onClick={() => setShowPreview(false)}
              >
                🔄 Modify & Regenerate
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal for generation */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            className="plc-modal-overlay-v2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowModal(false)}
          >
            <motion.div
              className="plc-modal-v2"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.3 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3>PLC Code Generator</h3>
                <button
                  className="close-btn"
                  onClick={() => setShowModal(false)}
                >
                  ✕
                </button>
              </div>

              <div className="modal-content">
                {/* Language selection */}
                <div className="selection-section">
                  <label className="section-label">Programming Language</label>
                  <div className="language-options">
                    {languages.map((lang) => (
                      <button
                        key={lang.value}
                        className={`lang-button ${language === lang.value ? 'active' : ''}`}
                        onClick={() => setLanguage(lang.value)}
                        title={lang.desc}
                      >
                        {lang.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Requirement input */}
                <div className="input-section">
                  <label className="section-label">Your Automation Logic</label>
                  <textarea
                    value={requirement}
                    onChange={(e) => setRequirement(e.target.value)}
                    placeholder="Describe your PLC automation in plain English. Example: Create a pump control system with low/high pressure sensors that turns the pump on when pressure is low and off when pressure is high..."
                    className="requirement-textarea"
                  />
                  <div className="input-footer">
                    <span className="char-count">{requirement.length} characters</span>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="modal-actions">
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      setShowModal(false);
                      setRequirement("");
                    }}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn-primary"
                    onClick={handleGenerate}
                    disabled={loading || !requirement.trim()}
                  >
                    {loading ? (
                      <>
                        <span className="spinner"></span> Generating...
                      </>
                    ) : (
                      "Generate Code"
                    )}
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

export default PlcGeneratorV2;
