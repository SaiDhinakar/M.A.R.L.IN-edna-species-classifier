#!/usr/bin/env python3
"""
Extract FASTA sequences from BLAST database files.
This is a helper script to convert BLAST database files to FASTA format.
"""

import os
import sys
import subprocess
import tarfile
from pathlib import Path


def extract_blast_db_to_fasta(blast_db_path: str, output_fasta: str):
    """
    Extract sequences from BLAST database to FASTA file.
    
    Args:
        blast_db_path: Path to BLAST database (without extension)
        output_fasta: Output FASTA file path
    """
    print(f"Extracting sequences from BLAST database: {blast_db_path}")
    
    try:
        # Run blastdbcmd to extract all sequences
        cmd = [
            "blastdbcmd",
            "-db", blast_db_path,
            "-entry", "all",
            "-out", output_fasta
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully extracted sequences to: {output_fasta}")
            
            # Count sequences
            with open(output_fasta, 'r') as f:
                seq_count = sum(1 for line in f if line.startswith('>'))
            print(f"   Extracted {seq_count} sequences")
            
            return True
        else:
            print(f"❌ Error running blastdbcmd:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Error: blastdbcmd not found")
        print("   Please install BLAST+ toolkit:")
        print("   - Ubuntu/Debian: sudo apt-get install ncbi-blast+")
        print("   - macOS: brew install blast")
        print("   - Or download from: https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/")
        return False


def create_tar_gz(fasta_file: str, output_archive: str):
    """Create tar.gz archive from FASTA file."""
    print(f"\nCreating archive: {output_archive}")
    
    with tarfile.open(output_archive, "w:gz") as tar:
        tar.add(fasta_file, arcname=os.path.basename(fasta_file))
    
    print(f"✅ Created archive: {output_archive}")
    
    # Show archive contents
    print("\nArchive contents:")
    with tarfile.open(output_archive, "r:gz") as tar:
        for member in tar.getmembers():
            print(f"  {member.name} ({member.size} bytes)")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python extract_blast_to_fasta.py <blast_db_path>")
        print("\nExample:")
        print("  python extract_blast_to_fasta.py data/archives/16S_ribosomal_RNA")
        print("\nThis will:")
        print("  1. Extract sequences to 16S_ribosomal_RNA.fasta")
        print("  2. Create 16S_ribosomal_RNA_sequences.tar.gz")
        sys.exit(1)
    
    blast_db_path = sys.argv[1]
    
    # Remove extension if provided
    blast_db_path = blast_db_path.replace('.nhr', '').replace('.nin', '').replace('.nsq', '')
    
    # Get base name
    base_name = os.path.basename(blast_db_path)
    output_dir = os.path.dirname(blast_db_path) or '.'
    
    # Output paths
    fasta_file = os.path.join(output_dir, f"{base_name}.fasta")
    archive_file = os.path.join(output_dir, f"{base_name}_sequences.tar.gz")
    
    print("=" * 60)
    print("BLAST Database to FASTA Converter")
    print("=" * 60)
    print(f"Input:  {blast_db_path}")
    print(f"Output: {fasta_file}")
    print(f"Archive: {archive_file}")
    print("=" * 60)
    
    # Check if BLAST database files exist
    required_extensions = ['.nhr', '.nin', '.nsq']
    missing_files = []
    
    for ext in required_extensions:
        if not os.path.exists(f"{blast_db_path}{ext}"):
            missing_files.append(f"{blast_db_path}{ext}")
    
    if missing_files:
        print("\n❌ Error: BLAST database files not found:")
        for file in missing_files:
            print(f"   {file}")
        sys.exit(1)
    
    # Extract sequences
    print()
    if extract_blast_db_to_fasta(blast_db_path, fasta_file):
        # Create archive
        create_tar_gz(fasta_file, archive_file)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"\nYou can now upload: {archive_file}")
        print("\nNext steps:")
        print("1. Upload the archive via API:")
        print(f"   curl -X POST http://localhost:8000/api/v1/dataset/upload \\")
        print(f"     -H 'Authorization: Bearer YOUR_TOKEN' \\")
        print(f"     -F 'file=@{archive_file}'")
        print("\n2. Approve the dataset in the admin panel")
        print("3. Trigger training")
    else:
        print("\n❌ FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
