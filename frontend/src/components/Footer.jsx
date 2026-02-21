import React from 'react';
import { FaGithub, FaLinkedin, FaTwitter } from 'react-icons/fa';

const Footer = ({ onPrivacy, onTerms, onHelp, onTicket, onAbout }) => {
  return (
    <footer className="bg-slate-900 text-white border-t border-slate-800 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          {/* Logo & Info */}
          <div className="col-span-1 md:col-span-1">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-blue-500">◆</span> Automind AI
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed mb-6">
              AI-Powered PLC & HMI Automation Platform.
            </p>
            <div className="flex gap-4">
              <a href="#" className="text-slate-400 hover:text-blue-600 transition-colors"><FaGithub size={20} /></a>
              <a href="#" className="text-slate-400 hover:text-blue-600 transition-colors"><FaLinkedin size={20} /></a>
              <a href="#" className="text-slate-400 hover:text-blue-600 transition-colors"><FaTwitter size={20} /></a>
            </div>
          </div>

          {/* Product Column */}
          <div>
            <h3 className="text-slate-900 dark:text-white font-bold mb-4">Product</h3>
            <ul className="space-y-3 text-sm text-slate-400">
              <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="hover:text-blue-400 transition-colors text-left">Features</button></li>
              <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="hover:text-blue-400 transition-colors text-left">PLC Generator</button></li>
              <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="hover:text-blue-400 transition-colors text-left">HMI Builder</button></li>
            </ul>
          </div>

          {/* Company Column */}
          <div>
            <h3 className="text-slate-900 dark:text-white font-bold mb-4">Company</h3>
            <ul className="space-y-3 text-sm text-slate-400">
              <li><button onClick={onAbout} className="hover:text-blue-400 transition-colors text-left">About Us</button></li>
              <li><button onClick={onAbout} className="hover:text-blue-400 transition-colors text-left">Contact</button></li>
            </ul>
          </div>

          {/* Support Column */}
          <div>
            <h3 className="text-slate-900 dark:text-white font-bold mb-4">Support</h3>
            <ul className="space-y-3 text-sm text-slate-400">
              <li><button onClick={onHelp} className="hover:text-blue-400 transition-colors text-left">Help Center</button></li>
              <li><button onClick={onTicket} className="hover:text-blue-400 transition-colors text-left">Submit Ticket</button></li>
              <li><a href="mailto:hm.lakshmi@parijat.com" className="hover:text-blue-400 transition-colors">hm.lakshmi@parijat.com</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} Parijat Controlware, Inc. All rights reserved.</p>
          <div className="flex gap-6">
            <button onClick={onPrivacy} className="hover:text-slate-300">Privacy Policy</button>
            <button onClick={onTerms} className="hover:text-slate-300">Terms of Service</button>
          </div>
        </div>
      </div>
    </footer>
  );
};
export default Footer;
