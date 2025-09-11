// TypeScript types for Qualitative Coding Analysis System

export interface Person {
  id: string;
  name: string;
  seniority?: string;
  division?: string;
  interview_count?: number;
}

export interface Organization {
  id: string;
  name: string;
  size?: string;
  sector?: string;
  employee_count?: number;
}

export interface Code {
  id: string;
  name: string;
  definition?: string;
  confidence?: number;
  frequency?: number;
  category?: string;
}

export interface Concept {
  id: string;
  name: string;
  description?: string;
  importance?: number;
}

export interface Location {
  id: string;
  name: string;
  type?: string;
}

export interface QueryResult {
  id: string;
  name: string;
  label: string;
  properties: Record<string, any>;
}

export interface QueryResponse {
  success: boolean;
  cypher?: string;
  data: QueryResult[];
  error?: string;
}

export interface NaturalLanguageQueryRequest {
  query: string;
  context?: Record<string, any>;
}

// UI-specific types
export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'processing' | 'complete';
  created_at: string;
  updated_at: string;
}

export interface Interview {
  id: string;
  participant: string;
  date: string;
  duration: number;
  status: 'pending' | 'coded' | 'reviewed';
}

export interface Quote {
  id: string;
  text: string;
  interview_id: string;
  codes: string[];
  timestamp?: string;
  page?: number;
}

// Graph visualization types
export interface GraphNode {
  id: string;
  label: string;
  type: 'Person' | 'Organization' | 'Code' | 'Concept' | 'Location';
  properties: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}