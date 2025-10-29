"""
UI panels for Difference Engine addon
"""
import bpy
import os
import logging
from typing import Optional
from .ui_helpers import DFM_UIHelpers, refresh_commit_list, refresh_branch_list
from ..classes.version_manager import DFM_VersionManager

# Setup logging
logger = logging.getLogger(__name__)

class DFM_Export_PT_panel(bpy.types.Panel):
    """Main export panel for Difference Machine"""
    bl_idname = 'DFM_PT_panel_new_version'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Difference Machine'
    bl_label = 'Make commit'
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode in {'OBJECT', 'EDIT_MESH'}
    
    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        active_obj = context.active_object
        
        if not active_obj or active_obj.type != 'MESH':
            box = layout.box()
            box.label(text="Select a mesh object to export", icon='INFO')
            return
        
        # Object info
        DFM_UIHelpers.draw_object_info(layout, active_obj)
        
        # Export options
        DFM_UIHelpers.draw_export_options(layout, scene)
        
        # Branch info (show which branch user is committing to)
        DFM_UIHelpers.draw_version_control(layout, scene)
        
        # Commit section
        DFM_UIHelpers.draw_commit_section(layout, scene)
        
        # Export button
        DFM_UIHelpers.draw_export_button(layout, scene)


class DFM_History_PT_panel(bpy.types.Panel):
    """Version history panel"""
    bl_idname = 'DFM_PT_panel_history'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Difference Machine'
    bl_label = 'Version History'
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object and context.active_object.type == 'MESH'
    
    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        active_obj = context.active_object
        
        # Refresh button
        row = layout.row()
        row.operator("object.dfm_refresh_commits", text="Refresh History", icon='FILE_REFRESH')
        
        # Auto-refresh if object changed (track by name)
        current_obj_name = active_obj.name if active_obj else ""
        last_obj_name = scene.get("dfm_last_obj_name", "")
        
        if current_obj_name != last_obj_name and active_obj and active_obj.type == 'MESH':
            # Object changed - need to refresh (but can't do it here)
            # Just show a notice
            box = layout.box()
            box.label(text=f"Object changed to: {current_obj_name}", icon='INFO')
            box.label(text="Click 'Refresh History' to load versions", icon='HAND')
            return
        
        # Check if we have a current branch
        current_branch = scene.dfm_current_branch or ""
        if not current_branch:
            box = layout.box()
            box.label(text="No branch selected", icon='ERROR')
            box.label(text="Please select a branch first", icon='HAND')
            return
        
        # Check if we have commits
        if len(scene.dfm_commit_list) == 0:
            box = layout.box()
            box.label(text=f"No versions in branch '{current_branch}'", icon='INFO')
            box.label(text="Click 'Refresh History' to load", icon='HAND')
            return
        
        # Branch indicator before commit list
        DFM_UIHelpers.draw_version_control(layout, scene)
        
        # UIList for commits
        row = layout.row()
        row.template_list(
            "DFM_CommitList_UL_items", "",
            scene, "dfm_commit_list",
            scene, "dfm_commit_list_index",
            rows=5
        )
        
        # Selected commit details
        if scene.dfm_commit_list and 0 <= scene.dfm_commit_list_index < len(scene.dfm_commit_list):
            self.draw_commit_details(layout, scene)
            # Import actions previously shown in DFM_VersionImport_PT_panel
            self.draw_import_section(layout, scene, context)
    
    def draw_commit_details(self, layout: bpy.types.UILayout, scene: bpy.types.Scene) -> None:
        """Draw details for selected commit"""
        commit = scene.dfm_commit_list[scene.dfm_commit_list_index]
        
        # Commit details
        box = layout.box()
        col = box.column(align=True)
        
        # Tag info (shown before message)
        tag_text = f"Tag: {commit.tag}" if getattr(commit, 'tag', '') else "Tag: —"
        row = col.row()
        row.label(text=tag_text, icon='BOOKMARKS')
        col.separator()
        
        # Full message
        col.label(text="Message:", icon='TEXT')
        message_lines = [commit.commit_message[i:i+50] for i in range(0, len(commit.commit_message), 50)]
        for line in message_lines[:3]:  # Max 3 lines
            col.label(text=line)

    def draw_import_section(self, layout: bpy.types.UILayout, scene: bpy.types.Scene, context: bpy.types.Context) -> None:
        """Draw import UI/actions for the selected commit (moved from DFM_VersionImport_PT_panel)"""
        commit = scene.dfm_commit_list[scene.dfm_commit_list_index]
        
        # Show which commit is selected
        box = layout.box()
        col = box.column(align=True)
        col.label(text=f"Version: {commit.timestamp}", icon='TIME')
        if getattr(commit, 'tag', None):
            col.label(text=f"Tag: {commit.tag}", icon='BOOKMARKS')
        
        # Import mode
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Import Mode:", icon='MODIFIER')
        col.prop(scene, "dfm_import_mode", text="")
        
        # Show hint based on mode
        if scene.dfm_import_mode == 'AUTO':
            col.label(text="Auto: New if geometry selected", icon='INFO')
        elif scene.dfm_import_mode == 'SELECTED':
            if not context.active_object:
                col.label(text="Select an object first!", icon='ERROR')
        
        # Import components using new helper
        DFM_UIHelpers.draw_import_options(layout, scene, scene.dfm_import_mode)
        
        # Show what will be imported
        import_all = scene.dfm_import_all
        imported_components = []
        
        if import_all:
            # If "Import All" is checked, show all components
            imported_components = ["Geometry", "Materials", "UV", "Transform"]
        else:
            # Check individual checkboxes
            if scene.dfm_import_geometry:
                imported_components.append("Geometry")
            if scene.dfm_import_materials:
                imported_components.append("Materials")
            if scene.dfm_import_uv:
                imported_components.append("UV")
            if scene.dfm_import_transform:
                imported_components.append("Transform")
        
        if imported_components:
            box = layout.box()
            if import_all:
                box.label(text=f"Will import all components", icon='INFO')
            else:
                box.label(text=f"Will import: {', '.join(imported_components)}", icon='INFO')
        else:
            box = layout.box()
            box.label(text="Warning: Nothing selected!", icon='ERROR')
        
        # Action buttons
        layout.separator()
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        
        op = row.operator("object.load_version", text="Load Version", icon='IMPORT')
        op.commit_path = commit.commit_path
        
        op = row.operator("object.replace_with_version", text="Replace", icon='FILE_REFRESH')
        op.commit_path = commit.commit_path
        
        # Compare button with standard blue pressed state when active
        is_comparison_active = bool(scene.dfm_comparison_active)
        op = row.operator("object.compare_versions", text="Compare", icon='SPLIT_HORIZONTAL', depress=is_comparison_active)
        op.commit_path = commit.commit_path
        
        # Delete button (separate row for emphasis)
        layout.separator()
        row = layout.row()
        row.scale_y = 1.2
        op = row.operator("object.dfm_delete_version", text="Delete This Version", icon='TRASH')
        op.commit_path = commit.commit_path
        op.commit_timestamp = commit.timestamp




