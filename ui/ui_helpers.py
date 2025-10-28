"""
UI helper functions and utilities for Difference Engine addon
"""
import bpy
import logging
import os
from typing import Optional, Any, Dict
from ..classes.version_manager import DFM_VersionManager

# Setup logging
logger = logging.getLogger(__name__)


class DFM_UIHelpers:
    """Helper methods for common UI patterns"""
    
    @staticmethod
    def draw_box_header(box: bpy.types.UILayout, text: str, icon: str = 'NONE') -> None:
        """Draw a consistent box header"""
        row = box.row()
        row.label(text=text, icon=icon)
    
    @staticmethod
    def draw_property_row(box: bpy.types.UILayout, scene: bpy.types.Scene, 
                         prop_name: str, label: Optional[str] = None, 
                         enabled: bool = True) -> bpy.types.UILayout:
        """Draw a property in a row"""
        row = box.row()
        row.enabled = enabled
        if label:
            row.prop(scene, prop_name, text=label)
        else:
            row.prop(scene, prop_name)
        return row
    
    @staticmethod
    def draw_operator_button(layout: bpy.types.UILayout, operator_id: str, 
                           text: str, icon: str = 'NONE', 
                           enabled: bool = True) -> bpy.types.UILayout:
        """Draw an operator button"""
        row = layout.row()
        row.enabled = enabled
        row.operator(operator_id, text=text, icon=icon)
        return row
    
    @staticmethod
    def draw_object_info(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
        """Draw object information"""
        box = layout.box()
        col = box.column(align=True)
        col.label(text=f"Object: {obj.name}", icon='OBJECT_DATA')
        col.label(text=f"Vertices: {len(obj.data.vertices)}", icon='VERTEXSEL')
        col.label(text=f"Faces: {len(obj.data.polygons)}", icon='FACESEL')
    
    @staticmethod
    def draw_export_options(layout: bpy.types.UILayout, scene: bpy.types.Scene) -> None:
        """Draw export options section"""
        box = layout.box()
        DFM_UIHelpers.draw_box_header(box, "Export Options", 'EXPORT')
        
        col = box.column(align=True)
        col.prop(scene, "dfm_export_all", text="Export All Components")
        
        if not scene.dfm_export_all:
            col.separator()
            # Create two columns for better organization
            split = col.split(factor=0.5)
            
            col_left = split.column(align=True)
            col_left.prop(scene, "dfm_export_geometry", text="Geometry", icon='MESH_DATA')
            col_left.prop(scene, "dfm_export_materials", text="Materials", icon='MATERIAL')
            
            col_right = split.column(align=True)
            col_right.prop(scene, "dfm_export_transform", text="Transform", icon='ORIENTATION_LOCAL')
            col_right.prop(scene, "dfm_export_uv", text="UV Layout", icon='UV')
    
    @staticmethod
    def draw_import_options(layout: bpy.types.UILayout, scene: bpy.types.Scene, 
                           import_mode: str = 'AUTO') -> None:
        """Draw import options section"""
        box = layout.box()
        DFM_UIHelpers.draw_box_header(box, "Import Components", 'IMPORT')
        
        col = box.column(align=True)
        col.prop(scene, "dfm_import_all", text="Import All Components")
        
        if not scene.dfm_import_all:
            col.separator()
            # Create two columns for better organization
            split = col.split(factor=0.5)
            
            col_left = split.column(align=True)
            row = col_left.row()
            row.prop(scene, "dfm_import_geometry", text="Geometry", icon='MESH_DATA')
            # Disable geometry if applying to selected
            if import_mode == 'SELECTED':
                row.enabled = False
            
            col_left.prop(scene, "dfm_import_materials", text="Materials", icon='MATERIAL')
            
            col_right = split.column(align=True)
            col_right.prop(scene, "dfm_import_uv", text="UV Layout", icon='UV')
            col_right.prop(scene, "dfm_import_transform", text="Transform", icon='ORIENTATION_LOCAL')
    
    @staticmethod
    def draw_version_control(layout: bpy.types.UILayout, scene: bpy.types.Scene) -> None:
        """Draw version control options"""
        box = layout.box()
        DFM_UIHelpers.draw_box_header(box, "Version Control", 'BOOKMARKS')
        
        col = box.column(align=True)
        
        # Branch info
        row = col.row(align=True)
        row.label(text="Branch:", icon='OUTLINER')
        row.label(text=scene.dfm_current_branch or 'main')
        
        col.separator()
        
        # Auto-compression option
        col.prop(scene, "dfm_auto_snapshot", text="Auto-compress Old Versions", icon='PACKAGE')
    
    @staticmethod
    def draw_commit_section(layout: bpy.types.UILayout, scene: bpy.types.Scene) -> None:
        """Draw commit message and tag section"""
        box = layout.box()
        DFM_UIHelpers.draw_box_header(box, "Commit Information", 'TEXT')
        
        col = box.column(align=True)
        col.prop(scene, "dfm_commit_tag", text="Tag (Optional)", icon='BOOKMARKS')
        col.separator()
        col.label(text="Message:", icon='WORDWRAP_ON')
        col.prop(scene, "dfm_commit_message", text="")
    
    @staticmethod
    def draw_export_button(layout: bpy.types.UILayout, scene: bpy.types.Scene) -> None:
        """Draw the main export button"""
        has_message = bool(scene.dfm_commit_message.strip())
        
        row = layout.row()
        row.scale_y = 1.5
        row.enabled = has_message
        row.operator("object.save_geometry", text="Export Geometry", icon='EXPORT')
        
        if not has_message:
            row = layout.row()
            row.label(text="Commit message required", icon='INFO')


def refresh_commit_list(context: bpy.types.Context) -> bool:
    """Helper function to refresh commit list (can be called from draw or execute)"""
    active_obj = context.active_object
    scene = context.scene
    
    if not active_obj or active_obj.type != 'MESH':
        return False
    
    try:
        # Clear existing list
        scene.dfm_commit_list.clear()
        
        # Get current branch
        current_branch = scene.dfm_current_branch or ""
        
        # If no current branch, return empty list
        if not current_branch:
            logger.info(f"No current branch set for {active_obj.name}")
            return True
        
        # Get history for current branch only
        history = DFM_VersionManager.get_branch_history(active_obj.name, current_branch)
        
        # Populate list
        for commit in history:
            item = scene.dfm_commit_list.add()
            item.commit_path = commit['commit_path']
            item.timestamp = commit['timestamp']
            item.commit_message = commit['commit_message']
            item.tag = commit.get('tag', '')
            item.branch = commit.get('branch', current_branch)
        
        # Reset selection
        scene.dfm_commit_list_index = 0
        
        logger.info(f"Refreshed commit list for {active_obj.name} branch '{current_branch}': {len(history)} commits")
        return True
        
    except Exception as e:
        logger.error(f"Failed to refresh commit list: {e}")
        return False


def refresh_branch_list(context: bpy.types.Context) -> bool:
    """Helper function to refresh branch list (can be called from draw or execute)"""
    active_obj = context.active_object
    scene = context.scene
    
    if not active_obj or active_obj.type != 'MESH':
        return False
    
    try:
        # Clear existing list
        scene.dfm_branch_list.clear()
        
        # Get branches
        branches = DFM_VersionManager.get_object_branches(active_obj.name)
        
        # If no branches, don't set any default branch
        if not branches:
            logger.info(f"No branches found for {active_obj.name}")
            return True
        
        # Only load saved current branch if we have branches and it's not already set
        if not scene.dfm_current_branch:
            saved_branch = DFM_VersionManager.load_current_branch(active_obj.name)
            if saved_branch:
                scene.dfm_current_branch = saved_branch
            else:
                # No saved branch, clear it
                scene.dfm_current_branch = ""
        
        current_branch = scene.dfm_current_branch or ""
        
        # Populate list
        for branch_data in branches:
            item = scene.dfm_branch_list.add()
            item.branch_name = branch_data['name']
            item.commit_count = branch_data['commit_count']
            item.last_commit = branch_data.get('last_commit', '')
            item.is_current = (branch_data['name'] == current_branch)
        
        # Reset selection
        scene.dfm_branch_list_index = 0
        
        logger.info(f"Refreshed branch list for {active_obj.name}: {len(branches)} branches")
        return True
        
    except Exception as e:
        logger.error(f"Failed to refresh branch list: {e}")
        return False


def load_saved_branch_on_startup(scene: bpy.types.Scene) -> None:
    """Handler to load saved branch when Blender starts up"""
    try:
        # Only run if we have an active object and it's a mesh
        if not bpy.context.active_object or bpy.context.active_object.type != 'MESH':
            return
        
        # Load saved branch and refresh UI
        mesh_name = bpy.context.active_object.name
        saved_branch = DFM_VersionManager.load_current_branch(mesh_name)
        if saved_branch and saved_branch != 'main':
            scene.dfm_current_branch = saved_branch
            # Refresh the branch list UI to show the loaded branch as current
            refresh_branch_list(bpy.context)
            logger.info(f"Loaded saved branch '{saved_branch}' for {mesh_name} on startup")
    except Exception as e:
        # Silently handle errors to avoid spam in console
        logger.debug(f"Startup branch loading failed: {e}")


# Global variable to track last loaded object
_last_loaded_object: Optional[str] = None


def load_saved_branch_on_object_change(scene: bpy.types.Scene) -> None:
    """Handler to load saved branch when object changes"""
    try:
        # Only run if we have an active object and it's a mesh
        if not bpy.context.active_object or bpy.context.active_object.type != 'MESH':
            return
        
        global _last_loaded_object
        current_obj = bpy.context.active_object.name
        
        # Always load branch info for new object (don't check if it changed)
        if current_obj != _last_loaded_object:
            mesh_name = current_obj
            
            # Check if mesh has any versions
            branches = DFM_VersionManager.get_object_branches(mesh_name)
            
            if not branches:
                # No versions, clear current branch
                scene.dfm_current_branch = ""
                logger.info(f"No versions found for {mesh_name}, cleared current branch")
            else:
                # Load saved branch from file
                saved_branch = DFM_VersionManager.load_current_branch(mesh_name)
                if saved_branch:
                    scene.dfm_current_branch = saved_branch
                else:
                    scene.dfm_current_branch = ""
                
                logger.info(f"Loaded branch '{saved_branch or 'None'}' for {mesh_name} on object change")
            
            # Refresh the branch and commit lists
            refresh_branch_list(bpy.context)
            refresh_commit_list(bpy.context)
            
            _last_loaded_object = current_obj
            
    except Exception as e:
        # Silently handle errors to avoid spam in console
        logger.debug(f"Object change branch loading failed: {e}")


