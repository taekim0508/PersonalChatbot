/**
 * Main App component - Clean entry point for the chat interface.
 * Sets up React Query and provides the chat container.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ChatContainer } from "./components/chat/ChatContainer";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChatContainer />
    </QueryClientProvider>
  );
}

export default App;
