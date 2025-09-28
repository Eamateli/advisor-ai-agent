// frontend/src/components/chat/ChatInput.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { cn, autoResizeTextarea } from '../../lib/utils';
import { constants } from '../../lib/config';
import { useChatStream } from '../../services/chat';
import { Button } from '../ui/Button';
import { 
  PaperAirplaneIcon,
  StopIcon,
  PlusIcon,
  MicrophoneIcon,
  PaperClipIcon 
} from '@heroicons/react/24/outline';

const chatSchema = z.object({
  message: z
    .string()
    .min(1, 'Message cannot be empty')
    .max(constants.MAX_MESSAGE_LENGTH, `Message too long (max ${constants.MAX_MESSAGE_LENGTH} characters)`),
});

type ChatFormData = z.infer<typeof chatSchema>;

interface ChatInputProps {
  onSendMessage?: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSendMessage,
  disabled = false,
  placeholder = "Ask anything about your meetings...",
  className,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, stopStream, isStreaming } = useChatStream();
  const [charCount, setCharCount] = useState(0);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isValid },
  } = useForm<ChatFormData>({
    resolver: zodResolver(chatSchema),
    mode: 'onChange',
  });

  const messageValue = watch('message') || '';

  // Update character count
  useEffect(() => {
    setCharCount(messageValue.length);
  }, [messageValue]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      autoResizeTextarea(textareaRef.current);
    }
  }, [messageValue]);

  // Focus textarea on mount
  useEffect(() => {
    if (textareaRef.current && !disabled) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const onSubmit = async (data: ChatFormData) => {
    if (disabled || isStreaming) return;

    const message = data.message.trim();
    if (!message) return;

    try {
      // Clear form immediately for better UX
      reset();
      setCharCount(0);

      // Send message through prop or service
      if (onSendMessage) {
        onSendMessage(message);
      } else {
        await sendMessage(message);
      }

      // Focus back to textarea
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(onSubmit)();
    }
  };

  const handleStop = () => {
    stopStream();
  };

  const isDisabled = disabled || isStreaming;
  const showCharCount = charCount > constants.MAX_MESSAGE_LENGTH * 0.8;

  return (
    <div className={cn('w-full max-w-4xl mx-auto', className)}>
      <form onSubmit={handleSubmit(onSubmit)} className="relative">
        {/* Main input container */}
        <div className="relative flex items-end gap-2 p-4 bg-background border border-input rounded-2xl shadow-sm focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background">
          {/* Add attachment button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="flex-shrink-0 w-8 h-8 rounded-full"
            disabled={isDisabled}
            title="Add attachment (coming soon)"
          >
            <PlusIcon className="w-4 h-4" />
          </Button>

          {/* Message textarea */}
          <div className="flex-1 min-w-0">
            <textarea
              {...register('message')}
              ref={textareaRef}
              rows={1}
              placeholder={placeholder}
              disabled={isDisabled}
              onKeyDown={handleKeyDown}
              className={cn(
                'w-full resize-none border-0 bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none auto-resize',
                'disabled:cursor-not-allowed disabled:opacity-50',
                errors.message && 'text-destructive'
              )}
              style={{ minHeight: '20px', maxHeight: '200px' }}
            />
            
            {/* Character count */}
            {showCharCount && (
              <div className={cn(
                'text-xs mt-1',
                charCount > constants.MAX_MESSAGE_LENGTH 
                  ? 'text-destructive' 
                  : 'text-muted-foreground'
              )}>
                {charCount}/{constants.MAX_MESSAGE_LENGTH}
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1 flex-shrink-0">
            {/* Voice input button (future feature) */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="w-8 h-8 rounded-full"
              disabled={true}
              title="Voice input (coming soon)"
            >
              <MicrophoneIcon className="w-4 h-4" />
            </Button>

            {/* Send or Stop button */}
            {isStreaming ? (
              <Button
                type="button"
                variant="destructive"
                size="icon"
                onClick={handleStop}
                className="w-8 h-8 rounded-full"
                title="Stop generation"
              >
                <StopIcon className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                type="submit"
                size="icon"
                disabled={!isValid || isDisabled || !messageValue.trim()}
                className="w-8 h-8 rounded-full"
                title="Send message"
              >
                <PaperAirplaneIcon className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Error message */}
        {errors.message && (
          <div className="mt-2 text-sm text-destructive px-4">
            {errors.message.message}
          </div>
        )}
      </form>

      {/* Quick actions or suggestions could go here */}
      <div className="mt-3 flex items-center justify-center">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Press Enter to send, Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
}