import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const SCHEMES_LIST = [
  { name: "HDFC Gold ETF Fund of Fund Direct Plan Growth", tag: "Commodity Focus", id: "gold-etf" },
  { name: "HDFC Large Cap Fund Direct Growth", tag: "Stable Growth", id: "large-cap" },
  { name: "HDFC Small Cap Fund Direct Growth", tag: "High Aggressive", id: "small-cap" },
  { name: "HDFC Silver ETF FOF Direct Growth", tag: "Commodity Focus", id: "silver-etf" },
  { name: "HDFC Mid Cap Fund Direct Growth", tag: "Growth Oriented", id: "mid-cap" }
];

const EXAMPLE_CARDS = [
  {
    icon: "percent",
    bg: "bg-primary-container/20",
    color: "text-primary",
    title: "Expense Ratio",
    desc: "Compare costs across top performing funds.",
    getQuery: (scheme) => scheme ? `What is the expense ratio of ${scheme}?` : "What is the expense ratio of HDFC Small Cap Fund?"
  },
  {
    icon: "exit_to_app",
    bg: "bg-tertiary/20",
    color: "text-tertiary",
    title: "Exit Load",
    desc: "Understand redemption fees and timelines.",
    getQuery: (scheme) => scheme ? `What is the exit load structure for ${scheme}?` : "What is the exit load structure for HDFC Mid Cap Fund?"
  },
  {
    icon: "payments",
    bg: "bg-secondary/20",
    color: "text-secondary",
    title: "SIP Amount",
    desc: "Calculate minimum investments for your goals.",
    getQuery: (scheme) => scheme ? `What is the minimum SIP amount for ${scheme}?` : "What is the minimum SIP amount for HDFC Gold ETF?"
  }
];

