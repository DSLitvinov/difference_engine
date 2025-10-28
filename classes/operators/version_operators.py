"""
Version control operators for loading and comparing versions
"""
import bpy
import logging
from ..version_manager import DFM_VersionManager

# Module-level logger for use in helper methods
logger = logging.getLogger(__name__)


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
    """Toggle comparison version with offset"""
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
        scene = context.scene
        
        # Check if comparison is already active
        if scene.dfm_comparison_active and scene.dfm_comparison_object_name:
            # Toggle OFF: Remove comparison object
            self._remove_comparison_object(context)
            scene.dfm_comparison_active = False
            scene.dfm_comparison_object_name = ""
            scene.dfm_original_object_name = ""
            self.report({'INFO'}, "Comparison mode disabled")
            return {'FINISHED'}
        
        # Toggle ON: Create comparison object
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
                
                # Get current selection to determine offset direction and store original object
                original_obj = None
                for o in context.selected_objects:
                    if "_compare" not in o.name:
                        original_obj = o
                        break
                
                # Store the original object name for later selection
                if original_obj:
                    scene.dfm_original_object_name = original_obj.name
                
                # Offset based on original object if available
                if original_obj:
                    obj.location.x = original_obj.location.x + self.offset_distance
                    obj.location.y = original_obj.location.y
                    obj.location.z = original_obj.location.z
                else:
                    # Default offset if no comparison available
                    obj.location.x += self.offset_distance
                
                # Make it slightly transparent for visual comparison
                if obj.active_material:
                    obj.active_material.use_nodes = True
                
                # Store comparison state
                scene.dfm_comparison_active = True
                scene.dfm_comparison_object_name = obj.name
                
                logger.info(f"Loaded comparison version '{commit_name}' with offset {self.offset_distance}")
                self.report({'INFO'}, f"Comparison mode enabled: {commit_name} (offset +{self.offset_distance})")
        
        return result
    
    def _remove_comparison_object(self, context):
        """Remove the comparison object and all its data from the blend file"""
        scene = context.scene
        comparison_name = scene.dfm_comparison_object_name
        
        if not comparison_name:
            return
        
        # Find and remove the comparison object
        if comparison_name in bpy.data.objects:
            obj = bpy.data.objects[comparison_name]
            
            # Safely capture references before deleting anything
            mesh_ref = obj.data if getattr(obj, 'data', None) else None
            materials_ref = []
            try:
                if mesh_ref and hasattr(mesh_ref, 'materials'):
                    materials_ref = [m for m in mesh_ref.materials if m]
            except ReferenceError:
                materials_ref = []
            
            # Deselect the object if needed
            try:
                if obj in context.selected_objects:
                    obj.select_set(False)
            except ReferenceError:
                pass
            
            # Remove the object first (and unlink)
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except ReferenceError:
                # Already removed
                pass
            
            # Remove mesh if it has no users
            if mesh_ref and mesh_ref.name in bpy.data.meshes:
                try:
                    if mesh_ref.users == 0:
                        bpy.data.meshes.remove(mesh_ref)
                except ReferenceError:
                    pass
            
            # Remove materials if they have no users
            for material in materials_ref:
                if material and material.name in bpy.data.materials:
                    try:
                        if material.users == 0:
                            bpy.data.materials.remove(material)
                    except ReferenceError:
                        pass
            
            logger.info(f"Removed comparison object: {comparison_name}")
            
            # Select and activate the original object
            original_name = scene.dfm_original_object_name
            if original_name and original_name in bpy.data.objects:
                original_obj = bpy.data.objects[original_name]
                # Deselect all
                for o in context.selected_objects:
                    o.select_set(False)
                # Select and activate original object
                original_obj.select_set(True)
                context.view_layer.objects.active = original_obj
                logger.info(f"Switched back to original object: {original_name}")
        
        # Clean up any orphaned data
        self._cleanup_orphaned_data()
    
    def _cleanup_orphaned_data(self):
        """Clean up orphaned materials and textures"""
        # Remove materials that are no longer used
        for material in list(bpy.data.materials):
            if not material.users:
                bpy.data.materials.remove(material)
        
        # Remove textures that are no longer used
        for texture in list(bpy.data.textures):
            if not texture.users:
                bpy.data.textures.remove(texture)
        
        # Remove images that are no longer used
        for image in list(bpy.data.images):
            if not image.users:
                bpy.data.images.remove(image)


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

