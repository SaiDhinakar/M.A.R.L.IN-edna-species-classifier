// Mock data for sequences
export const mockSequences = [
  {
    id: "SEQ_001",
    cluster: "CL_01",
    length: 150,
    quality: 98,
    taxa: "Proteobacteria",
    sequence: "ATGCGTACGTAGCTAGCTAGCTAGCTAG...",
    novelty_score: 0.2,
    sample_date: "2024-03-15",
    location: "Pacific Ocean Site A"
  },
  {
    id: "SEQ_002",
    cluster: "CL_02",
    length: 140,
    quality: 95,
    taxa: "Novel",
    sequence: "GCTAGCATGCGTACGTAGCTAGCTAG...",
    novelty_score: 0.8,
    sample_date: "2024-03-15",
    location: "Pacific Ocean Site A"
  },
  {
    id: "SEQ_003",
    cluster: "CL_01",
    length: 155,
    quality: 96,
    taxa: "Proteobacteria",
    sequence: "CGTACGTAGCTAGCTATGCGTACGTAG...",
    novelty_score: 0.1,
    sample_date: "2024-03-16",
    location: "Pacific Ocean Site B"
  },
  {
    id: "SEQ_004",
    cluster: "CL_03",
    length: 142,
    quality: 89,
    taxa: "Bacteroidetes",
    sequence: "TAGCTAGCTAGCATGCGTACGTAGCT...",
    novelty_score: 0.3,
    sample_date: "2024-03-16",
    location: "Pacific Ocean Site B"
  },
  {
    id: "SEQ_005",
    cluster: "CL_04",
    length: 148,
    quality: 92,
    taxa: "Novel",
    sequence: "ATGCGTACGTAGCTAGCTAGCTAGCT...",
    novelty_score: 0.9,
    sample_date: "2024-03-17",
    location: "Atlantic Ocean Site C"
  },
  {
    id: "SEQ_006",
    cluster: "CL_05",
    length: 138,
    quality: 87,
    taxa: "Firmicutes",
    sequence: "GCTAGCTAGCATGCGTACGTAGCTAG...",
    novelty_score: 0.2,
    sample_date: "2024-03-17",
    location: "Atlantic Ocean Site C"
  },
  {
    id: "SEQ_007",
    cluster: "CL_02",
    length: 145,
    quality: 94,
    taxa: "Novel",
    sequence: "CGTACGTAGCTAGCTAGCATGCGTAC...",
    novelty_score: 0.7,
    sample_date: "2024-03-18",
    location: "Mediterranean Sea Site D"
  },
  {
    id: "SEQ_008",
    cluster: "CL_06",
    length: 152,
    quality: 91,
    taxa: "Actinobacteria",
    sequence: "TAGCTAGCATGCGTACGTAGCTAGCT...",
    novelty_score: 0.4,
    sample_date: "2024-03-18",
    location: "Mediterranean Sea Site D"
  },
  {
    id: "SEQ_009",
    cluster: "CL_07",
    length: 144,
    quality: 88,
    taxa: "Novel",
    sequence: "ATGCGTACGTAGCTAGCTAGCTAGCT...",
    novelty_score: 0.85,
    sample_date: "2024-03-19",
    location: "Arctic Ocean Site E"
  },
  {
    id: "SEQ_010",
    cluster: "CL_08",
    length: 147,
    quality: 93,
    taxa: "Cyanobacteria",
    sequence: "GCTAGCTAGCATGCGTACGTAGCTAG...",
    novelty_score: 0.1,
    sample_date: "2024-03-19",
    location: "Arctic Ocean Site E"
  }
];

