"""
Scene properties for Difference Machine addon
"""
import bpy


def register_properties():
    """Register all scene properties"""
    # Export options
    bpy.types.Scene.dfm_export_all = bpy.props.BoolProperty(
        name="Export All",
        default=True,
        description="Export all components"
    )
    bpy.types.Scene.dfm_export_geometry = bpy.props.BoolProperty(
        name="Export Geometry",
        default=True,
        description="Export mesh geometry"
    )
    bpy.types.Scene.dfm_export_transform = bpy.props.BoolProperty(
        name="Export Transform",
        default=True,
        description="Export object transformation"
    )
    bpy.types.Scene.dfm_export_materials = bpy.props.BoolProperty(
        name="Export Materials",
        default=True,
        description="Export materials and textures"
    )
    bpy.types.Scene.dfm_export_uv = bpy.props.BoolProperty(
        name="Export UV",
        default=True,
        description="Export UV layout"
    )
    
    # Version control options
    bpy.types.Scene.dfm_auto_snapshot = bpy.props.BoolProperty(
        name="Auto-compression",
        default=True,  # Enabled by default for better disk usage
        description="Automatically compress old versions (saves disk space)"
    )
    bpy.types.Scene.dfm_commit_message = bpy.props.StringProperty(
        name="Commit Message",
        default="",
        description="Description of changes in this export"
    )
    bpy.types.Scene.dfm_commit_tag = bpy.props.StringProperty(
        name="Commit Tag",
        default="",
        description="Tag for this version (v1.0, release, etc.)"
    )
    bpy.types.Scene.dfm_current_branch = bpy.props.StringProperty(
        name="Current Branch",
        default="main",
        description="Current working branch"
    )
    
    # Version history UI list (collection property registered in ui_main)
    bpy.types.Scene.dfm_commit_list_index = bpy.props.IntProperty(
        name="Selected Commit",
        default=0,
        description="Currently selected commit in history"
    )
    bpy.types.Scene.dfm_selected_commit_path = bpy.props.StringProperty(
        name="Selected Commit Path",
        default="",
        description="Path to currently selected commit"
    )
    
    # Branch list UI properties
    bpy.types.Scene.dfm_branch_list_index = bpy.props.IntProperty(
        name="Selected Branch",
        default=0,
        description="Currently selected branch in list"
    )
    
    # Import options for version history
    bpy.types.Scene.dfm_import_all = bpy.props.BoolProperty(
        name="Import All",
        default=True,
        description="Import all components"
    )
    bpy.types.Scene.dfm_import_geometry = bpy.props.BoolProperty(
        name="Import Geometry",
        default=True,
        description="Import mesh geometry"
    )
    bpy.types.Scene.dfm_import_transform = bpy.props.BoolProperty(
        name="Import Transform",
        default=True,
        description="Import object transformation"
    )
    bpy.types.Scene.dfm_import_materials = bpy.props.BoolProperty(
        name="Import Materials",
        default=True,
        description="Import materials and textures"
    )
    bpy.types.Scene.dfm_import_uv = bpy.props.BoolProperty(
        name="Import UV",
        default=True,
        description="Import UV layout"
    )
    bpy.types.Scene.dfm_import_mode = bpy.props.EnumProperty(
        name="Import Mode",
        description="How to import the data",
        items=[
            ('NEW', "Create New", "Create a new object"),
            ('SELECTED', "Apply to Selected", "Apply to selected object"),
            ('AUTO', "Auto", "Auto-detect based on options")
        ],
        default='AUTO'
    )


def unregister_properties():
    """Unregister all scene properties"""
    del bpy.types.Scene.dfm_export_all
    del bpy.types.Scene.dfm_export_geometry
    del bpy.types.Scene.dfm_export_transform
    del bpy.types.Scene.dfm_export_materials
    del bpy.types.Scene.dfm_export_uv
    del bpy.types.Scene.dfm_auto_snapshot
    del bpy.types.Scene.dfm_commit_message
    del bpy.types.Scene.dfm_commit_tag
    del bpy.types.Scene.dfm_current_branch
    del bpy.types.Scene.dfm_commit_list_index
    del bpy.types.Scene.dfm_selected_commit_path
    del bpy.types.Scene.dfm_branch_list_index
    del bpy.types.Scene.dfm_import_all
    del bpy.types.Scene.dfm_import_geometry
    del bpy.types.Scene.dfm_import_transform
    del bpy.types.Scene.dfm_import_materials
    del bpy.types.Scene.dfm_import_uv
    del bpy.types.Scene.dfm_import_mode

