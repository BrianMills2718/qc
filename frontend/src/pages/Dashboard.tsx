// Dashboard Page - Entry point for researchers (01_dashboard.html)

import React, { useState } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Analytics as AnalyticsIcon,
  Folder as FolderIcon,
  Schedule as ScheduleIcon,
  Upload as UploadIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAllBaseData } from '../hooks/useQueries';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { people, organizations, codes, concepts, locations, isLoading, hasData } = useAllBaseData();

  // Projects would come from API in real implementation
  const projects: any[] = [];

  // Project creation state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<FileList | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [showResults, setShowResults] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'success';
      case 'processing': return 'warning';
      case 'draft': return 'default';
      default: return 'default';
    }
  };

  const handleCreateProject = () => {
    setCreateDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setCreateDialogOpen(false);
    setProjectName('');
    setProjectDescription('');
    setUploadedFiles(null);
    setUploadError(null);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    setUploadedFiles(files);
    setUploadError(null);
  };

  const waitForJobCompletion = async (jobId: string) => {
    const maxAttempts = 60; // 5 minutes maximum
    let attempt = 0;
    
    while (attempt < maxAttempts) {
      try {
        console.log(`Polling job status (attempt ${attempt + 1}/${maxAttempts}) for job: ${jobId}`);
        const statusResponse = await fetch(`http://127.0.0.1:8002/jobs/${jobId}`);
        console.log('Status response:', statusResponse.status, statusResponse.statusText);
        
        if (!statusResponse.ok) {
          const errorBody = await statusResponse.text();
          console.error('Status check failed:', statusResponse.status, errorBody);
          throw new Error(`Status check failed: ${statusResponse.status} ${statusResponse.statusText} - ${errorBody}`);
        }
        
        const statusData = await statusResponse.json();
        console.log('Status data:', statusData);
        
        if (statusData.status === 'completed') {
          // Get detailed results
          console.log('Job completed, fetching results...');
          const resultsResponse = await fetch(`http://127.0.0.1:8002/results/${jobId}`);
          
          if (!resultsResponse.ok) {
            const errorBody = await resultsResponse.text();
            console.error('Results fetch failed:', resultsResponse.status, errorBody);
            throw new Error(`Results fetch failed: ${resultsResponse.status} ${resultsResponse.statusText} - ${errorBody}`);
          }
          
          const resultsData = await resultsResponse.json();
          console.log('Results data:', resultsData);
          
          setAnalysisResults(resultsData);
          setShowResults(true);
          handleCloseDialog();
          return;
        } else if (statusData.status === 'failed') {
          throw new Error(statusData.error || 'Analysis failed');
        }
        
        // Update progress message
        if (statusData.status === 'processing') {
          setUploadError(null);
        }
        
        // Wait 5 seconds before next poll
        await new Promise(resolve => setTimeout(resolve, 5000));
        attempt++;
        
      } catch (error) {
        console.error('Error checking job status:', error);
        throw error;
      }
    }
    
    throw new Error('Analysis timed out after 5 minutes');
  };

  const handleSubmitProject = async () => {
    if (!projectName.trim()) {
      setUploadError('Project name is required');
      return;
    }

    if (!uploadedFiles || uploadedFiles.length === 0) {
      setUploadError('Please select interview files to upload');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      // Process uploaded files into interview data
      const interviews: any[] = [];
      
      for (let i = 0; i < uploadedFiles.length; i++) {
        const file = uploadedFiles[i];
        const text = await file.text();
        
        interviews.push({
          id: `interview_${i + 1}`,
          filename: file.name,
          content: text,
          participant: `Participant ${i + 1}`,
          date: new Date().toISOString()
        });
      }

      // Submit to analysis endpoint
      console.log('Submitting analysis request...');
      const response = await fetch('http://127.0.0.1:8002/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          interviews,
          config: {
            project_name: projectName,
            description: projectDescription
          }
        }),
      });

      console.log('Response status:', response.status, response.statusText);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorBody = await response.text();
        console.error('Response error body:', errorBody);
        throw new Error(`Analysis failed: ${response.status} ${response.statusText} - ${errorBody}`);
      }

      const result = await response.json();
      console.log('Analysis response:', result);
      
      if (result.job_id) {
        // Poll for job completion
        await waitForJobCompletion(result.job_id);
      } else {
        // Close dialog and navigate to workspace
        handleCloseDialog();
        navigate('/workspace/main-project');
      }
      
    } catch (error) {
      console.error('Upload error:', error);
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleOpenProject = (projectId: string) => {
    navigate(`/workspace/${projectId}`);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Typography variant="h4" component="h1" gutterBottom>
            Qualitative Coding Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Manage your research projects and analysis workflows
          </Typography>
        </div>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateProject}
          size="large"
        >
          Create New Project
        </Button>
      </Box>

      {/* Data Overview */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ minWidth: 160, flex: '1 1 160px' }}>
          <CardContent>
            <Typography color="text.secondary" gutterBottom variant="body2">
              People
            </Typography>
            <Typography variant="h4">
              {people.data?.data?.length || 0}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ minWidth: 160, flex: '1 1 160px' }}>
          <CardContent>
            <Typography color="text.secondary" gutterBottom variant="body2">
              Organizations
            </Typography>
            <Typography variant="h4">
              {organizations.data?.data?.length || 0}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ minWidth: 160, flex: '1 1 160px' }}>
          <CardContent>
            <Typography color="text.secondary" gutterBottom variant="body2">
              Codes
            </Typography>
            <Typography variant="h4">
              {codes.data?.data?.length || 0}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ minWidth: 160, flex: '1 1 160px' }}>
          <CardContent>
            <Typography color="text.secondary" gutterBottom variant="body2">
              Concepts
            </Typography>
            <Typography variant="h4">
              {concepts.data?.data?.length || 0}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ minWidth: 160, flex: '1 1 160px' }}>
          <CardContent>
            <Typography color="text.secondary" gutterBottom variant="body2">
              Locations
            </Typography>
            <Typography variant="h4">
              {locations.data?.data?.length || 0}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Projects Section */}
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Research Projects
      </Typography>
      
      {projects.length === 0 ? (
        <Box sx={{ 
          textAlign: 'center', 
          py: 6,
          border: '2px dashed',
          borderColor: 'grey.300',
          borderRadius: 2,
          backgroundColor: 'grey.50'
        }}>
          <FolderIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Projects Yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first research project to start analyzing qualitative data
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateProject}
          >
            Create First Project
          </Button>
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
          {projects.map((project) => (
            <Card 
              key={project.id}
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 6,
                },
              }}
              onClick={() => handleOpenProject(project.id)}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <FolderIcon color="primary" />
                  <Chip 
                    label={project.status} 
                    color={getStatusColor(project.status)} 
                    size="small"
                  />
                </Box>
                
                <Typography variant="h6" component="h2" gutterBottom>
                  {project.name}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {project.description}
                </Typography>

                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Interviews: {project.stats.interviews}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Codes: {project.stats.codes}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Quotes: {project.stats.quotes}
                  </Typography>
                </Box>

                <Typography variant="caption" color="text.secondary">
                  Updated: {new Date(project.updated_at).toLocaleDateString()}
                </Typography>
              </CardContent>
              
              <CardActions>
                <Button size="small" startIcon={<AnalyticsIcon />}>
                  Open Analysis
                </Button>
                <Button size="small" startIcon={<ScheduleIcon />}>
                  View Progress
                </Button>
              </CardActions>
            </Card>
          ))}
        </Box>
      )}

      {/* Quick Actions */}
      <Box sx={{ mt: 6, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Button variant="outlined" onClick={() => navigate('/workspace')}>
            Open Workspace
          </Button>
          <Button variant="outlined" onClick={() => navigate('/codes')}>
            Browse Codes
          </Button>
          <Button variant="outlined" onClick={() => navigate('/quotes')}>
            Explore Quotes
          </Button>
          <Button variant="outlined" onClick={() => navigate('/reports')}>
            Generate Report
          </Button>
        </Box>
      </Box>

      {/* Analysis Results Dialog */}
      <Dialog 
        open={showResults && analysisResults !== null} 
        onClose={() => setShowResults(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Qualitative Coding Analysis Results</DialogTitle>
        <DialogContent>
          {analysisResults && analysisResults.results && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
              {/* Summary */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Analysis Summary</Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Interviews Processed</Typography>
                      <Typography variant="h4">{analysisResults.results.summary?.interviews_processed || 0}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Codes Extracted</Typography>
                      <Typography variant="h4">{analysisResults.results.summary?.total_codes_extracted || 0}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Unique Codes</Typography>
                      <Typography variant="h4">{analysisResults.results.summary?.unique_codes || 0}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Quotes Extracted</Typography>
                      <Typography variant="h4">{analysisResults.results.summary?.total_quotes_extracted || 0}</Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>

              {/* Codes */}
              {analysisResults.results.codes && analysisResults.results.codes.length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Extracted Codes</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {analysisResults.results.codes.map((code: string, index: number) => (
                        <Chip key={index} label={code} color="primary" variant="outlined" />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              )}

              {/* Sample Quotes */}
              {analysisResults.results.sample_quotes && analysisResults.results.sample_quotes.length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Sample Quotes</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {analysisResults.results.sample_quotes.slice(0, 5).map((quote: string, index: number) => (
                        <Box key={index} sx={{ p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                          <Typography variant="body2">"{quote}"</Typography>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              )}

              {/* Analysis Metadata */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Analysis Details</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed at: {new Date(analysisResults.completed_at).toLocaleString()}
                  </Typography>
                  {analysisResults.results.analysis_metadata && (
                    <Typography variant="body2" color="text.secondary">
                      Extractor: {analysisResults.results.analysis_metadata.extractor} v{analysisResults.results.analysis_metadata.version}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowResults(false)}>Close</Button>
          <Button 
            variant="contained" 
            onClick={() => {
              setShowResults(false);
              navigate('/workspace/main-project');
            }}
          >
            Continue to Workspace
          </Button>
        </DialogActions>
      </Dialog>

      {/* Project Creation Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Research Project</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            <TextField
              label="Project Name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              fullWidth
              required
              error={!projectName.trim() && uploadError !== null}
              helperText={!projectName.trim() && uploadError !== null ? "Project name is required" : ""}
            />
            
            <TextField
              label="Project Description"
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              fullWidth
              multiline
              rows={3}
              placeholder="Describe your research goals and methodology..."
            />
            
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Upload Interview Files
              </Typography>
              <Box sx={{ 
                border: '2px dashed #ccc', 
                borderRadius: 1, 
                p: 3, 
                textAlign: 'center',
                '&:hover': { borderColor: 'primary.main' }
              }}>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  accept=".txt,.doc,.docx,.rtf,.pdf"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
                <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                  <CloudUploadIcon sx={{ fontSize: 48, color: 'action.active' }} />
                  <Typography variant="body1">
                    Click to select interview files
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Supports: .txt, .doc, .docx, .rtf, .pdf
                  </Typography>
                </label>
              </Box>
              
              {uploadedFiles && uploadedFiles.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Selected files ({uploadedFiles.length}):
                  </Typography>
                  {Array.from(uploadedFiles).map((file, index) => (
                    <Typography key={index} variant="body2" sx={{ ml: 2 }}>
                      • {file.name} ({(file.size / 1024).toFixed(1)} KB)
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>

            {uploadError && (
              <Alert severity="error">
                {uploadError}
              </Alert>
            )}

            {isUploading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <LinearProgress sx={{ flex: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Processing interviews and running analysis...
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={isUploading}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleSubmitProject}
            disabled={!projectName.trim() || !uploadedFiles || uploadedFiles.length === 0 || isUploading}
            startIcon={isUploading ? <CircularProgress size={20} /> : <UploadIcon />}
          >
            {isUploading ? 'Processing...' : 'Create Project & Analyze'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Dashboard;