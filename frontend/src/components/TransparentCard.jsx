import React from 'react';
import { motion } from 'framer-motion';

const contentMap = {
  support: {
    title: 'Support',
    content: 'For any issues, contact our 24x7 support at support@parijat.com or call +1 234 567 890.'
  },
  about: {
    title: 'About Us',
    content: 'We are committed to delivering state-of-the-art systems powered by artificial intelligence and real-time analytics.'
  },
  contact: {
    title: 'Contact Us',
    content: 'Reach us at contact@parijat.com or visit our HQ at 9603 Neuens Rd. Houston, TX. 77080'
  }
};

const TransparentCard = ({ tab, onClose }) => {
  const { title, content } = contentMap[tab];

  return (
    <>
      {/* BACKDROP */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          zIndex: 999, // below modal but above other UI
          backgroundColor: 'transparent'
        }}
      />
      
      {/* CARD */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.5 }}
        style={{
          position: 'absolute',
          top: '20%',
          left: '55%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          padding: '2rem',
          borderRadius: '10px',
          maxWidth: '500px',
          zIndex: 1000,
          boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
        }}
      >
        <h2 style={{ color: 'black' }}>{title}</h2>
        <p style={{ marginTop: '1rem', fontSize: '1.1rem', color: 'black' }}>{content}</p>
        <button onClick={onClose} style={{
          marginTop: '1.5rem',
          backgroundColor: 'black',
          color: 'white',
          border: 'none',
          padding: '0.6rem 1.2rem',
          borderRadius: '6px',
          cursor: 'pointer'
        }}>
          Close
        </button>
      </motion.div>
    </>
  );
};

export default TransparentCard;
