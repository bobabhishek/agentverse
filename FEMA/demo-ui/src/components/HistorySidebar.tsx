import React from 'react';
import {
  MessageSquare,
  Plus,
  PanelLeftClose,
  Sparkles,
  Trash2,
  FileDown
} from 'lucide-react';
import { ConversationSession } from '../types';

interface HistorySidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  conversations: ConversationSession[];
  activeConversationId: string;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string, e: React.MouseEvent) => void;
  onOpenInspector: () => void;
  completedConversations?: string[];
  onDownloadAuditTrail?: (id: string, e: React.MouseEvent) => void;
}

export const HistorySidebar: React.FC<HistorySidebarProps> = ({
  isOpen,
  onToggle,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  completedConversations = [],
  onDownloadAuditTrail
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onToggle}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-30 lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 bg-black/40 backdrop-blur-md border-r border-white/[0.08] flex flex-col p-3.5 transition-all duration-300 ease-in-out select-none ${
          isOpen
            ? 'w-[260px] translate-x-0'
            : 'w-0 -translate-x-full lg:w-0 lg:-translate-x-full overflow-hidden p-0 border-none'
        }`}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between mb-3.5 pb-2 border-b border-white/[0.08]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-semibold text-sm text-slate-100 tracking-tight leading-none">
                AgentVerse
              </h1>
              <p className="text-[10px] text-blue-400 font-mono mt-0.5">
                FEMA Guardrail
              </p>
            </div>
          </div>

          <button
            onClick={onToggle}
            title="Close sidebar"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.08] transition-colors cursor-pointer lg:hidden"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Action Button */}
        <div className="mb-3">
          <button
            onClick={onNewChat}
            className="w-full bg-white/[0.05] hover:bg-white/[0.10] text-slate-200 hover:text-white border border-white/[0.12] hover:border-blue-500/40 text-xs font-medium py-2 rounded-xl flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer backdrop-blur-xs"
          >
            <Plus className="w-3.5 h-3.5 text-blue-400" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Recents Section */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 px-2 py-1 font-semibold flex items-center justify-between">
            <span>Conversations</span>
            {conversations.length > 0 && (
              <span className="text-[10px] text-slate-600 font-mono">
                {conversations.length}
              </span>
            )}
          </div>

          {conversations.length === 0 ? (
            <div className="text-xs text-slate-500 px-2 py-6 text-center italic">
              No conversations yet
              <p className="text-[10px] text-slate-600 not-italic mt-1">
                Your chats will appear here
              </p>
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeConversationId;
              const hasAudit = completedConversations.includes(conv.id) || Boolean(conv.hasAuditTrail);

              return (
                <div
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition-all border ${
                    isActive
                      ? 'bg-white/[0.08] text-slate-100 border-blue-500/50 shadow-sm font-medium backdrop-blur-xs'
                      : 'text-slate-400 hover:bg-white/[0.05] hover:text-slate-200 border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate flex-1 min-w-0 pr-1 text-left">
                    <MessageSquare
                      className={`w-3.5 h-3.5 shrink-0 transition-colors ${
                        isActive
                          ? 'text-blue-400'
                          : 'text-slate-500 group-hover:text-blue-400'
                      }`}
                    />
                    <span className="truncate block">{conv.title}</span>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    {hasAudit && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDownloadAuditTrail?.(conv.id, e);
                        }}
                        title="Download Audit Trail"
                        className="p-1 rounded text-emerald-400 hover:text-emerald-300 hover:bg-emerald-950/60 transition-colors cursor-pointer"
                      >
                        <FileDown className="w-3.5 h-3.5" />
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={(e) => onDeleteConversation(conv.id, e)}
                      title="Delete conversation"
                      className="opacity-0 group-hover:opacity-100 hover:text-rose-400 transition-opacity p-1 text-slate-500 rounded shrink-0 cursor-pointer"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
};
