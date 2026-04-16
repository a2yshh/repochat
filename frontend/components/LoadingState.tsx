"use client";

import { useEffect, useState } from "react";

interface LoadingStateProps {
  status: string;
}

const STEPS = [
  { key: "cloning", label: "Cloning repository" },
  { key: "processing", label: "Processing code files" },
  { key: "embedding", label: "Creating embeddings" },
  { key: "ready", label: "Ready to chat" },
];

export default function LoadingState({ status }: LoadingStateProps) {
  const [dots, setDots] = useState("");

  useEffect(() => {
    if (status === "ready") return;
    const interval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 500);
    return () => clearInterval(interval);
  }, [status]);

  const currentIndex = STEPS.findIndex((s) => s.key === status);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
      <div className="w-full max-w-xl rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl">
        <h2 className="mb-2 text-center text-2xl font-semibold text-white">
          Setting up your repo
        </h2>
        <p className="mb-8 text-center text-sm text-slate-400">
          RepoChat is cloning, indexing, and preparing the repository for chat.
        </p>

        {STEPS.map((step, i) => {
          const isDone = i < currentIndex || status === "ready";
          const isCurrent = step.key === status && status !== "ready";

          return (
            <div key={step.key} className="flex items-center gap-3 py-2">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm
                  ${isDone ? "bg-emerald-500 text-white" : ""}
                  ${isCurrent ? "animate-pulse bg-blue-500 text-white" : ""}
                  ${!isDone && !isCurrent ? "bg-slate-800 text-slate-500" : ""}
                `}
              >
                {isDone ? "\u2713" : i + 1}
              </div>
              <span
                className={`${isDone ? "text-emerald-400" : ""} ${isCurrent ? "text-white" : ""} ${!isDone && !isCurrent ? "text-slate-500" : ""}`}
              >
                {step.label}
                {isCurrent ? dots : ""}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}