// SIMPLIFIED CHAT INPUT - GUARANTEED TO WORK
import React, { useState, useRef } from 'react';
import { useChatStream } from '../../services/chat';
import { Button } from '../ui/Button';
import { 
  PaperAirplaneIcon,
  StopIcon
} from '@heroicons/react/24/outline';

interface ChatInputSimpleProps {
  onSendMessage?: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInputSimple({
  onSendMessage,
  disabled = false,
  placeholder = "Type your message here...",
  className,
}: ChatInputSimpleProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, stopStream, isStreaming } = useChatStream();
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  };

  // Send message
  const handleSend = async () => {
    const trimmedMessage = message.trim();
    
    if (!trimmedMessage || isSubmitting || isStreaming) {
      console.log('❌ Send blocked:', { 
        hasMessage: !!trimmedMessage, 
        isSubmitting, 
        isStreaming 
      });
      return;
    }

    console.log('🚀 Sending message:', trimmedMessage);
    setIsSubmitting(true);

    try {
      if (onSendMessage) {
        await onSendMessage(trimmedMessage);
      } else {
        await sendMessage(trimmedMessage);
      }
      
      console.log('✅ Message sent successfully');
      setMessage('');
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (error) {
      console.error('❌ Error sending message:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle stop streaming
  const handleStop = () => {
    stopStream();
  };

  const isDisabled = disabled || isStreaming || isSubmitting;
  const canSend = message.trim().length > 0 && !isDisabled;

  return (
    <div className={`w-full max-w-4xl mx-auto ${className || ''}`}>
      <div className={`
        relative flex items-end gap-2 p-3 rounded-2xl
        bg-background border-2 border-border
        shadow-sm
        ${isDisabled ? 'opacity-60' : ''}
      `}>
        {/* Textarea */}
        <div className="flex-1 min-w-0 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isDisabled}
            className={`
              w-full resize-none border-0 bg-transparent
              text-sm text-foreground placeholder:text-muted-foreground
              focus:outline-none focus:ring-0 focus:border-0
              disabled:cursor-not-allowed disabled:opacity-50
              min-h-[24px] max-h-[200px] py-0.5
            `}
            rows={1}
          />
        </div>

        {/* Send or Stop button */}
        {isStreaming ? (
          <Button
            type="button"
            variant="destructive"
            size="icon"
            onClick={handleStop}
            className="w-9 h-9 rounded-full flex-shrink-0"
            title="Stop generation"
          >
            <StopIcon className="w-5 h-5" />
          </Button>
        ) : (
          <Button
            type="button"
            size="icon"
            disabled={!canSend}
            onClick={handleSend}
            className={`
              w-9 h-9 rounded-full flex-shrink-0
              ${canSend 
                ? 'bg-primary hover:bg-primary/90' 
                : 'bg-muted cursor-not-allowed'
              }
            `}
            title={canSend ? "Send message" : "Type a message to send"}
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </Button>
        )}
      </div>

      {/* Helper text */}
      <div className="mt-2 px-3 text-center">
        <span className="text-xs text-muted-foreground">
          Press <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded border">Enter</kbd> to send, 
          <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded border ml-1">Shift + Enter</kbd> for new line
        </span>
      </div>
    </div>
  );
}
