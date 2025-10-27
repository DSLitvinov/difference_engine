# Difference Engine - Index Structure Documentation

## Overview

The Difference Engine uses an index-based search system for fast retrieval of commits and branches across large datasets. This document describes the structure and usage of these indices.

## Index Files

### 1. Branches Index (`branches_index.json`)

**Location**: `<mesh_dir>/branches_index.json`  
**Purpose**: Quick access to branch information without filesystem traversal

#### Structure
```json
{
  "branches": [
    {
      "name": "main",
      "commit_count": 15,
      "last_commit_timestamp": "2025-01-20_14-30-00",
      "path": "/path/to/mesh_dir/main"
    },
    {
      "name": "experimental",
      "commit_count": 3,
      "last_commit_timestamp": "2025-01-19_10-15-30",
      "path": "/path/to/mesh_dir/experimental"
    }
  ],
  "last_updated": "2025-01-20_15-00-00",
  "mesh_name": "Cube"
}
```

#### Fields
- `branches`: Array of branch information
  - `name`: Branch name
  - `commit_count`: Number of commits in this branch
  - `last_commit_timestamp`: Timestamp of most recent commit
  - `path`: Full path to branch directory
- `last_updated`: Timestamp when index was last updated
- `mesh_name`: Name of the mesh object

### 2. Commits Index (`commits_index.json`)

**Location**: `<mesh_dir>/<branch_name>/commits_index.json`  
**Purpose**: Fast search through commits in a specific branch

#### Structure
```json
{
  "commits": [
    {
      "timestamp": "2025-01-20_14-30-00",
      "message": "Added new geometry",
      "author": "User",
      "path": "/path/to/commit_dir",
      "files": ["geometry.json", "transform.json"],
      "size": 1024000,
      "tag": "v1.2.0"
    }
  ],
  "last_updated": "2025-01-20_15-00-00",
  "branch_name": "main",
  "mesh_name": "Cube"
}
```

#### Fields
- `commits`: Array of commit information
  - `timestamp`: Commit timestamp (directory name)
  - `message`: Commit message
  - `author`: Author name
  - `path`: Full path to commit directory
  - `files`: List of files in commit
  - `size`: Total size in bytes
  - `tag`: Optional version tag
  - `corrupted`: (optional) True if commit file is corrupted
- `last_updated`: Timestamp when index was last updated
- `branch_name`: Name of the branch
- `mesh_name`: Name of the mesh object

## Index Operations

### Creating Indices

Indices are created automatically when:
- A commit is exported
- A branch is created
- Manual index update is triggered via UI

```python
from classes.index_manager import DFM_IndexManager

# Update all indices for a mesh
success = DFM_IndexManager.update_all_indices(mesh_name)
```

### Loading Indices

```python
# Load branches index
branches_index = DFM_IndexManager.load_index(mesh_name, 'branches_index')

# Load commits index for a branch
commits_data = DFM_IndexManager.create_commits_index(mesh_name, branch_name)
```

### Search Functionality

Quick search through commits by message, author, or timestamp:

```python
# Search commits (example implementation)
def search_commits(mesh_name, branch_name, query):
    commits_index = DFM_IndexManager.load_index(mesh_name, 'commits_index')
    results = []
    for commit in commits_index['commits']:
        if query.lower() in commit['message'].lower():
            results.append(commit)
    return results
```

## Index Maintenance

### Automatic Updates

Indices are automatically updated when:
- Exporting geometry (`DFM_SaveGeometryOperator`)
- Creating branches (`DFM_CreateBranchOperator`)
- Switching branches (`DFM_SwitchBranchOperator`)

### Manual Updates

Users can manually trigger index updates via the Index Management panel:
- **Update Indices**: Rebuild all indices
- **Validate Integrity**: Check index integrity and restore if corrupted
- **Backup/Restore**: Manage index backups

### Integrity Validation

The `validate_data_integrity` method:
1. Checks if index files exist
2. Validates JSON structure
3. Detects corrupted commit files
4. Automatically restores missing/corrupted indices

```python
result = DFM_IndexManager.validate_data_integrity(mesh_dir)
if not result['valid']:
    # Handle issues
    print(result['issues'])
```

## Performance Considerations

### Index Size

- **Branches Index**: Typically < 10KB even for hundreds of branches
- **Commits Index**: Scales linearly with commit count (~500 bytes per commit)

### Update Performance

- **Full index update**: O(n) where n is number of commits
- **Incremental update**: Not currently implemented (future optimization)

### Search Performance

- **Branch search**: O(1) with branches index
- **Commit search**: O(n) linear search (consider binary search for sorted data)

## Backup and Recovery

### Automatic Backups

Backups are created in `<mesh_dir>/.backup/` before:
- Index updates
- Index validation
- Data migrations

### Manual Backup

```python
success = DFM_IndexManager.backup_indices(mesh_dir)
```

### Restore from Backup

```python
success = DFM_IndexManager.restore_from_backup(mesh_dir)
```

## Corrupted Data Handling

### Detection

Corrupted data is detected during:
- Index loading
- Integrity validation
- Commit loading

### Recovery

The system attempts to:
1. Load from backup if available
2. Rebuild from filesystem data
3. Mark as corrupted with placeholder data

```python
# Commit marked as corrupted in index
{
  "timestamp": "2025-01-20_14-30-00",
  "message": "[Corrupted]",
  "author": "",
  "path": "/path/to/commit_dir",
  "files": [],
  "size": 0,
  "corrupted": true
}
```

## Migration

Indices may need to be migrated when:
- Data format changes
- New fields are added
- Structure changes

### Migration Process

1. Detect old format
2. Create backup
3. Migrate data
4. Update indices
5. Validate migrated data

## Future Improvements

### Planned Enhancements

1. **Incremental Updates**: Update only changed commits
2. **Binary Search**: Faster commit search in sorted indices
3. **Compressed Indices**: Reduce storage for large datasets
4. **Full-Text Search**: Advanced search capabilities
5. **Index Caching**: Keep indices in memory for faster access

### Performance Targets

- Branch search: < 1ms
- Commit search: < 10ms for 1000 commits
- Full index rebuild: < 1s for 1000 commits

## Troubleshooting

### Common Issues

1. **Index Out of Sync**: Use "Update Indices" to rebuild
2. **Missing Index**: Use "Validate Integrity" to restore
3. **Corrupted Data**: Use backup/restore functionality
4. **Slow Search**: Clear and rebuild indices

### Debug Information

Enable debug logging to see index operations:

```python
import logging
logging.getLogger('classes.index_manager').setLevel(logging.DEBUG)
```

## API Reference

See `classes/index_manager.py` for complete API documentation.

### Key Methods

- `DFM_IndexManager.create_branches_index(mesh_name)` - Create branches index
- `DFM_IndexManager.create_commits_index(mesh_name, branch_name)` - Create commits index
- `DFM_IndexManager.save_index(mesh_name, index_type, data)` - Save index
- `DFM_IndexManager.load_index(mesh_name, index_type)` - Load index
- `DFM_IndexManager.update_all_indices(mesh_name)` - Update all indices
- `DFM_IndexManager.validate_data_integrity(mesh_dir)` - Validate integrity
- `DFM_IndexManager.backup_indices(mesh_dir)` - Backup indices
- `DFM_IndexManager.restore_from_backup(mesh_dir)` - Restore from backup

