"""
UI operator classes for Difference Engine addon
"""
import bpy
import logging
from .ui_helpers import refresh_commit_list, refresh_branch_list, load_saved_branch_on_startup, load_saved_branch_on_object_change
from ..classes.version_manager import DFM_VersionManager
from ..classes.error_handler import DFM_ErrorHandler, DFM_Error, DFM_ErrorType

# Setup logging
logger = logging.getLogger(__name__)


class DFM_RefreshCommits_OT_operator(bpy.types.Operator):
    """Refresh commit list for current object"""
    bl_idname = "object.dfm_refresh_commits"
    bl_label = "Refresh Commits"
    bl_options = {'INTERNAL'}
    
    def execute(self, context: bpy.types.Context) -> set:
        try:
            DFM_ErrorHandler.log_operation_start("refresh_commits")
            
            active_obj = context.active_object
            scene = context.scene
            
            if not active_obj or active_obj.type != 'MESH':
                raise DFM_Error("Please select a mesh object", DFM_ErrorType.VALIDATION_ERROR)
            
            # Check if we have a current branch
            current_branch = scene.dfm_current_branch or ""
            if not current_branch:
                self.report({'WARNING'}, "No current branch selected. Please select a branch first.")
                return {'CANCELLED'}
            
            if refresh_commit_list(context):
                # Track which object we loaded for
                context.scene["dfm_last_obj_name"] = active_obj.name
                
                DFM_ErrorHandler.log_operation_success("refresh_commits", {'object': active_obj.name})
                self.report({'INFO'}, f"Refreshed history for branch '{current_branch}'")
                return {'FINISHED'}
            
            DFM_ErrorHandler.log_operation_failure("refresh_commits", 
                                                 DFM_Error("Failed to refresh commit list", DFM_ErrorType.UI_ERROR))
            return {'CANCELLED'}
            
        except Exception as e:
            return DFM_ErrorHandler.handle_operator_error(self, e, "refresh_commits")


class DFM_RefreshBranches_OT_operator(bpy.types.Operator):
    """Refresh branch list for current object and load saved branch"""
    bl_idname = "object.dfm_refresh_branches"
    bl_label = "Refresh Branches"
    bl_options = {'INTERNAL'}
    
    def execute(self, context: bpy.types.Context) -> set:
        try:
            DFM_ErrorHandler.log_operation_start("refresh_branches")
            
            active_obj = context.active_object
            scene = context.scene
            
            if not active_obj or active_obj.type != 'MESH':
                raise DFM_Error("Please select a mesh object", DFM_ErrorType.VALIDATION_ERROR)
            
            # Load saved branch first
            mesh_name = active_obj.name
            saved_branch = DFM_VersionManager.load_current_branch(mesh_name)
            
            if saved_branch:
                scene.dfm_current_branch = saved_branch
                self.report({'INFO'}, f"Loaded saved branch: {saved_branch}")
            else:
                # If no saved branch, clear it
                scene.dfm_current_branch = ""
                self.report({'INFO'}, "No saved branch found")
            
            # Now refresh the branch list with the loaded branch
            if refresh_branch_list(context):
                # Also refresh commit list to show commits from current branch
                refresh_commit_list(context)
                # Track which object we loaded for
                context.scene["dfm_last_branch_obj_name"] = active_obj.name
                
                DFM_ErrorHandler.log_operation_success("refresh_branches", {
                    'object': mesh_name,
                    'branch': saved_branch or 'None'
                })
                return {'FINISHED'}
            
            DFM_ErrorHandler.log_operation_failure("refresh_branches", 
                                                 DFM_Error("Failed to refresh branch list", DFM_ErrorType.UI_ERROR))
            return {'CANCELLED'}
            
        except Exception as e:
            return DFM_ErrorHandler.handle_operator_error(self, e, "refresh_branches")


class DFM_LoadSavedBranch_OT_operator(bpy.types.Operator):
    """Manually load saved branch for current object"""
    bl_idname = "object.dfm_load_saved_branch"
    bl_label = "Load Saved Branch"
    bl_options = {'INTERNAL'}
    
    def execute(self, context: bpy.types.Context) -> set:
        try:
            DFM_ErrorHandler.log_operation_start("load_saved_branch")
            
            active_obj = context.active_object
            scene = context.scene
            
            if not active_obj or active_obj.type != 'MESH':
                raise DFM_Error("Please select a mesh object", DFM_ErrorType.VALIDATION_ERROR)
            
            # Load saved branch
            mesh_name = active_obj.name
            saved_branch = DFM_VersionManager.load_current_branch(mesh_name)
            
            if saved_branch:
                scene.dfm_current_branch = saved_branch
                # Refresh the branch list UI to show the loaded branch as current
                refresh_branch_list(context)
                refresh_commit_list(context)
                self.report({'INFO'}, f"Loaded saved branch: {saved_branch}")
                
                DFM_ErrorHandler.log_operation_success("load_saved_branch", {
                    'object': mesh_name,
                    'branch': saved_branch
                })
            else:
                self.report({'INFO'}, "No saved branch found")
                scene.dfm_current_branch = ""
                refresh_branch_list(context)
                refresh_commit_list(context)
                
                DFM_ErrorHandler.log_operation_success("load_saved_branch", {
                    'object': mesh_name,
                    'branch': 'None'
                })
            
            return {'FINISHED'}
            
        except Exception as e:
            return DFM_ErrorHandler.handle_operator_error(self, e, "load_saved_branch")
