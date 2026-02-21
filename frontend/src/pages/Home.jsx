import React, { useState } from 'react';

import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import PlcGeneratorV2 from '../components/PlcGeneratorV2';
import HmiGeneratorV3 from '../components/HmiGeneratorV3';
import { LoginModal, RegisterModal } from '../components/LoginModal';
import Footer from '../components/Footer';
import TransparentCard from '../components/TransparentCard';
import { useAuth } from '../context/AuthContext';
import LandingPage from '../components/LandingPage';
import { PrivacyModal, TermsModal, HelpModal, SubmitTicketModal, AboutModal } from '../components/InfoModals';

const Home = () => {
  const { user, logout } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [activeTab, setActiveTab] = useState(null);

  // Content Modals State
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showTicket, setShowTicket] = useState(false);
  const [showAbout, setShowAbout] = useState(false);

  const handleLoginSuccess = () => {
    setShowLogin(false);
  };

  const handleRegisterSuccess = (username) => {
    setShowRegister(false);
    setShowLogin(true);
  };

  // 1. GUEST VIEW: Landing Page
  if (!user) {
    return (
      <>
        <LandingPage
          onLogin={() => setShowLogin(true)}
          onRegister={() => setShowRegister(true)}
        />

        <Footer
          onPrivacy={() => setShowPrivacy(true)}
          onTerms={() => setShowTerms(true)}
          onHelp={() => setShowHelp(true)}
          onTicket={() => setShowTicket(true)}
          onAbout={() => setShowAbout(true)}
        />

        {/* Auth Modals */}
        {showLogin && <LoginModal onClose={() => setShowLogin(false)} onLoginSuccess={handleLoginSuccess} />}
        {showRegister && <RegisterModal onClose={() => setShowRegister(false)} onRegisterSuccess={handleRegisterSuccess} />}

        {/* Content Modals */}
        {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}
        {showTerms && <TermsModal onClose={() => setShowTerms(false)} />}
        {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
        {showTicket && <SubmitTicketModal onClose={() => setShowTicket(false)} />}
        {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
      </>
    );
  }

  // 2. AUTHENTICATED VIEW: App Dashboard
  return (
    <div onClick={() => setActiveTab(null)}>
      <Navbar
        onLoginClick={() => setShowLogin(true)}
        onRegisterClick={() => setShowRegister(true)}
        onTabClick={(tab) => setActiveTab(tab)}
        user={user}
        onLogout={logout}
      />

      {/* Dashboard Content */}
      <PlcGeneratorV2 />

      {/* Industrial Separator */}
      <div className="w-full flex justify-center bg-transparent my-0">
        <div className="w-[90%] h-[1px] bg-slate-200 dark:bg-slate-700"></div>
      </div>

      <HmiGeneratorV3 />

      <Footer
        onPrivacy={() => setShowPrivacy(true)}
        onTerms={() => setShowTerms(true)}
        onHelp={() => setShowHelp(true)}
        onTicket={() => setShowTicket(true)}
        onAbout={() => setShowAbout(true)}
      />

      {activeTab && <TransparentCard tab={activeTab} onClose={() => setActiveTab(null)} />}

      {/* Content Modals for Authenticated Users too */}
      {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}
      {showTerms && <TermsModal onClose={() => setShowTerms(false)} />}
      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
      {showTicket && <SubmitTicketModal onClose={() => setShowTicket(false)} />}
      {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
    </div>
  );
};

export default Home;
