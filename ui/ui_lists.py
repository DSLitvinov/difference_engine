"""
UIList classes for Difference Engine addon
"""
import bpy
import logging
from typing import Any

# Setup logging
logger = logging.getLogger(__name__)


class DFM_CommitItem(bpy.types.PropertyGroup):
    """Property group to store commit data"""
    commit_path: bpy.props.StringProperty(name="Commit Path")
    timestamp: bpy.props.StringProperty(name="Timestamp")
    commit_message: bpy.props.StringProperty(name="Message")
    tag: bpy.props.StringProperty(name="Tag")
    branch: bpy.props.StringProperty(name="Branch")


class DFM_BranchItem(bpy.types.PropertyGroup):
    """Property group to store branch data"""
    branch_name: bpy.props.StringProperty(name="Branch Name")
    commit_count: bpy.props.IntProperty(name="Commit Count", default=0)
    last_commit: bpy.props.StringProperty(name="Last Commit")
    is_current: bpy.props.BoolProperty(name="Is Current", default=False)


class DFM_CommitList_UL_items(bpy.types.UIList):
    """UIList for displaying version history commits"""
    
    def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, 
                  data: Any, item: Any, icon: int, active_data: Any, 
                  active_propname: str) -> None:
        """Draw a single commit item in the list"""
        commit = item
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Main row with timestamp
            row = layout.row(align=True)
            
            # Show tag icon if exists
            if commit.tag:
                row.label(text="", icon='BOOKMARKS')
            
            # Timestamp
            row.label(text=commit.timestamp, icon='TIME')
            
            # Message (truncated)
            message = commit.commit_message
            if len(message) > 30:
                message = message[:27] + "..."
            row = layout.row()
            row.label(text=message)
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='TIME')
    
    def filter_items(self, context: bpy.types.Context, data: Any, propname: str) -> tuple:
        """Filter and sort items in the list"""
        items = getattr(data, propname)
        
        # Default filtering (no filtering)
        flt_flags = [self.bitflag_filter_item] * len(items)
        flt_neworder = []
        
        # Default sorting by timestamp (newest first)
        if items:
            # Sort by timestamp in descending order
            def sort_key(item):
                return item.timestamp
            
            flt_neworder = list(range(len(items)))
            flt_neworder.sort(key=lambda x: sort_key(items[x]), reverse=True)
        
        return flt_flags, flt_neworder


class DFM_BranchList_UL_items(bpy.types.UIList):
    """UIList for displaying branches"""
    
    def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, 
                  data: Any, item: Any, icon: int, active_data: Any, 
                  active_propname: str) -> None:
        """Draw a single branch item in the list"""
        branch = item
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Main row with branch name
            row = layout.row(align=True)
            
            # Show current branch icon
            if branch.is_current:
                row.label(text="", icon='DISCLOSURE_TRI_RIGHT')
            else:
                row.label(text="", icon='OUTLINER')
            
            # Branch name
            row.label(text=branch.branch_name)
            
            # Commit count and last commit info
            row = layout.row()
            row.label(text=f"{branch.commit_count} commits", icon='TIME')
            if branch.last_commit:
                row.label(text=f"Last: {branch.last_commit}", icon='INFO')
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER')
    
    def filter_items(self, context: bpy.types.Context, data: Any, propname: str) -> tuple:
        """Filter and sort items in the list"""
        items = getattr(data, propname)
        
        # Default filtering (no filtering)
        flt_flags = [self.bitflag_filter_item] * len(items)
        flt_neworder = []
        
        # Default sorting: current branch first, then alphabetical
        if items:
            def sort_key(item):
                # Current branch first, then alphabetical
                if item.is_current:
                    return (0, item.branch_name)
                else:
                    return (1, item.branch_name)
            
            flt_neworder = list(range(len(items)))
            flt_neworder.sort(key=lambda x: sort_key(items[x]))
        
        return flt_flags, flt_neworder
