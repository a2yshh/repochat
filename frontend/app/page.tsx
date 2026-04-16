"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import Sidebar from "@/components/Sidebar";
import RepoInput from "@/components/RepoInput";
import ChatInterface from "@/components/ChatInterface";
import LoadingState from "@/components/LoadingState";

const API_URL = "http://127.0.0.1:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  timestamp?: string;
}

interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: string;
}

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isReady, setIsReady] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (sessionId && isReady) {
      loadConversations();
      const interval = setInterval(loadConversations, 3000);
      return () => clearInterval(interval);
    }
  }, [sessionId, isReady]);

  const loadConversations = async () => {
    if (!sessionId) return;

    try {
      console.log("📡 Fetching conversations...");
      const res = await axios.get(`${API_URL}/api/conversations/${sessionId}`);
      setConversations(res.data.conversations);
    } catch (err) {
      console.error("❌ Failed to load conversations:", err);
    }
  };

  const handleProcessRepo = async (url: string) => {
    setRepoUrl(url);
    setIsProcessing(true);
    setError("");
    setProcessingStatus("cloning");

    try {
      console.log("🚀 Processing repo:", url);

      const res = await axios.post(`${API_URL}/api/process-repo`, {
        github_url: url,
      });

      const sid = res.data.session_id;
      console.log("✅ Session ID:", sid);

      setSessionId(sid);

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API_URL}/api/status/${sid}`);
          const status = statusRes.data.status;

          console.log("📊 Status:", status);

          setProcessingStatus(status);

          if (status === "ready") {
            clearInterval(pollInterval);
            setIsProcessing(false);
            setIsReady(true);
          } else if (status === "error") {
            clearInterval(pollInterval);
            setIsProcessing(false);
            setError("Processing failed.");
          }
        } catch (err) {
          console.error("❌ Polling error:", err);
          clearInterval(pollInterval);
          setIsProcessing(false);
          setError("Polling failed.");
        }
      }, 2000);
    } catch (error: any) {
      console.error("❌ Process repo error:", error);
      setIsProcessing(false);
      setError(error?.response?.data?.detail || "Failed to process repo");
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!sessionId) return;

    const userMsg: Message = {
      role: "user",
      content: message,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    console.log("📨 Sending message:", message);
    console.log("👉 API:", `${API_URL}/api/chat`);

    try {
      const controller = new AbortController();

      const timeout = setTimeout(() => {
        controller.abort();
      }, 60000);

      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message,
          conversation_id: conversationId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const newConversationId = res.headers.get("X-Conversation-ID");

      if (newConversationId && !conversationId) {
        setConversationId(newConversationId);
        setTimeout(loadConversations, 500);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No stream");

      const decoder = new TextDecoder();
      let fullText = "";

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "", timestamp: new Date().toISOString() },
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        fullText += chunk;

        let displayText = fullText;
        let sources: string[] = [];

        const marker = "\n\n---SOURCES---\n";

        if (fullText.includes(marker)) {
          const parts = fullText.split(marker);
          displayText = parts[0];
          sources = parts[1].split("\n").filter(Boolean);
        }

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: displayText,
            sources,
            timestamp: new Date().toISOString(),
          };
          return updated;
        });
      }
    } catch (err: any) {
      console.error("❌ CHAT ERROR:", err);

      let msg = "Something went wrong.";

      if (err.name === "AbortError") {
        msg = "Request timed out.";
      } else if (err.message.includes("Failed to fetch")) {
        msg = "Backend not reachable (CORS / server down)";
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: msg,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
  };

  const handleSelectConversation = async (convId: string) => {
    try {
      const res = await axios.get(`${API_URL}/api/conversation/${convId}`);
      setConversationId(convId);
      setMessages(res.data.messages);
    } catch (err) {
      console.error("❌ Load conversation error:", err);
    }
  };

  const handleBackToRepoSelection = () => {
    setRepoUrl("");
    setSessionId(null);
    setConversationId(null);
    setConversations([]);
    setMessages([]);
    setIsReady(false);
    setIsProcessing(false);
    setError("");
  };

  if (error && !isProcessing && !isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RepoInput onSubmit={handleProcessRepo} isProcessing={false} />
        <p className="text-red-500 mt-4">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      {isReady && sessionId && (
        <Sidebar
          conversations={conversations}
          currentConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
          onBackToRepoSelection={handleBackToRepoSelection}
          repoUrl={repoUrl}
        />
      )}

      <div className="flex-1 flex flex-col">
        {!isProcessing && !isReady && (
          <RepoInput onSubmit={handleProcessRepo} isProcessing={isProcessing} />
        )}

        {isProcessing && <LoadingState status={processingStatus} />}

        {isReady && sessionId && (
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isSending}
            repoUrl={repoUrl}
          />
        )}
      </div>
    </div>
  );
}