import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';

// Components
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Requests from './pages/Requests/Requests';
import Policies from './pages/Policies/Policies';
import Evaluations from './pages/Evaluations/Evaluations';
import Datasets from './pages/Datasets/Datasets';
import Settings from './pages/Settings/Settings';
import Login from './pages/Auth/Login';
import { AuthProvider } from './contexts/AuthContext';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
        },
      },
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <Box sx={{ display: 'flex', minHeight: '100vh' }}>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<Layout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="requests" element={<Requests />} />
                  <Route path="policies" element={<Policies />} />
                  <Route path="evaluations" element={<Evaluations />} />
                  <Route path="datasets" element={<Datasets />} />
                  <Route path="settings" element={<Settings />} />
                </Route>
              </Routes>
            </Box>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
