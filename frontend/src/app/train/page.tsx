"use client";

import { useState } from "react";
import axios from "axios";
import { Save, Database, ArrowLeft, CheckCircle2, AlertCircle, Zap } from "lucide-react";
import Link from "next/link";

export default function TrainPage() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [mode, setMode] = useState("informational");
  const [hookType, setHookType] = useState("shock");

  const [isTraining, setIsTraining] = useState(false);
  const [status, setStatus] = useState("");
  const [debugInfo, setDebugInfo] = useState("");

  const handleTrain = async () => {
    if (!title.trim() || !content.trim()) return alert("Please fill in Title and Script");

    setIsTraining(true);
    setStatus("Processing...");
    setDebugInfo("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await axios.post(`${apiUrl}/train_script`, {
        title,
        script_content: content,
        mode,
        hook_type: hookType
      });

      setStatus("Success");
      setDebugInfo(`ID: ${response.data.script_id} | Skel: ${response.data.meta_preview.skeleton}`);

      // Clear form after success
      setTitle("");
      setContent("");
      setTimeout(() => setStatus(""), 5000);

    } catch (error: unknown) {
      console.error(error);
      setStatus("Error");
      if (axios.isAxiosError(error)) {
        setDebugInfo(error.response?.data?.detail || error.message);
      } else if (error instanceof Error) {
        setDebugInfo(error.message);
      } else {
        setDebugInfo("An unknown error occurred");
      }
    } finally {
      setIsTraining(false);
    }
  };

  const getButtonStyle = () => {
    const baseStyle = {
      width: "100%",
      padding: "16px",
      borderRadius: "12px",
      fontSize: "14px",
      fontWeight: "700" as const,
      color: "#ffffff",
      border: "none",
      cursor: isTraining ? "not-allowed" : "pointer",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "8px",
      transition: "all 0.2s"
    };

    if (status === "Success") {
      return { ...baseStyle, backgroundColor: "#16a34a", boxShadow: "0 4px 12px rgba(22, 163, 74, 0.3)" };
    } else if (status === "Error") {
      return { ...baseStyle, backgroundColor: "#dc2626", boxShadow: "0 4px 12px rgba(220, 38, 38, 0.3)" };
    } else {
      return { ...baseStyle, backgroundColor: isTraining ? "#94a3b8" : "#4f46e5", boxShadow: isTraining ? "none" : "0 4px 12px rgba(79, 70, 229, 0.3)" };
    }
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f1f5f9", fontFamily: "system-ui, sans-serif" }}>

      {/* HEADER */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", backgroundColor: "#ffffff", borderBottom: "1px solid #e2e8f0" }}>
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

        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 16px", fontSize: "14px", fontWeight: "600", color: "#475569", textDecoration: "none", borderRadius: "8px", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0" }}>
          <ArrowLeft size={16} />
          Back to Studio
        </Link>
      </header>

      {/* MAIN CONTENT */}
      <div style={{ padding: "32px 24px", maxWidth: "800px", margin: "0 auto" }}>

        {/* Page Title */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
          <div style={{ height: "48px", width: "48px", backgroundColor: "#4f46e5", borderRadius: "12px", display: "flex", alignItems: "center", justifyContent: "center", color: "#ffffff" }}>
            <Database size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: "24px", fontWeight: "700", color: "#0f172a" }}>Train Knowledge Base</h2>
            <p style={{ fontSize: "14px", color: "#64748b" }}>Add successful scripts to improve AI output</p>
          </div>
        </div>

        {/* Form Card */}
        <div style={{ backgroundColor: "#ffffff", padding: "32px", borderRadius: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0" }}>

          {/* Metadata Row */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>
                Script Mode
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                style={{ width: "100%", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "12px", fontSize: "14px", fontWeight: "600", color: "#0f172a", outline: "none", cursor: "pointer" }}
              >
                <option value="informational">Informational (Story)</option>
                <option value="listical">Listical (Numbered)</option>
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>
                Hook Type
              </label>
              <select
                value={hookType}
                onChange={(e) => setHookType(e.target.value)}
                style={{ width: "100%", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "12px", fontSize: "14px", fontWeight: "600", color: "#0f172a", outline: "none", cursor: "pointer" }}
              >
                <option value="shock">Shock</option>
                <option value="question">Question</option>
                <option value="negative">Negative</option>
                <option value="story">Story</option>
              </select>
            </div>
          </div>

          {/* Title Input */}
          <div style={{ marginBottom: "24px" }}>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>
              Title (Internal Reference)
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Jio 5G Strategy"
              style={{ width: "100%", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "12px", fontSize: "14px", fontWeight: "600", color: "#0f172a", outline: "none" }}
            />
          </div>

          {/* Script Content */}
          <div style={{ marginBottom: "24px" }}>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "8px" }}>
              Full Script (Hook + Body)
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste the full successful script here..."
              style={{ width: "100%", height: "280px", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "12px", fontSize: "13px", fontFamily: "ui-monospace, monospace", lineHeight: "1.7", color: "#475569", outline: "none", resize: "none" }}
            />
          </div>

          {/* Action Button */}
          <button
            onClick={handleTrain}
            disabled={isTraining}
            style={getButtonStyle()}
          >
            {isTraining ? "Processing..." :
             status === "Success" ? <><CheckCircle2 size={20}/> Saved to Knowledge Base!</> :
             status === "Error" ? <><AlertCircle size={20}/> Training Failed</> :
             <><Save size={20}/> Train Model</>
            }
          </button>

          {/* Debug Output */}
          {debugInfo && (
            <div style={{ marginTop: "16px", padding: "12px", backgroundColor: status === "Success" ? "#f0fdf4" : "#fef2f2", borderRadius: "12px", border: `1px solid ${status === "Success" ? "#bbf7d0" : "#fecaca"}`, fontSize: "12px", fontFamily: "ui-monospace, monospace", color: status === "Success" ? "#166534" : "#991b1b", wordBreak: "break-all" }}>
              {debugInfo}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
