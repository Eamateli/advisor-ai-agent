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
  CalendarIcon
} from '@heroicons/react/24/outline';

const chatSchema = z.object({
  message: z
    .string()
    .min(1, 'Please enter a message')
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
    setValue,
    formState: { errors, isValid },
  } = useForm<ChatFormData>({
    resolver: zodResolver(chatSchema),
    mode: 'onBlur', // Changed from 'onChange' to 'onBlur' to reduce validation frequency
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
    if (disabled || isStreaming) {
      return;
    }

    const message = data.message.trim();
    if (!message) {
      return;
    }

    try {
      // Send message through prop or service
      if (onSendMessage) {
        await onSendMessage(message);
      } else {
        await sendMessage(message);
      }

      // Clear form after successful send
      reset();
      setCharCount(0);

      // Focus back to textarea
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Don't clear form on error so user can retry
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const message = messageValue.trim();
      if (message && !disabled && !isStreaming) {
        handleSubmit(onSubmit)();
      }
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
          'relative flex items-end gap-1 sm:gap-2 p-2 sm:p-3 rounded-2xl',
          'bg-background border-2 border-border',
          'focus-within:border-border focus-within:ring-0 focus-within:outline-none',
          'shadow-sm',
          isDisabled && 'opacity-60'
        )}>
          {/* Add context button - hide on very small screens */}

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
                'focus:outline-none focus:ring-0 focus:border-0 auto-resize',
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

          {/* Context selector button - hide on mobile */}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="flex-shrink-0 text-xs px-2 sm:px-3 h-8 sm:h-9 hidden sm:flex"
            disabled={isDisabled}
            title="Select context"
            onClick={() => {
              // TODO: Implement context selection
              console.log('Context selector clicked');
            }}
          >
            <CalendarIcon className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
            <span className="hidden md:inline">General</span>
          </Button>

          {/* Send or Stop button */}
          {isStreaming ? (
            <Button
              type="button"
              variant="destructive"
              size="icon"
              onClick={handleStop}
              className="w-8 h-8 sm:w-9 sm:h-9 rounded-full flex-shrink-0"
              title="Stop generation"
            >
              <StopIcon className="w-4 h-4 sm:w-5 sm:h-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              disabled={isDisabled}
              onClick={(e) => {
                e.preventDefault();
                const message = messageValue.trim();
                if (message && !disabled && !isStreaming) {
                  handleSubmit(onSubmit)();
                }
              }}
              className={cn(
                'w-8 h-8 sm:w-9 sm:h-9 rounded-full flex-shrink-0',
                (messageValue.trim() && !disabled && !isStreaming)
                  ? 'bg-primary hover:bg-primary/90' 
                  : 'bg-muted cursor-not-allowed'
              )}
              title="Send message"
            >
              <PaperAirplaneIcon className="w-4 h-4 sm:w-5 sm:h-5" />
            </Button>
          )}
        </div>

        {/* Error message - only show for real validation errors, not empty field */}
        {errors.message && messageValue.length > 0 && errors.message.type !== 'required' && (
          <div className="mt-2 text-sm text-destructive px-3">
            {errors.message.message}
          </div>
        )}
      </form>


      {/* Helper text - hide on mobile */}
      <div className="mt-2 px-3 text-center hidden sm:block">
        <span className="text-xs text-muted-foreground">
          Press <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded border border-border">Enter</kbd> to send, 
          <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded border border-border ml-1">Shift + Enter</kbd> for new line
        </span>
      </div>
    </div>
  );
}