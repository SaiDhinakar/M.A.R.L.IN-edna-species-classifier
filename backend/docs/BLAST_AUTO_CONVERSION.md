# BLAST Database Auto-Conversion Feature

## Overview

The training pipeline now **automatically converts BLAST databases to FASTA format** when detected during dataset loading. This eliminates the need for manual conversion and makes the system more user-friendly.

## How It Works

### 1. Detection Phase
When a dataset is loaded, the pipeline checks for sequence files:
- First looks for FASTA/FASTQ files (`.fasta`, `.fa`, `.fastq`, `.fq`, `.fna`, `.ffn`, `.faa`, `.frn`)
- If none found, checks for BLAST database files (`.nhr`, `.nin`, `.nsq`)

### 2. Conversion Phase
If BLAST database detected:
```
🔄 Automatic Conversion Triggered
├── Identifies database name (e.g., "16S_ribosomal_RNA")
├── Runs: blastdbcmd -db <db_name> -entry all -out <db_name>.fasta
├── Parses extracted FASTA file
└── Loads sequences into training pipeline
```

### 3. Cleanup Phase
After successful conversion:
```
🧹 Automatic Cleanup
├── Keeps: FASTA file (.fasta)
├── Removes: All BLAST database files
│   ├── .nhr (header)
│   ├── .nin (index)
│   ├── .nsq (sequences)
│   ├── .ndb (database)
│   ├── .nnd, .nni, .nog, .nos (other indexes)
│   ├── .not, .ntf, .nto (taxonomy)
│   ├── taxdb.btd, taxdb.bti (taxonomy database)
│   └── taxonomy4blast.sqlite3 (taxonomy SQLite)
└── Result: Clean directory with only FASTA file
```

## Example Workflow

### Before (Manual Process)
```bash
# 1. User downloads BLAST database
wget https://example.com/16S_ribosomal_RNA.tar.gz

# 2. User extracts archive
tar -xzf 16S_ribosomal_RNA.tar.gz

# 3. User manually converts to FASTA
blastdbcmd -db 16S_ribosomal_RNA -entry all -out sequences.fasta

# 4. User creates new archive
tar -czf sequences.tar.gz sequences.fasta

# 5. User uploads via API
curl -X POST http://localhost:8000/api/v1/dataset/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@sequences.tar.gz"
```

### After (Automatic Process)
```bash
# 1. User downloads BLAST database
wget https://example.com/16S_ribosomal_RNA.tar.gz

# 2. User uploads directly via API - DONE!
curl -X POST http://localhost:8000/api/v1/dataset/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@16S_ribosomal_RNA.tar.gz"

# Pipeline automatically:
# ✅ Detects BLAST database
# ✅ Converts to FASTA
# ✅ Cleans up unnecessary files
# ✅ Proceeds with training
```

## Log Output Example

When a BLAST database is uploaded, you'll see:

```
INFO: Loading dataset 1 from raw/16S_ribosomal_RNA.tar.gz
INFO: No FASTA/FASTQ files found in archive
INFO: Checking for BLAST database files...
INFO: 🔄 Detected BLAST database files. Auto-converting to FASTA...
INFO: Converting BLAST database: 16S_ribosomal_RNA
INFO: ✅ Successfully converted BLAST database to FASTA
INFO: Extracted 27354 sequences from BLAST database
INFO: Cleaning up BLAST database files...
INFO: ✅ Cleanup complete - kept FASTA file only
INFO: ✅ Loaded 27354 sequences from archive
INFO: Preprocessing 27354 sequences...
```

## Requirements

### System Dependencies
The auto-conversion feature requires **BLAST+ toolkit** to be installed:

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ncbi-blast+
```

#### macOS
```bash
brew install blast
```

#### Manual Installation
Download from: https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/

### Verification
Check if `blastdbcmd` is available:
```bash
blastdbcmd -version
```

Expected output:
```
blastdbcmd: 2.14.0+
Package: blast 2.14.0, build Aug  8 2023 16:49:06
```

## Supported Formats

### Input Formats (Auto-Detected)
1. **FASTA** - Direct processing
   - `.fasta`, `.fa`, `.fna`, `.ffn`, `.faa`, `.frn`
   
2. **FASTQ** - Direct processing
   - `.fastq`, `.fq`
   
3. **BLAST Database** - Auto-conversion
   - `.nhr`, `.nin`, `.nsq` (required files)
   - `.ndb`, `.nnd`, `.nni`, `.nog`, `.nos`, `.not`, `.ntf`, `.nto` (optional)

### Output Format
- Always converted to **FASTA** internally
- Only FASTA files are kept after conversion

## File Cleanup Details

### Files Removed After Conversion
```
BLAST Database Files (Removed):
├── Core Database
│   ├── *.nhr     (Header file)
│   ├── *.nin     (Index file)
│   └── *.nsq     (Sequence file)
├── Extended Indexes
│   ├── *.ndb     (Database file)
│   ├── *.nnd     (Numeric data index)
│   ├── *.nni     (Numeric data)
│   ├── *.nog     (OID to GI mapping)
│   └── *.nos     (OID list)
├── Taxonomy
│   ├── *.not     (Taxonomy ID index)
│   ├── *.ntf     (Taxonomy nodes)
│   ├── *.nto     (Taxonomy OID)
│   ├── taxdb.btd (Taxonomy database)
│   ├── taxdb.bti (Taxonomy index)
│   └── taxonomy4blast.sqlite3 (Taxonomy SQLite)
└── Other
    └── Any non-FASTA files
