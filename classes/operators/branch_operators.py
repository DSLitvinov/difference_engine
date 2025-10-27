"""
Branch management operators
"""
import bpy
import os
from ..utils import sanitize_path_component


class DFM_CreateBranchOperator(bpy.types.Operator):
    """Create a new branch"""
    bl_idname = "object.create_branch"
    bl_label = "Create Branch"
    
    branch_name: bpy.props.StringProperty(name="Branch Name", default="new-feature")
    
    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        # Validate that the .blend file has been saved
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        # Create branch directory with sanitized names
        base_dir = bpy.path.abspath("//.difference_machine/")
        mesh_dir = os.path.join(base_dir, sanitize_path_component(active_obj.name))
        branch_dir = os.path.join(mesh_dir, sanitize_path_component(self.branch_name))
        
        if not os.path.exists(branch_dir):
            os.makedirs(branch_dir, exist_ok=True)
            scene.dfm_current_branch = self.branch_name
            
            # Save the current branch to persist across restarts
            from ..version_manager import DFM_VersionManager
            DFM_VersionManager.save_current_branch(active_obj.name, self.branch_name)
            
            # Update index to include the new branch
            from ..index_manager import DFM_IndexManager
            DFM_IndexManager.update_all_indices(active_obj.name)
            
            # Refresh the branch list to show the new branch
            from ...ui.ui_helpers import refresh_branch_list
            refresh_branch_list(context)
            
            self.report({'INFO'}, f"Created branch: {self.branch_name}")
        else:
            self.report({'WARNING'}, f"Branch already exists: {self.branch_name}")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class DFM_SwitchBranchOperator(bpy.types.Operator):
    """Switch to the selected branch from the UI list"""
    bl_idname = "object.switch_branch"
    bl_label = "Switch Branch"
    
    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        # Validate that the .blend file has been saved
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        # Check if we have a selected branch
        if not scene.dfm_branch_list or scene.dfm_branch_list_index < 0 or scene.dfm_branch_list_index >= len(scene.dfm_branch_list):
            self.report({'ERROR'}, "Please select a branch from the list")
            return {'CANCELLED'}
        
        # Get the selected branch
        selected_branch = scene.dfm_branch_list[scene.dfm_branch_list_index]
        branch_name = selected_branch.branch_name
        
        # Check if branch exists (with sanitized names)
        base_dir = bpy.path.abspath("//.difference_machine/")
        mesh_dir = os.path.join(base_dir, sanitize_path_component(active_obj.name))
        branch_dir = os.path.join(mesh_dir, sanitize_path_component(branch_name))
        
        if not os.path.exists(branch_dir):
            self.report({'ERROR'}, f"Branch does not exist: {branch_name}")
            return {'CANCELLED'}
        
        # Switch to the branch
        scene.dfm_current_branch = branch_name
        self.report({'INFO'}, f"Switched to branch: {branch_name}")
        
        # Save the current branch to persist across restarts
        from ..version_manager import DFM_VersionManager
        DFM_VersionManager.save_current_branch(active_obj.name, branch_name)
        
        # Refresh the branch list to update the current branch status
        # Clear existing list
        scene.dfm_branch_list.clear()
        
        # Get branches
        branches = DFM_VersionManager.get_object_branches(active_obj.name)
        current_branch = scene.dfm_current_branch or 'main'
        
        # Populate list
        for branch_data in branches:
            item = scene.dfm_branch_list.add()
            item.branch_name = branch_data['name']
            item.commit_count = branch_data['commit_count']
            item.last_commit = branch_data.get('last_commit', '')
            item.is_current = (branch_data['name'] == current_branch)
        
        # Reset selection
        scene.dfm_branch_list_index = 0
        
        return {'FINISHED'}


class DFM_ListBranchesOperator(bpy.types.Operator):
    """List all available branches for current object"""
    bl_idname = "object.list_branches"
    bl_label = "List Branches"
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        # Validate that the .blend file has been saved
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        base_dir = bpy.path.abspath("//.difference_machine/")
        mesh_dir = os.path.join(base_dir, sanitize_path_component(active_obj.name))
        
        if not os.path.exists(mesh_dir):
            self.report({'INFO'}, "No branches found - no versions saved yet")
            return {'FINISHED'}
        
        branches = [d for d in os.listdir(mesh_dir) if os.path.isdir(os.path.join(mesh_dir, d))]
        
        if branches:
            branches_str = ", ".join(branches)
            self.report({'INFO'}, f"Available branches: {branches_str}")
        else:
            self.report({'INFO'}, "No branches found")
        
        return {'FINISHED'}


