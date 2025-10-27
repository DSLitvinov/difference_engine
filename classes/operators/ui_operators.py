"""
UI helper operators
"""
import bpy


class DFM_ToggleImportAll_OT_operator(bpy.types.Operator):
    """Enable all import options"""
    bl_idname = "object.dfm_toggle_import_all"
    bl_label = "Select All"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        scene.dfm_import_geometry = True
        scene.dfm_import_materials = True
        scene.dfm_import_uv = True
        scene.dfm_import_transform = True
        self.report({'INFO'}, "All import options enabled")
        return {'FINISHED'}


class DFM_ToggleImportNone_OT_operator(bpy.types.Operator):
    """Disable all import options"""
    bl_idname = "object.dfm_toggle_import_none"
    bl_label = "Select None"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        scene.dfm_import_geometry = False
        scene.dfm_import_materials = False
        scene.dfm_import_uv = False
        scene.dfm_import_transform = False
        self.report({'INFO'}, "All import options disabled")
        return {'FINISHED'}

