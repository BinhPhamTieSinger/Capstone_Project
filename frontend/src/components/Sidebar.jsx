import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Cpu, Command } from 'lucide-react';
import axios from 'axios';
import { motion } from 'framer-motion';

const Sidebar = ({ onUploadSuccess }) => {
    const [uploading, setUploading] = useState(false);
    const [status, setStatus] = useState(null); // 'success', 'error'
    const [info, setInfo] = useState('');

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        setStatus(null);
        setInfo('');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await axios.post('http://localhost:8000/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setStatus('success');
            setInfo(res.data.info);
            if (onUploadSuccess) onUploadSuccess();
        } catch (err) {
            console.error(err);
            setStatus('error');
            setInfo('Failed to upload PDF. Check backend console.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="w-72 h-full bg-zinc-950 border-r border-zinc-800 flex flex-col font-sans transition-all duration-300">
            {/* Header */}
            <div className="p-6 border-b border-zinc-800 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-zinc-100 flex items-center justify-center shadow-lg shadow-zinc-900/50">
                    <Command className="text-zinc-900 w-5 h-5" />
                </div>
                <div>
                    <h1 className="text-lg font-bold text-zinc-100 tracking-tight">AgentHub</h1>
                    <div className="text-[10px] text-zinc-500 font-mono tracking-wider">CAPSTONE.V1</div>
                </div>
            </div>

            <div className="p-4 flex-1 overflow-y-auto custom-scrollbar">
                {/* Upload Section */}
                <div className="mb-8">
                    <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4 px-2">Knowledge Base</h2>

                    <label className="flex flex-col items-center justify-center w-full h-28 border border-dashed border-zinc-700 rounded-xl cursor-pointer hover:border-zinc-500 hover:bg-zinc-900/50 transition-all group">
                        <div className="flex flex-col items-center justify-center pt-2 pb-3">
                            <motion.div
                                animate={uploading ? { y: [0, -3, 0] } : {}}
                                transition={{ repeat: Infinity, duration: 1 }}
                            >
                                <Upload className="w-6 h-6 mb-2 text-zinc-600 group-hover:text-zinc-300 transition-colors" />
                            </motion.div>
                            <p className="text-xs text-zinc-500 group-hover:text-zinc-400 font-medium">
                                {uploading ? 'Processing...' : 'Upload Document (PDF/TXT/DOCX)'}
                            </p>
                        </div>
                        <input type="file" className="hidden" accept=".pdf,.txt,.docx" onChange={handleFileUpload} disabled={uploading} />
                    </label>

                    {status && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className={`mt-3 text-[11px] p-2 rounded-md flex items-start gap-2 border ${status === 'success' ? 'bg-emerald-950/30 border-emerald-900/50 text-emerald-400' : 'bg-red-950/30 border-red-900/50 text-red-400'
                                }`}>
                            {status === 'success' ? <CheckCircle size={14} className="mt-0.5 shrink-0" /> : <AlertCircle size={14} className="mt-0.5 shrink-0" />}
                            <span className="leading-tight">{info}</span>
                        </motion.div>
                    )}

                    {/* Active File Indicator */}
                    {status === 'success' && (
                        <div className="mt-4 px-2">
                            <h3 className="text-[10px] font-semibold text-zinc-600 uppercase mb-2">Active Document</h3>
                            <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 p-2 rounded-md">
                                <FileText size={14} className="text-indigo-400 shrink-0" />
                                <span className="text-xs text-zinc-300 truncate">
                                    {info.replace('PDF processed successfully. Added ', '').replace(' chunks to knowledge base.', '')}
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Tools Section */}
                <div>
                    <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 px-2">Available Capabilities</h2>
                    <div className="flex flex-col gap-1">
                        {[
                            { name: 'RAG Search', icon: FileText, desc: 'Semantic document analysis' },
                            { name: 'Data Visualization', icon: Cpu, desc: 'Chart & graph generation' },
                            { name: 'Web Research', icon: Command, desc: 'Real-time internet fetching' },
                            { name: 'Calculator', icon: Cpu, desc: 'Math computations' },
                            { name: 'Word Counter', icon: FileText, desc: 'Text statistics' },
                            { name: 'Summarizer', icon: FileText, desc: 'Condense long text' },
                            { name: 'Sentiment', icon: FileText, desc: 'Analyze tone' },
                            { name: 'Translator', icon: Command, desc: 'Multi-language support' },
                            { name: 'URL Fetcher', icon: Command, desc: 'Extract web content' }
                        ].map((tool, i) => (
                            <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-zinc-900 transition-colors group cursor-default">
                                <div className="text-zinc-600 group-hover:text-zinc-400 transition-colors">
                                    <tool.icon size={16} />
                                </div>
                                <div>
                                    <div className="text-sm font-medium text-zinc-300 group-hover:text-zinc-100">{tool.name}</div>
                                    <div className="text-[10px] text-zinc-600 group-hover:text-zinc-500">{tool.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-zinc-800">
                <div className="flex items-center gap-2 text-zinc-600">
                    <div className="w-2 h-2 rounded-full bg-emerald-500/50 animate-pulse"></div>
                    <span className="text-xs font-medium">System Operational</span>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
