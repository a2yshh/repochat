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
    <div className="w-full max-w-2xl mx-auto">
      <h1 className="text-4xl font-bold text-white mb-8 text-center">
        RepoChat
      </h1>
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="owner/repo or https://github.com/owner/repo"
          className="flex-1 px-4 py-3 bg-gray-800 text-white border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500"
          disabled={isProcessing}
        />
        <button
          type="submit"
          disabled={isProcessing || !url.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium rounded-lg transition"
        >
          {isProcessing ? "Processing..." : "Process Repo"}
        </button>
      </form>
      <p className="text-gray-400 text-sm text-center mt-4">
        Paste a public GitHub repository URL or use owner/repo format.
      </p>
    </div>
  );
}