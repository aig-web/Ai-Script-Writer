"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import {
  Send, BookOpen, Layers,
  FileText, Copy, Zap,
  File, X, CheckCircle
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
  const [skipResearch, setSkipResearch] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [status, setStatus] = useState("Ready");

  // Outputs
  const [researchData, setResearchData] = useState<string[]>([]);
  const [finalScript, setFinalScript] = useState("");
  const [optimizedScript, setOptimizedScript] = useState("");
  const [hookRanking, setHookRanking] = useState<HookRanking | null>(null);

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
    setStatus("Agent Starting...");

    const formData = new FormData();
    formData.append("topic", topic);
    formData.append("user_notes", notes);
    formData.append("mode", mode);

    for (const file of files) {
      formData.append("files", file);
    }

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
            } else if (json.type === "hook_ranking") {
              setHookRanking(json.data);
            } else if (json.type === "result") {
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

  const displayScript = optimizedScript || finalScript;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">

      {/* --- HEADER --- */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
              <Zap size={22} fill="currentColor" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                ScriptAI <span className="text-slate-400">Studio</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Link href="/train" className="text-sm font-medium text-slate-600 hover:text-indigo-600 px-4 py-2 hover:bg-slate-50 rounded-lg transition-colors">
              Train Brain
            </Link>

            <div className={`px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 ${
              isGenerating
                ? "bg-indigo-100 text-indigo-700"
                : status === "Complete!"
                  ? "bg-green-100 text-green-700"
                  : "bg-slate-100 text-slate-600"
            }`}>
              {isGenerating && <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"/>}
              {status === "Complete!" && <CheckCircle size={14} />}
              {isGenerating ? `AGENT STARTING (${mode.toUpperCase()})...` : status}
            </div>
          </div>
        </div>
      </header>

      {/* --- MAIN CONTENT --- */}
      <main className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* 1. INPUT PANEL (3 Cols) */}
          <div className="lg:col-span-3 space-y-4">

            {/* Topic Input */}
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="PopEVE is an AI that learned"
                className="w-full text-slate-900 font-medium placeholder:text-slate-400 outline-none"
              />
            </div>

            {/* Mode Selector */}
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 block">Mode</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setMode("informational")}
                  className={`p-3 rounded-lg text-sm font-semibold transition-all ${
                    mode === "informational"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  Informational
                </button>
                <button
                  onClick={() => setMode("listical")}
                  className={`p-3 rounded-lg text-sm font-semibold transition-all ${
                    mode === "listical"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  Listical
                </button>
              </div>
            </div>

            {/* Source File */}
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 block">Source File (Optional)</label>
              <label className="flex items-center gap-3 p-3 rounded-lg border border-dashed border-slate-300 cursor-pointer hover:border-indigo-400 hover:bg-slate-50 transition-all">
                <File size={18} className="text-slate-400" />
                <span className="text-sm text-slate-500">Choose PDF...</span>
                <input type="file" accept=".pdf,.txt,.md" multiple onChange={handleFileChange} className="hidden" />
              </label>

              {/* File List */}
              {files.length > 0 && (
                <div className="mt-3 space-y-2">
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <FileText size={16} className="text-indigo-600 flex-shrink-0" />
                        <span className="text-sm text-slate-700 truncate">{file.name}</span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-red-500 transition-colors"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Context / Notes */}
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 block">Context / Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Specific angles or requirements..."
                className="w-full h-32 text-sm text-slate-700 placeholder:text-slate-400 outline-none resize-none"
              />
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`w-full py-4 rounded-xl font-semibold text-white flex items-center justify-center gap-2 transition-all ${
                isGenerating
                  ? "bg-slate-400 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-700"
              }`}
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

          {/* 2. RESEARCH PANEL (4 Cols) */}
          <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 flex flex-col min-h-[600px]">
            <div className="p-4 border-b border-slate-200 flex items-center gap-2">
              <Layers size={18} className="text-indigo-600" />
              <span className="font-semibold text-slate-700">Research</span>
            </div>

            <div className="flex-1 p-4 overflow-y-auto">
              {researchData.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-400">
                  <FileText size={32} className="text-slate-300 mb-2" />
                  <p className="text-sm">Facts will appear here...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {researchData.map((fact, i) => (
                    <div
                      key={i}
                      className="p-3 bg-slate-50 rounded-lg text-sm text-slate-700 leading-relaxed"
                    >
                      {fact.replace(/^[-•]\s*/, "")}
                    </div>
                  ))}
                  <div ref={researchEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* 3. SCRIPT OUTPUT PANEL (5 Cols) */}
          <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 flex flex-col min-h-[600px]">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <FileText size={18} className="text-indigo-600" />
                <span className="font-semibold text-slate-700">Script Output</span>
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(displayScript)}
                className="text-sm text-indigo-600 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
              >
                <Copy size={14} /> Copy
              </button>
            </div>

            <div className="flex-1 p-4 overflow-y-auto">
              {displayScript ? (
                <div className="prose prose-sm max-w-none text-slate-700">
                  <ReactMarkdown>{displayScript}</ReactMarkdown>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-400">
                  <FileText size={32} className="text-slate-300 mb-2" />
                  <p className="text-sm">Your script will appear here...</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
