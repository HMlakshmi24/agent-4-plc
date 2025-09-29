import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./hmi.css";

const Hmi = () => {
  const [showModal, setShowModal] = useState(false);

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
        <h2>AI-Powered HMI Design</h2>
        <p>
          Build smarter Human-Machine Interfaces with AI-driven automation.
          Craft modern HMI screens with minimal effort and maximum efficiency.
        </p>
      </div>

      <div className="hmi-action">
        <motion.button
          className="hmi-btn"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleTryNow}
        >
          HMI Try Now
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
              <h3>🚀 Coming Soon!</h3>
              <p>
                HMI generation with AI is under development. Stay tuned for the
                upcoming release.
              </p>
              <button className="cancel-btn" onClick={() => setShowModal(false)}>
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Hmi;
