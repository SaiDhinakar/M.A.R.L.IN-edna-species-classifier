"""
Utilities for parsing species names from FASTA headers.
"""
import re
from typing import Dict, Optional


def parse_species_from_header(header: str) -> Optional[str]:
    """
    Parse species name from FASTA header.
    
    Format examples:
    - ">NR_118889.1 Amycolatopsis azurea strain NRRL 11412 16S ribosomal RNA, partial sequence"
    - ">NR_074334.1 Archaeoglobus fulgidus DSM 4304 16S ribosomal RNA, complete sequence"
    
    Returns genus + species (first two words after accession).
    """
    # Remove '>' if present
    header = header.lstrip('>')
    
    # Split by whitespace
    parts = header.split()
    
    if len(parts) < 3:
        return None
    
    # First part is accession (e.g., "NR_118889.1")
    # Next parts are species name (genus + species)
    genus = parts[1] if len(parts) > 1 else ""
    species = parts[2] if len(parts) > 2 else ""
    
    # Combine genus and species
    if genus and species:
        # Handle cases where species might be "DSM" or "strain" (skip these)
        if species.lower() in ["dsm", "strain", "atcc", "nrrl", "type"]:
            return genus  # Return just genus if species is a strain identifier
        return f"{genus} {species}"
    
    return genus if genus else None


def extract_accession_from_header(header: str) -> str:
    """
    Extract accession number from FASTA header.
    
    Example: ">NR_118889.1 Amycolatopsis azurea..." -> "NR_118889.1"
    """
    header = header.lstrip('>')
    parts = header.split()
    return parts[0] if parts else ""


def build_species_mapping_from_fasta(fasta_path: str) -> Dict[str, str]:
    """
    Build a mapping of accession -> species name from a FASTA file.
    
    Args:
        fasta_path: Path to FASTA file
        
    Returns:
        Dictionary mapping accession numbers to species names
    """
    mapping = {}
    
    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                accession = extract_accession_from_header(line)
                species = parse_species_from_header(line)
                
                if accession and species:
                    mapping[accession] = species
    
    return mapping


def get_full_taxonomy_info(header: str) -> dict:
    """
    Extract full taxonomy information from FASTA header.
    
    Returns:
        {
            'accession': str,
            'species': str,
            'strain': str (optional),
            'description': str
        }
    """
    header = header.lstrip('>')
    parts = header.split()
    
    if not parts:
        return {}
    
    result = {
        'accession': parts[0],
        'species': None,
        'strain': None,
        'description': header
    }
    
    # Extract species (genus + species)
    if len(parts) >= 3:
        genus = parts[1]
        species_name = parts[2]
        
        if species_name.lower() not in ["dsm", "strain", "atcc", "nrrl", "type"]:
            result['species'] = f"{genus} {species_name}"
        else:
            result['species'] = genus
    
    # Extract strain if present
    strain_keywords = ["strain", "DSM", "ATCC", "NRRL", "type"]
    for i, part in enumerate(parts):
        if part in strain_keywords and i + 1 < len(parts):
            result['strain'] = parts[i + 1]
            break
    
    return result
