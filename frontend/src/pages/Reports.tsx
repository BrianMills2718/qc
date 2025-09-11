// Reports Page - Generate and export analysis reports (05_reports.html)

import React from 'react';
import {
  Container,
  Typography,
  Box,
} from '@mui/material';

const Reports: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Reports
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Generate and export analysis reports
      </Typography>
      
      <Box sx={{ mt: 4 }}>
        <Typography variant="body1">
          🚧 Reports generation interface coming soon...
        </Typography>
      </Box>
    </Container>
  );
};

export default Reports;