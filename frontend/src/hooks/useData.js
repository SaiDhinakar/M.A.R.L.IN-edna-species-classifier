import { useState, useEffect, useMemo } from 'react';
import { 
  mockSequences, 
  mockClusters, 
  mockMetrics, 
  mockTaxonomicDistribution,
  mockDiversityOverTime,
  mockClusterSizes 
} from '../data/mockData';

// Simulate API delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Hook for fetching sequences
export const useSequences = (filters = {}) => {
  const [sequences, setSequences] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Memoize filters to prevent unnecessary re-renders
  const memoizedFilters = useMemo(() => filters, [
    filters.search,
    filters.cluster,
    filters.taxa,
    filters.minQuality
  ]);

  useEffect(() => {
    const fetchSequences = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Simulate API call
        await delay(300);
        
        let filteredSequences = [...mockSequences];
        
        // Apply filters
        if (memoizedFilters.search) {
          const search = memoizedFilters.search.toLowerCase();
          filteredSequences = filteredSequences.filter(seq => 
            seq.id.toLowerCase().includes(search) ||
            seq.cluster.toLowerCase().includes(search) ||
            seq.taxa.toLowerCase().includes(search)
          );
        }
        
        if (memoizedFilters.cluster) {
          filteredSequences = filteredSequences.filter(seq => seq.cluster === memoizedFilters.cluster);
        }
        
        if (memoizedFilters.taxa) {
          filteredSequences = filteredSequences.filter(seq => seq.taxa === memoizedFilters.taxa);
        }
        
        if (memoizedFilters.minQuality) {
          filteredSequences = filteredSequences.filter(seq => seq.quality >= memoizedFilters.minQuality);
        }
        
        setSequences(filteredSequences);
      } catch (err) {
        setError('Failed to fetch sequences');
        console.error('Error fetching sequences:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSequences();
  }, [memoizedFilters]);

  return { sequences, loading, error };
};

// Hook for fetching a single sequence
export const useSequence = (id) => {
  const [sequence, setSequence] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) return;

    const fetchSequence = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await delay(300);
        const foundSequence = mockSequences.find(seq => seq.id === id);
        if (!foundSequence) {
          throw new Error('Sequence not found');
        }
        setSequence(foundSequence);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSequence();
  }, [id]);

  return { sequence, loading, error };
};

// Hook for fetching clusters
export const useClusters = (filters = {}) => {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Memoize filters to prevent unnecessary re-renders
  const memoizedFilters = useMemo(() => filters, [
    filters.search,
    filters.minSize,
    filters.minNovelty
  ]);

  useEffect(() => {
    const fetchClusters = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await delay(200);
        
        let filteredClusters = [...mockClusters];
        
        // Apply filters
        if (memoizedFilters.search) {
          const search = memoizedFilters.search.toLowerCase();
          filteredClusters = filteredClusters.filter(cluster => 
            cluster.id.toLowerCase().includes(search) ||
            cluster.dominant_taxa.toLowerCase().includes(search)
          );
        }
        
        if (memoizedFilters.minSize) {
          filteredClusters = filteredClusters.filter(cluster => cluster.sequence_count >= memoizedFilters.minSize);
        }
        
        if (memoizedFilters.minNovelty) {
          filteredClusters = filteredClusters.filter(cluster => cluster.novelty_score >= memoizedFilters.minNovelty);
        }
        
        console.log('Setting clusters:', filteredClusters);
        setClusters(filteredClusters);
      } catch (err) {
        setError('Failed to fetch clusters');
        console.error('Error fetching clusters:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchClusters();
  }, [memoizedFilters]);

  return { clusters, loading, error };
};

// Hook for fetching a single cluster
export const useCluster = (id) => {
  const [cluster, setCluster] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) return;

    const fetchCluster = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await delay(300);
        const foundCluster = mockClusters.find(cluster => cluster.id === id);
        if (!foundCluster) {
          throw new Error('Cluster not found');
        }
        setCluster(foundCluster);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCluster();
  }, [id]);

  return { cluster, loading, error };
};

// Hook for fetching metrics
export const useMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      setError(null);
      
      try {
        await delay(100);
        console.log('Setting metrics:', mockMetrics);
        setMetrics(mockMetrics);
      } catch (err) {
        setError('Failed to fetch metrics');
        console.error('Error fetching metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  return { metrics, loading, error };
};

// Hook for fetching taxonomic distribution
export const useTaxonomicDistribution = () => {
  const [distribution, setDistribution] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDistribution = async () => {
      setError(null);
      
      try {
        await delay(150);
        console.log('Setting taxonomic distribution:', mockTaxonomicDistribution);
        setDistribution(mockTaxonomicDistribution);
      } catch (err) {
        setError('Failed to fetch taxonomic distribution');
        console.error('Error fetching taxonomic distribution:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDistribution();
  }, []);

  return { distribution, loading, error };
};

// Hook for fetching diversity over time
export const useDiversityOverTime = () => {
  const [diversityData, setDiversityData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDiversityData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await delay(500);
        setDiversityData(mockDiversityOverTime);
      } catch (err) {
        setError('Failed to fetch diversity data');
      } finally {
        setLoading(false);
      }
    };

    fetchDiversityData();
  }, []);

  return { diversityData, loading, error };
};

// Hook for fetching cluster sizes
export const useClusterSizes = () => {
  const [clusterSizes, setClusterSizes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchClusterSizes = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await delay(400);
        setClusterSizes(mockClusterSizes);
      } catch (err) {
        setError('Failed to fetch cluster sizes');
      } finally {
        setLoading(false);
      }
    };

    fetchClusterSizes();
  }, []);

  return { clusterSizes, loading, error };
};