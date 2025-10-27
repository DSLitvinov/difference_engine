"""
Index management operators
"""
import bpy
import os
from ..index_manager import DFM_IndexManager
from ..version_manager import DFM_VersionManager


class DFM_UpdateIndicesOperator(bpy.types.Operator):
    """Update all index files for quick search"""
    bl_idname = "object.dfm_update_indices"
    bl_label = "Update Indices"
    bl_description = "Update all index files for faster search and navigation"
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        mesh_name = active_obj.name
        
        try:
            if DFM_IndexManager.update_all_indices(mesh_name):
                self.report({'INFO'}, f"Updated indices for {mesh_name}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Failed to update indices for {mesh_name}")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error updating indices: {str(e)}")
            return {'CANCELLED'}


class DFM_ValidateIntegrityOperator(bpy.types.Operator):
    """Validate data integrity and restore if necessary"""
    bl_idname = "object.dfm_validate_integrity"
    bl_label = "Validate Integrity"
    bl_description = "Check data integrity and restore corrupted index files"
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        mesh_name = active_obj.name
        mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
        
        try:
            result = DFM_IndexManager.validate_data_integrity(mesh_dir)
            
            if result['valid']:
                self.report({'INFO'}, f"Data integrity check passed for {mesh_name}")
            else:
                issues_count = len(result['issues'])
                restored_count = len(result['restored'])
                corrupted_count = len(result['corrupted_commits'])
                
                message = f"Found {issues_count} issues, restored {restored_count} files"
                if corrupted_count > 0:
                    message += f", {corrupted_count} corrupted commits"
                
                self.report({'WARNING'}, message)
                
                # Show detailed issues in console
                if result['issues']:
                    print(f"Integrity issues for {mesh_name}:")
                    for issue in result['issues']:
                        print(f"  - {issue}")
                
                if result['restored']:
                    print(f"Restored files for {mesh_name}:")
                    for restored in result['restored']:
                        print(f"  + {restored}")
                
                if result['corrupted_commits']:
                    print(f"Corrupted commits for {mesh_name}:")
                    for commit in result['corrupted_commits']:
                        print(f"  ! {commit['branch']}/{commit['commit']}: {commit['issue']}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error validating integrity: {str(e)}")
            return {'CANCELLED'}


class DFM_BackupIndicesOperator(bpy.types.Operator):
    """Backup critical index files"""
    bl_idname = "object.dfm_backup_indices"
    bl_label = "Backup Indices"
    bl_description = "Create backups of critical index files"
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        mesh_name = active_obj.name
        mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
        
        try:
            if DFM_IndexManager.backup_indices(mesh_dir):
                self.report({'INFO'}, f"Backed up indices for {mesh_name}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Failed to backup indices for {mesh_name}")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error backing up indices: {str(e)}")
            return {'CANCELLED'}


class DFM_RestoreFromBackupOperator(bpy.types.Operator):
    """Restore index files from backup"""
    bl_idname = "object.dfm_restore_from_backup"
    bl_label = "Restore from Backup"
    bl_description = "Restore index files from backup"
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        mesh_name = active_obj.name
        mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
        
        try:
            if DFM_IndexManager.restore_from_backup(mesh_dir):
                self.report({'INFO'}, f"Restored indices from backup for {mesh_name}")
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, f"No backup found or failed to restore for {mesh_name}")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error restoring from backup: {str(e)}")
            return {'CANCELLED'}


class DFM_QuickSearchOperator(bpy.types.Operator):
    """Quick search through commits and branches"""
    bl_idname = "object.dfm_quick_search"
    bl_label = "Quick Search"
    bl_description = "Search through commits and branches using indices"
    
    search_query: bpy.props.StringProperty(
        name="Search Query",
        description="Search for commits by message, author, or timestamp",
        default=""
    )
    
    search_type: bpy.props.EnumProperty(
        name="Search Type",
        description="Type of search to perform",
        items=[
            ('COMMITS', "Commits", "Search in commit messages and metadata"),
            ('BRANCHES', "Branches", "Search in branch names"),
            ('ALL', "All", "Search in both commits and branches")
        ],
        default='ALL'
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        if not self.search_query.strip():
            self.report({'ERROR'}, "Please enter a search query")
            return {'CANCELLED'}
        
        mesh_name = active_obj.name
        query = self.search_query.lower().strip()
        
        try:
            results = []
            
            if self.search_type in ['COMMITS', 'ALL']:
                # Search in commits
                branches_index = DFM_IndexManager.load_index(mesh_name, 'branches_index')
                if branches_index and 'branches' in branches_index:
                    for branch in branches_index['branches']:
                        branch_name = branch['name']
                        commits_index = DFM_IndexManager.load_index(mesh_name, f'commits_index_{branch_name}')
                        if not commits_index:
                            # Try loading from branch directory
                            mesh_dir = DFM_IndexManager.get_mesh_dir(mesh_name)
                            branch_path = os.path.join(mesh_dir, branch_name)
                            commits_file = os.path.join(branch_path, 'commits_index.json')
                            if os.path.exists(commits_file):
                                import json
                                with open(commits_file, 'r') as f:
                                    commits_index = json.load(f)
                        
                        if commits_index and 'commits' in commits_index:
                            for commit in commits_index['commits']:
                                # Search in message, author, and timestamp
                                if (query in commit.get('message', '').lower() or
                                    query in commit.get('author', '').lower() or
                                    query in commit.get('timestamp', '').lower()):
                                    results.append({
                                        'type': 'commit',
                                        'branch': branch_name,
                                        'timestamp': commit.get('timestamp', ''),
                                        'message': commit.get('message', ''),
                                        'author': commit.get('author', ''),
                                        'path': commit.get('path', '')
                                    })
            
            if self.search_type in ['BRANCHES', 'ALL']:
                # Search in branches
                branches_index = DFM_IndexManager.load_index(mesh_name, 'branches_index')
                if branches_index and 'branches' in branches_index:
                    for branch in branches_index['branches']:
                        if query in branch['name'].lower():
                            results.append({
                                'type': 'branch',
                                'name': branch['name'],
                                'commit_count': branch['commit_count'],
                                'last_commit': branch['last_commit_timestamp']
                            })
            
            # Display results
            if results:
                print(f"\nSearch results for '{self.search_query}' in {mesh_name}:")
                for i, result in enumerate(results[:20]):  # Limit to 20 results
                    if result['type'] == 'commit':
                        print(f"  {i+1}. COMMIT [{result['branch']}] {result['timestamp']}")
                        print(f"     Message: {result['message']}")
                        print(f"     Author: {result['author']}")
                    else:
                        print(f"  {i+1}. BRANCH: {result['name']} ({result['commit_count']} commits)")
                
                if len(results) > 20:
                    print(f"  ... and {len(results) - 20} more results")
                
                self.report({'INFO'}, f"Found {len(results)} results for '{self.search_query}'")
            else:
                self.report({'INFO'}, f"No results found for '{self.search_query}'")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error during search: {str(e)}")
            return {'CANCELLED'}
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column()
        col.prop(self, "search_query")
        col.prop(self, "search_type")
        
        layout.separator()
        layout.label(text="Search will look in commit messages, authors, timestamps, and branch names.", icon='INFO')
