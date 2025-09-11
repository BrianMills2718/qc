// API service layer for FastAPI backend integration

import axios from 'axios';
import { QueryResponse, NaturalLanguageQueryRequest } from '../types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8002',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API service functions
export const apiService = {
  // Health check
  async checkHealth(): Promise<any> {
    const response = await api.get('/health');
    return response.data;
  },

  // Query system health
  async checkQueryHealth(): Promise<any> {
    const response = await api.get('/api/query/health');
    return response.data;
  },

  // Natural language query processing
  async processNaturalLanguageQuery(request: NaturalLanguageQueryRequest): Promise<QueryResponse> {
    const response = await api.post('/api/query/natural-language', request);
    return response.data;
  },

  // Convenience methods for common queries
  async queryAllPeople(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ query: 'Show me all people' });
  },

  async queryAllOrganizations(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ query: 'Show me all organizations' });
  },

  async queryAllCodes(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ query: 'Show me all codes' });
  },

  async queryAllConcepts(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ query: 'Show me all concepts' });
  },

  async queryAllLocations(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ query: 'Show me all locations' });
  },

  // Advanced queries
  async querySeniorPeople(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ 
      query: 'Show me all senior people' 
    });
  },

  async queryPeopleInOrganizations(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ 
      query: 'Show me people who work at organizations' 
    });
  },

  async queryRelatedConcepts(): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ 
      query: 'Show me concepts and their relationships' 
    });
  },

  // Custom query method for user input
  async customQuery(query: string, context?: Record<string, any>): Promise<QueryResponse> {
    return this.processNaturalLanguageQuery({ 
      query, 
      context: context || {} 
    });
  }
};

export default apiService;