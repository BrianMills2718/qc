// Main App component with routing and React Query setup

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { ErrorBoundary } from 'react-error-boundary';

// Import pages (we'll create these)
import Dashboard from './pages/Dashboard';
import ProjectWorkspace from './pages/ProjectWorkspace';
import CodesBrowser from './pages/CodesBrowser';
import QuotesExplorer from './pages/QuotesExplorer';
import Reports from './pages/Reports';
import Navigation from './components/common/Navigation';
import ErrorFallback from './components/common/ErrorFallback';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error && typeof error === 'object' && 'status' in error) {
          const status = (error as any).status;
          if (status >= 400 && status < 500) {
            return false;
          }
        }
        return failureCount < 3;
      },
      staleTime: 60000, // 1 minute
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Create Material-UI theme matching your UI planning design system
const theme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32', // Deep green - professional, analytical
    },
    secondary: {
      main: '#1565C0', // Deep blue - trust, depth
    },
    background: {
      default: '#FAFAFA', // Soft white
      paper: '#FFFFFF', // Pure white
    },
    text: {
      primary: '#212121', // Near black
    },
  },
  typography: {
    h1: { fontWeight: 600 },
    h2: { fontWeight: 600 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    body1: { fontWeight: 400 },
    body2: { fontWeight: 400 },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              <Navigation />
              <main style={{ flexGrow: 1 }}>
                <Routes>
                  {/* Default route redirects to dashboard */}
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  
                  {/* Main pages matching your UI planning */}
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/workspace" element={<ProjectWorkspace />} />
                  <Route path="/workspace/:projectId" element={<ProjectWorkspace />} />
                  <Route path="/codes" element={<CodesBrowser />} />
                  <Route path="/quotes" element={<QuotesExplorer />} />
                  <Route path="/reports" element={<Reports />} />
                  
                  {/* 404 fallback */}
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </main>
            </div>
          </Router>
        </ThemeProvider>
        
        {/* React Query DevTools (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
