"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, BookOpen, Layers, FileText, Copy, Zap, FileUp, X, ChevronRight, CheckCircle, MessageCircle, Loader2 } from "lucide-react";
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

interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

interface SessionData {
  id: string;
  topic: string;
  mode: string;
  user_notes: string;
  research_data: string;
  research_sources: any[];
  files?: any[];
  scripts?: any[];
  chat_history?: { [key: number]: ChatMessage[] };
  created_at: string;
  updated_at: string;
}

export default function StudioPage() {
  // Remove trailing slash from API URL to prevent double-slash issues
  const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

  const [topic, setTopic] = useState("");
  const [notes, setNotes] = useState("");
  const [mode, setMode] = useState("informational");
  const [files, setFiles] = useState<File[]>([]);
  const [useOnlyMyContent, setUseOnlyMyContent] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [status, setStatus] = useState("Ready");

  const [researchData, setResearchData] = useState<string[]>([]);
  const [finalScript, setFinalScript] = useState("");

  // Multi-angle state
  const [angles, setAngles] = useState<ScriptAngle[]>([]);
  const [scripts, setScripts] = useState<string[]>([]);
  const [activeScriptTab, setActiveScriptTab] = useState(0);

  // Session state (Supabase)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Chat state (per-script)
  const [showChat, setShowChat] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<{ [key: number]: ChatMessage[] }>({ 1: [], 2: [], 3: [] });
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Text selection state for "Edit with Claude" popup
  const [selectedText, setSelectedText] = useState("");
  const [selectionPopup, setSelectionPopup] = useState<{ show: boolean; x: number; y: number }>({ show: false, x: 0, y: 0 });

  // Angle selection state (for generic topics)
  const [showAngleSelection, setShowAngleSelection] = useState(false);
  const [angleOptions, setAngleOptions] = useState<string[]>([]);
  const [angleMessage, setAngleMessage] = useState("");

  const researchEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load sessions from Supabase AND localStorage on mount
  useEffect(() => {
    loadSessions();
    loadLocalHistory();
  }, []);

  // Load history from localStorage (fallback when Supabase not available)
  const loadLocalHistory = () => {
    try {
      const stored = localStorage.getItem("scriptai_history");
      if (stored) {
        const localSessions = JSON.parse(stored);
        // Merge with Supabase sessions (local sessions have id starting with "local-")
        setSessions(prev => {
          const supabaseSessions = prev.filter(s => !s.id.startsWith("local-"));
          return [...supabaseSessions, ...localSessions];
        });
      }
    } catch (e) {
      console.log("No local history found");
    }
  };

  // Save to localStorage history
  const saveToLocalHistory = (topic: string, mode: string, scripts: string[], angles: ScriptAngle[], research: string) => {
    try {
      const stored = localStorage.getItem("scriptai_history");
      const existing = stored ? JSON.parse(stored) : [];

      const newSession = {
        id: `local-${Date.now()}`,
        topic,
        mode,
        user_notes: notes,
        research_data: research,
        scripts: scripts.map((s, i) => ({
          script_content: s,
          angle_name: angles[i]?.name || "",
          angle_focus: angles[i]?.focus || "",
          script_number: i + 1
        })),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      // Keep only last 20 sessions
      const updated = [newSession, ...existing].slice(0, 20);
      localStorage.setItem("scriptai_history", JSON.stringify(updated));

      // Update state
      setSessions(prev => {
        const supabaseSessions = prev.filter(s => !s.id.startsWith("local-"));
        return [...supabaseSessions, ...updated];
      });

      console.log("[LocalHistory] Saved:", newSession.id);
    } catch (e) {
      console.error("Failed to save local history", e);
    }
  };

  // Scroll chat to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, activeScriptTab]);

  // Handle text selection in script area - show popup after mouseup
  const handleTextSelection = () => {
    // Use setTimeout to ensure selection is complete
    setTimeout(() => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();

      // Only show popup if there's meaningful selected text and scripts exist
      if (text && text.length > 10 && hasMultipleScripts) {
        // Store the selected text
        setSelectedText(text);

        // Get position for popup
        const range = selection?.getRangeAt(0);
        if (range) {
          const rect = range.getBoundingClientRect();
          setSelectionPopup({
            show: true,
            x: rect.left + rect.width / 2,
            y: rect.top - 10
          });
        }
      }
    }, 50);
  };

  // Hide popup when clicking outside (but not on the popup itself)
  useEffect(() => {
    const handleMouseDown = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      // Don't hide if clicking on the popup
      if (target.closest('.selection-popup')) {
        return;
      }
      // Hide popup on any other click
      if (selectionPopup.show) {
        setSelectionPopup({ show: false, x: 0, y: 0 });
      }
    };

    document.addEventListener('mousedown', handleMouseDown);
    return () => document.removeEventListener('mousedown', handleMouseDown);
  }, [selectionPopup.show]);

  // Edit selected text with Claude - called when popup is clicked
  const editSelectedText = () => {
    // Get the currently stored selected text
    const textToEdit = selectedText;

    if (!textToEdit) {
      console.log("No selected text to edit");
      return;
    }

    console.log("Editing text:", textToEdit.slice(0, 50));

    // Hide popup first
    setSelectionPopup({ show: false, x: 0, y: 0 });

    // Clear browser selection
    window.getSelection()?.removeAllRanges();

    // Open chat panel and pre-fill with context
    setShowChat(true);
    const truncatedText = textToEdit.length > 100 ? textToEdit.slice(0, 100) + '...' : textToEdit;
    setChatInput(`"${truncatedText}"\n\nMake it `);

    // Focus the chat input after a short delay
    setTimeout(() => {
      const chatInputEl = document.querySelector('textarea[placeholder*="Tell Claude"]') as HTMLTextAreaElement;
      if (chatInputEl) {
        chatInputEl.focus();
        // Move cursor to end
        const len = chatInputEl.value.length;
        chatInputEl.setSelectionRange(len, len);
      }
    }, 300);
  };

  const loadSessions = async () => {
    try {
      const response = await fetch(`${apiUrl}/sessions`);
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (e) {
      // Sessions may not be available if Supabase tables don't exist - this is OK
      console.log("Sessions not available - Supabase may not be configured");
      setSessions([]);
    }
  };

  // Load a session from history (supports both Supabase and localStorage)
  const loadFromHistory = async (sessionId: string) => {
    try {
      // Check if this is a local session
      if (sessionId.startsWith("local-")) {
        // Load from localStorage
        const stored = localStorage.getItem("scriptai_history");
        if (stored) {
          const localSessions = JSON.parse(stored);
          const session = localSessions.find((s: any) => s.id === sessionId);
          if (session) {
            setCurrentSessionId(session.id);
            setTopic(session.topic);
            setMode(session.mode);
            setNotes(session.user_notes || "");

            if (session.research_data) {
              const lines = session.research_data.split("\n").filter((l: string) => l.trim().length > 10);
              setResearchData(lines);
            }

            if (session.scripts && session.scripts.length > 0) {
              const scriptContents = session.scripts.map((s: any) => s.script_content);
              const scriptAngles = session.scripts.map((s: any) => ({
                name: s.angle_name || "",
                focus: s.angle_focus || "",
                hook_style: s.angle_hook_style || ""
              }));
              setScripts(scriptContents);
              setAngles(scriptAngles);
              setFinalScript(scriptContents[0] || "");
            }

            setChatMessages({ 1: [], 2: [], 3: [] });
            setShowHistory(false);
            setStatus("Session loaded (local)");
            return;
          }
        }
        throw new Error("Local session not found");
      }

      // Load from Supabase
      const response = await fetch(`${apiUrl}/sessions/${sessionId}`);
      if (!response.ok) throw new Error("Failed to load session");

      const session: SessionData = await response.json();

      // Restore all state
      setCurrentSessionId(session.id);
      setTopic(session.topic);
      setMode(session.mode);
      setNotes(session.user_notes || "");

      // Restore research data
      if (session.research_data) {
        const lines = session.research_data.split("\n").filter((l: string) => l.trim().length > 10);
        setResearchData(lines);
      }

      // Restore scripts and angles
      if (session.scripts && session.scripts.length > 0) {
        const scriptContents = session.scripts.map((s: any) => s.script_content);
        const scriptAngles = session.scripts.map((s: any) => ({
          name: s.angle_name || "",
          focus: s.angle_focus || "",
          hook_style: s.angle_hook_style || ""
        }));
        setScripts(scriptContents);
        setAngles(scriptAngles);
        setFinalScript(scriptContents[0] || "");
      }

      // Restore chat history
      if (session.chat_history) {
        setChatMessages(session.chat_history as { [key: number]: ChatMessage[] });
      }

      setShowHistory(false);
      setStatus("Session loaded");
    } catch (e) {
      console.error("Failed to load session", e);
      alert("Failed to load session");
    }
  };

  // Delete a session (supports both Supabase and localStorage)
  const deleteFromHistory = async (sessionId: string) => {
    try {
      // Check if this is a local session
      if (sessionId.startsWith("local-")) {
        // Delete from localStorage
        const stored = localStorage.getItem("scriptai_history");
        if (stored) {
          const localSessions = JSON.parse(stored);
          const updated = localSessions.filter((s: any) => s.id !== sessionId);
          localStorage.setItem("scriptai_history", JSON.stringify(updated));
        }
        setSessions(sessions.filter(s => s.id !== sessionId));
        return;
      }

      // Delete from Supabase
      await fetch(`${apiUrl}/sessions/${sessionId}`, { method: "DELETE" });
      setSessions(sessions.filter(s => s.id !== sessionId));
    } catch (e) {
      console.error("Failed to delete session", e);
    }
  };

  // Send chat message - works in both local and Supabase mode
  const sendChatMessage = async () => {
    if (!chatInput.trim() || isChatLoading) return;

    // Need script content to chat
    const currentScriptContent = scripts[activeScriptTab];
    if (!currentScriptContent) {
      alert("No script to edit. Generate scripts first.");
      return;
    }

    const scriptNumber = activeScriptTab + 1;
    const userMessage: ChatMessage = { role: "user", content: chatInput };
    const messageToSend = chatInput;

    // Add user message to UI immediately
    setChatMessages(prev => ({
      ...prev,
      [scriptNumber]: [...(prev[scriptNumber] || []), userMessage]
    }));
    setChatInput("");
    setIsChatLoading(true);

    try {
      // Use local chat endpoint (works without Supabase)
      const currentAngle = angles[activeScriptTab] || {};
      const response = await fetch(`${apiUrl}/chat/local`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          script_content: currentScriptContent,
          message: messageToSend,
          script_number: scriptNumber,
          angle_name: currentAngle.name || "",
          angle_focus: currentAngle.focus || ""
        })
      });

      if (!response.ok) throw new Error("Chat failed");

      const data = await response.json();

      // Add assistant response
      const assistantMessage: ChatMessage = { role: "assistant", content: data.response };
      setChatMessages(prev => ({
        ...prev,
        [scriptNumber]: [...(prev[scriptNumber] || []), assistantMessage]
      }));

      // Update script if changed
      if (data.script_changed && data.updated_script) {
        setScripts(prev => {
          const updated = [...prev];
          updated[activeScriptTab] = data.updated_script;
          return updated;
        });
      }
    } catch (e) {
      console.error("Chat error", e);
      // Add error message
      setChatMessages(prev => ({
        ...prev,
        [scriptNumber]: [...(prev[scriptNumber] || []), { role: "assistant", content: "Sorry, something went wrong. Please try again." }]
      }));
    } finally {
      setIsChatLoading(false);
    }
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
    setChatMessages({ 1: [], 2: [], 3: [] });
    setShowChat(false);
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

    // Variables to collect data for saving
    let collectedResearch = "";
    let collectedScripts: string[] = [];
    let collectedAngles: ScriptAngle[] = [];

    try {
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

              // Collect research for saving
              collectedResearch = json.data;

              setResearchData(prev => {
                const merged = [...prev, ...newBullets];
                return Array.from(new Set(merged));
              });
            } else if (json.type === "angles") {
              // Multi-angle: received angle definitions
              collectedAngles = json.data || [];
              setAngles(json.data || []);
            } else if (json.type === "script_complete") {
              // Multi-angle: individual script completed
              setStatus(`Completed Script ${json.script_number}: ${json.angle_name}`);
            } else if (json.type === "result") {
              // Handle both old format (string) and new format (object with multiple scripts)
              if (typeof json.data === "string") {
                setFinalScript(json.data);
                collectedScripts = [json.data];
              } else if (json.data) {
                // New multi-angle format
                if (json.data.scripts && Array.isArray(json.data.scripts)) {
                  collectedScripts = json.data.scripts;
                  setScripts(json.data.scripts);
                }
                if (json.data.angles && Array.isArray(json.data.angles)) {
                  collectedAngles = json.data.angles;
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

      // Auto-save: Try Supabase first, fallback to localStorage
      if (collectedScripts.length > 0) {
        let savedToSupabase = false;

        // Try Supabase first
        try {
          const sessionRes = await fetch(`${apiUrl}/sessions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              topic,
              mode,
              user_notes: notes,
              research_data: collectedResearch,
              skip_research: useOnlyMyContent
            })
          });

          if (sessionRes.ok) {
            const session = await sessionRes.json();
            setCurrentSessionId(session.id);

            // Only save scripts if we got a real session ID (not local-session)
            if (session.id && session.id !== "local-session") {
              // Save all scripts
              for (let i = 0; i < collectedScripts.length; i++) {
                const angle = collectedAngles[i] || {};
                await fetch(`${apiUrl}/sessions/scripts`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    session_id: session.id,
                    script_number: i + 1,
                    script_content: collectedScripts[i],
                    angle_name: angle.name || "",
                    angle_focus: angle.focus || "",
                    angle_hook_style: angle.hook_style || ""
                  })
                });
              }

              // Reload sessions list
              loadSessions();
              savedToSupabase = true;
              console.log("[Session] Saved to Supabase:", session.id);
            }
          }
        } catch (e) {
          console.log("Supabase not available, using localStorage");
        }

        // Fallback: Save to localStorage if Supabase didn't work
        if (!savedToSupabase) {
          saveToLocalHistory(topic, mode, collectedScripts, collectedAngles, collectedResearch);
          setCurrentSessionId(`local-${Date.now()}`);
        }
      }
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
          <div style={{ height: "40px", width: "40px", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", borderRadius: "12px", display: "flex", alignItems: "center", justifyContent: "center", color: "#ffffff", boxShadow: "0 4px 12px rgba(99, 102, 241, 0.3)", fontWeight: "800", fontSize: "18px" }}>
            S
          </div>
          <div>
            <h1 style={{ fontSize: "20px", fontWeight: "700", color: "#0f172a", lineHeight: "1.2" }}>
              SISINTY <span style={{ color: "#94a3b8", fontWeight: "400" }}>Studio</span>
            </h1>
            <p style={{ fontSize: "10px", fontWeight: "600", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em" }}>Multi-Angle Viral Engine</p>
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

          {/* COLUMN 2: RESEARCH / CHAT */}
          <div style={{ display: "flex", flexDirection: "column", backgroundColor: "#ffffff", borderRadius: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", border: "1px solid #e2e8f0", overflow: "hidden", height: "100%", position: "relative" }}>
            {/* Research Header - Always visible */}
            {!showChat && (
              <>
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
              </>
            )}

            {/* Chat Panel - Replaces Research when active */}
            {showChat && hasMultipleScripts && (
              <>
                <div style={{ padding: "16px", borderBottom: "1px solid #f1f5f9", backgroundColor: "#f8fafc", display: "flex", justifyContent: "space-between", alignItems: "center", flexShrink: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <MessageCircle size={18} style={{ color: "#6366f1" }} />
                    <span style={{ fontSize: "14px", fontWeight: "700", color: "#334155" }}>Edit Script {activeScriptTab + 1}</span>
                  </div>
                  <button
                    onClick={() => setShowChat(false)}
                    style={{ fontSize: "12px", fontWeight: "600", backgroundColor: "#eef2ff", color: "#4f46e5", padding: "4px 10px", borderRadius: "6px", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px" }}
                  >
                    <X size={12} /> Close
                  </button>
                </div>

                <div style={{ flex: 1, padding: "16px", overflowY: "auto", backgroundColor: "#fafbfc", display: "flex", flexDirection: "column" }}>
                  {/* Quick suggestions */}
                  {(chatMessages[activeScriptTab + 1] || []).length === 0 && (
                    <div style={{ marginBottom: "16px" }}>
                      <p style={{ fontSize: "11px", fontWeight: "600", color: "#94a3b8", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Quick edits</p>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                        {["Make it shorter", "More engaging hook", "Add statistics", "Fear angle", "Add urgency"].map((suggestion) => (
                          <button
                            key={suggestion}
                            onClick={() => setChatInput(suggestion)}
                            style={{
                              padding: "8px 12px",
                              fontSize: "12px",
                              color: "#4f46e5",
                              backgroundColor: "#ffffff",
                              border: "1px solid #e2e8f0",
                              borderRadius: "8px",
                              cursor: "pointer"
                            }}
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Chat messages */}
                  <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "12px" }}>
                    {(chatMessages[activeScriptTab + 1] || []).map((msg, idx) => (
                      <div key={idx} style={{ padding: "12px", backgroundColor: msg.role === "user" ? "#eef2ff" : "#ffffff", border: "1px solid #f1f5f9", borderRadius: "12px", fontSize: "12px", color: "#475569", lineHeight: "1.6", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
                        <span style={{ color: msg.role === "user" ? "#4f46e5" : "#16a34a", fontWeight: "700", marginRight: "8px" }}>
                          {msg.role === "user" ? "You:" : "Claude:"}
                        </span>
                        {msg.content.length > 200 ? msg.content.substring(0, 200) + "..." : msg.content}
                      </div>
                    ))}
                    {isChatLoading && (
                      <div style={{ padding: "12px", backgroundColor: "#ffffff", border: "1px solid #f1f5f9", borderRadius: "12px", fontSize: "12px", color: "#6366f1", display: "flex", alignItems: "center", gap: "8px" }}>
                        <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
                        Editing script...
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>
                </div>

                {/* Chat input */}
                <div style={{ padding: "16px", borderTop: "1px solid #f1f5f9", backgroundColor: "#f8fafc", flexShrink: 0 }}>
                  <div style={{ display: "flex", gap: "8px", alignItems: "flex-end" }}>
                    <textarea
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          sendChatMessage();
                        }
                      }}
                      placeholder="Tell Claude how to edit... (Shift+Enter for new line)"
                      rows={Math.min(4, Math.max(1, chatInput.split('\n').length))}
                      style={{
                        flex: 1,
                        padding: "12px 14px",
                        borderRadius: "10px",
                        border: "1px solid #e2e8f0",
                        fontSize: "13px",
                        outline: "none",
                        fontFamily: "inherit",
                        backgroundColor: "#ffffff",
                        resize: "none",
                        minHeight: "44px",
                        maxHeight: "120px",
                        lineHeight: "1.4"
                      }}
                      disabled={isChatLoading}
                    />
                    <button
                      onClick={sendChatMessage}
                      disabled={!chatInput.trim() || isChatLoading}
                      style={{
                        padding: "12px 16px",
                        borderRadius: "10px",
                        border: "none",
                        backgroundColor: chatInput.trim() && !isChatLoading ? "#4f46e5" : "#e2e8f0",
                        color: chatInput.trim() && !isChatLoading ? "#ffffff" : "#9ca3af",
                        cursor: chatInput.trim() && !isChatLoading ? "pointer" : "not-allowed",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "13px",
                        fontWeight: "600",
                        height: "44px"
                      }}
                    >
                      <Send size={14} />
                    </button>
                  </div>
                </div>
              </>
            )}
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
                  {currentSessionId && (
                    <span style={{ fontSize: "11px", fontWeight: "600", backgroundColor: "#dcfce7", color: "#16a34a", padding: "4px 10px", borderRadius: "6px", display: "flex", alignItems: "center", gap: "4px" }}>
                      <CheckCircle size={12} />
                      Auto-saved
                    </span>
                  )}
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <button
                    onClick={() => setShowHistory(!showHistory)}
                    style={{ display: "flex", alignItems: "center", gap: "4px", padding: "6px 12px", fontSize: "12px", fontWeight: "700", color: "#6366f1", backgroundColor: "#eef2ff", border: "none", borderRadius: "8px", cursor: "pointer" }}
                  >
                    <Layers size={14} /> History
                  </button>
                  {hasMultipleScripts && (
                    <button
                      onClick={() => setShowChat(!showChat)}
                      title="Edit script with AI"
                      style={{ display: "flex", alignItems: "center", gap: "4px", padding: "6px 12px", fontSize: "12px", fontWeight: "600", color: showChat ? "#ffffff" : "#4f46e5", backgroundColor: showChat ? "#4f46e5" : "#eef2ff", border: "none", borderRadius: "8px", cursor: "pointer" }}
                    >
                      <MessageCircle size={14} /> Edit
                    </button>
                  )}
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
                    <span style={{ fontSize: "14px", fontWeight: "700", color: "#334155" }}>Session History</span>
                    <button onClick={() => setShowHistory(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8" }}>
                      <X size={16} />
                    </button>
                  </div>
                  <div style={{ maxHeight: "340px", overflowY: "auto" }}>
                    {sessions.length === 0 ? (
                      <div style={{ padding: "24px", textAlign: "center", color: "#94a3b8" }}>
                        <p style={{ fontSize: "13px" }}>No sessions yet</p>
                        <p style={{ fontSize: "11px", marginTop: "4px" }}>Generate scripts to see them here</p>
                      </div>
                    ) : (
                      sessions.map((session) => (
                        <div key={session.id} style={{ padding: "12px 16px", borderBottom: "1px solid #f1f5f9", cursor: "pointer", transition: "background 0.2s", backgroundColor: session.id === currentSessionId ? "#eef2ff" : "#ffffff" }}
                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = session.id === currentSessionId ? "#eef2ff" : "#f8fafc"}
                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = session.id === currentSessionId ? "#eef2ff" : "#ffffff"}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                            <div onClick={() => loadFromHistory(session.id)} style={{ flex: 1 }}>
                              <p style={{ fontSize: "13px", fontWeight: "600", color: "#334155", marginBottom: "4px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "250px" }}>
                                {session.topic}
                              </p>
                              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                                <span style={{ fontSize: "10px", padding: "2px 6px", backgroundColor: "#eef2ff", color: "#4f46e5", borderRadius: "4px" }}>{session.mode}</span>
                                <span style={{ fontSize: "10px", color: "#94a3b8" }}>{new Date(session.created_at).toLocaleDateString()}</span>
                                {session.id === currentSessionId && (
                                  <span style={{ fontSize: "10px", padding: "2px 6px", backgroundColor: "#dcfce7", color: "#16a34a", borderRadius: "4px" }}>Current</span>
                                )}
                              </div>
                            </div>
                            <button onClick={() => deleteFromHistory(session.id)} style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", padding: "4px" }}>
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

            <div
              style={{ flex: 1, overflowY: "auto", padding: "24px", backgroundColor: "#ffffff", position: "relative" }}
              onMouseUp={handleTextSelection}
            >
              {/* Selection Popup - Edit with Claude */}
              {selectionPopup.show && (
                <button
                  className="selection-popup"
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    editSelectedText();
                  }}
                  style={{
                    position: "fixed",
                    left: selectionPopup.x,
                    top: selectionPopup.y,
                    transform: "translate(-50%, -100%)",
                    backgroundColor: "#1e293b",
                    color: "white",
                    padding: "8px 14px",
                    borderRadius: "8px",
                    fontSize: "13px",
                    fontWeight: "600",
                    fontFamily: "inherit",
                    cursor: "pointer",
                    zIndex: 1000,
                    boxShadow: "0 4px 16px rgba(0,0,0,0.25)",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    whiteSpace: "nowrap",
                    border: "none",
                    outline: "none"
                  }}
                >
                  <MessageCircle size={14} />
                  Edit with Claude
                </button>
              )}

              {displayContent ? (
                <>
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
                  {/* Angle info - shown at the end of script */}
                  {currentAngle && (
                    <div style={{
                      marginTop: "24px",
                      padding: "12px 16px",
                      backgroundColor: "#f8fafc",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px"
                    }}>
                      <ChevronRight size={16} style={{ color: "#6366f1" }} />
                      <div>
                        <span style={{ fontSize: "12px", fontWeight: "700", color: "#4f46e5" }}>
                          Angle: {currentAngle.name}
                        </span>
                        {currentAngle.focus && (
                          <span style={{ fontSize: "11px", color: "#64748b", marginLeft: "8px" }}>
                            — {currentAngle.focus}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </>
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

      {/* CSS Animation for loading spinner */}
      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
