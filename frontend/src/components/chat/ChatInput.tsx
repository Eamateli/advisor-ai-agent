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
  FaceSmileIcon,
  CalendarIcon
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
        <div className={cn(
          'relative flex items-end gap-2 p-3 rounded-2xl',
          'bg-background border-2 border-border',
          'focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/10',
          'transition-all duration-200 shadow-sm',
          isDisabled && 'opacity-60'
        )}>
          {/* Add context button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="flex-shrink-0 w-9 h-9 rounded-full"
            disabled={isDisabled}
            title="Add context"
          >
            <PlusIcon className="w-5 h-5" />
          </Button>

          {/* Message textarea */}
          <div className="flex-1 min-w-0 relative">
            <textarea
              {...register('message')}
              ref={textareaRef}
              rows={1}
              placeholder={placeholder}
              disabled={isDisabled}
              onKeyDown={handleKeyDown}
              className={cn(
                'w-full resize-none border-0 bg-transparent',
                'text-sm text-foreground placeholder:text-muted-foreground',
                'focus:outline-none auto-resize',
                'disabled:cursor-not-allowed disabled:opacity-50',
                'min-h-[24px] max-h-[200px] py-0.5',
                errors.message && 'text-destructive'
              )}
            />
            
            {/* Character count (only show when approaching limit) */}
            {showCharCount && (
              <div className={cn(
                'absolute -top-6 right-0 text-xs',
                charCount > constants.MAX_MESSAGE_LENGTH 
                  ? 'text-destructive' 
                  : 'text-muted-foreground'
              )}>
                {charCount}/{constants.MAX_MESSAGE_LENGTH}
              </div>
            )}
          </div>

          {/* Context selector button */}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="flex-shrink-0 text-xs px-3 h-9 hidden sm:flex"
            disabled={isDisabled}
            title="Select context"
          >
            <CalendarIcon className="w-4 h-4 mr-1" />
            <span className="hidden md:inline">All meetings</span>
          </Button>

          {/* Emoji/Reactions button (future feature) */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="w-9 h-9 rounded-full flex-shrink-0 hidden sm:flex"
            disabled={true}
            title="Add reaction (coming soon)"
          >
            <FaceSmileIcon className="w-5 h-5" />
          </Button>

          {/* Voice input button (future feature) */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="w-9 h-9 rounded-full flex-shrink-0"
            disabled={true}
            title="Voice input (coming soon)"
          >
            <MicrophoneIcon className="w-5 h-5" />
          </Button>

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
              type="submit"
              size="icon"
              disabled={!isValid || isDisabled || !messageValue.trim()}
              className={cn(
                'w-9 h-9 rounded-full flex-shrink-0',
                (isValid && messageValue.trim() && !isDisabled)
                  ? 'bg-primary hover:bg-primary/90' 
                  : 'bg-muted cursor-not-allowed'
              )}
              title="Send message"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </Button>
          )}
        </div>

        {/* Error message */}
        {errors.message && (
          <div className="mt-2 text-sm text-destructive px-3">
            {errors.message.message}
          </div>
        )}
      </form>

      {/* Helper text */}
      <div className="mt-2 px-3 text-center">
        <span className="text-xs text-muted-foreground">
          Press <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded border border-border">Enter</kbd> to send, 
          <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded border border-border ml-1">Shift + Enter</kbd> for new line
        </span>
      </div>
    </div>
  );
}