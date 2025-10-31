"""
Main UI module for Difference Machine addon
"""
import bpy
import logging
from . import properties
from .ui_helpers import load_saved_branch_on_startup, load_saved_branch_on_object_change, clear_caches, clear_all_scene_ui_data
from .ui_lists import DFM_CommitItem, DFM_BranchItem, DFM_CommitList_UL_items, DFM_BranchList_UL_items
from .ui_panels import (
    DFM_Export_PT_panel,
    DFM_History_PT_panel,
    DFM_Branches_PT_panel
)
from .ui_operators import (
    DFM_RefreshCommits_OT_operator,
    DFM_RefreshBranches_OT_operator,
    DFM_LoadSavedBranch_OT_operator
)

# Setup logging
logger = logging.getLogger(__name__)

# Import the operator classes
from ..classes.operators import classes as operator_classes

# Classes list for registration
classes = [
    # Property groups
    DFM_CommitItem,
    DFM_BranchItem,
    
    # UI Lists
    DFM_CommitList_UL_items,
    DFM_BranchList_UL_items,
    
    # UI Operators
    DFM_RefreshCommits_OT_operator,
    DFM_RefreshBranches_OT_operator,
    DFM_LoadSavedBranch_OT_operator,
    
    # UI Panels 
    DFM_Export_PT_panel,
    DFM_History_PT_panel,
    DFM_Branches_PT_panel,
] + operator_classes


def register():
    """Register UI classes and properties"""
    try:
        logger.info("Registering Difference Engine UI components")
        
        # Clear caches on reload
        clear_caches()
        
        # Register properties first
        properties.register_properties()
        
        # Register UI classes
        for cls in classes:
            bpy.utils.register_class(cls)
        
        # Register commit list collection
        bpy.types.Scene.dfm_commit_list = bpy.props.CollectionProperty(type=DFM_CommitItem)
        
        # Register branch list collection
        bpy.types.Scene.dfm_branch_list = bpy.props.CollectionProperty(type=DFM_BranchItem)
        
        # Add handler to clear UI data BEFORE file loads (prevents showing stale data)
        if not hasattr(bpy.app.handlers, 'load_pre'):
            bpy.app.handlers.load_pre = []
        bpy.app.handlers.load_pre.append(clear_all_scene_ui_data)
        
        # Add handler to load saved branch on Blender startup
        bpy.app.handlers.load_post.append(load_saved_branch_on_startup)
        
        # Add handler to load saved branch when object changes
        bpy.app.handlers.depsgraph_update_post.append(load_saved_branch_on_object_change)
        
        logger.info("Successfully registered Difference Engine UI components")
        
    except Exception as e:
        logger.error(f"Failed to register UI components: {e}")
        raise


def unregister():
    """Unregister UI classes and properties"""
    try:
        logger.info("Unregistering Difference Engine UI components")
        
        # Remove load_pre handler if exists
        if hasattr(bpy.app.handlers, 'load_pre'):
            if clear_all_scene_ui_data in bpy.app.handlers.load_pre:
                bpy.app.handlers.load_pre.remove(clear_all_scene_ui_data)
        
        # Remove startup handler
        if load_saved_branch_on_startup in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_saved_branch_on_startup)
        
        # Remove object change handler
        if load_saved_branch_on_object_change in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(load_saved_branch_on_object_change)
        
        # Unregister commit list collection
        del bpy.types.Scene.dfm_commit_list
        
        # Unregister branch list collection
        del bpy.types.Scene.dfm_branch_list
        
        # Unregister UI classes
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        
        # Unregister properties
        properties.unregister_properties()
        
        logger.info("Successfully unregistered Difference Engine UI components")
        
    except Exception as e:
        logger.error(f"Failed to unregister UI components: {e}")
        raise
