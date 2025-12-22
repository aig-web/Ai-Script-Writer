"use client";

import { useState } from "react";
import axios from "axios";
import { Save, Database, ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";
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

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans p-6 lg:p-10">
      <div className="max-w-3xl mx-auto">

        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/" className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-600">
            <ArrowLeft size={24} />
          </Link>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-slate-900">
            <div className="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white">
               <Database size={18} />
            </div>
            Train Knowledge Base
          </h1>
        </div>

        {/* Form Card */}
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 space-y-6">

          {/* Metadata Row */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Script Mode (Strict)
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-xl p-3 font-bold text-slate-700 outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
              >
                <option value="informational">Informational (Story)</option>
                <option value="listical">Listical (Numbered)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Hook Type
              </label>
              <select
                value={hookType}
                onChange={(e) => setHookType(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-xl p-3 font-bold text-slate-700 outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
              >
                <option value="shock">Shock</option>
                <option value="question">Question</option>
                <option value="negative">Negative</option>
                <option value="story">Story</option>
              </select>
            </div>
          </div>

          {/* Inputs */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Title (Internal Reference)
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Jio 5G Strategy"
              className="w-full bg-white border border-slate-200 rounded-xl p-3 font-medium text-slate-900 outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-400 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Full Script (Hook + Body)
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste the full successful script here..."
              className="w-full h-64 bg-white border border-slate-200 rounded-xl p-3 font-mono text-sm leading-relaxed text-slate-900 outline-none focus:ring-2 focus:ring-indigo-500 resize-none placeholder:text-slate-400 transition-all"
            />
          </div>

          {/* Action Button */}
          <button
            onClick={handleTrain}
            disabled={isTraining}
            className={`w-full py-4 rounded-xl font-bold text-white flex items-center justify-center gap-2 transition-all shadow-md ${
              status === "Success" ? "bg-green-600 hover:bg-green-700" :
              status === "Error" ? "bg-red-600 hover:bg-red-700" :
              "bg-indigo-600 hover:bg-indigo-700 hover:shadow-lg"
            }`}
          >
            {isTraining ? "Processing..." :
             status === "Success" ? <><CheckCircle2 size={20}/> Saved!</> :
             status === "Error" ? <><AlertCircle size={20}/> Failed</> :
             <><Save size={20}/> Train Model</>
            }
          </button>

          {/* Debug Output */}
          {debugInfo && (
            <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono text-slate-600 break-all">
              {debugInfo}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
