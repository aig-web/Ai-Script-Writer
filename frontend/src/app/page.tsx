"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, BookOpen, Layers, FileText, Copy, Zap, FileUp, X, ChevronRight, CheckCircle } from "lucide-react";
import Link from "next/link";

// Animated dots component for loading states
function AnimatedDots() {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? "" : prev + ".");
    }, 400);
    return () => clearInterval(interval);
  }, []);

  return <span style={{ display: "inline-block", width: "20px", textAlign: "left" }}>{dots}</span>;
}

interface ScriptAngle {
  name: string;
  focus: string;
  hook_style?: string;
}

interface SavedScript {
  id: string;
  topic: string;
  mode: string;
  scripts: string[];
  angles: ScriptAngle[];
  timestamp: Date;
}

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

  // Multi-angle state (NEW)
  const [angles, setAngles] = useState<ScriptAngle[]>([]);
  const [scripts, setScripts] = useState<string[]>([]);
  const [activeScriptTab, setActiveScriptTab] = useState(0);

  // Script history state
  const [scriptHistory, setScriptHistory] = useState<SavedScript[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  // Angle selection state (for generic topics)
  const [showAngleSelection, setShowAngleSelection] = useState(false);
  const [angleOptions, setAngleOptions] = useState<string[]>([]);
  const [angleMessage, setAngleMessage] = useState("");

  const researchEndRef = useRef<HTMLDivElement>(null);

  // Load history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("scriptHistory");
    if (saved) {
      try {
        setScriptHistory(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to load history", e);
      }
    }
  }, []);

  // Save script to history
  const saveToHistory = () => {
    const hasContent = scripts.length > 0 || finalScript.length > 0;
    if (!hasContent) return;

    const newEntry: SavedScript = {
      id: Date.now().toString(),
      topic: topic,
      mode: mode,
      scripts: scripts.length > 0 ? scripts : [finalScript],
      angles: angles,
      timestamp: new Date(),
    };

    const updated = [newEntry, ...scriptHistory].slice(0, 50); // Keep last 50
    setScriptHistory(updated);
    localStorage.setItem("scriptHistory", JSON.stringify(updated));
    setSaveMessage("Saved!");
    setTimeout(() => setSaveMessage(""), 2000);
  };

  // Load script from history
  const loadFromHistory = (entry: SavedScript) => {
    setTopic(entry.topic);
    setMode(entry.mode);
    setScripts(entry.scripts);
    setAngles(entry.angles);
    setFinalScript(entry.scripts[0] || "");
    setShowHistory(false);
  };

  // Delete from history
  const deleteFromHistory = (id: string) => {
    const updated = scriptHistory.filter(s => s.id !== id);
    setScriptHistory(updated);
    localStorage.setItem("scriptHistory", JSON.stringify(updated));
  };

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

  // Handle angle selection - regenerate with selected angle as new topic
  const handleAngleSelect = (selectedAngle: string) => {
    setShowAngleSelection(false);
    setAngleOptions([]);
    setAngleMessage("");
    // Use the selected angle as the new topic
    setTopic(selectedAngle);
    // Auto-generate with the new topic after a brief delay
    setTimeout(() => {
      const generateBtn = document.querySelector('[data-generate-btn]') as HTMLButtonElement;
      if (generateBtn) generateBtn.click();
    }, 100);
  };

  const handleGenerate = async () => {
    if (!topic) return alert("Please enter a topic");

    setIsGenerating(true);
    setFinalScript("");
    setScripts([]);
    setAngles([]);
    setActiveScriptTab(0);
    setResearchData([]);
    setStatus("Initializing...");
    setShowAngleSelection(false);
    setAngleOptions([]);
    setAngleMessage("");

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
              // Split by newlines and filter out short/empty lines
              // Handle both bullet points and paragraphs
              const lines = json.data.split("\n");
              const newBullets: string[] = [];

              for (const line of lines) {
                const trimmed = line.trim();
                // Skip empty or very short lines
                if (trimmed.length < 10) continue;
                // Skip header-like lines (all caps, colons only)
                if (trimmed.endsWith(":") && trimmed.length < 50) continue;
                // Skip lines that are just punctuation or numbers
                if (/^[\d\.\-\:\s]+$/.test(trimmed)) continue;
                newBullets.push(trimmed);
              }

              setResearchData(prev => {
                const merged = [...prev, ...newBullets];
                return Array.from(new Set(merged));
              });
            } else if (json.type === "angles") {
              // Multi-angle: received angle definitions
              setAngles(json.data || []);
            } else if (json.type === "script_complete") {
              // Multi-angle: individual script completed
              setStatus(`Completed Script ${json.script_number}: ${json.angle_name}`);
            } else if (json.type === "result") {
              // Handle both old format (string) and new format (object with multiple scripts)
              if (typeof json.data === "string") {
                setFinalScript(json.data);
              } else if (json.data) {
                // New multi-angle format
                if (json.data.scripts && Array.isArray(json.data.scripts)) {
                  setScripts(json.data.scripts);
                }
                if (json.data.angles && Array.isArray(json.data.angles)) {
                  setAngles(json.data.angles);
                }
                if (json.data.full_output) {
                  setFinalScript(json.data.full_output);
                } else if (json.data.optimized) {
                  setFinalScript(json.data.optimized);
                } else if (json.data.draft) {
                  setFinalScript(json.data.draft);
                }
              }
            } else if (json.type === "needs_input") {
              // Generic topic detected - show angle selection
              if (json.input_type === "angle_selection" || json.input_type === "clarification") {
                setAngleMessage(json.message || "This topic needs a specific angle. Please select one:");
                setAngleOptions(json.options || []);
                setShowAngleSelection(true);
                setIsGenerating(false);
                setStatus("Select an angle to continue");
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
      setStatus("Complete");
    }
  };

  useEffect(() => {
    researchEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [researchData]);

  // Get the content to display based on whether we have multi-angle or single script
  const hasMultipleScripts = scripts.length > 1;
  const displayContent = hasMultipleScripts ? scripts[activeScriptTab] : finalScript;
  const currentAngle = hasMultipleScripts && angles[activeScriptTab] ? angles[activeScriptTab] : null;

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
            <p style={{ fontSize: "10px", fontWeight: "600", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em" }}>Multi-Angle Viral Engine v2.0</p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Link href="/train" style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 16px", fontSize: "14px", fontWeight: "600", color: "#475569", textDecoration: "none", borderRadius: "8px" }}>
            <BookOpen size={16} />
            Train Brain
          </Link>

          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "8px 18px",
            borderRadius: "24px",
            border: isGenerating ? "2px solid #4f46e5" : "1px solid #e2e8f0",
            fontSize: "13px",
            fontWeight: "700",
            letterSpacing: "0.02em",
            backgroundColor: isGenerating ? "#eef2ff" : "#ffffff",
            color: isGenerating ? "#4f46e5" : "#64748b",
            boxShadow: isGenerating ? "0 0 12px rgba(79, 70, 229, 0.25)" : "none",
            transition: "all 0.3s ease"
          }}>
            {isGenerating && (
              <span style={{
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                backgroundColor: "#4f46e5",
                boxShadow: "0 0 8px rgba(79, 70, 229, 0.6)",
                animation: "pulse 1.2s ease-in-out infinite"
              }}></span>
            )}
            <span>{status}</span>
            {isGenerating && <AnimatedDots />}
          </div>
        </div>
      </header>

      {/* ANGLE SELECTION MODAL */}
      {showAngleSelection && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(15, 23, 42, 0.6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          backdropFilter: "blur(4px)"
        }}>
          <div style={{
            backgroundColor: "#ffffff",
            borderRadius: "20px",
            padding: "32px",
            maxWidth: "600px",
            width: "90%",
            maxHeight: "80vh",
            overflowY: "auto",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <div style={{
                width: "40px",
                height: "40px",
                borderRadius: "12px",
                background: "linear-gradient(135deg, #f59e0b, #d97706)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                <Layers size={20} style={{ color: "#ffffff" }} />
              </div>
              <h2 style={{ fontSize: "20px", fontWeight: "700", color: "#0f172a", margin: 0 }}>
                Select a Viral Angle
              </h2>
            </div>

            <p style={{ fontSize: "14px", color: "#64748b", marginBottom: "24px", lineHeight: "1.6" }}>
              {angleMessage}
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {angleOptions.map((angle, index) => (
                <button
                  key={index}
                  onClick={() => handleAngleSelect(angle)}
                  style={{
                    padding: "16px 20px",
                    backgroundColor: "#f8fafc",
                    border: "2px solid #e2e8f0",
                    borderRadius: "12px",
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    fontSize: "14px",
                    fontWeight: "500",
                    color: "#334155",
                    lineHeight: "1.5"
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = "#4f46e5";
                    e.currentTarget.style.backgroundColor = "#eef2ff";
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = "#e2e8f0";
                    e.currentTarget.style.backgroundColor = "#f8fafc";
                  }}
                >
                  <span style={{ color: "#4f46e5", fontWeight: "700", marginRight: "12px" }}>
                    {index + 1}.
                  </span>
                  {angle}
                </button>
              ))}
            </div>

            <button
              onClick={() => {
                setShowAngleSelection(false);
                setStatus("Ready");
              }}
              style={{
                marginTop: "24px",
                padding: "12px 24px",
                backgroundColor: "transparent",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                fontSize: "14px",
                fontWeight: "600",
                color: "#64748b",
                cursor: "pointer",
                width: "100%"
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

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
                  data-generate-btn
                  style={{ width: "100%", padding: "16px", borderRadius: "12px", fontSize: "14px", fontWeight: "700", color: "#ffffff", backgroundColor: isGenerating ? "#94a3b8" : "#4f46e5", border: "none", cursor: isGenerating ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", boxShadow: isGenerating ? "none" : "0 4px 12px rgba(79, 70, 229, 0.3)", transition: "all 0.2s" }}
                >
                  {isGenerating ? "Generating 3 Scripts..." : <><Send size={18} /> Generate 3 Viral Scripts</>}
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

          {/* COLUMN 3: OUTPUT WITH TABS */}
          <div style={{ display: "flex", flexDirection: "column", backgroundColor: "#ffffff", borderRadius: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0", overflow: "hidden", height: "100%", position: "relative" }}>
            {/* Header with tabs for multiple scripts */}
            <div style={{ padding: "12px 16px", borderBottom: "1px solid #f1f5f9", backgroundColor: "#f8fafc", flexShrink: 0, position: "relative" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: hasMultipleScripts ? "12px" : "0" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <FileText size={18} style={{ color: "#6366f1" }} />
                  <span style={{ fontSize: "14px", fontWeight: "700", color: "#334155" }}>
                    {hasMultipleScripts ? "3 Viral Scripts" : "Final Script"}
                  </span>
                  {hasMultipleScripts && (
                    <span style={{ fontSize: "11px", fontWeight: "600", backgroundColor: "#dcfce7", color: "#16a34a", padding: "2px 8px", borderRadius: "4px" }}>
                      <CheckCircle size={12} style={{ display: "inline", marginRight: "4px", verticalAlign: "middle" }} />
                      3 Angles
                    </span>
                  )}
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  {saveMessage && (
                    <span style={{ fontSize: "11px", fontWeight: "600", color: "#16a34a" }}>{saveMessage}</span>
                  )}
                  <button
                    onClick={saveToHistory}
                    disabled={!displayContent && !finalScript}
                    style={{ display: "flex", alignItems: "center", gap: "4px", padding: "6px 12px", fontSize: "12px", fontWeight: "700", color: "#16a34a", backgroundColor: "#dcfce7", border: "none", borderRadius: "8px", cursor: "pointer", opacity: (!displayContent && !finalScript) ? 0.5 : 1 }}
                  >
                    <BookOpen size={14} /> Save
                  </button>
                  <button
                    onClick={() => setShowHistory(!showHistory)}
                    style={{ display: "flex", alignItems: "center", gap: "4px", padding: "6px 12px", fontSize: "12px", fontWeight: "700", color: "#6366f1", backgroundColor: "#eef2ff", border: "none", borderRadius: "8px", cursor: "pointer", position: "relative" }}
                  >
                    <Layers size={14} /> History
                    {scriptHistory.length > 0 && (
                      <span style={{ position: "absolute", top: "-4px", right: "-4px", backgroundColor: "#ef4444", color: "white", fontSize: "10px", fontWeight: "700", padding: "2px 5px", borderRadius: "10px", minWidth: "16px", textAlign: "center" }}>
                        {scriptHistory.length}
                      </span>
                    )}
                  </button>
                  <button
                    onClick={() => navigator.clipboard.writeText(displayContent || finalScript)}
                    style={{ display: "flex", alignItems: "center", gap: "4px", padding: "6px 12px", fontSize: "12px", fontWeight: "700", color: "#4f46e5", backgroundColor: "transparent", border: "none", borderRadius: "8px", cursor: "pointer" }}
                  >
                    <Copy size={14} /> Copy
                  </button>
                </div>
              </div>

              {/* Script Tabs - Only show if we have multiple scripts */}
              {hasMultipleScripts && (
                <div style={{ display: "flex", gap: "8px" }}>
                  {scripts.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setActiveScriptTab(index)}
                      style={{
                        padding: "8px 16px",
                        borderRadius: "8px",
                        fontSize: "12px",
                        fontWeight: "600",
                        border: activeScriptTab === index ? "none" : "1px solid #e2e8f0",
                        backgroundColor: activeScriptTab === index ? "#4f46e5" : "#ffffff",
                        color: activeScriptTab === index ? "#ffffff" : "#64748b",
                        cursor: "pointer",
                        transition: "all 0.2s",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px"
                      }}
                    >
                      <span>Script {index + 1}</span>
                      {angles[index] && (
                        <span style={{
                          fontSize: "10px",
                          opacity: 0.8,
                          maxWidth: "100px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap"
                        }}>
                          {angles[index].name}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}

              {/* History Panel Dropdown */}
              {showHistory && (
                <div style={{
                  position: "absolute",
                  top: "100%",
                  right: "0",
                  width: "350px",
                  maxHeight: "400px",
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "12px",
                  boxShadow: "0 10px 25px rgba(0,0,0,0.15)",
                  zIndex: 100,
                  overflow: "hidden"
                }}>
                  <div style={{ padding: "12px 16px", borderBottom: "1px solid #f1f5f9", backgroundColor: "#f8fafc", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "14px", fontWeight: "700", color: "#334155" }}>Script History</span>
                    <button onClick={() => setShowHistory(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8" }}>
                      <X size={16} />
                    </button>
                  </div>
                  <div style={{ maxHeight: "340px", overflowY: "auto" }}>
                    {scriptHistory.length === 0 ? (
                      <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8" }}>
                        <p style={{ fontSize: "13px" }}>No saved scripts yet</p>
                        <p style={{ fontSize: "11px", marginTop: "4px" }}>Click Save to store scripts here</p>
                      </div>
                    ) : (
                      scriptHistory.map((entry) => (
                        <div key={entry.id} style={{ padding: "12px 16px", borderBottom: "1px solid #f1f5f9", cursor: "pointer", transition: "background 0.2s" }}
                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#f8fafc"}
                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "#ffffff"}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                            <div onClick={() => loadFromHistory(entry)} style={{ flex: 1 }}>
                              <p style={{ fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "4px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "250px" }}>
                                {entry.topic}
                              </p>
                              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                                <span style={{ fontSize: "10px", padding: "2px 6px", backgroundColor: "#eef2ff", color: "#4f46e5", borderRadius: "4px" }}>{entry.mode}</span>
                                <span style={{ fontSize: "10px", color: "#94a3b8" }}>{entry.scripts.length} script{entry.scripts.length > 1 ? "s" : ""}</span>
                                <span style={{ fontSize: "10px", color: "#94a3b8" }}>{new Date(entry.timestamp).toLocaleDateString()}</span>
                              </div>
                            </div>
                            <button onClick={() => deleteFromHistory(entry.id)} style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", padding: "4px" }}>
                              <X size={14} />
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Current angle info */}
            {currentAngle && (
              <div style={{
                padding: "12px 16px",
                backgroundColor: "#fef3c7",
                borderBottom: "1px solid #fcd34d",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}>
                <ChevronRight size={16} style={{ color: "#d97706" }} />
                <div>
                  <span style={{ fontSize: "12px", fontWeight: "700", color: "#92400e" }}>
                    Angle: {currentAngle.name}
                  </span>
                  {currentAngle.focus && (
                    <span style={{ fontSize: "11px", color: "#a16207", marginLeft: "8px" }}>
                      — {currentAngle.focus}
                    </span>
                  )}
                </div>
              </div>
            )}

            <div style={{ flex: 1, overflowY: "auto", padding: "24px", backgroundColor: "#ffffff" }}>
              {displayContent ? (
                <div style={{ maxWidth: "none", color: "#334155", lineHeight: "1.9", fontSize: "14px" }}>
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => (
                        <h1 style={{ fontSize: "18px", fontWeight: "700", color: "#0f172a", marginBottom: "16px", paddingBottom: "8px", borderBottom: "2px solid #e2e8f0" }}>{children}</h1>
                      ),
                      h2: ({ children }) => (
                        <h2 style={{ fontSize: "16px", fontWeight: "700", color: "#1e293b", marginTop: "24px", marginBottom: "12px" }}>{children}</h2>
                      ),
                      h3: ({ children }) => (
                        <h3 style={{ fontSize: "14px", fontWeight: "700", color: "#334155", marginTop: "20px", marginBottom: "8px" }}>{children}</h3>
                      ),
                      p: ({ children }) => (
                        <p style={{ marginBottom: "12px", lineHeight: "1.8" }}>{children}</p>
                      ),
                      strong: ({ children }) => (
                        <strong style={{ fontWeight: "700", color: "#0f172a" }}>{children}</strong>
                      ),
                      hr: () => (
                        <hr style={{ border: "none", borderTop: "2px solid #e2e8f0", margin: "24px 0" }} />
                      ),
                    }}
                  >{displayContent}</ReactMarkdown>
                </div>
              ) : finalScript ? (
                <div style={{ maxWidth: "none", color: "#334155", lineHeight: "1.9", fontSize: "14px" }}>
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => (
                        <h1 style={{ fontSize: "18px", fontWeight: "700", color: "#0f172a", marginBottom: "16px", paddingBottom: "8px", borderBottom: "2px solid #e2e8f0" }}>{children}</h1>
                      ),
                      h2: ({ children }) => (
                        <h2 style={{ fontSize: "16px", fontWeight: "700", color: "#1e293b", marginTop: "24px", marginBottom: "12px" }}>{children}</h2>
                      ),
                      h3: ({ children }) => (
                        <h3 style={{ fontSize: "14px", fontWeight: "700", color: "#334155", marginTop: "20px", marginBottom: "8px" }}>{children}</h3>
                      ),
                      p: ({ children }) => (
                        <p style={{ marginBottom: "12px", lineHeight: "1.8" }}>{children}</p>
                      ),
                      strong: ({ children }) => (
                        <strong style={{ fontWeight: "700", color: "#0f172a" }}>{children}</strong>
                      ),
                      hr: () => (
                        <hr style={{ border: "none", borderTop: "2px solid #e2e8f0", margin: "24px 0" }} />
                      ),
                    }}
                  >{finalScript}</ReactMarkdown>
                </div>
              ) : (
                <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#cbd5e1", gap: "12px" }}>
                  <div style={{ padding: "16px", backgroundColor: "#f1f5f9", borderRadius: "50%" }}>
                    <Zap size={24} />
                  </div>
                  <p style={{ fontSize: "14px", fontWeight: "500" }}>Ready to write 3 viral scripts.</p>
                  <p style={{ fontSize: "12px", color: "#94a3b8" }}>Each script explores a different angle with 5 unique hooks.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
