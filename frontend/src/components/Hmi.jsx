import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./hmi.css";
import { API } from "../config/api";

const Hmi = () => {
  const [showModal, setShowModal] = useState(false);
  const [requirement, setRequirement] = useState("");
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  // Trigger API for HMI HTML code generation
  const handleGenerate = async () => {
    if (!requirement.trim()) return alert("Please enter a requirement!");

    setLoading(true);
    try {
      const response = await fetch(`${API}/plc/generate-hmi`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requirement: `Generate an HTML-based HMI interface for: ${requirement}`,
        }),
      });

      if (!response.ok) throw new Error("Error generating HMI code");

      const data = await response.json();
      console.log("Backend HMI response:", data);

      setGenerated(true);
    } catch (err) {
      alert("Failed to generate HMI code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Download the generated HMI file
  const handleDownload = () => {
    window.location.href = `${API}/download/hmi`;
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
    <div className="hmi-section">
      <div className="hmi-text">
        <h2>AI-Powered HMI Code Generation</h2>
        <p>
          Generate intelligent and responsive Human-Machine Interface (HMI) HTML
          designs from natural language. Enter your system requirement and let
          AI create modern, interactive control panels instantly.
        </p>
      </div>

      <div className="hmi-action">
        <motion.button
          className="hmi-generate-btn"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleTryNow}
        >
          Generate HMI
        </motion.button>
      </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            className="hmi-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="hmi-modal"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              {!generated ? (
                <>
                  <h3>Enter HMI Requirement</h3>
                  <textarea
                    value={requirement}
                    onChange={(e) => setRequirement(e.target.value)}
                    placeholder="e.g. Create a tank control HMI with start/stop buttons and temperature gauge..."
                  />
                  <div className="hmi-modal-buttons">
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
                      {loading ? "Generating..." : "Generate HMI"}
                    </button>
                  </div>
                </>
              ) : (
                <div className="hmi-success">
                  <p>✅ Your HMI HTML code has been generated successfully!</p>
                  <button className="download-btn" onClick={handleDownload}>
                    Download HMI
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

export default Hmi;
