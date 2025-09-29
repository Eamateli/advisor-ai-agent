// frontend/src/types/index.ts

export interface User {
  id: number;
  email: string;
  full_name?: string;
  profile_picture?: string;
  created_at: string;
  google_connected: boolean;
  hubspot_connected: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tool_calls?: ToolCall[];
  created_at: string;
  isStreaming?: boolean;
}

export interface ToolCall {
  id: string;
  type: string;
  function: {
    name: string;
    arguments: string;
  };
  result?: any;
}

export interface StreamEvent {
  type: 'content' | 'tool_use_start' | 'tool_result' | 'done' | 'error';
  content?: string;
  tool_name?: string;
  tool_input?: any;
  tool_result?: any;
  error?: string;
  status_code?: number;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  currentStreamingMessageId: string | null;
  error: string | null;
}

export interface Meeting {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
    attendees?: Array<{  // Make it optional and generic
    name?: string;
    email: string;
    avatar?: string;
    status?: 'accepted' | 'declined' | 'pending';
  }>;
  description?: string;
  location?: string;
  meeting_link?: string;
}

export interface Participant {
  email: string;
  name?: string;
  avatar?: string;
  status?: 'accepted' | 'declined' | 'pending';
}

export interface SyncStatus {
  gmail: {
    connected: boolean;
    last_sync: string | null;
    status: 'idle' | 'syncing' | 'error';
    total_emails: number;
  };
  hubspot: {
    connected: boolean;
    last_sync: string | null;
    status: 'idle' | 'syncing' | 'error';
    total_contacts: number;
  };
  calendar: {
    connected: boolean;
    last_sync: string | null;
    status: 'idle' | 'syncing' | 'error';
    total_events: number;
  };
}

export interface ConversationThread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message: string;
}

export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  notifications: {
    email: boolean;
    push: boolean;
    sound: boolean;
  };
  privacy: {
    data_sharing: boolean;
    analytics: boolean;
  };
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface APIError {
  error: string;
  detail?: string;
  status_code?: number;
  request_id?: string;
}

// Theme context types
export interface ThemeState {
  theme: 'light' | 'dark' | 'system';
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

// Form types
export interface ChatForm {
  message: string;
}

export interface ProfileForm {
  full_name: string;
  email: string;
  notifications: {
    email: boolean;
    push: boolean;
  };
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
  total: number;
}

// Context filter types for meetings
export interface MeetingFilter {
  timeframe: 'today' | 'week' | 'month' | 'all';
  participants?: string[];
  search?: string;
}

// Environment variables type
export interface Config {
  API_URL: string;
  WS_URL: string;
  ENVIRONMENT: 'development' | 'production';
  GOOGLE_CLIENT_ID?: string;
}


// ========== Additional Types  ==========

export interface Attendee {
  name: string;
  email: string;
  avatar?: string;
  responseStatus?: 'accepted' | 'declined' | 'tentative' | 'needsAction';
  isOrganizer?: boolean;
}

export interface ContextFilter {
  label: string;
  startDate?: string;
  endDate?: string;
  attendees?: string[];
  keywords?: string[];
}