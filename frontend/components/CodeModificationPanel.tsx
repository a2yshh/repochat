
"use client";

import { useState } from "react";
import axios from "axios";
import { Download, FileCode, AlertCircle, CheckCircle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Diff {
  file: string;
  diff: string;
  additions: number;
}

interface ModificationResult {
  modification_id: string;
  summary: string;
  files_changed: string[];
  diffs: Diff[];
  intent_analysis: any;
}

interface CodeModificationPanelProps {
  sessionId: string;
}

export default function CodeModificationPanel({ sessionId }: CodeModificationPanelProps) {
  const [query, setQuery] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<ModificationResult | null>(null);
  const [error, setError] = useState("");

  const handleModify = async () => {
    if (!query.trim()) return;

    setIsProcessing(true);
    setError("");
    setResult(null);

    try {
      const res = await axios.post(`${API_URL}/api/modify-code`, {
        session_id: sessionId,
        modification_query: query,
      });

      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Modification failed");
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadPatch = () => {
    if (!result) return;
    window.open(`${API_URL}/api/download-patch/${result.modification_id}`, "_blank");
  };

  const downloadModifiedRepo = () => {
    if (!result) return;
    window.open(`${API_URL}/api/download-modified-repo/${result.modification_id}`, "_blank");
  };

  return (
    <div className="bg-gray-800/30 backdrop-blur-xl border border-gray-700/30 rounded-xl p-6">
      <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <FileCode className="w-5 h-5 text-blue-400" />
        AI Code Editor
      </h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-2">
            Describe what you want to change:
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Example: Make the UI more attractive with better colors and spacing"
            className="w-full px-4 py-3 bg-gray-700/50 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            disabled={isProcessing}
          />
        </div>

        <button
          onClick={handleModify}
          disabled={isProcessing || !query.trim()}
          className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:from-gray-700 disabled:to-gray-700 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
        >
          {isProcessing ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Analyzing & Modifying...
            </>
          ) : (
            "Generate Code Changes"
          )}
        </button>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-4 mt-6">
            <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-green-400 font-medium">{result.summary}</p>
                <p className="text-gray-400 text-sm mt-1">
                  Intent: {result.intent_analysis.description}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={downloadPatch}
                className="py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download Patch
              </button>
              <button
                onClick={downloadModifiedRepo}
                className="py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download Repo
              </button>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-gray-300">Files Changed:</h4>
              {result.files_changed.map((file, idx) => (
                <div
                  key={idx}
                  className="px-3 py-2 bg-gray-700/30 rounded border border-gray-600/30 text-sm text-gray-300 font-mono"
                >
                  {file}
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-gray-300">Code Diffs:</h4>
              {result.diffs.map((diff, idx) => (
                <details key={idx} className="group">
                  <summary className="px-3 py-2 bg-gray-700/30 rounded border border-gray-600/30 text-sm text-gray-300 cursor-pointer hover:bg-gray-700/50">
                    {diff.file} ({diff.additions > 0 ? '+' : ''}{diff.additions} lines)
                  </summary>
                  <pre className="mt-2 p-4 bg-gray-900 rounded border border-gray-700 text-xs text-gray-300 overflow-x-auto">
                    {diff.diff}
                  </pre>
                </details>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}