/**
 * ChatContainer - Main chat interface component.
 * 
 * Purpose: Manages chat state, handles user messages, and displays conversation.
 * This component bridges the UI (ChatBubble, ChatInput) with the backend API.
 * 
 * Why this design:
 * - Centralized state management for messages
 * - Handles API communication in one place
 * - Separates UI components from API logic
 * - Easy to add features like message history, retry, etc.
 */

import { useState, useRef, useEffect } from "react";
import { ChatHeader } from "./ChatHeader";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
// API client for making backend requests
// Purpose: Handles HTTP communication with FastAPI backend
import { sendChatRequest } from "@/api/client";
// TypeScript types matching backend schema
// Purpose: Ensures type safety between frontend and backend
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

  /**
   * Handles sending a user message to the backend and displaying the response.
   * 
   * Purpose: Main integration point between frontend UI and backend API.
   * 
   * Flow:
   * 1. Create user message and add to UI immediately (optimistic update)
   * 2. Show typing indicator
   * 3. Send request to backend via API client
   * 4. Receive response with LLM answer, citations, and evidence
   * 5. Display bot response in chat
   * 6. Handle errors gracefully
   * 
   * Why this approach:
   * - Optimistic UI update (user message appears immediately)
   * - Async/await for clean error handling
   * - Preserves citations/evidence for potential future features (e.g., showing sources)
   * - Error handling provides user feedback instead of silent failures
   * 
   * Design decisions:
   * - top_k: 6 - Good balance of context vs speed/cost
   * - Error messages are user-friendly, not technical
   * - Citations/evidence stored but not displayed yet (can be added to ChatBubble later)
   */
  const handleSend = async (text: string) => {
    // Create user message object
    // Purpose: Represents the user's input in the message list
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isUser: true,
      timestamp: getTimestamp(),
    };

    // Add user message to UI immediately (optimistic update)
    // Why: Better UX - user sees their message right away, not after API call
    setMessages((prev) => [...prev, userMessage]);
    
    // Show typing indicator while waiting for response
    // Purpose: Visual feedback that request is being processed
    setIsTyping(true);

    try {
      // Send request to backend API
      // The API client handles:
      // - HTTP POST to /chat endpoint
      // - JSON serialization
      // - Error handling
      // - Response parsing
      // 
      // Request structure matches ChatRequest type (query + top_k)
      // Response structure matches ChatResponse type (answer + citations + evidence)
      const response: ChatResponse = await sendChatRequest({
        query: text,
        top_k: 6, // Number of chunks to retrieve from knowledge base
      });

      // Create bot response message from API response
      // Purpose: Convert API response format to UI message format
      // 
      // Why preserve citations/evidence:
      // - Citations: Chunks explicitly referenced by LLM (could show as sources)
      // - Evidence: All chunks considered (could show for transparency)
      // - Currently not displayed in UI, but data is available for future features
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer, // The LLM-generated answer text
        isUser: false,
        timestamp: getTimestamp(),
        citations: response.citations, // Chunks cited by LLM
        evidence: response.evidence, // All chunks retrieved
      };

      // Hide typing indicator and add bot response to chat
      setIsTyping(false);
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      // Handle API errors gracefully
      // Purpose: Provide user feedback instead of silent failure
      // 
      // Why this error handling:
      // - Extracts error message from API error response if available
      // - Falls back to generic message if error format is unexpected
      // - Displays error as a bot message so user knows what happened
      setIsTyping(false);
      const errorMessage =
        error && typeof error === "object" && "message" in error
          ? (error as ApiError).message
          : "An unexpected error occurred. Please try again.";

      // Create error message to display in chat
      // Purpose: Show error to user in a user-friendly way
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error: ${errorMessage}`,
        isUser: false,
        timestamp: getTimestamp(),
        error: errorMessage, // Store error for potential debugging/analytics
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