// Mock data for clusters
export const mockClusters = [
  {
    id: "CL_01",
    sequence_count: 120,
    consensus_sequence: "ATGCGTACGTAGCTAGCTAGCTAGCTAGCGATCGATCGATC...",
    novelty_score: 0.2,
    dominant_taxa: "Proteobacteria",
    avg_quality: 97,
    sequences: ["SEQ_001", "SEQ_003"],
    locations: ["Pacific Ocean Site A", "Pacific Ocean Site B"]
  },
  {
    id: "CL_02",
    sequence_count: 85,
    consensus_sequence: "GCTAGCATGCGTACGTAGCTAGCTAGGATCGATCGATCGAT...",
    novelty_score: 0.8,
    dominant_taxa: "Novel",
    avg_quality: 94,
    sequences: ["SEQ_002", "SEQ_007"],
    locations: ["Pacific Ocean Site A", "Mediterranean Sea Site D"]
  },
  {
    id: "CL_03",
    sequence_count: 67,
    consensus_sequence: "TAGCTAGCTAGCATGCGTACGTAGCTGATCGATCGATCGAT...",
    novelty_score: 0.3,
    dominant_taxa: "Bacteroidetes",
    avg_quality: 89,
    sequences: ["SEQ_004"],
    locations: ["Pacific Ocean Site B"]
  },
  {
    id: "CL_04",
    sequence_count: 42,
    consensus_sequence: "ATGCGTACGTAGCTAGCTAGCTAGCTGATCGATCGATCGAT...",
    novelty_score: 0.9,
    dominant_taxa: "Novel",
    avg_quality: 92,
    sequences: ["SEQ_005"],
    locations: ["Atlantic Ocean Site C"]
  },
  {
    id: "CL_05",
    sequence_count: 38,
    consensus_sequence: "GCTAGCTAGCATGCGTACGTAGCTAGGATCGATCGATCGAT...",
    novelty_score: 0.2,
    dominant_taxa: "Firmicutes",
    avg_quality: 87,
    sequences: ["SEQ_006"],
    locations: ["Atlantic Ocean Site C"]
  }
];

// Mock data for metrics
export const mockMetrics = {
  shannon_index: 3.5,
  richness: 120,
  evenness: 0.78,
  known_taxa_percent: 65,
  novel_taxa_percent: 35,
  total_sequences: 1247,
  total_clusters: 156,
  novel_taxa_count: 42,
  quality_score_avg: 91.2
};

// Mock data for taxonomic distribution
export const mockTaxonomicDistribution = [
  { name: "Proteobacteria", value: 35, count: 436 },
  { name: "Bacteroidetes", value: 22, count: 274 },
  { name: "Firmicutes", value: 18, count: 224 },
  { name: "Actinobacteria", value: 12, count: 150 },
  { name: "Cyanobacteria", value: 8, count: 100 },
  { name: "Novel Taxa", value: 5, count: 63 }
];

// Mock data for diversity over time
export const mockDiversityOverTime = [
  { date: "2024-03-15", shannon: 3.2, richness: 95, samples: 45 },
  { date: "2024-03-16", shannon: 3.4, richness: 108, samples: 52 },
  { date: "2024-03-17", shannon: 3.6, richness: 115, samples: 48 },
  { date: "2024-03-18", shannon: 3.5, richness: 120, samples: 56 },
  { date: "2024-03-19", shannon: 3.7, richness: 125, samples: 49 }
];

// Mock data for cluster size distribution
export const mockClusterSizes = [
  { cluster: "CL_01", size: 120, novelty: 0.2 },
  { cluster: "CL_02", size: 85, novelty: 0.8 },
  { cluster: "CL_03", size: 67, novelty: 0.3 },
  { cluster: "CL_04", size: 42, novelty: 0.9 },
  { cluster: "CL_05", size: 38, novelty: 0.2 },
  { cluster: "CL_06", size: 35, novelty: 0.4 },
  { cluster: "CL_07", size: 28, novelty: 0.85 },
  { cluster: "CL_08", size: 24, novelty: 0.1 },
  { cluster: "CL_09", size: 19, novelty: 0.6 },
  { cluster: "CL_10", size: 15, novelty: 0.3 }
];