class DFM_Branches_PT_panel(bpy.types.Panel):
    """Branch management panel"""
    bl_idname = 'DFM_PT_panel_branches'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Difference Machine'
    bl_label = 'Branch Management'
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object and context.active_object.type == 'MESH'

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        active_obj = context.active_object
        
        # Refresh button
        row = layout.row()
        row.operator("object.dfm_refresh_branches", text="Refresh Branches", icon='FILE_REFRESH')
        
        # Auto-refresh if object changed (track by name)
        current_obj_name = active_obj.name if active_obj else ""
        last_obj_name = scene.get("dfm_last_branch_obj_name", "")
        
        if current_obj_name != last_obj_name and active_obj and active_obj.type == 'MESH':
            # Object changed - need to refresh (but can't do it here)
            # Just show a notice
            box = layout.box()
            box.label(text=f"Object changed to: {current_obj_name}", icon='INFO')
            box.label(text="Click 'Refresh Branches' to load branches", icon='HAND')
            return
        
        # Check if we have branches
        if len(scene.dfm_branch_list) == 0:
            box = layout.box()
            box.label(text="No branches found", icon='INFO')
            box.label(text="Click 'Refresh Branches' to load", icon='HAND')
        else:
            # UIList for branches
            row = layout.row()
            row.template_list(
                "DFM_BranchList_UL_items", "",
                scene, "dfm_branch_list",
                scene, "dfm_branch_list_index",
                rows=6  # Stretchable list with 6 rows by default
            )
        
        # Branch operations
        layout.separator()
        
        col = layout.column(align=True)
        col.operator("object.create_branch", text="Create New Branch", icon='ADD')
        col.operator("object.switch_branch", text="Switch Branch", icon='FILE_REFRESH')
        
        # Delete branch button (only show if branches exist and one is selected)
        if (scene.dfm_branch_list and 
            scene.dfm_branch_list_index >= 0 and 
            scene.dfm_branch_list_index < len(scene.dfm_branch_list)):
            layout.separator()
            row = layout.row()
            row.scale_y = 1.2
            row.operator("object.delete_branch", text="Delete Branch", icon='TRASH')


