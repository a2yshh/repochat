"use client";

import { MessageSquare, Plus, Github, ArrowLeft } from "lucide-react";

interface SidebarProps {
  conversations: any[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onBackToRepoSelection: () => void;
  repoUrl: string;
}

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewChat,
  onBackToRepoSelection,
  repoUrl,
}: SidebarProps) {
  const repoName = repoUrl.split("/").slice(-2).join("/").replace(".git", "");

  return (
    <div className="w-72 bg-gray-900/50 backdrop-blur-xl border-r border-gray-800/50 flex flex-col shadow-2xl">
      {/* Header */}
      <div className="p-5 border-b border-gray-800/50">
        <button
          onClick={onBackToRepoSelection}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-3 text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Change Repository
        </button>
        <div className="flex items-center gap-2 mb-2">
          <Github className="w-5 h-5 text-blue-400" />
          <h2 className="text-white font-semibold text-sm">Current Repo</h2>
        </div>
        <p className="text-gray-400 text-xs truncate font-mono bg-gray-800/30 px-2 py-1 rounded">
          {repoName}
        </p>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-blue-500/25"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Chat Threads */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Chat Threads ({conversations.length})
        </div>
        <div className="px-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <MessageSquare className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-gray-500 text-sm">No conversations yet</p>
              <p className="text-gray-600 text-xs mt-1">
                Start chatting to create one
              </p>
            </div>
          ) : (
            conversations.map((conv, index) => (
              <button
                key={conv.conversation_id}
                onClick={() => onSelectConversation(conv.conversation_id)}
                className={`w-full text-left px-3 py-3 rounded-lg transition-all duration-200 group ${
                  currentConversationId === conv.conversation_id
                    ? "bg-blue-600/20 border border-blue-500/30 shadow-lg"
                    : "hover:bg-gray-800/50 border border-transparent"
                }`}
              >
                <div className="flex items-start gap-2">
                  <MessageSquare
                    className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                      currentConversationId === conv.conversation_id
                        ? "text-blue-400"
                        : "text-gray-500 group-hover:text-gray-400"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <div
                      className={`text-sm font-medium truncate ${
                        currentConversationId === conv.conversation_id
                          ? "text-white"
                          : "text-gray-300 group-hover:text-white"
                      }`}
                    >
                      {conv.title || `Chat ${conversations.length - index}`}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {conv.message_count} messages
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800/50">
        <div className="text-xs text-gray-500 text-center">
          Powered by{" "}
          <span className="text-blue-400 font-semibold">Groq</span> + Local
          Embeddings
        </div>
      </div>
    </div>
  );
}