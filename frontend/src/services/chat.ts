export function useChatStream() {
  return {
    sendMessage: async () => {
      console.log('Send message stub');
    },
    stopStream: () => {},
    isStreaming: false,
  };
}
