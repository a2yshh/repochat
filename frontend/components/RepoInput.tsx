"use client";

import { useState } from "react";

interface RepoInputProps {
  onSubmit: (url: string) => void;
  isProcessing: boolean;
}

export default function RepoInput({ onSubmit, isProcessing }: RepoInputProps) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSubmit(url.trim());
    }
  };

  return (
    <div className="w-full h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent">
            RepoChat
          </h1>
          <p className="text-lg text-slate-400">
            Explore and understand repositories with AI
          </p>
        </div>

        {/* Input Container */}
        <div className="space-y-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="owner/repo or https://github.com/owner/repo"
              className="flex-1 px-6 py-4 bg-slate-900/60 backdrop-blur-xl text-white border border-white/10 rounded-xl focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all placeholder-slate-500"
              disabled={isProcessing}
            />
            <button
              type="submit"
              disabled={isProcessing || !url.trim()}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-semibold rounded-xl transition-all shadow-lg hover:shadow-blue-500/40 disabled:shadow-none"
            >
              {isProcessing ? "Processing..." : "Process Repo"}
            </button>
          </form>
        </div>

        {/* Description */}
        <div className="text-center">
          <p className="text-slate-400 text-sm">
            Paste a public GitHub repository URL or use owner/repo format
          </p>
          <p className="text-xs text-slate-500 mt-3">
            Example: torvalds/linux or https://github.com/facebook/react
          </p>
        </div>
      </div>
    </div>
  );
}