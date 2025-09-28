// frontend/src/components/chat/MessageBubble.tsx
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ChatMessage } from '../../types';
import { cn, formatDate, copyToClipboard } from '../../lib/utils';
import { useTheme } from '../../lib/theme';
import { Avatar } from '../ui/Avatar';
import { Button } from '../ui/Button';
import { TypingIndicator } from '../ui/LoadingSpinner';
import { 
  ClipboardIcon, 
  CheckIcon,
  UserIcon,
  CpuChipIcon 
} from '@heroicons/react/24/outline';

interface MessageBubbleProps {
  message: ChatMessage;
  isLatest?: boolean;
}

export function MessageBubble({ message, isLatest }: MessageBubbleProps) {
  const { resolvedTheme } = useTheme();
  const [copiedStates, setCopiedStates] = useState<{ [key: string]: boolean }>({});

  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;

  const handleCopyCode = async (code: string, blockId: string) => {
    const success = await copyToClipboard(code);
    if (success) {
      setCopiedStates(prev => ({ ...prev, [blockId]: true }));
      setTimeout(() => {
        setCopiedStates(prev => ({ ...prev, [blockId]: false }));
      }, 2000);
    }
  };

  return (
    <div
      className={cn(
        'flex gap-3 max-w-4xl message-fade-in',
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      )}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <Avatar
            size="md"
            name="You"
            className="bg-primary text-primary-foreground"
            fallbackClassName="bg-primary text-primary-foreground"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <CpuChipIcon className="w-4 h-4 text-white" />
          </div>
        )}
      </div>

      {/* Message content */}
      <div
        className={cn(
          'flex flex-col min-w-0 flex-1',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        {/* Message bubble */}
        <div
          className={cn(
            'relative rounded-2xl px-4 py-3 max-w-[85%] break-words',
            isUser
              ? 'bg-primary text-primary-foreground rounded-br-md'
              : 'bg-muted/50 text-foreground rounded-bl-md border'
          )}
        >
          {/* Streaming indicator or content */}
          {isStreaming && !message.content ? (
            <TypingIndicator />
          ) : (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                components={{
                  code: ({ node, inline, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const language = match ? match[1] : '';
                    const codeString = String(children).replace(/\n$/, '');
                    const blockId = `${message.id}-${Math.random()}`;

                    if (!inline && language) {
                      return (
                        <div className="code-block">
                          {/* Code header with language and copy button */}
                          <div className="flex items-center justify-between px-4 py-2 bg-muted/30 border-b text-sm">
                            <span className="font-medium text-muted-foreground">
                              {language}
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCopyCode(codeString, blockId)}
                              className="h-6 px-2"
                            >
                              {copiedStates[blockId] ? (
                                <CheckIcon className="w-3 h-3" />
                              ) : (
                                <ClipboardIcon className="w-3 h-3" />
                              )}
                            </Button>
                          </div>
                          <SyntaxHighlighter
                            style={resolvedTheme === 'dark' ? oneDark : oneLight}
                            language={language}
                            PreTag="div"
                            customStyle={{
                              margin: 0,
                              background: 'transparent',
                            }}
                            {...props}
                          >
                            {codeString}
                          </SyntaxHighlighter>
                        </div>
                      );
                    }

                    return (
                      <code
                        className={cn(
                          className,
                          'relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm'
                        )}
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="mb-2 pl-4">{children}</ul>,
                  ol: ({ children }) => <ol className="mb-2 pl-4">{children}</ol>,
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-muted-foreground/25 pl-4 italic text-muted-foreground">
                      {children}
                    </blockquote>
                  ),
                  h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold mb-2">{children}</h3>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Streaming cursor */}
          {isStreaming && message.content && (
            <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" />
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            'text-xs text-muted-foreground mt-1 px-1',
            isUser ? 'text-right' : 'text-left'
          )}
        >
          {formatDate(message.created_at, { relative: true, includeTime: true })}
        </div>

        {/* Tool calls (if any) */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.tool_calls.map((tool, index) => (
              <div
                key={index}
                className="text-xs bg-muted/30 rounded px-2 py-1 text-muted-foreground"
              >
                🔧 Used {tool.function.name}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}