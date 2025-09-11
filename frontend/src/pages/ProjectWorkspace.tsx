// Project Workspace Page - Main analysis interface (02_project_workspace.html)

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Send as SendIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import { useNaturalLanguageQuery, useAllBaseData } from '../hooks/useQueries';

const ProjectWorkspace: React.FC = () => {
  const { projectId } = useParams();
  const [query, setQuery] = useState('');
  const { executeQuery, data, isLoading, error, isSuccess } = useNaturalLanguageQuery();
  const baseData = useAllBaseData();

  const handleSubmitQuery = () => {
    if (query.trim()) {
      executeQuery(query.trim());
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmitQuery();
    }
  };

  const suggestedQueries = [
    'Show me all people',
    'Find all organizations',
    'Show me all codes',
    'List all concepts',
    'Show me senior people',
    'Find people who work at organizations',
  ];

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Project Workspace
          {projectId && (
            <Chip 
              label={`Project: ${projectId}`} 
              color="primary" 
              size="small" 
              sx={{ ml: 2 }} 
            />
          )}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Interactive analysis interface with graph visualization and natural language queries
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Left Panel - Query Interface */}
        <Box sx={{ flex: { md: '0 0 33%' } }}>
          <Paper sx={{ p: 3, height: 'fit-content' }}>
            <Typography variant="h6" gutterBottom>
              Natural Language Query
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                variant="outlined"
                placeholder="Ask questions about your data in natural language..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
              />
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={isLoading ? <CircularProgress size={20} /> : <SendIcon />}
                  onClick={handleSubmitQuery}
                  disabled={!query.trim() || isLoading}
                >
                  {isLoading ? 'Processing...' : 'Execute Query'}
                </Button>
              </Box>
            </Box>

            {/* Suggested Queries */}
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
              Try these queries:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {suggestedQueries.map((suggestion, index) => (
                <Chip
                  key={index}
                  label={suggestion}
                  variant="outlined"
                  size="small"
                  onClick={() => setQuery(suggestion)}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>

            {/* Data Overview */}
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
              Available Data:
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">
                People: {baseData.people.data?.data?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Organizations: {baseData.organizations.data?.data?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Codes: {baseData.codes.data?.data?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Concepts: {baseData.concepts.data?.data?.length || 0}
              </Typography>
            </Box>
          </Paper>
        </Box>

        {/* Center Panel - Results/Graph Area */}
        <Box sx={{ flex: 1 }}>
          <Paper sx={{ p: 3, minHeight: 600 }}>
            <Typography variant="h6" gutterBottom>
              Query Results & Graph Visualization
            </Typography>

            {/* Query Results */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Error: {error instanceof Error ? error.message : 'Failed to execute query'}
              </Alert>
            )}

            {isSuccess && data && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Generated Cypher Query:
                </Typography>
                <Box sx={{ 
                  p: 2, 
                  bgcolor: 'grey.100', 
                  borderRadius: 1, 
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  mb: 2
                }}>
                  {data.cypher}
                </Box>

                <Typography variant="subtitle2" gutterBottom>
                  Results ({data.data?.length || 0} items):
                </Typography>
                
                {data.data && data.data.length > 0 ? (
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
                    {data.data.map((item, index) => (
                        <Card key={index} variant="outlined">
                          <CardContent>
                            <Typography variant="h6" gutterBottom>
                              {item.label || item.name || 'Unknown'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              ID: {item.id}
                            </Typography>
                            {Object.entries(item.properties || {}).map(([key, value]) => (
                              <Typography key={key} variant="caption" display="block">
                                <strong>{key}:</strong> {String(value)}
                              </Typography>
                            ))}
                          </CardContent>
                        </Card>
                    ))}
                  </Box>
                ) : (
                  <Typography color="text.secondary">
                    No results found for this query.
                  </Typography>
                )}
              </Box>
            )}

            {!isSuccess && !error && !isLoading && (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: 400,
                color: 'text.secondary'
              }}>
                <PsychologyIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
                <Typography variant="h6" gutterBottom>
                  Ready for Analysis
                </Typography>
                <Typography variant="body2" textAlign="center">
                  Enter a natural language query to explore your qualitative data.
                  The system will generate Cypher queries and visualize results.
                </Typography>
              </Box>
            )}

            {/* Future: Cytoscape.js graph visualization will go here */}
            <Box sx={{ 
              mt: 3, 
              p: 2, 
              border: '2px dashed', 
              borderColor: 'grey.300',
              borderRadius: 1,
              textAlign: 'center',
              color: 'text.secondary'
            }}>
              <Typography variant="body2">
                📊 Graph visualization (Cytoscape.js) will be integrated here
              </Typography>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
};

export default ProjectWorkspace;