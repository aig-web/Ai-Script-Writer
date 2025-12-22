"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import {
  Send, BookOpen, Layers,
  FileText, Copy, Zap,
  File, X, Award, CheckCircle,
  ChevronDown, ChevronUp
} from "lucide-react";
import Link from "next/link";

interface HookRanking {
  ranking: number[];
  best: number;
}

interface ResultData {
  draft: string;
  optimized: string;
}

export default function StudioPage() {
  // --- STATE ---
  const [topic, setTopic] = useState("");
  const [notes, setNotes] = useState("");
  const [mode, setMode] = useState("informational");
  const [files, setFiles] = useState<File[]>([]);
  const [skipResearch, setSkipResearch] = useState(false); // NEW: Skip Tavily research

  const [isGenerating, setIsGenerating] = useState(false);
  const [status, setStatus] = useState("Ready");

  // Outputs
  const [researchData, setResearchData] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [finalScript, setFinalScript] = useState("");
  const [optimizedScript, setOptimizedScript] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [hookRanking, setHookRanking] = useState<HookRanking | null>(null);

  // UI States
  const [showOptimized, setShowOptimized] = useState(true);
  const [showAnalysis, setShowAnalysis] = useState(false);

  // Refs for auto-scroll
  const researchEndRef = useRef<HTMLDivElement>(null);

  // --- HANDLERS ---

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleGenerate = async () => {
    if (!topic) return alert("Please enter a topic");

    setIsGenerating(true);
    setFinalScript("");
    setOptimizedScript("");
    setResearchData([]);
    setSources([]);
    setAnalysis("");
    setHookRanking(null);
    setStatus("Initializing...");

    const formData = new FormData();
    formData.append("topic", topic);
    formData.append("user_notes", notes);
    formData.append("mode", mode);

    // Append all files
    for (const file of files) {
      formData.append("files", file);
    }

    // Skip research option
    formData.append("skip_research", skipResearch.toString());

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/generate_stream`, {
        method: "POST",
        body: formData,
      });

      if (!response.body) throw new Error("No stream body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n").filter(line => line.trim() !== "");

        for (const line of lines) {
          try {
            const json = JSON.parse(line);

            if (json.type === "status") {
              setStatus(json.message);
            } else if (json.type === "research") {
              const newBullets = json.data.split("\n").filter((b: string) => b.length > 5);
              setResearchData(prev => {
                const merged = [...prev, ...newBullets];
                return Array.from(new Set(merged));
              });
            } else if (json.type === "sources") {
              setSources(json.data);
            } else if (json.type === "analysis") {
              setAnalysis(json.data);
            } else if (json.type === "hook_ranking") {
              setHookRanking(json.data);
            } else if (json.type === "result") {
              // Handle both old and new format
              if (typeof json.data === "string") {
                setFinalScript(json.data);
                setOptimizedScript(json.data);
              } else {
                const result = json.data as ResultData;
                setFinalScript(result.draft);
                setOptimizedScript(result.optimized);
              }
            } else if (json.type === "error") {
              alert("Error: " + json.message);
              setIsGenerating(false);
            }
          } catch (e) {
            console.error("JSON Parse Error", e);
          }
        }
      }
    } catch (error) {
      console.error(error);
      setStatus("Connection Failed");
    } finally {
      setIsGenerating(false);
      setStatus("Complete!");
    }
  };

  // Auto-scroll research
  useEffect(() => {
    researchEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [researchData]);

  // Format script for better display
  const formatScript = (text: string) => {
    if (!text) return "";

    // Add visual spacing after sections
    let formatted = text
      // Ensure headers have proper spacing
      .replace(/^(##\s+.+)$/gm, "\n$1\n")
      // Add dividers before major sections
      .replace(/^(## HOOK OPTIONS)/gm, "---\n\n$1")
      .replace(/^(## FINAL SCRIPT)/gm, "\n---\n\n$1")
      // Space out numbered items
      .replace(/^(\d+\.)/gm, "\n$1")
      // Clean up excessive newlines
      .replace(/\n{4,}/g, "\n\n\n");

    return formatted;
  };

  const displayScript = showOptimized ? optimizedScript : finalScript;

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900 font-sans p-6 overflow-hidden">

      {/* --- HEADER --- */}
      <header className="flex justify-between items-center mb-6 shrink-0 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-md">
            <Zap size={22} fill="currentColor" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              ScriptAI <span className="text-indigo-600">Pro</span>
            </h1>
            <p className="text-xs text-slate-500">Vibhay Style Viral Scripts</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/train" className="text-sm font-bold text-slate-600 hover:text-indigo-600 flex items-center gap-2 px-4 py-2 hover:bg-slate-100 rounded-xl transition-colors">
            <BookOpen size={16} />
            Train Brain
          </Link>

          <div className={`px-4 py-2 rounded-xl border text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${
            isGenerating
              ? "bg-indigo-50 border-indigo-200 text-indigo-700"
              : status === "Complete!"
                ? "bg-green-50 border-green-200 text-green-700"
                : "bg-slate-100 border-slate-200 text-slate-600"
          }`}>
             {isGenerating && <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"/>}
             {status === "Complete!" && <CheckCircle size={14} />}
             {status}
          </div>
        </div>
      </header>

      {/* --- MAIN GRID --- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">

        {/* 1. INPUT PANEL (3 Cols) */}
        <div className="lg:col-span-3 flex flex-col gap-4 overflow-y-auto pr-2 pb-2">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 h-full">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Topic</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. ChatGPT 5 Launch"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 font-medium text-slate-900 mb-6 focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all placeholder:text-slate-400"
            />

            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Mode</label>
            <div className="grid grid-cols-2 gap-2 mb-6">
              <button
                onClick={() => setMode("informational")}
                className={`p-3 rounded-xl text-sm font-bold transition-all border ${mode === "informational" ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-transparent shadow-md" : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"}`}
              >
                Informational
              </button>
              <button
                onClick={() => setMode("listical")}
                className={`p-3 rounded-xl text-sm font-bold transition-all border ${mode === "listical" ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-transparent shadow-md" : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"}`}
              >
                Listical
              </button>
            </div>

            {/* Research Mode Toggle */}
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Research Mode</label>
            <div
              onClick={() => setSkipResearch(!skipResearch)}
              className={`mb-6 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                skipResearch
                  ? "border-indigo-400 bg-gradient-to-r from-indigo-50 to-purple-50 shadow-md"
                  : "border-slate-200 bg-slate-50 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
                    skipResearch ? "bg-indigo-100" : "bg-slate-200"
                  }`}>
                    <FileText size={18} className={skipResearch ? "text-indigo-600" : "text-slate-500"} />
                  </div>
                  <div>
                    <span className={`text-sm font-bold ${skipResearch ? "text-indigo-700" : "text-slate-700"}`}>
                      Use Only My Content
                    </span>
                    <p className="text-xs text-slate-500 mt-0.5">Skip Perplexity web research</p>
                  </div>
                </div>
                <div
                  className={`relative w-14 h-7 rounded-full transition-colors ${
                    skipResearch ? "bg-gradient-to-r from-indigo-500 to-purple-500" : "bg-slate-300"
                  }`}
                >
                  <div className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow-md transition-transform ${
                    skipResearch ? "translate-x-8" : "translate-x-1"
                  }`} />
                </div>
              </div>
              {skipResearch && (
                <p className="text-xs text-indigo-600 mt-3 pl-13 flex items-center gap-1">
                  <CheckCircle size={12} /> Files & notes will be used as research data
                </p>
              )}
            </div>

            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Source Files (Multiple OK)</label>
            <div className="mb-4">
              <label className="flex flex-col items-center justify-center w-full p-4 rounded-xl border-2 border-dashed border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50 text-slate-600 hover:bg-white hover:border-indigo-400 hover:shadow-md cursor-pointer transition-all group">
                <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center mb-2 group-hover:bg-indigo-200 transition-colors">
                  <File size={20} className="text-indigo-600" />
                </div>
                <span className="text-sm font-bold text-indigo-700">Click to add files</span>
                <span className="text-xs text-slate-500 mt-1">PDF, TXT, MD supported</span>
                <input type="file" accept=".pdf,.txt,.md" multiple onChange={handleFileChange} className="hidden" />
              </label>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="mb-6 space-y-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-600">{files.length} file(s) added</span>
                  <button
                    onClick={() => setFiles([])}
                    className="text-xs text-red-500 hover:text-red-700 font-medium"
                  >
                    Clear all
                  </button>
                </div>
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-white rounded-xl border border-indigo-100 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                        <FileText size={14} className="text-white" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-slate-800 truncate">{file.name}</p>
                        <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="w-7 h-7 rounded-full bg-slate-100 hover:bg-red-100 flex items-center justify-center text-slate-400 hover:text-red-500 transition-all ml-2 flex-shrink-0"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Context / Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Specific angles, keywords to include..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 h-28 text-sm mb-6 focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none resize-none placeholder:text-slate-400 text-slate-900 transition-all"
            />

            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`w-full py-4 rounded-xl font-bold text-white shadow-lg flex items-center justify-center gap-2 transition-all ${isGenerating ? "bg-slate-400 cursor-not-allowed" : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 hover:shadow-xl hover:-translate-y-0.5"}`}
            >
              {isGenerating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Generating...
                </>
              ) : (
                <><Send size={18} /> Generate Script</>
              )}
            </button>
          </div>
        </div>

        {/* 2. RESEARCH PANEL (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden h-full">
          <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-slate-100 flex justify-between items-center shrink-0">
            <h3 className="font-bold text-slate-700 flex items-center gap-2 text-sm">
              <Layers size={18} className="text-indigo-600"/> Research Facts
            </h3>
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full">{researchData.length} facts</span>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50/50">
            {researchData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-2">
                <Layers size={40} className="text-slate-300" />
                <p className="text-sm font-medium">Research facts will appear here...</p>
                <p className="text-xs text-slate-400">Live from Tavily search</p>
              </div>
            ) : (
              researchData.map((fact, i) => (
                <div
                  key={i}
                  className="p-4 bg-white border border-slate-100 rounded-xl text-sm text-slate-700 leading-relaxed shadow-sm hover:shadow-md transition-shadow"
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <div className="flex gap-3">
                    <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </span>
                    <span>{fact.replace(/^[-•]\s*/, "")}</span>
                  </div>
                </div>
              ))
            )}
            <div ref={researchEndRef} />
          </div>

          {/* Sources */}
          {sources.length > 0 && (
            <div className="p-3 border-t border-slate-200 bg-slate-50 shrink-0">
              <p className="text-xs font-bold text-slate-500 uppercase mb-2">Sources</p>
              <div className="flex flex-wrap gap-1">
                {sources.slice(0, 5).map((src, i) => (
                  <span key={i} className="text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md truncate max-w-[150px]">
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 3. EDITOR PANEL (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden h-full">
          <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-slate-100 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-3">
              <h3 className="font-bold text-slate-700 flex items-center gap-2 text-sm">
                <FileText size={18} className="text-indigo-600"/>
                {showOptimized ? "Optimized Script" : "Original Draft"}
              </h3>

              {/* Toggle between original and optimized */}
              {optimizedScript && finalScript && optimizedScript !== finalScript && (
                <div className="flex bg-slate-100 rounded-lg p-0.5">
                  <button
                    onClick={() => setShowOptimized(true)}
                    className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${showOptimized ? "bg-white shadow-sm text-indigo-600" : "text-slate-500"}`}
                  >
                    Optimized
                  </button>
                  <button
                    onClick={() => setShowOptimized(false)}
                    className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${!showOptimized ? "bg-white shadow-sm text-indigo-600" : "text-slate-500"}`}
                  >
                    Original
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              {hookRanking && (
                <div className="flex items-center gap-1 text-xs font-bold text-amber-600 bg-amber-50 px-2 py-1 rounded-lg">
                  <Award size={14} />
                  Best Hook: #{hookRanking.best}
                </div>
              )}
              <button
                onClick={() => navigator.clipboard.writeText(displayScript)}
                className="text-xs font-bold text-indigo-600 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
              >
                <Copy size={14} /> Copy
              </button>
            </div>
          </div>

          {/* Analysis Accordion */}
          {analysis && (
            <div className="border-b border-slate-200">
              <button
                onClick={() => setShowAnalysis(!showAnalysis)}
                className="w-full p-3 flex items-center justify-between bg-gradient-to-r from-purple-50 to-indigo-50 hover:from-purple-100 hover:to-indigo-100 transition-colors"
              >
                <span className="text-sm font-bold text-purple-700 flex items-center gap-2">
                  <Award size={16} />
                  Hook Analysis & Ranking
                </span>
                {showAnalysis ? <ChevronUp size={16} className="text-purple-600" /> : <ChevronDown size={16} className="text-purple-600" />}
              </button>
              {showAnalysis && (
                <div className="p-4 bg-white max-h-60 overflow-y-auto border-t border-purple-100">
                  <div className="prose prose-sm max-w-none prose-purple text-slate-700">
                    <ReactMarkdown>{analysis}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-6 bg-white">
             {displayScript ? (
               <div className="prose prose-sm max-w-none prose-slate prose-headings:font-bold prose-headings:text-slate-900 prose-headings:border-b prose-headings:border-slate-200 prose-headings:pb-2 prose-headings:mb-4 prose-p:text-slate-700 prose-p:leading-relaxed prose-strong:text-indigo-600 prose-li:text-slate-700 prose-hr:border-slate-200 prose-hr:my-6">
                 <ReactMarkdown>
                   {formatScript(displayScript)}
                 </ReactMarkdown>
               </div>
             ) : (
               <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-3">
                 <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center">
                   <FileText size={32} className="text-slate-300" />
                 </div>
                 <p className="text-sm font-medium">Your script will appear here...</p>
                 <p className="text-xs text-slate-400">With hook analysis & optimization</p>
               </div>
             )}
          </div>
        </div>

      </div>
    </div>
  );
}
