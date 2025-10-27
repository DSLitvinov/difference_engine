"""
Index management for quick search functionality
"""
import bpy
import json
import os
import shutil
import logging
from typing import List, Dict, Any, Optional
from .utils import sanitize_path_component

# Setup logging
logger = logging.getLogger(__name__)


class DFM_IndexManager:
    """Manages indexing for quick search functionality"""
    
    @staticmethod
    def get_mesh_dir(mesh_name: str) -> str:
        """Get the mesh directory path"""
        base_dir = bpy.path.abspath("//.difference_machine/")
        return os.path.join(base_dir, sanitize_path_component(mesh_name))
    
    @staticmethod
    def create_branches_index(mesh_name: str) -> Dict[str, Any]:
        """
        Create a lightweight branches index for quick navigation.
        
        Args:
            mesh_name: Name of the mesh object
            
        Returns:
            Dictionary containing branches index data
        """
        mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
        
        if not os.path.exists(mesh_dir):
            return {'branches': [], 'last_updated': ''}
        
        branches = []
        try:
            for branch_name in os.listdir(mesh_dir):
                branch_path = os.path.join(mesh_dir, branch_name)
                if os.path.isdir(branch_path) and branch_name != '.backup':
                    # Count commits quickly without loading full commit data
                    commit_count = 0
                    last_commit_timestamp = ''
                    
                    for commit_dir in os.listdir(branch_path):
                        commit_path = os.path.join(branch_path, commit_dir)
                        if os.path.isdir(commit_path):
                            commit_file = os.path.join(commit_path, "commit.json")
                            if os.path.exists(commit_file):
                                commit_count += 1
                                # Use directory name as timestamp (it's the commit timestamp)
                                if not last_commit_timestamp:
                                    last_commit_timestamp = commit_dir
                    
                    branches.append({
                        'name': branch_name,
                        'commit_count': commit_count,
                        'last_commit_timestamp': last_commit_timestamp,
                        'path': branch_path
                    })
        except OSError as e:
            logger.error(f"Failed to read mesh directory {mesh_dir}: {e}")
            return {'branches': [], 'last_updated': ''}
        
        # Sort branches (main first, then alphabetical)
        branches.sort(key=lambda x: (x['name'] != 'main', x['name']))
        
        return {
            'branches': branches,
            'last_updated': bpy.context.scene.get('dfm_last_updated', ''),
            'mesh_name': mesh_name
        }
    
    @staticmethod
    def create_commits_index(mesh_name: str, branch_name: str) -> Dict[str, Any]:
        """
        Create a detailed commits index for a specific branch.
        
        Args:
            mesh_name: Name of the mesh object
            branch_name: Name of the branch
            
        Returns:
            Dictionary containing commits index data
        """
        mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
        branch_path = os.path.join(mesh_dir, sanitize_path_component(branch_name))
        
        if not os.path.exists(branch_path):
            return {'commits': [], 'last_updated': ''}
        
        commits = []
        try:
            for commit_dir in os.listdir(branch_path):
                commit_path = os.path.join(branch_path, commit_dir)
                if os.path.isdir(commit_path):
                    commit_file = os.path.join(commit_path, "commit.json")
                    if os.path.exists(commit_file):
                        try:
                            with open(commit_file, 'r') as f:
                                commit_data = json.load(f)
                            
                            # Extract essential info for quick search
                            commits.append({
                                'timestamp': commit_data.get('timestamp', commit_dir),
                                'message': commit_data.get('message', ''),
                                'author': commit_data.get('author', ''),
                                'path': commit_path,
                                'files': commit_data.get('files', []),
                                'size': commit_data.get('size', 0)
                            })
                        except (json.JSONDecodeError, IOError) as e:
                            logger.warning(f"Failed to read commit file {commit_file}: {e}")
                            # Add minimal info even if file is corrupted
                            commits.append({
                                'timestamp': commit_dir,
                                'message': '[Corrupted]',
                                'author': '',
                                'path': commit_path,
                                'files': [],
                                'size': 0,
                                'corrupted': True
                            })
        except OSError as e:
            logger.error(f"Failed to read branch directory {branch_path}: {e}")
            return {'commits': [], 'last_updated': ''}
        
        # Sort by timestamp (newest first)
        commits.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'commits': commits,
            'last_updated': bpy.context.scene.get('dfm_last_updated', ''),
            'branch_name': branch_name,
            'mesh_name': mesh_name
        }
    
    @staticmethod
    def save_index(mesh_name: str, index_type: str, data: Dict[str, Any]) -> bool:
        """
        Save an index file to disk.
        
        Args:
            mesh_name: Name of the mesh object
            index_type: Type of index ('branches_index' or 'commits_index')
            data: Index data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
            os.makedirs(mesh_dir, exist_ok=True)
            
            index_file = os.path.join(mesh_dir, f"{index_type}.json")
            with open(index_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {index_type} for mesh '{mesh_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {index_type} for {mesh_name}: {e}")
            return False
    
    @staticmethod
    def load_index(mesh_name: str, index_type: str) -> Optional[Dict[str, Any]]:
        """
        Load an index file from disk.
        
        Args:
            mesh_name: Name of the mesh object
            index_type: Type of index ('branches_index' or 'commits_index')
            
        Returns:
            Index data or None if not found/error
        """
        try:
            mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
            index_file = os.path.join(mesh_dir, f"{index_type}.json")
            
            if not os.path.exists(index_file):
                return None
            
            with open(index_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load {index_type} for {mesh_name}: {e}")
            return None
    
    @staticmethod
    def update_all_indices(mesh_name: str) -> bool:
        """
        Update all index files for a mesh object.
        
        Args:
            mesh_name: Name of the mesh object
            
        Returns:
            True if all indices updated successfully, False otherwise
        """
        try:
            # Update branches index
            branches_data = DFM_IndexManager.create_branches_index(mesh_name)
            if not DFM_IndexManager.save_index(mesh_name, 'branches_index', branches_data):
                return False
            
            # Update commits index for each branch
            for branch in branches_data['branches']:
                branch_name = branch['name']
                commits_data = DFM_IndexManager.create_commits_index(mesh_name, branch_name)
                
                # Save commits index in the branch directory
                mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
                branch_path = os.path.join(mesh_dir, sanitize_path_component(branch_name))
                os.makedirs(branch_path, exist_ok=True)
                
                commits_file = os.path.join(branch_path, 'commits_index.json')
                with open(commits_file, 'w') as f:
                    json.dump(commits_data, f, indent=2)
            
            logger.info(f"Updated all indices for mesh '{mesh_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update indices for {mesh_name}: {e}")
            return False
    
    @staticmethod
    def validate_data_integrity(mesh_dir: str) -> Dict[str, Any]:
        """
        Verifies data integrity and restores if necessary.
        
        Args:
            mesh_dir: Path to the mesh directory
            
        Returns:
            Dictionary with validation results and restoration info
        """
        result = {
            'valid': True,
            'issues': [],
            'restored': [],
            'corrupted_commits': []
        }
        
        if not os.path.exists(mesh_dir):
            result['valid'] = False
            result['issues'].append('Mesh directory does not exist')
            return result
        
        try:
            # Check branches index
            branches_index_file = os.path.join(mesh_dir, 'branches_index.json')
            if not os.path.exists(branches_index_file):
                result['issues'].append('Missing branches_index.json')
                # Restore from filesystem
                mesh_name = os.path.basename(mesh_dir)
                branches_data = DFM_IndexManager.create_branches_index(mesh_name)
                DFM_IndexManager.save_index(mesh_name, 'branches_index', branches_data)
                result['restored'].append('branches_index.json')
            else:
                # Validate branches index content
                try:
                    with open(branches_index_file, 'r') as f:
                        branches_data = json.load(f)
                    if 'branches' not in branches_data:
                        raise ValueError("Invalid branches index structure")
                except (json.JSONDecodeError, ValueError) as e:
                    result['issues'].append(f'Corrupted branches_index.json: {e}')
                    # Restore from filesystem
                    mesh_name = os.path.basename(mesh_dir)
                    branches_data = DFM_IndexManager.create_branches_index(mesh_name)
                    DFM_IndexManager.save_index(mesh_name, 'branches_index', branches_data)
                    result['restored'].append('branches_index.json')
            
            # Check each branch's commits index
            for branch_name in os.listdir(mesh_dir):
                branch_path = os.path.join(mesh_dir, branch_name)
                if os.path.isdir(branch_path) and branch_name != '.backup':
                    commits_index_file = os.path.join(branch_path, 'commits_index.json')
                    
                    if not os.path.exists(commits_index_file):
                        result['issues'].append(f'Missing commits_index.json for branch {branch_name}')
                        # Restore from filesystem
                        commits_data = DFM_IndexManager.create_commits_index(
                            os.path.basename(mesh_dir), branch_name
                        )
                        with open(commits_index_file, 'w') as f:
                            json.dump(commits_data, f, indent=2)
                        result['restored'].append(f'commits_index.json for branch {branch_name}')
                    else:
                        # Validate commits index content
                        try:
                            with open(commits_index_file, 'r') as f:
                                commits_data = json.load(f)
                            if 'commits' not in commits_data:
                                raise ValueError("Invalid commits index structure")
                        except (json.JSONDecodeError, ValueError) as e:
                            result['issues'].append(f'Corrupted commits_index.json for branch {branch_name}: {e}')
                            # Restore from filesystem
                            commits_data = DFM_IndexManager.create_commits_index(
                                os.path.basename(mesh_dir), branch_name
                            )
                            with open(commits_index_file, 'w') as f:
                                json.dump(commits_data, f, indent=2)
                            result['restored'].append(f'commits_index.json for branch {branch_name}')
                    
                    # Check individual commits for corruption
                    for commit_dir in os.listdir(branch_path):
                        commit_path = os.path.join(branch_path, commit_dir)
                        if os.path.isdir(commit_path):
                            commit_file = os.path.join(commit_path, "commit.json")
                            if os.path.exists(commit_file):
                                try:
                                    with open(commit_file, 'r') as f:
                                        commit_data = json.load(f)
                                    if 'timestamp' not in commit_data:
                                        result['corrupted_commits'].append({
                                            'branch': branch_name,
                                            'commit': commit_dir,
                                            'issue': 'Missing timestamp'
                                        })
                                except (json.JSONDecodeError, IOError) as e:
                                    result['corrupted_commits'].append({
                                        'branch': branch_name,
                                        'commit': commit_dir,
                                        'issue': f'Corrupted commit file: {e}'
                                    })
            
            # Set overall validity
            if result['issues'] or result['corrupted_commits']:
                result['valid'] = False
            
            logger.info(f"Data integrity validation completed for {mesh_dir}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to validate data integrity for {mesh_dir}: {e}")
            result['valid'] = False
            result['issues'].append(f'Validation error: {e}')
            return result
    
    @staticmethod
    def backup_indices(mesh_dir: str) -> bool:
        """
        Creates backups of critical index files.
        
        Args:
            mesh_dir: Path to the mesh directory
            
        Returns:
            True if backup successful, False otherwise
        """
        if not os.path.exists(mesh_dir):
            logger.warning(f"Mesh directory does not exist: {mesh_dir}")
            return False
        
        try:
            backup_dir = os.path.join(mesh_dir, '.backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup branches index
            branches_index_file = os.path.join(mesh_dir, 'branches_index.json')
            if os.path.exists(branches_index_file):
                backup_file = os.path.join(backup_dir, 'branches_index.json.backup')
                shutil.copy2(branches_index_file, backup_file)
                logger.debug(f"Backed up branches_index.json")
            
            # Backup current branch file
            current_branch_file = os.path.join(mesh_dir, 'current_branch.json')
            if os.path.exists(current_branch_file):
                backup_file = os.path.join(backup_dir, 'current_branch.json.backup')
                shutil.copy2(current_branch_file, backup_file)
                logger.debug(f"Backed up current_branch.json")
            
            # Backup commits indices for each branch
            for branch_name in os.listdir(mesh_dir):
                branch_path = os.path.join(mesh_dir, branch_name)
                if os.path.isdir(branch_path) and branch_name != '.backup':
                    commits_index_file = os.path.join(branch_path, 'commits_index.json')
                    if os.path.exists(commits_index_file):
                        branch_backup_dir = os.path.join(backup_dir, branch_name)
                        os.makedirs(branch_backup_dir, exist_ok=True)
                        backup_file = os.path.join(branch_backup_dir, 'commits_index.json.backup')
                        shutil.copy2(commits_index_file, backup_file)
                        logger.debug(f"Backed up commits_index.json for branch {branch_name}")
            
            logger.info(f"Successfully backed up indices for {mesh_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup indices for {mesh_dir}: {e}")
            return False
    
    @staticmethod
    def restore_from_backup(mesh_dir: str) -> bool:
        """
        Restore index files from backup.
        
        Args:
            mesh_dir: Path to the mesh directory
            
        Returns:
            True if restoration successful, False otherwise
        """
        backup_dir = os.path.join(mesh_dir, '.backup')
        if not os.path.exists(backup_dir):
            logger.warning(f"Backup directory does not exist: {backup_dir}")
            return False
        
        try:
            restored_count = 0
            
            # Restore branches index
            backup_file = os.path.join(backup_dir, 'branches_index.json.backup')
            if os.path.exists(backup_file):
                target_file = os.path.join(mesh_dir, 'branches_index.json')
                shutil.copy2(backup_file, target_file)
                restored_count += 1
                logger.debug(f"Restored branches_index.json")
            
            # Restore current branch file
            backup_file = os.path.join(backup_dir, 'current_branch.json.backup')
            if os.path.exists(backup_file):
                target_file = os.path.join(mesh_dir, 'current_branch.json')
                shutil.copy2(backup_file, target_file)
                restored_count += 1
                logger.debug(f"Restored current_branch.json")
            
            # Restore commits indices for each branch
            for branch_name in os.listdir(backup_dir):
                branch_backup_path = os.path.join(backup_dir, branch_name)
                if os.path.isdir(branch_backup_path):
                    backup_file = os.path.join(branch_backup_path, 'commits_index.json.backup')
                    if os.path.exists(backup_file):
                        branch_path = os.path.join(mesh_dir, branch_name)
                        os.makedirs(branch_path, exist_ok=True)
                        target_file = os.path.join(branch_path, 'commits_index.json')
                        shutil.copy2(backup_file, target_file)
                        restored_count += 1
                        logger.debug(f"Restored commits_index.json for branch {branch_name}")
            
            logger.info(f"Successfully restored {restored_count} index files from backup")
            return restored_count > 0
            
        except Exception as e:
            logger.error(f"Failed to restore from backup for {mesh_dir}: {e}")
            return False