class DFM_DeleteBranchOperator(bpy.types.Operator):
    """Delete the selected branch from the UI list"""
    bl_idname = "object.delete_branch"
    bl_label = "Delete Branch"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        # Validate that the .blend file has been saved
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        # Check if we have a selected branch
        if not scene.dfm_branch_list or scene.dfm_branch_list_index < 0 or scene.dfm_branch_list_index >= len(scene.dfm_branch_list):
            self.report({'ERROR'}, "Please select a branch from the list")
            return {'CANCELLED'}
        
        # Get the selected branch
        selected_branch = scene.dfm_branch_list[scene.dfm_branch_list_index]
        branch_name = selected_branch.branch_name
        
        # Don't allow deleting the main branch
        if branch_name == 'main':
            self.report({'ERROR'}, "Cannot delete the main branch")
            return {'CANCELLED'}
        
        # Check if this is the current branch
        if branch_name == scene.dfm_current_branch:
            self.report({'ERROR'}, "Cannot delete the current branch. Switch to another branch first.")
            return {'CANCELLED'}
        
        # Check if branch exists (with sanitized names)
        base_dir = bpy.path.abspath("//.difference_machine/")
        mesh_dir = os.path.join(base_dir, sanitize_path_component(active_obj.name))
        branch_dir = os.path.join(mesh_dir, sanitize_path_component(branch_name))
        
        if not os.path.exists(branch_dir):
            self.report({'ERROR'}, f"Branch does not exist: {branch_name}")
            return {'CANCELLED'}
        
        # Delete the branch directory
        try:
            import shutil
            shutil.rmtree(branch_dir)
            self.report({'INFO'}, f"Deleted branch: {branch_name}")
            
            # Update index to remove the deleted branch
            from ..index_manager import DFM_IndexManager
            DFM_IndexManager.update_all_indices(active_obj.name)
            
            # Refresh the branch list
            from ...ui.ui_helpers import refresh_branch_list
            refresh_branch_list(context)
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to delete branch: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """Show confirmation dialog before deleting"""
        scene = context.scene
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        # Check if we have a selected branch
        if not scene.dfm_branch_list or scene.dfm_branch_list_index < 0 or scene.dfm_branch_list_index >= len(scene.dfm_branch_list):
            self.report({'ERROR'}, "Please select a branch from the list")
            return {'CANCELLED'}
        
        # Get the selected branch
        selected_branch = scene.dfm_branch_list[scene.dfm_branch_list_index]
        branch_name = selected_branch.branch_name
        
        # Don't allow deleting the main branch
        if branch_name == 'main':
            self.report({'ERROR'}, "Cannot delete the main branch")
            return {'CANCELLED'}
        
        # Check if this is the current branch
        if branch_name == scene.dfm_current_branch:
            self.report({'ERROR'}, "Cannot delete the current branch. Switch to another branch first.")
            return {'CANCELLED'}
        
        # Show confirmation dialog
        return context.window_manager.invoke_confirm(self, event)


class DFM_GoToBranchOperator(bpy.types.Operator):
    """Switch to the selected branch from the UI list"""
    bl_idname = "object.go_to_branch"
    bl_label = "Go to Branch"
    
    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "Please select an object")
            return {'CANCELLED'}
        
        # Validate that the .blend file has been saved
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        # Check if we have a selected branch
        if not scene.dfm_branch_list or scene.dfm_branch_list_index < 0 or scene.dfm_branch_list_index >= len(scene.dfm_branch_list):
            self.report({'ERROR'}, "Please select a branch from the list")
            return {'CANCELLED'}
        
        # Get the selected branch
        selected_branch = scene.dfm_branch_list[scene.dfm_branch_list_index]
        branch_name = selected_branch.branch_name
        
        # Check if branch exists (with sanitized names)
        base_dir = bpy.path.abspath("//.difference_machine/")
        mesh_dir = os.path.join(base_dir, sanitize_path_component(active_obj.name))
        branch_dir = os.path.join(mesh_dir, sanitize_path_component(branch_name))
        
        if not os.path.exists(branch_dir):
            self.report({'ERROR'}, f"Branch does not exist: {branch_name}")
            return {'CANCELLED'}
        
        # Switch to the branch
        scene.dfm_current_branch = branch_name
        self.report({'INFO'}, f"Switched to branch: {branch_name}")
        
        return {'FINISHED'}

