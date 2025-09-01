import React from 'react';

const Footer = () => {
  return (
    <div style={{ backgroundColor: '#f3f8fc', color: '#002b5b', padding: '3rem 1rem', fontFamily: 'Arial, sans-serif' }}>
      {/* Top Contact Section */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '4rem',
        marginBottom: '6rem',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold' }}>Call us</div>
          <div>+1-234-567-890</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold' }}>Write to us</div>
          <div>sales@parijat.com</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontWeight: 'bold' }}>Address</div>
          <div>9603 Neuens Rd. Houston, TX. 77080</div>
        </div>
      </div>

      {/* Bottom Content Section */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: '10rem',
        marginBottom: '2rem',
      }}>
        {/* About Us */}
        <div style={{ maxWidth: '250px' }}>
          <img src="https://parijat.com/wp-content/uploads/2023/08/ezgif.com-gif-maker-87.webp" alt="Parijat Logo" style={{ width: '180px', marginBottom: '1rem' }} />
          <p style={{ fontSize: '0.9rem' }}>
            Since 1989, Our Team Has Succeeded In Understanding The Needs Of The Industry And Creating Reliable Products To Serve Them All.
          </p>
        </div>

        {/* Quick Links */}
        <div>
          <h4>Quick Links</h4>
          <p>Products</p>
          <p>Services</p>
          <p>Solutions</p>
          
        </div>

        {/* Important Links */}
        <div>
          <h4>Important Links</h4>
          <p>About Us</p>
          <p>Contact Us</p>
        
          <p>Disclaimer</p>
        </div>


        
        {/* Follow Us */}
        <div>
          <h4>Follow Us</h4>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
            <div style={{
              backgroundColor: '#002b5b',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              color: 'white',
              fontSize: '1rem'
            }}>
              in
            </div>
            <div style={{
              backgroundColor: '#002b5b',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              color: 'white',
              fontSize: '1rem'
            }}>
              ▶
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div style={{ backgroundColor: 'black', color: 'white', padding: '1rem', textAlign: 'center' }}>
        <p style={{ margin: 0 }}>© Copyright Parijat, All Rights Reserved Parijat.</p>
      </div>
    </div>
  );
};

export default Footer;