```

### Files Retained
```
✅ *.fasta  (Converted sequences)
```

## Error Handling

### Error: blastdbcmd Not Found
```
❌ blastdbcmd not found. Please install BLAST+ toolkit:
   Ubuntu/Debian: sudo apt-get install ncbi-blast+
   macOS: brew install blast
   Or download from: https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/
```

**Solution:** Install BLAST+ toolkit as shown above

### Error: Conversion Timeout
```
❌ blastdbcmd timed out after 5 minutes
```

**Solution:** 
- Large databases may need more time
- Consider pre-converting to FASTA for very large datasets (>100K sequences)
- Or increase timeout in `training_workflow.py` line ~155: `timeout=300`

### Error: Conversion Failed
```
❌ Failed to convert BLAST database: [error details]
```

**Solution:**
- Check BLAST database integrity
- Verify all required files present (.nhr, .nin, .nsq)
- Try manual conversion to diagnose issue

## Performance Impact

### Conversion Times (Approximate)

| Database Size | Sequences | Conversion Time | Total Overhead |
|--------------|-----------|-----------------|----------------|
| Small (18S) | 3,692 | ~10s | Minimal |
| Medium (28S) | 11,345 | ~30s | Low |
| Large (16S) | 27,354 | ~60s | Moderate |
| Very Large | 100,000+ | ~5min | Significant* |

*For very large databases, pre-conversion to FASTA is recommended*

### Storage Savings

After cleanup, storage usage is reduced:
- **Before:** BLAST database + FASTA = 2x space
- **After:** FASTA only = 1x space

Example:
- 16S BLAST database: ~50MB
- 16S FASTA: ~43MB
- **Savings:** ~7MB (14%)

## Advanced Usage

### Skip Auto-Conversion
If you want to upload FASTA directly (skip conversion):
1. Pre-convert using the extraction script:
   ```bash
   python extract_blast_to_fasta.py data/archives/16S_ribosomal_RNA
   ```
2. Upload the `*_sequences.tar.gz` file

### Manual Conversion
```bash
# Extract BLAST database
tar -xzf 16S_ribosomal_RNA.tar.gz

# Convert to FASTA
blastdbcmd -db 16S_ribosomal_RNA -entry all -out sequences.fasta

# Create clean archive
tar -czf sequences.tar.gz sequences.fasta

# Upload
curl -X POST http://localhost:8000/api/v1/dataset/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@sequences.tar.gz"
```

### Batch Processing
For multiple BLAST databases:
```bash
for db in *.tar.gz; do
  echo "Uploading $db (auto-conversion will happen)..."
  curl -X POST http://localhost:8000/api/v1/dataset/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$db"
done
```

## Implementation Details

### Code Location
File: `backend/app/services/training_workflow.py`
Method: `load_data()` (lines 40-200)

### Key Logic
```python
# 1. Try parsing FASTA/FASTQ files first
for file in files:
    if file.endswith(sequence_extensions):
        parse_sequences(file)

# 2. If no sequences found, check for BLAST database
if len(sequences) == 0:
    blast_db_files = find_blast_databases()
    
    if blast_db_files:
        # 3. Convert using blastdbcmd
        convert_blast_to_fasta()
        
        # 4. Parse converted FASTA
        parse_sequences(converted_fasta)
        
        # 5. Clean up BLAST files
        cleanup_blast_files()
```

### Dependencies
- `subprocess`: For running blastdbcmd
- `shutil`: For cleaning up directories
- `Bio.SeqIO`: For parsing FASTA files
- `tarfile`: For extracting archives

## Benefits

✅ **User Experience**
- No manual conversion required
- Upload BLAST databases directly
- Transparent process with clear logging

✅ **Storage Efficiency**
- Automatic cleanup of unnecessary files
- Only FASTA files retained
- Reduced storage footprint

✅ **Error Handling**
- Clear error messages
- Helpful installation instructions
- Timeout protection

✅ **Compatibility**
- Supports all BLAST database versions
- Works with NCBI standard formats
- Fallback to manual process if needed

## Migration Guide

### Existing Datasets
If you have existing BLAST databases:
1. No action needed - just upload them
2. Pipeline will auto-convert on first use
3. Cleanup happens automatically

### CI/CD Integration
If using automated pipelines:
1. Add BLAST+ installation to Docker image
2. No code changes needed
3. Works transparently

Example Dockerfile addition:
```dockerfile
RUN apt-get update && \
    apt-get install -y ncbi-blast+ && \
    apt-get clean
```

## Troubleshooting

### Issue: Conversion works but sequences empty
**Cause:** BLAST database may be corrupted
**Solution:** 
```bash
# Verify database integrity
blastdbcmd -db <db_name> -info

# Re-download if corrupted
```

### Issue: Cleanup fails
**Cause:** File permission issues
**Solution:**
- Check tmpdir permissions
- Run with appropriate user privileges

### Issue: Large memory usage
**Cause:** Large database conversion
**Solution:**
- Increase Docker memory limits
- Pre-convert very large databases
- Use streaming if possible

## Future Enhancements

Potential improvements:
- [ ] Progress bar for long conversions
- [ ] Streaming conversion for very large databases
- [ ] Caching converted FASTA files
- [ ] Parallel conversion for multiple databases
- [ ] Support for other database formats (DIAMOND, etc.)

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Verify BLAST+ installation: `blastdbcmd -version`
3. Try manual conversion to isolate issue
4. Review DATASET_PREPARATION.md for alternatives
