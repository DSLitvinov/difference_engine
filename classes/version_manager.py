"""
Version control management functionality
"""
import bpy
import json
import os
import shutil
import zipfile
import logging
from typing import List, Dict, Any, Optional
from .utils import sanitize_path_component

# Setup logging
logger = logging.getLogger(__name__)


class DFM_VersionManager:
    """Manages version control operations"""
    
    @staticmethod
    def get_object_history(mesh_name: str) -> List[Dict[str, Any]]:
        """
        Get commit history for an object.
        
        Args:
            mesh_name: Name of the mesh object
            
        Returns:
            List of commit data dictionaries, sorted by timestamp (newest first)
        """
        base_dir = bpy.path.abspath("//.difference_machine/")
        mesh_dir = os.path.join(base_dir, sanitize_path_component(mesh_name))
        
        if not os.path.exists(mesh_dir):
            return []
        
        history = []
        try:
            for branch in os.listdir(mesh_dir):
                branch_path = os.path.join(mesh_dir, branch)
                if os.path.isdir(branch_path):
                    try:
                        for commit in os.listdir(branch_path):
                            commit_path = os.path.join(branch_path, commit)
                            commit_file = os.path.join(commit_path, "commit.json")
                            
                            if os.path.exists(commit_file):
                                try:
                                    with open(commit_file, 'r') as f:
                                        commit_data = json.load(f)
                                        # Validate required fields
                                        if 'timestamp' not in commit_data:
                                            logger.warning(f"Commit file missing timestamp: {commit_file}")
                                            continue
                                        commit_data['commit_path'] = commit_path
                                        commit_data['branch'] = branch
                                        history.append(commit_data)
                                except (json.JSONDecodeError, IOError) as e:
                                    logger.error(f"Failed to read commit file {commit_file}: {e}")
                                    continue
                    except OSError as e:
                        logger.error(f"Failed to read branch directory {branch_path}: {e}")
                        continue
        except OSError as e:
            logger.error(f"Failed to read mesh directory {mesh_dir}: {e}")
            return []
        
        # Sort by timestamp with safe default
        history.sort(key=lambda x: x.get('timestamp', '0000-00-00_00-00-00'), reverse=True)
        return history
    
    @staticmethod
    def get_object_branches(mesh_name: str) -> List[Dict[str, Any]]:
        """
        Get all branches for an object with commit counts and last commit info.
        
        Args:
            mesh_name: Name of the mesh object
            
        Returns:
            List of branch data dictionaries with name, commit_count, and last_commit
        """
        base_dir = bpy.path.abspath("//.difference_machine/")
        mesh_dir = os.path.join(base_dir, sanitize_path_component(mesh_name))
        
        if not os.path.exists(mesh_dir):
            return []
        
        branches = []
        try:
            for branch_name in os.listdir(mesh_dir):
                branch_path = os.path.join(mesh_dir, branch_name)
                if os.path.isdir(branch_path) and branch_name != '.backup':
                    try:
                        # Count commits in this branch
                        commit_count = 0
                        last_commit = ""
                        
                        for commit_dir in os.listdir(branch_path):
                            commit_path = os.path.join(branch_path, commit_dir)
                            if os.path.isdir(commit_path):
                                commit_file = os.path.join(commit_path, "commit.json")
                                if os.path.exists(commit_file):
                                    commit_count += 1
                                    # Get timestamp for last commit (directories are sorted by name which is timestamp)
                                    if not last_commit:
                                        last_commit = commit_dir
                        
                        branches.append({
                            'name': branch_name,
                            'commit_count': commit_count,
                            'last_commit': last_commit
                        })
                        
                    except OSError as e:
                        logger.error(f"Failed to read branch directory {branch_path}: {e}")
                        continue
        except OSError as e:
            logger.error(f"Failed to read mesh directory {mesh_dir}: {e}")
            return []
        
        # Sort branches by name (main first, then alphabetical)
        branches.sort(key=lambda x: (x['name'] != 'main', x['name']))
        
        return branches
    
    @staticmethod
    def compress_old_versions(mesh_name: str, keep_versions: int = 10) -> None:
        """
        Compress old versions to save space.
        
        Safely compresses older commits by:
        1. Creating a zip archive
        2. Validating the archive
        3. Only then removing the original directory
        
        Args:
            mesh_name: Name of the mesh object
            keep_versions: Number of recent versions to keep uncompressed
        """
        history = DFM_VersionManager.get_object_history(mesh_name)
        
        if len(history) <= keep_versions:
            logger.debug(f"Not enough versions to compress for {mesh_name}")
            return
        
        compressed_count = 0
        # Keep the most recent versions, compress the rest
        for commit in history[keep_versions:]:
            commit_path = commit['commit_path']
            
            # Validate commit path for security
            if not commit_path or not isinstance(commit_path, str):
                logger.warning(f"Invalid commit path: {commit_path}")
                continue
            
            # Additional security check - ensure path is within expected directory
            base_dir = bpy.path.abspath("//.difference_machine/")
            if not commit_path.startswith(base_dir):
                logger.warning(f"Commit path outside expected directory: {commit_path}")
                continue
            
            zip_path = commit_path + '.zip'
            
            # Skip if already compressed
            if os.path.exists(zip_path):
                logger.debug(f"Version already compressed: {commit_path}")
                continue
            
            # Skip if directory doesn't exist
            if not os.path.isdir(commit_path):
                logger.warning(f"Commit directory not found: {commit_path}")
                continue
                
            try:
                # Create zip archive
                logger.info(f"Compressing version: {commit_path}")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(commit_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, commit_path)
                            zipf.write(file_path, arcname)
                
                # Validate the zip file before removing original
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    bad_file = zipf.testzip()
                    if bad_file:
                        raise zipfile.BadZipFile(f"Corrupted file in archive: {bad_file}")
                
                # Only remove original after successful validation
                shutil.rmtree(commit_path)
                compressed_count += 1
                logger.info(f"Successfully compressed and removed: {commit_path}")
                
            except Exception as e:
                logger.error(f"Failed to compress {commit_path}: {e}")
                # Clean up partial zip file if it exists
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                        logger.info(f"Cleaned up partial zip: {zip_path}")
                    except Exception as cleanup_error:
                        logger.error(f"Failed to clean up partial zip {zip_path}: {cleanup_error}")
        
        if compressed_count > 0:
            logger.info(f"Compressed {compressed_count} old versions for {mesh_name}")
    
    @staticmethod
    def delete_version(commit_path: str) -> bool:
        """
        Delete a specific version from history.
        
        Safely deletes a commit by removing both the directory and any compressed zip file.
        
        Args:
            commit_path: Full path to the commit directory
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not commit_path or not os.path.exists(commit_path):
            logger.warning(f"Commit path does not exist: {commit_path}")
            return False
        
        zip_path = commit_path + '.zip'
        success = True
        
        try:
            # Remove the directory if it exists
            if os.path.isdir(commit_path):
                shutil.rmtree(commit_path)
                logger.info(f"Deleted commit directory: {commit_path}")
            
            # Remove the zip file if it exists
            if os.path.exists(zip_path):
                os.remove(zip_path)
                logger.info(f"Deleted compressed version: {zip_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete version at {commit_path}: {e}")
            return False
    
    @staticmethod
    def save_current_branch(mesh_name: str, branch_name: str) -> bool:
        """
        Save the current branch for a mesh object to persist across restarts.
        
        Args:
            mesh_name: Name of the mesh object
            branch_name: Name of the branch to save as current
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            base_dir = bpy.path.abspath("//.difference_machine/")
            mesh_dir = os.path.join(base_dir, sanitize_path_component(mesh_name))
            
            # Create mesh directory if it doesn't exist
            os.makedirs(mesh_dir, exist_ok=True)
            
            # Save current branch info
            branch_info = {
                'current_branch': branch_name,
                'last_updated': bpy.context.scene.get('dfm_last_updated', '')
            }
            
            branch_file = os.path.join(mesh_dir, 'current_branch.json')
            with open(branch_file, 'w') as f:
                json.dump(branch_info, f, indent=2)
            
            logger.info(f"Saved current branch '{branch_name}' for mesh '{mesh_name}'")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save current branch for {mesh_name}: {e}")
            return False
    
    @staticmethod
    def load_current_branch(mesh_name: str) -> str:
        """
        Load the saved current branch for a mesh object.
        
        Args:
            mesh_name: Name of the mesh object
            
        Returns:
            Name of the current branch, or 'main' if not found or error
        """
        try:
            base_dir = bpy.path.abspath("//.difference_machine/")
            mesh_dir = os.path.join(base_dir, sanitize_path_component(mesh_name))
            branch_file = os.path.join(mesh_dir, 'current_branch.json')
            
            if not os.path.exists(branch_file):
                return 'main'
            
            with open(branch_file, 'r') as f:
                branch_info = json.load(f)
            
            current_branch = branch_info.get('current_branch', 'main')
            logger.info(f"Loaded current branch '{current_branch}' for mesh '{mesh_name}'")
            return current_branch
            
        except Exception as e:
            logger.error(f"Failed to load current branch for {mesh_name}: {e}")
            return 'main'

