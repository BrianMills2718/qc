// Error Fallback component for React Error Boundary

import React from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  Alert,
  AlertTitle,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { FallbackProps } from 'react-error-boundary';

const ErrorFallback: React.FC<FallbackProps> = ({ error, resetErrorBoundary }) => {
  return (
    <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom color="error">
          Something went wrong
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          We're sorry, but something unexpected happened. Please try refreshing the page.
        </Typography>
      </Box>

      <Alert severity="error" sx={{ mb: 4, textAlign: 'left' }}>
        <AlertTitle>Error Details</AlertTitle>
        <Typography variant="body2" component="pre" sx={{ 
          whiteSpace: 'pre-wrap', 
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          overflow: 'auto',
          maxHeight: 200,
        }}>
          {error.message}
        </Typography>
      </Alert>

      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={resetErrorBoundary}
        >
          Try Again
        </Button>
        <Button
          variant="outlined"
          onClick={() => window.location.href = '/'}
        >
          Go to Dashboard
        </Button>
      </Box>

      {process.env.NODE_ENV === 'development' && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Stack Trace (Development Only)
          </Typography>
          <Alert severity="info">
            <Typography variant="body2" component="pre" sx={{ 
              whiteSpace: 'pre-wrap', 
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              overflow: 'auto',
              maxHeight: 300,
            }}>
              {error.stack}
            </Typography>
          </Alert>
        </Box>
      )}
    </Container>
  );
};

export default ErrorFallback;