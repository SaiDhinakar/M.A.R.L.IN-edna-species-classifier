import requests
import json
from typing import List, Dict, Any, Optional
import logging
from app.core.config import get_settings
from app.core.utils import get_minio_client

logger = logging.getLogger(__name__)
settings = get_settings()


class TaxonomyAssigner:
    """Handles taxonomic assignment for DNA sequences"""
    
    def __init__(self):
        self.minio_client = get_minio_client()
        self.reference_db = None
        self.taxonomy_cache = {}
        
        # NCBI API settings
        self.ncbi_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.blast_url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
        
        # Load reference taxonomy database
        self._load_reference_db()
    
    def _load_reference_db(self):
        """Load reference taxonomy database"""
        try:
            # Try to load from MinIO first
            ref_db = self.minio_client.download_json(
                settings.minio_bucket_models, 
                "taxonomy/reference_db.json"
            )
            
            if ref_db:
                self.reference_db = ref_db
                logger.info("Loaded reference taxonomy database from MinIO")
            else:
                # Initialize with basic taxonomy structure
                self.reference_db = self._get_default_taxonomy_db()
                logger.info("Using default taxonomy database")
                
        except Exception as e:
            logger.error(f"Error loading reference database: {e}")
            self.reference_db = self._get_default_taxonomy_db()
    
    def _get_default_taxonomy_db(self) -> Dict[str, Any]:
        """Get default taxonomy database structure"""
        return {
            "marine_fish": {
                "sequences": [],
                "taxonomy": {
                    "kingdom": "Animalia",
                    "phylum": "Chordata",
                    "class": "Actinopterygii",
                    "order": "Various",
                    "family": "Various",
                    "genus": "Various",
                    "species": "Various"
                }
            },
            "marine_invertebrates": {
                "sequences": [],
                "taxonomy": {
                    "kingdom": "Animalia",
                    "phylum": "Various",
                    "class": "Various",
                    "order": "Various",
                    "family": "Various", 
                    "genus": "Various",
                    "species": "Various"
                }
            },
            "marine_plants": {
                "sequences": [],
                "taxonomy": {
                    "kingdom": "Plantae",
                    "phylum": "Various",
                    "class": "Various",
                    "order": "Various",
                    "family": "Various",
                    "genus": "Various", 
                    "species": "Various"
                }
            }
        }
    
    def assign_taxonomy_local(self, sequence: str, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """Assign taxonomy using local reference database"""
        try:
            best_match = {
                "taxonomy": self._get_unknown_taxonomy(),
                "confidence": 0.0,
                "method": "local_reference",
                "match_details": None
            }
            
            if not self.reference_db:
                return best_match
            
            # Simple sequence similarity check (placeholder)
            # In production, use proper sequence alignment algorithms
            for category, data in self.reference_db.items():
                ref_sequences = data.get("sequences", [])
                
                for ref_seq in ref_sequences:
                    # Calculate simple similarity (replace with proper alignment)
                    similarity = self._calculate_similarity(sequence, ref_seq.get("sequence", ""))
                    
                    if similarity > best_match["confidence"] and similarity >= similarity_threshold:
                        best_match = {
                            "taxonomy": data.get("taxonomy", self._get_unknown_taxonomy()),
                            "confidence": similarity,
                            "method": "local_reference",
                            "match_details": {
                                "reference_id": ref_seq.get("id"),
                                "category": category,
                                "similarity_score": similarity
                            }
                        }
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error in local taxonomy assignment: {e}")
            return {
                "taxonomy": self._get_unknown_taxonomy(),
                "confidence": 0.0,
                "method": "local_reference",
                "error": str(e)
            }
    
    def assign_taxonomy_ncbi(self, sequence: str) -> Dict[str, Any]:
        """Assign taxonomy using NCBI BLAST"""
        try:
            # Submit BLAST search
            blast_result = self._submit_blast_search(sequence)
            
            if not blast_result:
                return {
                    "taxonomy": self._get_unknown_taxonomy(),
                    "confidence": 0.0,
                    "method": "ncbi_blast",
                    "error": "BLAST search failed"
                }
            
            # Parse BLAST results and get taxonomy
            taxonomy_result = self._parse_blast_results(blast_result)
            
            return taxonomy_result
            
        except Exception as e:
            logger.error(f"Error in NCBI taxonomy assignment: {e}")
            return {
                "taxonomy": self._get_unknown_taxonomy(),
                "confidence": 0.0,
                "method": "ncbi_blast",
                "error": str(e)
            }
    
    def _submit_blast_search(self, sequence: str) -> Optional[Dict[str, Any]]:
        """Submit BLAST search to NCBI (placeholder implementation)"""
        # This is a placeholder - implement actual NCBI BLAST API calls
        # For production, you would:
        # 1. Submit sequence to BLAST
        # 2. Poll for results
        # 3. Parse XML/JSON results
        
        logger.info("BLAST search submitted (placeholder)")
        return None
    
    def _parse_blast_results(self, blast_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse BLAST results and extract taxonomy"""
        # Placeholder implementation
        return {
            "taxonomy": self._get_unknown_taxonomy(),
            "confidence": 0.0,
            "method": "ncbi_blast",
            "match_details": blast_result
        }
    
    def _calculate_similarity(self, seq1: str, seq2: str) -> float:
        """Calculate simple sequence similarity (placeholder)"""
        if not seq1 or not seq2:
            return 0.0
        
        # Simple character-by-character comparison
        # In production, use proper sequence alignment algorithms
        min_len = min(len(seq1), len(seq2))
        matches = sum(1 for i in range(min_len) if seq1[i] == seq2[i])
        
        return matches / max(len(seq1), len(seq2))
    
    def _get_unknown_taxonomy(self) -> Dict[str, str]:
        """Get taxonomy structure for unknown sequences"""
        return {
            "kingdom": "Unknown",
            "phylum": "Unknown", 
            "class": "Unknown",
            "order": "Unknown",
            "family": "Unknown",
            "genus": "Unknown",
            "species": "Unknown"
        }
    
    def assign_taxonomy_batch(self, sequences: List[str], method: str = "local") -> List[Dict[str, Any]]:
        """Assign taxonomy to multiple sequences"""
        results = []
        
        for i, sequence in enumerate(sequences):
            try:
                if method == "local":
                    result = self.assign_taxonomy_local(sequence)
                elif method == "ncbi":
                    result = self.assign_taxonomy_ncbi(sequence)
                else:
                    # Try local first, fallback to NCBI if confidence is low
                    result = self.assign_taxonomy_local(sequence)
                    if result.get("confidence", 0) < 0.5:
                        ncbi_result = self.assign_taxonomy_ncbi(sequence)
                        if ncbi_result.get("confidence", 0) > result.get("confidence", 0):
                            result = ncbi_result
                
                result["sequence_index"] = i
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(sequences)} sequences for taxonomy")
                    
            except Exception as e:
                logger.error(f"Error processing sequence {i}: {e}")
                results.append({
                    "sequence_index": i,
                    "taxonomy": self._get_unknown_taxonomy(),
                    "confidence": 0.0,
                    "method": method,
                    "error": str(e)
                })
        
        return results
    
    def add_reference_sequence(self, sequence: str, taxonomy: Dict[str, str], 
                             category: str = "custom", sequence_id: str = None) -> bool:
        """Add a sequence to the reference database"""
        try:
            if category not in self.reference_db:
                self.reference_db[category] = {
                    "sequences": [],
                    "taxonomy": taxonomy
                }
            
            sequence_entry = {
                "id": sequence_id or f"seq_{len(self.reference_db[category]['sequences'])}",
                "sequence": sequence,
                "taxonomy": taxonomy
            }
            
            self.reference_db[category]["sequences"].append(sequence_entry)
            
            # Save updated database
            return self._save_reference_db()
            
        except Exception as e:
            logger.error(f"Error adding reference sequence: {e}")
            return False
    
    def _save_reference_db(self) -> bool:
        """Save reference database to MinIO"""
        try:
            return self.minio_client.upload_json(
                settings.minio_bucket_models,
                "taxonomy/reference_db.json",
                self.reference_db
            )
        except Exception as e:
            logger.error(f"Error saving reference database: {e}")
            return False
    
    def get_taxonomy_stats(self) -> Dict[str, Any]:
        """Get statistics about taxonomy assignments"""
        if not self.reference_db:
            return {"total_categories": 0, "total_sequences": 0}
        
        total_sequences = sum(
            len(data.get("sequences", [])) 
            for data in self.reference_db.values()
        )
        
        return {
            "total_categories": len(self.reference_db),
            "total_sequences": total_sequences,
            "categories": list(self.reference_db.keys())
        }


# Global instance
taxonomy_assigner = TaxonomyAssigner()


def get_taxonomy_assigner() -> TaxonomyAssigner:
    """Get the global taxonomy assigner instance"""
    return taxonomy_assigner