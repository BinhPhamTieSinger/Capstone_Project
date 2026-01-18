import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, AlertTriangle, Mic, MicOff } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

// Chart Renderer Component
const ChartRenderer = ({ data }) => {
    try {
        // Extract JSON if embedded in text
        let jsonStr = data;
        const jsonMatch = data.match(/\{[\s\S]*"type"[\s\S]*"datasets"[\s\S]*\}/);
        if (jsonMatch) {
            jsonStr = jsonMatch[0];
        }

        // Clean markdown code blocks if present
        const cleanData = jsonStr.replace(/```json/g, '').replace(/```/g, '').trim();
        const chartData = JSON.parse(cleanData);
        if (!chartData.datasets || !chartData.labels) return null;

        // Transform data for Recharts (Array of objects)
        const transformedData = chartData.labels.map((label, i) => {
            const entry = { name: label };
            chartData.datasets.forEach(dataset => {
                entry[dataset.label] = dataset.data[i];
            });
            return entry;
        });

        const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

        const commonProps = {
            width: 500,
            height: 300,
            data: transformedData,
            margin: { top: 5, right: 30, left: 20, bottom: 5 }
        };

        return (
            <div className="my-4 p-5 rounded-lg bg-zinc-900 border border-zinc-800 w-full max-w-lg shadow-sm">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-sm font-semibold text-zinc-100">{chartData.title}</h3>
                    <div className="text-xs text-zinc-500 font-mono bg-zinc-800 px-2 py-1 rounded">{chartData.type.toUpperCase()}</div>
                </div>

                <div className="w-full h-64 text-xs">
                    <ResponsiveContainer width="100%" height="100%">
                        {chartData.type === 'line' ? (
                            <LineChart {...commonProps}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis dataKey="name" stroke="#666" />
                                <YAxis stroke="#666" />
                                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                                <Legend />
                                {chartData.datasets.map((dataset, i) => (
                                    <Line key={i} type="monotone" dataKey={dataset.label} stroke={colors[i % colors.length]} strokeWidth={2} />
                                ))}
                            </LineChart>
                        ) : chartData.type === 'pie' ? (
                            <PieChart>
                                <Pie
                                    data={transformedData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey={chartData.datasets[0].label}
                                >
                                    {transformedData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                                <Legend />
                            </PieChart>
                        ) : (
                            // Default to Bar
                            <BarChart {...commonProps}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                <XAxis dataKey="name" stroke="#666" />
                                <YAxis stroke="#666" />
                                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                                <Legend />
                                {chartData.datasets.map((dataset, i) => (
                                    <Bar key={i} dataKey={dataset.label} fill={colors[i % colors.length]} radius={[4, 4, 0, 0]} />
                                ))}
                            </BarChart>
                        )}
                    </ResponsiveContainer>
                </div>
            </div>
        );
    } catch (e) {
        console.error(e);
        return <code className="text-xs text-red-500 bg-red-950/20 px-2 py-1 rounded flex items-center gap-2"><AlertTriangle size={12} /> Visualization Error</code>;
    }
};

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Ready to assist. Upload a document or ask a question to begin.' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const recognitionRef = useRef(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const res = await axios.post('http://localhost:8000/chat', {
                message: userMsg,
                thread_id: "demo-thread"
            });

            setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { role: 'assistant', content: "Server Error: Unable to reach the backend. Please verify your connection." }]);
        } finally {
            setLoading(false);
        }
    };

    const isChart = (text) => {
        if (!text) return false;
        // Check for JSON-like structure (type, datasets) even if surrounded by text
        return text.includes('"type":') && text.includes('"datasets":') && text.includes('{');
    };

    return (
        <div className="flex-1 h-full flex flex-col bg-[#09090b] relative">
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 z-10 custom-scrollbar">
                <AnimatePresence>
                    {messages.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start max-w-3xl'}`}
                        >
                            {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0 mt-4">
                                    <Bot size={14} className="text-zinc-300" />
                                </div>
                            )}

                            <div className={`p-4 rounded-lg shadow-sm text-sm leading-relaxed ${msg.role === 'user'
                                ? 'bg-zinc-100 text-zinc-900 font-medium max-w-[80%]'
                                : 'bg-transparent text-zinc-300 w-full'
                                }`}>
                                {isChart(msg.content) ? (
                                    <ChartRenderer data={msg.content} />
                                ) : (
                                    <div className="markdown-content whitespace-pre-wrap leading-loose">
                                        <ReactMarkdown
                                            components={{
                                                code: ({ node, ...props }) => <code className="bg-zinc-800 text-zinc-200 px-1 py-0.5 rounded text-xs font-mono" {...props} />
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {loading && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 max-w-3xl">
                        <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center mt-4">
                            <Sparkles size={14} className="text-zinc-400 animate-pulse" />
                        </div>
                        <div className="p-4 text-zinc-500 text-sm flex items-center gap-2">
                            <span className="animate-pulse">Thinking</span>
                            <span className="flex gap-0.5">
                                <span className="w-1 h-1 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                                <span className="w-1 h-1 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                <span className="w-1 h-1 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                            </span>
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 md:p-6 border-t border-zinc-800 bg-[#09090b] z-20">
                <form className="max-w-4xl mx-auto relative group">
                    <div className="relative flex items-end bg-zinc-900/50 border border-zinc-800 rounded-xl p-2 shadow-sm focus-within:border-zinc-600 focus-within:bg-zinc-900 transition-all duration-300">
                        <textarea
                            value={input}
                            onChange={(e) => {
                                setInput(e.target.value);
                                e.target.style.height = 'auto';
                                e.target.style.height = `${Math.min(e.target.scrollHeight, 256)}px`;
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage(e);
                                    e.target.style.height = 'auto';
                                }
                            }}
                            placeholder="Ask about your documents or request a task..."
                            className="flex-1 bg-transparent border-none outline-none text-zinc-200 px-4 placeholder:text-zinc-600 text-sm py-3 font-medium resize-none min-h-[44px] custom-scrollbar leading-relaxed"
                            rows={1}
                            disabled={loading}
                            autoFocus
                        />

                        {/* Voice Input Button */}
                        <div className="flex items-center pb-1 pr-2 gap-1 self-end">
                            <button
                                type="button"
                                onClick={async () => {
                                    if (loading) return;

                                    if (isRecording) {
                                        // User specifically wants to cancel/stop? 
                                        // Since backend is synchronous blocking, we can't easily cancel" 
                                        // without a separate specific interrupt, so we just set state off.
                                        setIsRecording(false);
                                        return;
                                    }

                                    setIsRecording(true);

                                    try {
                                        // Call backend to listen
                                        const res = await axios.post('http://localhost:8000/voice');

                                        if (res.data.error) {
                                            alert(res.data.error);
                                        } else if (res.data.text) {
                                            const newText = res.data.text;
                                            // Append with space if needed
                                            setInput(prev => {
                                                const spacing = (prev && !prev.endsWith(' ')) ? ' ' : '';
                                                return prev + spacing + newText;
                                            });
                                        }
                                    } catch (err) {
                                        console.error("Voice Error", err);
                                        alert("Error connecting to Voice Service. Make sure backend is running.");
                                    } finally {
                                        setIsRecording(false);
                                    }
                                }}
                                className={`h-full w-full flex items-center justify-center rounded-lg transition-all ${isRecording ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 animate-pulse' : 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
                                title={isRecording ? "Listening on Server..." : "Start Voice Input (Server)"}
                            >
                                {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
                            </button>

                            <button
                                type="button"
                                onClick={sendMessage}
                                disabled={loading || !input.trim()}
                                className="w-full h-full flex items-center justify-center rounded-lg bg-zinc-100 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-sm"
                            >
                                <Send size={20} className="text-gray-500" />
                            </button>
                        </div>
                    </div>
                    <div className="text-center mt-3 text-[10px] text-zinc-600">
                        AI can make mistakes. Please verify important information.
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
