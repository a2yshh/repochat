"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import CodeModificationPanel from "./CodeModificationPanel";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  timestamp?: string;
  sessionId?: string;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  repoUrl: string;
  sessionId : string;
}

export default function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  repoUrl,
  sessionId,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const repoName = repoUrl.replace("https://github.com/", "");

  return (
    <div className="mx-auto flex h-[calc(100vh-2rem)] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-slate-950/45 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div>
          <h1 className="text-lg font-semibold text-white">RepoChat Workspace</h1>
          <p className="text-sm text-slate-400">{repoName}</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
        {messages.length === 0 && (
          <div className="mt-20 text-center text-slate-500">
            <p className="text-lg text-white">Ask anything about this repository</p>
            <p className="mt-2 text-sm">
              Try: &quot;What does this project do?&quot; or &quot;How is authentication handled?&quot;
            </p>
          </div>
        )}



        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-5 py-4 shadow-lg ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-blue-600 to-cyan-500 text-white"
                  : "border border-white/10 bg-white/5 text-gray-100"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="prose prose-invert prose-sm max-w-none
                  prose-headings:text-gray-100 prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2
                  prose-h2:text-lg prose-h3:text-base
                  prose-p:text-gray-200 prose-p:leading-relaxed prose-p:my-2
                  prose-strong:text-white prose-strong:font-semibold
                  prose-code:text-blue-300 prose-code:bg-gray-900 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
                  prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700 prose-pre:rounded-lg prose-pre:my-3
                  prose-ul:my-2 prose-ol:my-2 prose-li:text-gray-200 prose-li:my-0.5
                  prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
                ">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <p>{msg.content}</p>
              )}

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-600">
                  <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Referenced Files</p>
                  <div className="flex flex-wrap gap-2">
                    {msg.sources.map((src, j) => (
                      <span
                        key={j}
                    className="rounded-md bg-slate-800/90 px-2.5 py-1 font-mono text-xs text-blue-300"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-400">
              <div className="flex gap-1">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span>
              </div>
            </div>
          </div>
        )}


        <div ref={messagesEndRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-white/10 px-5 py-4"
      >
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the codebase..."
            disabled={isLoading}
            className="flex-1 rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-3
              text-white placeholder-gray-500 focus:outline-none focus:ring-2
              focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-500 px-6 py-3 font-medium text-white
              hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500
              disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </form>

      <div className="border-t border-white/10 px-5 py-4">
        <CodeModificationPanel sessionId={sessionId} />
      </div>
    </div>
  );
}