import { useState, useRef, useEffect } from "react";
import { ChatHeader } from "./ChatHeader";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
import { sendChatRequest } from "@/api/client";
import type { ChatResponse, ApiError } from "@/types/api";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
  citations?: Array<{ chunk_id: string; section: string; entity: string }>;
  evidence?: Array<{
    id: string;
    score: number;
    section: string;
    entity: string;
    keywords: string[];
    text_preview: string;
  }>;
  error?: string;
}

const getTimestamp = () => {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export const ChatContainer = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Hello! I'm your AI assistant. I can help you with questions about my background, experience, and skills.\n\nAsk me anything about:\n- **My experience** — Work history and projects\n- **My skills** — Technical abilities and expertise\n- **My background** — Education and qualifications\n\nHow can I assist you today?",
      isUser: false,
      timestamp: getTimestamp(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isUser: true,
      timestamp: getTimestamp(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response: ChatResponse = await sendChatRequest({
        query: text,
        top_k: 6,
      });

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        isUser: false,
        timestamp: getTimestamp(),
        citations: response.citations,
        evidence: response.evidence,
      };

      setIsTyping(false);
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      setIsTyping(false);
      const errorMessage =
        error && typeof error === "object" && "message" in error
          ? (error as ApiError).message
          : "An unexpected error occurred. Please try again.";

      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error: ${errorMessage}`,
        isUser: false,
        timestamp: getTimestamp(),
        error: errorMessage,
      };

      setMessages((prev) => [...prev, errorResponse]);
    }
  };

  // Group messages to determine avatar visibility
  const shouldShowAvatar = (index: number) => {
    if (messages[index].isUser) return false;
    if (index === 0) return true;
    return messages[index - 1].isUser;
  };

  return (
    <div className="h-screen flex flex-col chat-container">
      <ChatHeader name="Resume Chatbot" status="Ready to help" />

      <div className="flex-1 overflow-y-auto py-6 space-y-4">
        <div className="max-w-3xl mx-auto">
          {messages.map((message, index) => (
            <div key={message.id} className="mb-4">
              <ChatBubble
                message={message.text}
                isUser={message.isUser}
                timestamp={message.timestamp}
                showAvatar={shouldShowAvatar(index)}
              />
            </div>
          ))}
          {isTyping && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <ChatInput onSend={handleSend} disabled={isTyping} />
    </div>
  );
};


