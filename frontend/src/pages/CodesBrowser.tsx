// Codes Browser Page - Hierarchical exploration (03_codes_browser.html)

import React from 'react';
import {
  Container,
  Typography,
  Box,
} from '@mui/material';
import { useAllCodes } from '../hooks/useQueries';

const CodesBrowser: React.FC = () => {
  const { data, isLoading, error } = useAllCodes();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Codes Browser
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Hierarchical exploration of the coding system
      </Typography>
      
      <Box sx={{ mt: 4 }}>
        <Typography variant="body1">
          🚧 Codes browser interface coming soon...
        </Typography>
        {data && (
          <Typography variant="body2" sx={{ mt: 2 }}>
            Found {data.data?.length || 0} codes in the system.
          </Typography>
        )}
      </Box>
    </Container>
  );
};

export default CodesBrowser;