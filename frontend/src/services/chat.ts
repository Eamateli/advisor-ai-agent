export function useChatStream() {
  return {
    sendMessage: async (message: string) => {
      console.log('Send message stub');
    },
    stopStream: () => {},
    isStreaming: false,
  };
}
