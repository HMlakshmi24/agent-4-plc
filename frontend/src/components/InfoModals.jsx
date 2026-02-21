import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiX, FiCheckCircle, FiAlertTriangle, FiMail } from 'react-icons/fi';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001/api";
const ModalBase = ({ title, onClose, children }) => (
    <AnimatePresence>
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 sm:p-6">
            <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
                onClick={onClose}
            />
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="relative w-full max-w-3xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
            >
                <div className="flex justify-between items-center p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white">{title}</h3>
                    <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                        <FiX size={24} />
                    </button>
                </div>
                <div className="p-8 overflow-y-auto text-slate-600 dark:text-slate-300 leading-relaxed text-sm md:text-base space-y-6">
                    {children}
                </div>
                <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex justify-end">
                    <button onClick={onClose} className="px-6 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-semibold rounded-lg transition-colors">
                        Close
                    </button>
                </div>
            </motion.div>
        </div>
    </AnimatePresence>
);

export const PrivacyModal = ({ onClose }) => (
    <ModalBase title="Privacy Policy" onClose={onClose}>
        <p><strong>Automind AI respects your privacy.</strong></p>
        <p>We collect:</p>
        <ul className="list-disc pl-5 space-y-1">
            <li>Name</li>
            <li>Email</li>
            <li>Company information</li>
            <li>Usage logs (non-sensitive)</li>
            <li>Project prompts for system improvement</li>
        </ul>
        <p>We do NOT:</p>
        <ul className="list-disc pl-5 space-y-1">
            <li>Sell user data</li>
            <li>Share user projects with third parties</li>
            <li>Store sensitive industrial process data without consent</li>
        </ul>
        <p>All user data is handled securely and used only to improve service quality.</p>
        <p className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            For privacy concerns, contact: <a href="mailto:hm.lakshmi@parijat.com" className="text-blue-600 hover:underline">hm.lakshmi@parijat.com</a>
        </p>
    </ModalBase>
);

export const TermsModal = ({ onClose }) => (
    <ModalBase title="Terms & Conditions" onClose={onClose}>
        <p>By using Automind AI, you agree that:</p>
        <ol className="list-decimal pl-5 space-y-2">
            <li>You are responsible for verifying generated code.</li>
            <li>The platform provides AI-assisted development tools, not certified engineering approval.</li>
            <li>You will not use the platform for malicious, illegal, or unsafe industrial activities.</li>
            <li>Parijat Controlware, Inc. is not liable for damages resulting from unverified PLC deployment.</li>
        </ol>
        <p className="mt-4">The platform may update features and policies periodically. Continued use implies agreement with updated terms.</p>
    </ModalBase>
);

export const HelpModal = ({ onClose }) => (
    <ModalBase title="Help Center" onClose={onClose}>
        <div className="space-y-6">
            <div>
                <h4 className="font-bold text-slate-900 dark:text-white mb-2">1. Is the generated PLC code production ready?</h4>
                <p>The platform generates structured IEC-compliant logic. However, engineers must review and validate all logic before deployment in production systems.</p>
            </div>
            <div>
                <h4 className="font-bold text-slate-900 dark:text-white mb-2">2. Does Automind AI replace PLC engineers?</h4>
                <p>No. Automind AI assists engineers. It accelerates development but does not replace engineering validation and domain expertise.</p>
            </div>
            <div>
                <h4 className="font-bold text-slate-900 dark:text-white mb-2">3. Can I use this with Siemens / Allen Bradley / Codesys?</h4>
                <p>The platform generates IEC 61131-3 compliant Structured Text, compatible with most IEC-based PLC environments.</p>
            </div>
            <div>
                <h4 className="font-bold text-slate-900 dark:text-white mb-2">4. What if AI makes a mistake?</h4>
                <p>AI may occasionally generate imperfect logic. Always verify logic against your process requirements before commissioning.</p>
            </div>
        </div>
    </ModalBase>
);