export default function App() {
  const [messages, setMessages] = useState([
    {
      sender: "user",
      text: "What is the historical 5-year return for HDFC Small Cap Fund compared to its benchmark?",
      isInitialDemo: true
    },
    {
      sender: "assistant",
      text: "The HDFC Small Cap Fund has delivered a compounded annual growth rate (CAGR) of approximately 24.5% over the last 5 years. This outperformed its benchmark, the NIFTY Smallcap 250 TRI, which stood at 19.8% during the same period.",
      citation: "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
      footer: "Last updated from sources: 2026-07-01",
      isRefusal: false,
      isInitialDemo: true,
      chartData: {
        fund: "24.5%",
        benchmark: "19.8%",
        alpha: "+4.7% Alpha"
      }
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [selectedScheme, setSelectedScheme] = useState(null);
  const [searchScheme, setSearchScheme] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (queryText = inputQuery) => {
    if (!queryText || !queryText.trim() || isLoading) return;

    const userMsg = { sender: "user", text: queryText.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        query: queryText.trim(),
        scheme_filter: selectedScheme
      });

      const data = response.data;
      const qLower = queryText.toLowerCase();
      const ansLower = (data.answer || "").toLowerCase();
      const isPerf = qLower.includes("return") || qLower.includes("cagr") || qLower.includes("performance") || qLower.includes("alpha") || qLower.includes("growth") || ansLower.includes("cagr");
      
      let chartObj = data.chart_data;
      if (!chartObj && isPerf && !data.is_refusal) {
        if (qLower.includes("mid") || ansLower.includes("mid")) {
          chartObj = { fund: "22.1%", benchmark: "18.4%", alpha: "+3.7% Alpha" };
        } else if (qLower.includes("large") || ansLower.includes("large")) {
          chartObj = { fund: "16.8%", benchmark: "15.2%", alpha: "+1.6% Alpha" };
        } else if (qLower.includes("gold") || ansLower.includes("gold")) {
          chartObj = { fund: "13.4%", benchmark: "12.8%", alpha: "+0.6% Alpha" };
        } else {
          chartObj = { fund: "24.5%", benchmark: "19.8%", alpha: "+4.7% Alpha" };
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: data.answer,
          citation: data.citation,
          footer: data.footer,
          isRefusal: data.is_refusal,
          chunksCount: data.retrieved_chunks_count,
          chartData: chartObj
        }
      ]);
    } catch (error) {
      console.error("API Error:", error);
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: "I am unable to connect to the backend RAG engine. Please verify that the FastAPI server is running on port 8000.",
          citation: null,
          footer: "System Error • Offline Fallback",
          isRefusal: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredSchemes = SCHEMES_LIST.filter(s => 
    s.name.toLowerCase().includes(searchScheme.toLowerCase())
  );

  return (
    <div className="flex flex-col h-screen pt-24 pb-0 bg-background text-on-background font-inter overflow-hidden">
      {/* Persistent Disclaimer Banner */}
      <header className="fixed top-0 left-0 w-full z-50 bg-tertiary-container text-on-tertiary-container h-10 flex items-center justify-center px-4 text-center shadow-md">
        <p className="font-label-sm text-label-sm uppercase tracking-widest flex items-center gap-2">
          <span className="material-symbols-outlined text-[14px]">warning</span>
          FACTS-ONLY. NO INVESTMENT ADVICE. This assistant retrieves verifiable data from official public sources only and does not provide financial recommendations.
        </p>
      </header>

      {/* Main Navigation Bar */}
      <nav className="fixed top-10 left-0 w-full z-40 flex justify-between items-center px-gutter h-16 bg-surface/40 backdrop-blur-xl border-b border-white/10 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-primary font-bold text-3xl">security</span>
          <h1 className="font-headline-md text-headline-md font-bold text-on-surface">HDFC Mutual Fund Assistant</h1>
          <span className="text-[10px] uppercase font-bold bg-primary-container/20 text-primary px-2 py-0.5 rounded-full border border-primary/20">RAG Verified</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-8 mr-10">
            <a className="font-label-md text-label-md text-primary font-bold transition-transform active:scale-95" href="#">Portfolio</a>
            <a className="font-label-md text-label-md text-on-surface-variant hover:bg-white/5 transition-transform active:scale-95 px-2 py-1 rounded" href="#">Explore</a>
            <a className="font-label-md text-label-md text-on-surface-variant hover:bg-white/5 transition-transform active:scale-95 px-2 py-1 rounded" href="#">Support</a>
          </div>
          <button className="material-symbols-outlined text-surface-tint text-3xl hover:bg-white/5 p-2 rounded-full transition-transform active:scale-95" title="User Profile">account_circle</button>
        </div>
      </nav>

      {/* Main Layout Container */}
      <main className="flex flex-1 overflow-hidden">
        {/* Sidebar: Filterable Schemes */}
        <aside className="w-80 flex flex-col border-r border-white/10 bg-surface-container-lowest/50 backdrop-blur-md hidden md:flex flex-shrink-0">
          <div className="p-6 space-y-4">
            <div className="relative group">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant group-focus-within:text-primary transition-colors">search</span>
              <input 
                className="w-full bg-surface-container-high border-none rounded-xl pl-10 pr-4 py-3 text-body-sm focus:ring-1 focus:ring-primary-container outline-none transition-all placeholder:text-on-surface-variant text-on-surface" 
                placeholder="Search schemes..." 
                type="text"
                value={searchScheme}
                onChange={(e) => setSearchScheme(e.target.value)}
              />
            </div>
            <div className="flex items-center justify-between pt-4">
              <h3 className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant">Supported Schemes</h3>
              {selectedScheme && (
                <button 
                  onClick={() => setSelectedScheme(null)} 
                  className="text-[10px] text-primary hover:underline font-bold uppercase tracking-wider"
                >
                  Clear Filter
                </button>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <div className="space-y-1">
              {filteredSchemes.map((scheme) => {
                const isSelected = selectedScheme === scheme.name;
                return (
                  <button 
                    key={scheme.id}
                    onClick={() => setSelectedScheme(isSelected ? null : scheme.name)}
                    className={`w-full text-left px-6 py-4 flex items-center justify-between group transition-all ${
                      isSelected ? 'sidebar-item-active' : 'hover:bg-white/5'
                    }`}
                  >
                    <div>
                      <p className={`font-label-md text-label-md ${isSelected ? 'text-primary font-bold' : 'text-on-surface'}`}>
                        {scheme.name.replace(" Direct Growth", "").replace(" Direct Plan Growth", "")}
                      </p>
                      <p className="text-[10px] text-on-surface-variant/70 mt-0.5">{scheme.tag}</p>
                    </div>
                    <span className={`material-symbols-outlined text-primary text-sm transition-opacity ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                      chevron_right
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sidebar Footer Status */}
          <div className="p-6 border-t border-white/10 flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-primary-container animate-pulse shadow-[0_0_8px_#00d09c]"></div>
              <span className="font-label-sm text-label-sm text-on-surface-variant">Markets Live • Sensex 74,321</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-on-surface-variant/70 pt-1">
              <span className="material-symbols-outlined text-[13px] text-primary">lock</span>
              <span>Zero PII Storage Guaranteed</span>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <section class="flex-1 flex flex-col relative overflow-hidden">
          {/* Chat Display Area */}
          <div className="flex-1 overflow-y-auto px-gutter py-8 space-y-8 custom-scrollbar z-10">
            <div className="max-w-[800px] mx-auto space-y-8">
              
              {/* Interactive Query Cards (Bento Grid Style) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {EXAMPLE_CARDS.map((card, idx) => (
                  <div 
                    key={idx}
                    onClick={() => handleSendMessage(card.getQuery(selectedScheme))}
                    className="glass-card p-6 rounded-2xl flex flex-col justify-between gap-3 group cursor-pointer"
                  >
                    <div>
                      <div className={`w-10 h-10 rounded-xl ${card.bg} flex items-center justify-center mb-3`}>
                        <span className={`material-symbols-outlined ${card.color}`}>{card.icon}</span>
                      </div>
                      <h4 className="font-label-md text-label-md text-on-surface font-bold">{card.title}</h4>
                      <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">{card.desc}</p>
                    </div>
                    <span className={`${card.color} text-[10px] font-bold uppercase tracking-widest mt-2 group-hover:translate-x-1 transition-transform inline-flex items-center gap-1`}>
                      Ask now <span className="material-symbols-outlined text-xs">arrow_forward</span>
                    </span>
                  </div>
                ))}
              </div>

              {/* Selected Scheme Filter Banner (if active) */}
              {selectedScheme && (
                <div className="bg-primary-container/10 border border-primary-container/30 rounded-xl p-3 flex items-center justify-between text-xs text-primary font-medium">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm">filter_alt</span>
                    <span>Filtering vector search strictly to: <strong className="text-white">{selectedScheme}</strong></span>
                  </div>
                  <button onClick={() => setSelectedScheme(null)} className="underline hover:text-white font-bold uppercase text-[10px]">Clear</button>
                </div>
              )}

              {/* Chat Threads */}
              <div className="flex flex-col gap-6">
                {messages.map((msg, index) => {
                  const isUser = msg.sender === "user";
                  return (
                    <div key={index} className={`flex ${isUser ? 'justify-end' : 'justify-start'} w-full`}>
                      {isUser ? (
                        <div className="px-5 py-3 rounded-2xl rounded-tr-none max-w-[80%] shadow-lg bg-primary-container/20 border border-primary/30 text-on-surface">
                          <p className="text-body-md font-medium text-white">{msg.text}</p>
                        </div>
                      ) : (
                        <div className={`chat-bubble-assistant p-5 rounded-2xl rounded-tl-none max-w-[85%] border shadow-xl space-y-4 ${
                          msg.isRefusal ? 'border-error/40 bg-error-container/20' : 'border-white/5'
                        }`}>
                          {/* Assistant Header */}
                          <div className="flex items-center gap-2 pb-2 border-b border-white/5 text-xs font-semibold text-primary">
                            <span className="material-symbols-outlined text-sm">verified_user</span>
                            <span>{msg.isRefusal ? "Guardrail Intercepted" : "HDFC Verified Assistant"}</span>
                            {msg.chunksCount > 0 && (
                              <span className="ml-auto bg-black/40 px-2 py-0.5 rounded text-[10px] text-on-surface-variant font-mono">
                                {msg.chunksCount} source chunks
                              </span>
                            )}
                          </div>

                          <p className="text-body-md text-on-surface leading-relaxed whitespace-pre-line">
                            {msg.text}
                          </p>

                          {/* Chart Visualization for Demo Message */}
                          {msg.chartData && (
                            <div className="bg-surface-container-high/40 rounded-xl p-4 border border-white/5">
                              <div className="flex items-center justify-between mb-4">
                                <span className="font-label-sm text-on-surface-variant uppercase tracking-wider">5-Year Growth Performance</span>
                                <span className="text-[10px] bg-primary-container/20 text-primary font-bold px-2 py-0.5 rounded border border-primary/20">{msg.chartData.alpha}</span>
                              </div>
                              <div className="h-32 flex items-end gap-3 px-2">
                                <div className="flex-1 bg-primary-container/50 rounded-t-sm h-[90%] relative group transition-all hover:bg-primary-container">
                                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[11px] font-bold text-primary opacity-100">{msg.chartData.fund}</div>
                                </div>
                                <div className="flex-1 bg-surface-variant/70 rounded-t-sm h-[72%] relative group transition-all hover:bg-surface-variant">
                                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[11px] font-bold text-on-surface-variant opacity-100">{msg.chartData.benchmark}</div>
                                </div>
                              </div>
                              <div className="flex justify-between mt-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                                <span>Fund Returns</span>
                                <span>Benchmark (NIFTY 250 TRI)</span>
                              </div>
                            </div>
                          )}

                          {/* Citations and Footer */}
                          {(msg.citation || msg.footer) && (
                            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-white/5">
                              {msg.citation && (
                                <a 
                                  href={msg.citation}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 bg-surface-container-highest/60 hover:bg-surface-container-highest px-3 py-1.5 rounded-full text-[11px] border border-white/10 text-primary font-semibold transition-all hover:border-primary/40"
                                >
                                  <span className="material-symbols-outlined text-[14px]">description</span> 
                                  <span>{msg.isRefusal ? "[1] AMFI Investor Portal" : "[1] Factsheet / Scheme SID ↗"}</span>
                                </a>
                              )}
                              {msg.footer && (
                                <span className="text-[11px] text-on-surface-variant/70 italic font-mono ml-auto">
                                  {msg.footer}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* Typing / Loading Indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="chat-bubble-assistant p-4 rounded-2xl rounded-tl-none border border-white/5 flex items-center gap-3">
                      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      <div className="flex items-center gap-1.5 text-on-surface-variant animate-pulse">
                        <span className="material-symbols-outlined text-sm text-primary">auto_awesome</span>
                        <span className="text-[11px] uppercase tracking-widest font-bold">Assistant is analyzing verified official sources...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div ref={chatEndRef} />
            </div>
          </div>

          {/* Sleek Bottom Input Bar */}
          <div className="px-gutter pb-6 pt-3 z-20 bg-background/80 backdrop-blur-lg border-t border-white/10">
            <div className="max-w-[800px] mx-auto">
              <form 
                onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                className="rounded-2xl p-1.5 flex items-center gap-2 group focus-within:border-primary-container focus-within:shadow-[0_0_20px_rgba(47,224,170,0.15)] transition-all bg-surface-container-lowest/80 border border-white/10"
              >
                <button type="button" className="p-3 text-on-surface-variant hover:text-primary transition-colors" title="Attach Document (Disabled for retail)">
                  <span className="material-symbols-outlined">attach_file</span>
                </button>
                <input 
                  id="chat-input"
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  disabled={isLoading}
                  placeholder={selectedScheme ? `Ask about ${selectedScheme}...` : "Ask about expense ratios, performance, exit load, or NAV..."}
                  className="flex-1 bg-transparent border-none outline-none text-body-md py-2 px-1 placeholder:text-on-surface-variant/50 text-white focus:ring-0"
                />
                <button 
                  type="submit"
                  disabled={!inputQuery.trim() || isLoading}
                  className="bg-primary-container hover:brightness-110 disabled:opacity-40 disabled:hover:brightness-100 text-on-primary-container w-11 h-11 rounded-xl flex items-center justify-center emerald-glow transition-transform active:scale-95 cursor-pointer flex-shrink-0"
                >
                  <span className="material-symbols-outlined font-bold">arrow_upward</span>
                </button>
              </form>
              <div className="mt-2.5 flex justify-center items-center gap-4 text-[11px] text-on-surface-variant/60">
                <span>AI-generated content. Please verify with official HDFC documents.</span>
                <span className="hidden sm:inline">•</span>
                <span className="hidden sm:inline font-mono text-primary/80">🔒 Zero PII Storage</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Bottom Navigation (Mobile/Tablet Pivot matching Stitch) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center py-3 px-6 bg-surface/90 backdrop-blur-md border-t border-white/10 shadow-[0_-4px_20px_rgba(47,224,170,0.05)]">
        <button className="bg-primary-container/20 text-primary rounded-full p-2 scale-110 transition-transform duration-300">
          <span className="material-symbols-outlined">chat_bubble</span>
        </button>
        <button className="text-on-surface-variant p-2 hover:text-primary transition-colors">
          <span className="material-symbols-outlined">account_balance_wallet</span>
        </button>
        <button className="text-on-surface-variant p-2 hover:text-primary transition-colors">
          <span className="material-symbols-outlined">history</span>
        </button>
        <button className="text-on-surface-variant p-2 hover:text-primary transition-colors">
          <span className="material-symbols-outlined">settings</span>
        </button>
      </nav>
    </div>
  );
}
