"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, BookOpen, Layers, FileText, Copy, Zap, FileUp, X } from "lucide-react";
import Link from "next/link";

export default function StudioPage() {
  const [topic, setTopic] = useState("");
  const [notes, setNotes] = useState("");
  const [mode, setMode] = useState("informational");
  const [files, setFiles] = useState<File[]>([]);
  const [useOnlyMyContent, setUseOnlyMyContent] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [status, setStatus] = useState("Ready");

  const [researchData, setResearchData] = useState<string[]>([]);
  const [finalScript, setFinalScript] = useState("");

  const researchEndRef = useRef<HTMLDivElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...newFiles]);
    }
    // Reset input so same file can be added again if removed
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleGenerate = async () => {
    if (!topic) return alert("Please enter a topic");

    setIsGenerating(true);
    setFinalScript("");
    setResearchData([]);
    setStatus("Initializing...");

    const formData = new FormData();
    formData.append("topic", topic);
    formData.append("user_notes", notes);
    formData.append("mode", mode);
    formData.append("skip_research", useOnlyMyContent.toString());

    // Append all files
    files.forEach((file) => {
      formData.append("files", file);
    });

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
            } else if (json.type === "result") {
              // Handle both old format (string) and new format (object with draft/optimized)
              if (typeof json.data === "string") {
                setFinalScript(json.data);
              } else if (json.data?.optimized) {
                setFinalScript(json.data.optimized);
              } else if (json.data?.draft) {
                setFinalScript(json.data.draft);
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
    }
  };

  useEffect(() => {
    researchEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [researchData]);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#f1f5f9", fontFamily: "system-ui, sans-serif", overflow: "hidden" }}>

      {/* HEADER */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", backgroundColor: "#ffffff", borderBottom: "1px solid #e2e8f0", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ height: "40px", width: "40px", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", borderRadius: "12px", display: "flex", alignItems: "center", justifyContent: "center", color: "#ffffff", boxShadow: "0 4px 12px rgba(99, 102, 241, 0.3)" }}>
            <Zap size={22} fill="currentColor" />
          </div>
          <div>
            <h1 style={{ fontSize: "20px", fontWeight: "700", color: "#0f172a", lineHeight: "1.2" }}>
              ScriptAI <span style={{ color: "#94a3b8", fontWeight: "400" }}>Studio</span>
            </h1>
            <p style={{ fontSize: "10px", fontWeight: "600", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em" }}>Viral Engine v1.0</p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Link href="/train" style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 16px", fontSize: "14px", fontWeight: "600", color: "#475569", textDecoration: "none", borderRadius: "8px" }}>
            <BookOpen size={16} />
            Train Brain
          </Link>

          <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 16px", borderRadius: "20px", border: "1px solid #e2e8f0", fontSize: "12px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.05em", backgroundColor: isGenerating ? "#eef2ff" : "#ffffff", color: isGenerating ? "#4f46e5" : "#64748b" }}>
            {isGenerating && <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#4f46e5", animation: "pulse 1.5s infinite" }}></span>}
            {status}
          </div>
        </div>
      </header>

      {/* MAIN GRID */}
      <div style={{ flex: 1, padding: "24px", minHeight: 0, backgroundColor: "#f1f5f9" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr 1.7fr", gap: "24px", height: "100%" }}>

          {/* COLUMN 1: INPUTS */}
          <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
            <div style={{ backgroundColor: "#ffffff", padding: "24px", borderRadius: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0", height: "100%", display: "flex", flexDirection: "column", overflowY: "auto" }}>

              <label style={{ fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>Topic</label>
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. The Dark Side of AI"
                style={{ width: "100%", boxSizing: "border-box", backgroundColor: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "12px", fontSize: "14px", fontWeight: "500", color: "#0f172a", marginBottom: "24px", outline: "none", fontFamily: "inherit" }}
              />

              <label style={{ fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>Mode</label>
              <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
                <button
                  onClick={() => setMode("informational")}
                  style={{ padding: "10px 24px", borderRadius: "20px", fontSize: "13px", fontWeight: "600", border: mode === "informational" ? "none" : "1px solid #e2e8f0", backgroundColor: mode === "informational" ? "#4f46e5" : "#ffffff", color: mode === "informational" ? "#ffffff" : "#64748b", cursor: "pointer", transition: "all 0.2s" }}
                >
                  Informational
                </button>
                <button
                  onClick={() => setMode("listical")}
                  style={{ padding: "10px 24px", borderRadius: "20px", fontSize: "13px", fontWeight: "600", border: mode === "listical" ? "none" : "1px solid #e2e8f0", backgroundColor: mode === "listical" ? "#4f46e5" : "#ffffff", color: mode === "listical" ? "#ffffff" : "#64748b", cursor: "pointer", transition: "all 0.2s" }}
                >
                  Listical
                </button>
              </div>

              {/* Use Only My Content Toggle */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <div>
                  <p style={{ fontSize: "14px", fontWeight: "600", color: "#334155" }}>Use Only My Content</p>
                  <p style={{ fontSize: "12px", color: "#94a3b8" }}>Skip web research</p>
                </div>
                <button
                  onClick={() => setUseOnlyMyContent(!useOnlyMyContent)}
                  style={{
                    width: "48px",
                    height: "26px",
                    borderRadius: "13px",
                    border: "none",
                    backgroundColor: useOnlyMyContent ? "#4f46e5" : "#d1d5db",
                    cursor: "pointer",
                    position: "relative",
                    transition: "background-color 0.2s"
                  }}
                >
                  <span style={{
                    position: "absolute",
                    top: "2px",
                    left: useOnlyMyContent ? "24px" : "2px",
                    width: "22px",
                    height: "22px",
                    borderRadius: "50%",
                    backgroundColor: "#ffffff",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.15)",
                    transition: "left 0.2s"
                  }}></span>
                </button>
              </div>

              {/* Source Files - Multiple */}
              <label style={{ fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>Source Files (Multiple OK)</label>
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", width: "100%", padding: "16px", borderRadius: "12px", border: "2px dashed #e2e8f0", backgroundColor: "#ffffff", color: "#94a3b8", cursor: "pointer", transition: "all 0.2s" }}>
                  <FileUp size={18} />
                  <span style={{ fontSize: "12px", fontWeight: "700" }}>Add PDF or TXT files...</span>
                  <input type="file" onChange={handleFileChange} style={{ display: "none" }} accept=".pdf,.txt,.md" multiple />
                </label>
              </div>

              {/* File List */}
              {files.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "16px" }}>
                  {files.map((file, index) => (
                    <div key={index} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", backgroundColor: "#eef2ff", border: "1px solid #c7d2fe", borderRadius: "10px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <FileText size={16} style={{ color: "#4f46e5" }} />
                        <span style={{ fontSize: "12px", fontWeight: "600", color: "#4f46e5", maxWidth: "180px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        style={{ background: "none", border: "none", cursor: "pointer", padding: "2px", display: "flex", alignItems: "center", justifyContent: "center" }}
                      >
                        <X size={16} style={{ color: "#64748b" }} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <label style={{ fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>Context / Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Specific angles, keywords to include..."
                style={{ width: "100%", boxSizing: "border-box", backgroundColor: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "14px", fontSize: "14px", color: "#334155", flex: 1, minHeight: "120px", marginBottom: "16px", outline: "none", resize: "none", fontFamily: "inherit", lineHeight: "1.5" }}
              />

              <div style={{ marginTop: "auto", paddingTop: "16px" }}>
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  style={{ width: "100%", padding: "16px", borderRadius: "12px", fontSize: "14px", fontWeight: "700", color: "#ffffff", backgroundColor: isGenerating ? "#94a3b8" : "#4f46e5", border: "none", cursor: isGenerating ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", boxShadow: isGenerating ? "none" : "0 4px 12px rgba(79, 70, 229, 0.3)", transition: "all 0.2s" }}
                >
                  {isGenerating ? "Generating..." : <><Send size={18} /> Generate Script</>}
                </button>
              </div>
            </div>
          </div>

          {/* COLUMN 2: RESEARCH */}
          <div style={{ display: "flex", flexDirection: "column", backgroundColor: "#ffffff", borderRadius: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0", overflow: "hidden", height: "100%" }}>
            <div style={{ padding: "16px", borderBottom: "1px solid #f1f5f9", backgroundColor: "#f8fafc", display: "flex", justifyContent: "space-between", alignItems: "center", flexShrink: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Layers size={18} style={{ color: "#6366f1" }} />
                <span style={{ fontSize: "14px", fontWeight: "700", color: "#334155" }}>Research Agent</span>
              </div>
              <span style={{ fontSize: "12px", fontWeight: "700", backgroundColor: "#eef2ff", color: "#4f46e5", padding: "4px 10px", borderRadius: "6px" }}>{researchData.length} Facts</span>
            </div>

            <div style={{ flex: 1, padding: "16px", overflowY: "auto", backgroundColor: "#fafbfc" }}>
              {researchData.length === 0 ? (
                <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#cbd5e1", gap: "12px" }}>
                  <div style={{ padding: "16px", backgroundColor: "#f1f5f9", borderRadius: "50%" }}>
                    <FileText size={24} />
                  </div>
                  <p style={{ fontSize: "14px", fontWeight: "500" }}>Research will stream here...</p>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {researchData.map((fact, i) => (
                    <div key={i} style={{ padding: "12px", backgroundColor: "#ffffff", border: "1px solid #f1f5f9", borderRadius: "12px", fontSize: "12px", color: "#475569", lineHeight: "1.6", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
                      <span style={{ color: "#6366f1", fontWeight: "700", marginRight: "8px" }}>•</span>
                      {fact.replace(/^- /, "")}
                    </div>
                  ))}
                  <div ref={researchEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* COLUMN 3: OUTPUT */}
          <div style={{ display: "flex", flexDirection: "column", backgroundColor: "#ffffff", borderRadius: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0", overflow: "hidden", height: "100%" }}>
            <div style={{ padding: "16px", borderBottom: "1px solid #f1f5f9", backgroundColor: "#f8fafc", display: "flex", justifyContent: "space-between", alignItems: "center", flexShrink: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <FileText size={18} style={{ color: "#6366f1" }} />
                <span style={{ fontSize: "14px", fontWeight: "700", color: "#334155" }}>Final Script</span>
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(finalScript)}
                style={{ display: "flex", alignItems: "center", gap: "4px", padding: "6px 12px", fontSize: "12px", fontWeight: "700", color: "#4f46e5", backgroundColor: "transparent", border: "none", borderRadius: "8px", cursor: "pointer" }}
              >
                <Copy size={14} /> Copy
              </button>
            </div>

            <div style={{ flex: 1, overflowY: "auto", padding: "32px", backgroundColor: "#ffffff" }}>
              {finalScript ? (
                <div className="prose prose-sm" style={{ maxWidth: "none", color: "#475569", lineHeight: "1.8" }}>
                  <ReactMarkdown>{finalScript}</ReactMarkdown>
                </div>
              ) : (
                <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#cbd5e1", gap: "12px" }}>
                  <div style={{ padding: "16px", backgroundColor: "#f1f5f9", borderRadius: "50%" }}>
                    <Zap size={24} />
                  </div>
                  <p style={{ fontSize: "14px", fontWeight: "500" }}>Ready to write viral scripts.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
