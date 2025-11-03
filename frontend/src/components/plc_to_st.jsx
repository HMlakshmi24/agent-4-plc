import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./plc_to_st.css";
import { API } from '../config/api'; 

const PlcGenerator = () => {
  const [showModal, setShowModal] = useState(false);
  const [requirement, setRequirement] = useState("");
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  const handleGenerate = async () => {
    if (!requirement.trim()) return alert("Please enter a requirement!");

    setLoading(true);
    try {
      const response = await fetch(`${API}/plc/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirement }),
      });

      if (!response.ok) throw new Error("Error generating code");

      const data = await response.json();
      console.log("Backend response:", data);

      setGenerated(true); // Show success message & download button
    } catch (err) {
      alert("Failed to generate ST code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    window.location.href = `${API}/download/plc`;
  };

  // Handle Try Now click
  const handleTryNow = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please login first!");
      return;
    }
    setShowModal(true);
  };

  return (
    <div className="plc-section">
      <div className="plc-text">
        <h2>AI Smarter PLC Code Generation</h2>
        <p>
          Automate your PLC Structured Text coding with AI-driven precision.
          Enter your requirement, and let our agent instantly craft optimized,
          ready-to-deploy ST logic.
        </p>
      </div>

      <div className="plc-action">
        <motion.button
          className="plc-generate-btn"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleTryNow}
        >
          Try Now
        </motion.button>
      </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            className="plc-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="plc-modal"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {!generated ? (
                <>
                  <h3>Enter Requirement</h3>
                  <textarea
                    value={requirement}
                    onChange={(e) => setRequirement(e.target.value)}
                    placeholder="e.g. Generate Siemens ST code for a tank system..."
                  />
                  <div className="plc-modal-buttons">
                    <button
                      className="cancel-btn"
                      onClick={() => setShowModal(false)}
                    >
                      Cancel
                    </button>
                    <button
                      className="generate-btn"
                      onClick={handleGenerate}
                      disabled={loading}
                    >
                      {loading ? "Generating..." : "Generate"}
                    </button>
                  </div>
                </>
              ) : (
                <div className="plc-success">
                  <p>✅ Your code has been generated successfully!</p>
                  <button className="download-btn" onClick={handleDownload}>
                    Download Code
                  </button>
                  <button
                    className="cancel-btn"
                    onClick={() => {
                      setShowModal(false);
                      setGenerated(false);
                      setRequirement("");
                    }}
                  >
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

export default PlcGenerator;
