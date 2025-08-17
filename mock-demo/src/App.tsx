/**
 * AI Governance Dashboard - Mock Demo App
 * 
 * I created this as the main application component that provides the theme
 * and layout for the mock demo version of the AI Governance Dashboard.
 * 
 * Author: Oliver Ellison
 * Created: 2024
 */

import React from 'react';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material/styles';
import Dashboard from './Dashboard';

// I create a custom theme for the mock demo
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
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#333333',
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Dashboard />
    </ThemeProvider>
  );
};

export default App;
