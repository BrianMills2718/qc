// React Query hooks for API data fetching

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { QueryResponse, NaturalLanguageQueryRequest } from '../types';

// Query keys for caching
export const QUERY_KEYS = {
  HEALTH: 'health',
  QUERY_HEALTH: 'query-health',
  ALL_PEOPLE: 'all-people',
  ALL_ORGANIZATIONS: 'all-organizations',
  ALL_CODES: 'all-codes',
  ALL_CONCEPTS: 'all-concepts',
  ALL_LOCATIONS: 'all-locations',
  CUSTOM_QUERY: 'custom-query',
} as const;

// Health check hooks
export const useHealth = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.HEALTH],
    queryFn: () => apiService.checkHealth(),
    staleTime: 60000, // 1 minute
    retry: 3,
  });
};

export const useQueryHealth = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.QUERY_HEALTH],
    queryFn: () => apiService.checkQueryHealth(),
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
};

// Data fetching hooks
export const useAllPeople = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.ALL_PEOPLE],
    queryFn: () => apiService.queryAllPeople(),
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

export const useAllOrganizations = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.ALL_ORGANIZATIONS],
    queryFn: () => apiService.queryAllOrganizations(),
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

export const useAllCodes = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.ALL_CODES],
    queryFn: () => apiService.queryAllCodes(),
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

export const useAllConcepts = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.ALL_CONCEPTS],
    queryFn: () => apiService.queryAllConcepts(),
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

export const useAllLocations = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.ALL_LOCATIONS],
    queryFn: () => apiService.queryAllLocations(),
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
};

// Custom query hook with mutation for user-driven queries
export const useCustomQuery = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ query, context }: { query: string; context?: Record<string, any> }) => 
      apiService.customQuery(query, context),
    onSuccess: (data, variables) => {
      // Cache successful queries
      queryClient.setQueryData(
        [QUERY_KEYS.CUSTOM_QUERY, variables.query], 
        data
      );
    },
    onError: (error) => {
      console.error('Custom query failed:', error);
    },
  });
};

// Hook for getting cached custom query results
export const useCachedCustomQuery = (query: string) => {
  return useQuery({
    queryKey: [QUERY_KEYS.CUSTOM_QUERY, query],
    queryFn: () => apiService.customQuery(query),
    enabled: false, // Don't fetch automatically, only when triggered
    staleTime: 600000, // 10 minutes
    retry: 1,
  });
};

// Convenience hook for natural language queries
export const useNaturalLanguageQuery = () => {
  const mutation = useCustomQuery();
  
  const executeQuery = (query: string, context?: Record<string, any>) => {
    return mutation.mutate({ query, context });
  };

  return {
    executeQuery,
    data: mutation.data,
    isLoading: mutation.isPending,
    error: mutation.error,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    reset: mutation.reset,
  };
};

// Hook for all base data (useful for dashboard)
export const useAllBaseData = () => {
  const people = useAllPeople();
  const organizations = useAllOrganizations();
  const codes = useAllCodes();
  const concepts = useAllConcepts();
  const locations = useAllLocations();

  return {
    people,
    organizations,
    codes,
    concepts,
    locations,
    isLoading: people.isLoading || organizations.isLoading || codes.isLoading || 
               concepts.isLoading || locations.isLoading,
    hasData: people.data || organizations.data || codes.data || 
             concepts.data || locations.data,
    errors: [people.error, organizations.error, codes.error, concepts.error, locations.error]
      .filter(Boolean),
  };
};