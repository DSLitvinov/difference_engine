"""
Import operator for loading geometry and materials
Supports selective import: apply materials/UV/transform to existing mesh or create new
"""
import bpy
import json
import os
import logging
from ..material_importer import DFM_MaterialImporter

# Setup logging
logger = logging.getLogger(__name__)


class DFM_LoadGeometryOperator(bpy.types.Operator):
    bl_idname = "object.load_geometry"
    bl_label = "Import Geometry"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to the geometry JSON file or commit directory",
        subtype='FILE_PATH'
    )
    
    # Import mode
    import_mode: bpy.props.EnumProperty(
        name="Import Mode",
        description="How to import the data",
        items=[
            ('NEW', "Create New Object", "Create a new object with imported data"),
            ('SELECTED', "Apply to Selected", "Apply import data to currently selected object (requires selection)"),
            ('AUTO', "Auto", "Create new if geometry is imported, otherwise apply to selected")
        ],
        default='AUTO'
    )
    
    # Import options
    import_geometry: bpy.props.BoolProperty(
        name="Geometry",
        default=True,
        description="Import mesh geometry (vertices, faces)"
    )
    
    import_transform: bpy.props.BoolProperty(
        name="Transform",
        default=True,
        description="Import object transformation (location, rotation, scale)"
    )
    
    import_materials: bpy.props.BoolProperty(
        name="Materials",
        default=True,
        description="Import materials and textures"
    )
    
    import_uv: bpy.props.BoolProperty(
        name="UV Layouts",
        default=True,
        description="Import UV layouts"
    )
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        
        try:
            # Determine if filepath is a directory (commit) or file (geometry.json)
            if os.path.isdir(self.filepath):
                commit_dir = self.filepath
                geometry_file = os.path.join(commit_dir, "geometry.json")
            else:
                geometry_file = self.filepath
                commit_dir = os.path.dirname(self.filepath)
            
            # Check if anything is selected to import
            if not any([self.import_geometry, self.import_transform, self.import_materials, self.import_uv]):
                self.report({'WARNING'}, "No import options selected")
                return {'CANCELLED'}
            
            # Load geometry data only if geometry or UV import is requested
            mesh_data = None
            mesh_name = 'ImportedMesh'
            
            if (self.import_geometry or self.import_uv) and os.path.exists(geometry_file):
                with open(geometry_file, 'r') as f:
                    mesh_data = json.load(f)
                mesh_name = mesh_data.get('name', 'ImportedMesh')
            elif self.import_geometry or self.import_uv:
                self.report({'ERROR'}, "Geometry file not found but required for geometry/UV import")
                return {'CANCELLED'}
            else:
                # Try to get mesh name from commit.json if only importing materials/transform
                commit_file = os.path.join(commit_dir, "commit.json")
                if os.path.exists(commit_file):
                    with open(commit_file, 'r') as f:
                        commit_data = json.load(f)
                    mesh_name = commit_data.get('mesh_name', 'ImportedMesh')
            
            # Determine import mode
            mode = self.import_mode
            if mode == 'AUTO':
                # Auto mode: create new if importing geometry, otherwise apply to selected
                mode = 'NEW' if self.import_geometry else 'SELECTED'
            
            # Get or create object based on mode
            if mode == 'NEW':
                obj, mesh = self._create_new_object(context, mesh_name)
            elif mode == 'SELECTED':
                obj = context.active_object
                if not obj or obj.type != 'MESH':
                    self.report({'ERROR'}, "Please select a mesh object to apply import to")
                    return {'CANCELLED'}
                mesh = obj.data
            
            # Import geometry
            if self.import_geometry and mesh_data:
                self._import_geometry(mesh, mesh_data)
            
            # Import UV layers
            if self.import_uv and mesh_data:
                if 'uv_layers' in mesh_data:
                    self._import_uv_layers(mesh, mesh_data)
                    logger.info("Imported UV layers")
                else:
                    logger.warning("UV import requested but no uv_layers in geometry.json")
            
            # Import transform
            if self.import_transform:
                self._import_transform(obj, commit_dir)
                logger.info("Imported transform")
            
            # Import materials
            if self.import_materials:
                self._import_materials(obj, commit_dir)
                logger.info("Imported materials")
            
            # Final mesh update and validation (single call after all operations)
            if obj and obj.data:
                obj.data.update()
                obj.data.validate()
                logger.debug("Final mesh update and validation completed")
            
            # Link new object to scene if created
            if mode == 'NEW':
                context.collection.objects.link(obj)
                context.view_layer.objects.active = obj
                obj.select_set(True)
                self.report({'INFO'}, f"Created new object: {mesh_name}")
            else:
                self.report({'INFO'}, f"Applied import to: {obj.name}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def _create_new_object(self, context, mesh_name):
        """Create a new mesh and object"""
        mesh = bpy.data.meshes.new(mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        return obj, mesh
    
    def _import_geometry(self, mesh, mesh_data):
        """Import mesh geometry (vertices and faces)"""
        vertices = [v['co'] for v in mesh_data.get('vertices', [])]
        faces = [f['vertices'] for f in mesh_data.get('faces', [])]
        
        # Clear existing mesh data to avoid array size conflicts
        mesh.clear_geometry()
        
        # Import new geometry (update called later in execute)
        mesh.from_pydata(vertices, [], faces)
    
    def _import_uv_layers(self, mesh, mesh_data):
        """
        Import UV layers to mesh with optimized batch processing.
        
        Performance optimization:
        - Uses foreach_set for 5-10x faster UV assignment on large meshes
        - Flattens UV coordinates into a single list for batch operation
        - Uses itertools.chain for efficient flattening
        """
        from itertools import chain
        
        # Clear existing UV layers if importing to existing mesh
        while mesh.uv_layers:
            mesh.uv_layers.remove(mesh.uv_layers[0])
        
        # Import UV layers from data
        for uv_layer_name, uv_data in mesh_data['uv_layers'].items():
            uv_layer = mesh.uv_layers.new(name=uv_layer_name)
            
            # Optimize: Use foreach_set for batch UV assignment (much faster)
            # Flatten the UV coordinates: [[x,y], [x,y]] -> [x, y, x, y, ...]
            if len(uv_data) > 0 and len(uv_layer.data) > 0:
                # Ensure we don't exceed actual UV data length
                count = min(len(uv_data), len(uv_layer.data))
                # Use itertools.chain for faster flattening
                flat_uvs = list(chain.from_iterable(uv_data[:count]))
                uv_layer.data.foreach_set("uv", flat_uvs)
        
        # Mesh update moved to end of import process
    
    def _import_transform(self, obj, commit_dir):
        """Import object transformation"""
        transform_file = os.path.join(commit_dir, "transform.json")
        if os.path.exists(transform_file):
            with open(transform_file, 'r') as f:
                transform_data = json.load(f)
            
            if 'location' in transform_data:
                obj.location = transform_data['location']
            if 'rotation' in transform_data:
                obj.rotation_euler = transform_data['rotation']
            if 'scale' in transform_data:
                obj.scale = transform_data['scale']
            logger.debug(f"Applied transform from {transform_file}")
        else:
            logger.debug(f"Transform file not found: {transform_file}")
    
    def _import_materials(self, obj, commit_dir):
        """Import materials and apply to object"""
        logger.info(f"Starting material import for object: {obj.name}")
        
        # Clear existing materials if replacing
        obj.data.materials.clear()
        
        # Look for material files in the commit directory using scandir
        material_files = []
        try:
            with os.scandir(commit_dir) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.startswith('material_') and entry.name.endswith('.json'):
                        material_files.append(entry.name)
        except OSError as e:
            logger.error(f"Failed to scan commit directory {commit_dir}: {e}")
            return
        
        logger.info(f"Found {len(material_files)} material files in {commit_dir}")
        
        for material_file in material_files:
            material_path = os.path.join(commit_dir, material_file)
            logger.debug(f"Importing material from: {material_file}")
            material = DFM_MaterialImporter.import_material(material_path, commit_dir)
            
            if material:
                obj.data.materials.append(material)
                logger.info(f"Successfully applied material '{material.name}' to object '{obj.name}'")
                logger.debug(f"Object now has {len(obj.data.materials)} material(s)")
            else:
                logger.warning(f"Failed to import material from {material_file}")
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        layout = self.layout
        
        # Import mode section
        box = layout.box()
        box.label(text="Import Mode:", icon='MODIFIER')
        box.prop(self, "import_mode", text="")
        
        # Show hint based on mode
        if self.import_mode == 'AUTO':
            box.label(text="Will create new if geometry is selected", icon='INFO')
        elif self.import_mode == 'SELECTED' and not context.active_object:
            box.label(text="Warning: No object selected!", icon='ERROR')
        
        # Import options section
        box = layout.box()
        box.label(text="Import Components:", icon='IMPORT')
        
        col = box.column(align=True)
        
        # Geometry option (can only import with new object)
        row = col.row()
        row.prop(self, "import_geometry")
        if self.import_mode == 'SELECTED':
            row.enabled = False
            if row.enabled:
                row.label(text="(Geometry cannot be applied to existing)", icon='INFO')
        
        # Other options can be applied to existing or new
        col.prop(self, "import_materials")
        col.prop(self, "import_uv")
        col.prop(self, "import_transform")
        
        # Summary
        components = []
        if self.import_geometry:
            components.append("Geometry")
        if self.import_materials:
            components.append("Materials")
        if self.import_uv:
            components.append("UV")
        if self.import_transform:
            components.append("Transform")
        
        if components:
            box = layout.box()
            box.label(text=f"Will import: {', '.join(components)}", icon='CHECKMARK')