export const SubmitTicketModal = ({ onClose }) => {
    const [issueType, setIssueType] = useState('Technical Issue');
    const [description, setDescription] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!description.trim()) {
            alert("Please provide a description.");
            return;
        }

        setSubmitting(true);
        try {
            const token = localStorage.getItem('automind_token') || localStorage.getItem('token');
            const response = await axios.post(`${API_BASE_URL}/support/ticket`, {
                issue_type: issueType,
                description: description
            }, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            alert(response.data.message || "Ticket submitted successfully. We will be in touch shortly!");
            onClose();
        } catch (err) {
            console.error("Support API Error:", err);
            // Fallback alert for unauthenticated users or server errors
            alert("Failed to send ticket. Please email hm.lakshmi@parijat.com directly.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <ModalBase title="Submit Support Ticket" onClose={onClose}>
            <div className="flex flex-col gap-4">
                <p>Please provide details about your issue. Our engineering team will review your request and respond within 24–48 business hours.</p>

                <form className="space-y-4" onSubmit={handleSubmit}>
                    <div>
                        <label className="block text-sm font-semibold mb-1">Issue Type</label>
                        <select
                            value={issueType}
                            onChange={(e) => setIssueType(e.target.value)}
                            className="w-full p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                        >
                            <option value="Technical Issue">Technical Issue</option>
                            <option value="Billing Question">Billing Question</option>
                            <option value="Feature Request">Feature Request</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-semibold mb-1">Description</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="w-full p-2 h-32 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                            placeholder="Describe your issue..."
                        ></textarea>
                    </div>
                    <div className="text-sm text-slate-500">
                        Ticket responses will be sent to your registered email.
                    </div>
                    <button
                        type="submit"
                        disabled={submitting}
                        className={`w-full py-3 text-white font-bold rounded-xl shadow-lg transition-colors ${submitting ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'}`}
                    >
                        {submitting ? 'Submitting...' : 'Submit Ticket'}
                    </button>
                </form>

                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 text-center text-sm">
                    Or email us directly at <a href="mailto:hm.lakshmi@parijat.com" className="text-blue-600 font-bold">hm.lakshmi@parijat.com</a>
                </div>
            </div>
        </ModalBase>
    );
};

export const AboutModal = ({ onClose }) => (
    <ModalBase title="About Parijat Controlware, Inc." onClose={onClose}>
        <div className="flex flex-col items-center mb-6">
            <div className="text-4xl text-blue-600 mb-2">⚙️</div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Parijat Controlware, Inc.</h2>
            <p className="text-sm font-bold text-slate-500 uppercase tracking-widest">Automation & Controls Solution</p>
        </div>

        <p className="mb-4">
            <strong>Parijat Controlware, Inc.</strong> is a Houston-based automation and controls engineering company serving industrial clients since 1989.
        </p>

        <p className="mb-4">With decades of experience in:</p>
        <ul className="list-disc pl-5 space-y-1 mb-4">
            <li>Process automation</li>
            <li>Control systems engineering</li>
            <li>Industrial instrumentation</li>
            <li>SCADA systems</li>
            <li>Compliance solutions</li>
        </ul>

        <p className="mb-6">
            Parijat has built a reputation for delivering reliable, industry-grade automation systems across multiple sectors.
            <br /><br />
            <strong>Automind AI</strong> is an innovation initiative built to modernize PLC and automation logic development using artificial intelligence while maintaining industrial compliance standards.
        </p>

        <div className="bg-slate-100 dark:bg-slate-800 p-4 rounded-xl text-center">
            <p className="font-bold">Address:</p>
            <p>9603 Neuens Rd. Houston, TX 77080</p>
            <p className="mt-2"><a href="https://parijat.com" target="_blank" className="text-blue-600 hover:underline">https://parijat.com</a></p>
        </div>
    </ModalBase>
);
