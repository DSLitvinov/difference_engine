"""
Migration utilities for Difference Engine addon
"""
import os
import json
import logging
from typing import List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

# Global cache for migration status to avoid repeated checks
_migration_cache = {}


class DFM_Migration:
    """Handles migration of data structures between versions"""
    
    @staticmethod
    def migrate_commit_indexes_to_branches(base_dir: str) -> bool:
        """
        Migrate old mesh-level commit indexes to branch-level indexes.
        
        This migration moves commits_index.json from mesh level to branch level.
        
        Args:
            base_dir: Base directory of the difference machine data
            
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            if not os.path.exists(base_dir):
                logger.info("No base directory found, nothing to migrate")
                return True
            
            migrated_count = 0
            
            # Find all mesh directories
            for mesh_name in os.listdir(base_dir):
                mesh_dir = os.path.join(base_dir, mesh_name)
                if not os.path.isdir(mesh_dir):
                    continue
                
                # Check if old commits_index.json exists
                old_index_path = os.path.join(mesh_dir, 'commits_index.json')
                if not os.path.exists(old_index_path):
                    continue
                
                logger.info(f"Migrating commit index for mesh: {mesh_name}")
                
                # Load old index
                try:
                    with open(old_index_path, 'r') as f:
                        old_index_data = json.load(f)
                    old_commits = old_index_data.get('commits', [])
                except Exception as e:
                    logger.error(f"Failed to load old index for {mesh_name}: {e}")
                    continue
                
                # Group commits by branch
                branch_commits = {}
                for commit in old_commits:
                    branch_name = commit.get('branch', 'main')
                    if branch_name not in branch_commits:
                        branch_commits[branch_name] = []
                    branch_commits[branch_name].append(commit)
                
                # Create new branch-level indexes
                for branch_name, commits in branch_commits.items():
                    branch_dir = os.path.join(mesh_dir, branch_name)
                    if not os.path.exists(branch_dir):
                        logger.warning(f"Branch directory {branch_dir} doesn't exist, skipping")
                        continue
                    
                    new_index_path = os.path.join(branch_dir, 'commits_index.json')
                    
                    # Create new index data
                    new_index_data = {
                        'commits': commits,
                        'last_updated': old_index_data.get('last_updated', ''),
                        'migrated_from': 'mesh_level'
                    }
                    
                    # Save new index
                    try:
                        with open(new_index_path, 'w') as f:
                            json.dump(new_index_data, f)
                        logger.info(f"Created branch index: {new_index_path}")
                        migrated_count += 1
                    except Exception as e:
                        logger.error(f"Failed to save new index for {mesh_name}/{branch_name}: {e}")
                        continue
                
                # Backup old index
                backup_path = old_index_path + '.backup'
                try:
                    os.rename(old_index_path, backup_path)
                    logger.info(f"Backed up old index: {backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to backup old index: {e}")
            
            logger.info(f"Migration completed. Migrated {migrated_count} branch indexes.")
            # Clear cache after successful migration
            _migration_cache[base_dir] = False
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    @staticmethod
    def check_migration_needed(base_dir: str) -> bool:
        """
        Check if migration is needed by looking for old mesh-level commit indexes.
        Uses caching to avoid repeated filesystem checks.
        
        Args:
            base_dir: Base directory of the difference machine data
            
        Returns:
            True if migration is needed, False otherwise
        """
        # Check cache first
        if base_dir in _migration_cache:
            return _migration_cache[base_dir]
        
        try:
            if not os.path.exists(base_dir):
                _migration_cache[base_dir] = False
                return False
            
            # Look for any mesh directories with old commit indexes
            for mesh_name in os.listdir(base_dir):
                mesh_dir = os.path.join(base_dir, mesh_name)
                if not os.path.isdir(mesh_dir):
                    continue
                
                old_index_path = os.path.join(mesh_dir, 'commits_index.json')
                if os.path.exists(old_index_path):
                    _migration_cache[base_dir] = True
                    return True
            
            _migration_cache[base_dir] = False
            return False
            
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            _migration_cache[base_dir] = False
            return False
    
    @staticmethod
    def run_migration_if_needed() -> bool:
        """
        Run migration if needed, using the current Blender file's base directory.
        
        Returns:
            True if migration was successful or not needed, False otherwise
        """
        try:
            import bpy
            base_path = bpy.path.abspath("//")
            if not base_path:
                logger.info("No Blender file saved, no migration needed")
                return True
            
            base_dir = os.path.join(base_path, ".difference_machine")
            
            if not DFM_Migration.check_migration_needed(base_dir):
                logger.info("No migration needed")
                return True
            
            logger.info("Migration needed, starting migration process...")
            return DFM_Migration.migrate_commit_indexes_to_branches(base_dir)
            
        except Exception as e:
            logger.error(f"Failed to run migration: {e}")
            return False
    
    @staticmethod
    def clear_migration_cache(base_dir: str = None) -> None:
        """
        Clear migration cache for a specific directory or all directories.
        
        Args:
            base_dir: Specific directory to clear from cache, or None to clear all
        """
        if base_dir:
            _migration_cache.pop(base_dir, None)
            logger.debug(f"Cleared migration cache for: {base_dir}")
        else:
            _migration_cache.clear()
            logger.debug("Cleared all migration cache")
