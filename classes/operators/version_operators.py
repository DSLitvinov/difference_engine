"""
Version control operators for loading and comparing versions
"""
import bpy
from ..version_manager import DFM_VersionManager


class DFM_LoadVersionOperator(bpy.types.Operator):
    """Load a specific version from version history using import settings"""
    bl_idname = "object.load_version"
    bl_label = "Load Version"
    bl_options = {'REGISTER', 'UNDO'}
    
    commit_path: bpy.props.StringProperty()
    
    def execute(self, context):
        scene = context.scene
        
        # Use the import settings from the scene
        import_mode = scene.dfm_import_mode
        
        # Respect the "import all" master checkbox
        import_all = scene.dfm_import_all
        if import_all:
            # If "Import All" is checked, enable all components
            import_geometry = True
            import_transform = True
            import_materials = True
            import_uv = True
        else:
            # Use individual checkboxes
            import_geometry = scene.dfm_import_geometry
            import_transform = scene.dfm_import_transform
            import_materials = scene.dfm_import_materials
            import_uv = scene.dfm_import_uv
        
        # Debug: Report what we're importing
        components = []
        if import_geometry: components.append("Geometry")
        if import_transform: components.append("Transform")
        if import_materials: components.append("Materials")
        if import_uv: components.append("UV")
        
        self.report({'INFO'}, f"Importing: {', '.join(components) if components else 'Nothing selected'}")
        
        # Call the load_geometry operator with the settings
        result = bpy.ops.object.load_geometry(
            filepath=self.commit_path,
            import_mode=import_mode,
            import_geometry=import_geometry,
            import_transform=import_transform,
            import_materials=import_materials,
            import_uv=import_uv
        )
        
        return result


class DFM_CompareVersionsOperator(bpy.types.Operator):
    """Load a comparison version with offset"""
    bl_idname = "object.compare_versions"
    bl_label = "Compare Versions"
    bl_options = {'REGISTER', 'UNDO'}
    
    commit_path: bpy.props.StringProperty()
    offset_distance: bpy.props.FloatProperty(
        name="Offset Distance",
        description="Distance to offset the comparison version",
        default=2.0,
        min=0.0,
        max=10.0
    )
    
    def execute(self, context):
        import json
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Load commit info
        commit_file = os.path.join(self.commit_path, "commit.json")
        commit_name = "Version"
        try:
            if os.path.exists(commit_file):
                with open(commit_file, 'r') as f:
                    commit_data = json.load(f)
                commit_name = commit_data.get('timestamp', 'Version')
                logger.info(f"Comparing with version: {commit_name}")
        except Exception as e:
            logger.warning(f"Failed to load commit info: {e}")
        
        # Always create new object for comparison with all components
        result = bpy.ops.object.load_geometry(
            filepath=self.commit_path,
            import_mode='NEW',
            import_geometry=True,
            import_transform=True,
            import_materials=True,
            import_uv=True
        )
        
        if result == {'FINISHED'}:
            # Offset the comparison object
            if context.active_object:
                obj = context.active_object
                # Add "_compare" suffix to name for easy identification
                obj.name = obj.name + "_compare"
                obj.data.name = obj.data.name + "_compare"
                
                # Get current selection to determine offset direction
                original_obj = None
                for o in context.selected_objects:
                    if "_compare" not in o.name:
                        original_obj = o
                        break
                
                # Offset based on original object if available
                if original_obj:
                    obj.location.x = original_obj.location.x + self.offset_distance
                    obj.location.y = original_obj.location.y
                    obj.location.z = original_obj.location.z
                else:
                    # Default offset if no comparison available
                    obj.location.x += self.offset_distance
                
                # Make it slightly transparent for visual comparison
                obj.active_material.use_nodes = True
                
                logger.info(f"Loaded comparison version '{commit_name}' with offset {self.offset_distance}")
                self.report({'INFO'}, f"Loaded comparison version: {commit_name} (offset +{self.offset_distance})")
        
        return result


class DFM_DeleteVersionOperator(bpy.types.Operator):
    """Delete a version from history"""
    bl_idname = "object.dfm_delete_version"
    bl_label = "Delete Version"
    bl_options = {'REGISTER', 'UNDO'}
    
    commit_path: bpy.props.StringProperty()
    commit_timestamp: bpy.props.StringProperty()
    
    def invoke(self, context, event):
        """Show confirmation dialog before deleting"""
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        """Delete the selected version"""
        if not self.commit_path:
            self.report({'ERROR'}, "No commit path specified")
            return {'CANCELLED'}
        
        # Delete the version
        success = DFM_VersionManager.delete_version(self.commit_path)
        
        if success:
            self.report({'INFO'}, f"Deleted version: {self.commit_timestamp}")
            
            # Refresh the commit list
            bpy.ops.object.dfm_refresh_commits()
            
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to delete version")
            return {'CANCELLED'}

