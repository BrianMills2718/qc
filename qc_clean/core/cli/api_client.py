"""
API Client for CLI - HTTP client for communicating with QC API server
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Custom exception for API client errors"""
    pass


class APIClient:
    """HTTP client for QC API server communication"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8002", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.debug(f"Initialized API client for {self.base_url}")
    
    def health_check(self) -> bool:
        """Check if the API server is running and responsive"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Check response content if available
            try:
                data = response.json()
                return data.get('status') == 'healthy'
            except (ValueError, KeyError):
                # If no JSON or status field, assume healthy if 200 status
                return True
                
        except requests.exceptions.ConnectionError:
            logger.debug("Connection refused - server not running")
            return False
        except requests.exceptions.Timeout:
            logger.debug("Health check timeout")
            return False
        except requests.exceptions.RequestException as e:
            logger.debug(f"Health check failed: {e}")
            return False
    
    def start_analysis(self, files: List[str], config: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit files for analysis and return job ID
        
        Args:
            files: List of file paths to analyze
            config: Optional analysis configuration
            
        Returns:
            Job ID string for monitoring progress
            
        Raises:
            APIClientError: If analysis submission fails
        """
        if not files:
            raise APIClientError("No files provided for analysis")
        
        # Validate files exist and are readable
        validated_files = []
        for file_path in files:
            path = Path(file_path)
            if not path.exists():
                raise APIClientError(f"File does not exist: {file_path}")
            if not path.is_file():
                raise APIClientError(f"Path is not a file: {file_path}")
            if not path.stat().st_size > 0:
                raise APIClientError(f"File is empty: {file_path}")
            
            # Read file content based on file type
            try:
                file_ext = path.suffix.lower()
                
                if file_ext == '.txt':
                    # Plain text files
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                elif file_ext in ['.docx', '.doc']:
                    # Word documents - try to extract text
                    try:
                        import docx
                        doc = docx.Document(path)
                        content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                    except ImportError:
                        raise APIClientError(f"python-docx package required for .docx files. Install with: pip install python-docx")
                elif file_ext == '.pdf':
                    # PDF files - try to extract text
                    try:
                        import PyPDF2
                        with open(path, 'rb') as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            content = '\n'.join([page.extract_text() for page in pdf_reader.pages])
                    except ImportError:
                        raise APIClientError(f"PyPDF2 package required for .pdf files. Install with: pip install PyPDF2")
                elif file_ext == '.rtf':
                    # RTF files - basic text extraction
                    try:
                        from striprtf.striprtf import rtf_to_text
                        with open(path, 'r', encoding='utf-8') as f:
                            rtf_content = f.read()
                        content = rtf_to_text(rtf_content)
                    except ImportError:
                        raise APIClientError(f"striprtf package required for .rtf files. Install with: pip install striprtf")
                else:
                    # Try as plain text with fallback encoding
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(path, 'r', encoding='latin-1') as f:
                            content = f.read()
                
                if not content.strip():
                    raise APIClientError(f"No readable content found in file: {file_path}")
                
                validated_files.append({
                    'name': path.name,
                    'path': str(path),
                    'content': content
                })
                
            except APIClientError:
                # Re-raise our custom errors
                raise
            except Exception as e:
                raise APIClientError(f"Error reading file {file_path}: {e}")
        
        # Prepare request payload (API expects 'interviews' not 'files')
        payload = {
            'interviews': validated_files,
            'config': config or {}
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            job_id = result.get('job_id')
            if not job_id:
                raise APIClientError("Server did not return job_id")
                
            logger.info(f"Analysis submitted successfully, Job ID: {job_id}")
            return job_id
            
        except requests.exceptions.ConnectionError:
            raise APIClientError(
                "Cannot connect to server. "
                "Please start the server with: python start_server.py"
            )
        except requests.exceptions.Timeout:
            raise APIClientError("Analysis request timed out")
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('detail', str(e))
            except (ValueError, AttributeError):
                error_msg = str(e)
            raise APIClientError(f"Analysis request failed: {error_msg}")
        except Exception as e:
            raise APIClientError(f"Unexpected error during analysis: {e}")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status and results of analysis job
        
        Args:
            job_id: Job ID returned from start_analysis
            
        Returns:
            Dictionary with job status and results
            
        Raises:
            APIClientError: If status check fails
        """
        if not job_id:
            raise APIClientError("No job ID provided")
        
        try:
            response = self.session.get(
                f"{self.base_url}/jobs/{job_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise APIClientError(
                "Cannot connect to server. "
                "Please ensure the server is running."
            )
        except requests.exceptions.Timeout:
            raise APIClientError("Job status request timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise APIClientError(f"Job not found: {job_id}")
            try:
                error_data = e.response.json()
                error_msg = error_data.get('detail', str(e))
            except (ValueError, AttributeError):
                error_msg = str(e)
            raise APIClientError(f"Job status request failed: {error_msg}")
        except Exception as e:
            raise APIClientError(f"Unexpected error checking job status: {e}")
    
    def wait_for_job_completion(self, job_id: str, max_wait_time: int = 300, poll_interval: int = 2) -> Dict[str, Any]:
        """
        Poll job status until completion or timeout
        
        Args:
            job_id: Job ID to monitor
            max_wait_time: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            Final job status and results
            
        Raises:
            APIClientError: If job fails or times out
        """
        start_time = time.time()
        
        while True:
            status_data = self.get_job_status(job_id)
            status = status_data.get('status', 'unknown')
            
            if status in ['completed', 'success']:
                return status_data
            elif status in ['failed', 'error']:
                error_msg = status_data.get('error', 'Job failed without error message')
                raise APIClientError(f"Job failed: {error_msg}")
            elif time.time() - start_time > max_wait_time:
                raise APIClientError(f"Job timed out after {max_wait_time} seconds")
            
            # Continue polling
            time.sleep(poll_interval)
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities"""
        try:
            response = self.session.get(
                f"{self.base_url}/info",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            # Fallback - return basic info from health check
            if self.health_check():
                return {
                    'status': 'running',
                    'base_url': self.base_url,
                    'available_endpoints': [
                        '/health', '/analyze', '/jobs/{id}'
                    ]
                }
            else:
                return {'status': 'not_running'}