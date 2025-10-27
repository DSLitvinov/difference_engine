"""
Material and texture export functionality
"""
import bpy
import json
import os
import shutil
import logging
from typing import Optional, Dict, Any, List
from .utils import convert_to_json_serializable, validate_file_path, validate_directory_path, is_safe_file_extension
from .error_handler import DFM_ErrorHandler, DFM_Error, DFM_ErrorType, error_handler_decorator

# Setup logging
logger = logging.getLogger(__name__)


class DFM_MaterialExporter:
    """Class for exporting materials and textures"""
    
    @staticmethod
    @error_handler_decorator(DFM_ErrorType.MATERIAL_ERROR)
    def export_material(material: bpy.types.Material, export_path: str) -> Optional[str]:
        """
        Export material to JSON and copy textures.
        
        Args:
            material: Blender material object to export
            export_path: Directory path where to export the material
            
        Returns:
            Name of the exported material file, or None if export failed
            
        Raises:
            DFM_ValidationError: If input parameters are invalid
            DFM_FileOperationError: If file operations fail
            DFM_MaterialError: If material export fails
        """
        DFM_ErrorHandler.log_operation_start("export_material", {
            'material_name': material.name if material else 'None',
            'export_path': export_path
        })
        
        # Validate inputs
        if not material:
            raise DFM_Error("Material cannot be None", DFM_ErrorType.VALIDATION_ERROR)
        
        if not export_path:
            raise DFM_Error("Export path cannot be empty", DFM_ErrorType.VALIDATION_ERROR)
        
        # Validate export path
        if not validate_directory_path(export_path, create_if_missing=True):
            raise DFM_Error(f"Invalid export path: {export_path}", DFM_ErrorType.FILE_OPERATION_ERROR)
        
        try:
            material_data = {
                "name": material.name,
                "type": material.use_nodes and "NODES" or "SURFACE",
                "diffuse_color": list(material.diffuse_color[:4]),  # RGBA as list
                "specular_color": list(material.specular_color[:3]),  # RGB as list
                "roughness": float(material.roughness),
                "metallic": float(material.metallic),
                "use_nodes": material.use_nodes
            }
            
            # Create textures directory
            textures_dir = os.path.join(export_path, "textures")
            if not validate_directory_path(textures_dir, create_if_missing=True):
                raise DFM_Error(f"Failed to create textures directory: {textures_dir}", DFM_ErrorType.FILE_OPERATION_ERROR)
            
            # Export node-based materials
            if material.use_nodes and material.node_tree:
                node_tree_data = DFM_MaterialExporter.export_node_tree(material.node_tree, textures_dir)
                material_data["nodes"] = node_tree_data.get("nodes", [])
                material_data["links"] = node_tree_data.get("links", [])
            
            # Save material JSON
            material_file = os.path.join(export_path, f"material_{material.name}.json")
            
            # Validate file path before writing
            if not validate_file_path(material_file):
                raise DFM_Error(f"Invalid material file path: {material_file}", DFM_ErrorType.FILE_OPERATION_ERROR)
            
            with open(material_file, 'w') as f:
                json.dump(material_data, f)
            
            DFM_ErrorHandler.log_operation_success("export_material", {
                'material_name': material.name,
                'file': os.path.basename(material_file)
            })
            
            return os.path.basename(material_file)
            
        except Exception as e:
            DFM_ErrorHandler.log_operation_failure("export_material", e, {
                'material_name': material.name,
                'export_path': export_path
            })
            raise
    
    @staticmethod
    @error_handler_decorator(DFM_ErrorType.MATERIAL_ERROR)
    def export_node_tree(node_tree: bpy.types.NodeTree, textures_dir: str) -> Dict[str, Any]:
        """
        Export node tree structure with enhanced validation.
        
        Args:
            node_tree: Blender node tree to export
            textures_dir: Directory where textures should be saved
            
        Returns:
            Dictionary containing nodes and links data
            
        Raises:
            DFM_ValidationError: If input parameters are invalid
            DFM_MaterialError: If node tree export fails
        """
        DFM_ErrorHandler.log_operation_start("export_node_tree", {
            'node_tree_name': node_tree.name if node_tree else 'None',
            'textures_dir': textures_dir
        })
        
        # Validate inputs
        if not node_tree:
            raise DFM_Error("Node tree cannot be None", DFM_ErrorType.VALIDATION_ERROR)
        
        if not textures_dir:
            raise DFM_Error("Textures directory cannot be empty", DFM_ErrorType.VALIDATION_ERROR)
        
        try:
            nodes_data = []
            
            for node in node_tree.nodes:
                node_data = {
                    "name": node.name,
                    "type": node.type,
                    "location": [float(node.location.x), float(node.location.y)],  # 2D vector [X, Y]
                    "width": float(node.width),
                    "inputs": [],
                    "outputs": [],
                    "properties": {}  # Additional node-specific properties
                }
                
                # Export common node properties with validation
                DFM_MaterialExporter._export_node_properties(node, node_data)
                
                # Export Node Group reference
                if node.type == 'GROUP' and hasattr(node, 'node_tree') and node.node_tree:
                    node_data["properties"]["node_tree_name"] = node.node_tree.name
                    logger.debug(f"Exporting Group node referencing: {node.node_tree.name}")
                
                # Export ColorRamp (ValToRGB) data
                if node.type == 'VALTORGB' and hasattr(node, 'color_ramp'):
                    DFM_MaterialExporter._export_color_ramp(node, node_data)
                
                # Export Curve data (Float, RGB, Vector curves)
                if node.type in ('CURVE_FLOAT', 'CURVE_RGB', 'CURVE_VEC'):
                    DFM_MaterialExporter._export_curve_data(node, node_data)
                
                # Handle image texture nodes with enhanced validation
                if node.type == 'TEX_IMAGE' and node.image:
                    DFM_MaterialExporter._export_image_texture(node, node_data, textures_dir)
                
                # Export input sockets with validation
                DFM_MaterialExporter._export_input_sockets(node, node_data)
                
                # Export output sockets
                DFM_MaterialExporter._export_output_sockets(node, node_data)
                
                nodes_data.append(node_data)
            
            # Export node links (connections between nodes)
            links_data = DFM_MaterialExporter._export_node_links(node_tree)
            
            result = {"nodes": nodes_data, "links": links_data}
            
            DFM_ErrorHandler.log_operation_success("export_node_tree", {
                'node_tree_name': node_tree.name,
                'nodes_count': len(nodes_data),
                'links_count': len(links_data)
            })
            
            return result
            
        except Exception as e:
            DFM_ErrorHandler.log_operation_failure("export_node_tree", e, {
                'node_tree_name': node_tree.name if node_tree else 'None'
            })
            raise
    
    @staticmethod
    def _export_node_properties(node: bpy.types.Node, node_data: Dict[str, Any]) -> None:
        """Export common node properties with validation"""
        try:
            if hasattr(node, 'operation'):  # Math, VectorMath, etc.
                node_data["properties"]["operation"] = node.operation
            if hasattr(node, 'blend_type'):  # Mix nodes
                node_data["properties"]["blend_type"] = node.blend_type
            if hasattr(node, 'interpolation'):  # Image Texture
                node_data["properties"]["interpolation"] = node.interpolation
            if hasattr(node, 'extension'):  # Image Texture
                node_data["properties"]["extension"] = node.extension
            if hasattr(node, 'color_space'):  # Image Texture
                node_data["properties"]["color_space"] = node.color_space
            if hasattr(node, 'label'):
                node_data["properties"]["label"] = node.label
            if hasattr(node, 'hide'):
                node_data["properties"]["hide"] = node.hide
            if hasattr(node, 'mute'):
                node_data["properties"]["mute"] = node.mute
        except Exception as e:
            logger.warning(f"Failed to export properties for node {node.name}: {e}")
    
    @staticmethod
    def _export_color_ramp(node: bpy.types.Node, node_data: Dict[str, Any]) -> None:
        """Export ColorRamp data with validation"""
        try:
            ramp = node.color_ramp
            ramp_data = {
                "color_mode": ramp.color_mode,
                "interpolation": ramp.interpolation,
                "elements": []
            }
            for element in ramp.elements:
                ramp_data["elements"].append({
                    "position": float(element.position),
                    "color": [float(element.color[0]), float(element.color[1]), 
                             float(element.color[2]), float(element.color[3])]
                })
            node_data["properties"]["color_ramp"] = ramp_data
        except Exception as e:
            logger.warning(f"Failed to export color ramp for node {node.name}: {e}")
    
    @staticmethod
    def _export_curve_data(node: bpy.types.Node, node_data: Dict[str, Any]) -> None:
        """Export curve data with validation"""
        try:
            if hasattr(node, 'mapping'):
                mapping = node.mapping
                curves_data = {
                    "use_clip": mapping.use_clip if hasattr(mapping, 'use_clip') else True,
                    "curves": []
                }
                for curve in mapping.curves:
                    curve_points = []
                    for point in curve.points:
                        curve_points.append({
                            "location": [float(point.location[0]), float(point.location[1])],
                            "handle_type": point.handle_type
                        })
                    curves_data["curves"].append(curve_points)
                node_data["properties"]["mapping"] = curves_data
        except Exception as e:
            logger.warning(f"Failed to export curve data for node {node.name}: {e}")
    
    @staticmethod
    def _export_image_texture(node: bpy.types.Node, node_data: Dict[str, Any], textures_dir: str) -> None:
        """Export image texture with enhanced validation"""
        try:
            node_data["image"] = node.image.name
            node_data["image_file"] = node.image.filepath
            
            # Handle packed images
            if node.image.packed_file:
                # Save packed image to textures directory
                image_filename = node.image.name
                if not image_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tga', '.bmp', '.exr')):
                    image_filename += '.png'
                
                dest_path = os.path.join(textures_dir, image_filename)
                
                # Validate destination path
                if not validate_file_path(dest_path):
                    logger.warning(f"Invalid destination path for packed image: {dest_path}")
                    return
                
                node.image.save_render(dest_path)
                node_data["copied_texture"] = image_filename
                node_data["was_packed"] = True
                
            # Copy texture file from disk
            elif node.image.filepath and os.path.exists(bpy.path.abspath(node.image.filepath)):
                source_path = bpy.path.abspath(node.image.filepath)
                
                # Validate source path
                if not validate_file_path(source_path, must_exist=True, must_be_file=True):
                    logger.warning(f"Invalid source path for image: {source_path}")
                    return
                
                # Check file extension safety
                if not is_safe_file_extension(source_path):
                    logger.warning(f"Unsafe file extension for image: {source_path}")
                    return
                
                dest_path = os.path.join(textures_dir, os.path.basename(node.image.filepath))
                
                # Validate destination path
                if not validate_file_path(dest_path):
                    logger.warning(f"Invalid destination path for image: {dest_path}")
                    return
                
                shutil.copy2(source_path, dest_path)
                node_data["copied_texture"] = os.path.basename(dest_path)
                node_data["was_packed"] = False
                
        except Exception as e:
            logger.warning(f"Failed to export image texture for node {node.name}: {e}")
    
    @staticmethod
    def _export_input_sockets(node: bpy.types.Node, node_data: Dict[str, Any]) -> None:
        """Export input sockets with validation"""
        try:
            for input_socket in node.inputs:
                # Handle default_value which might be a Blender type (Vector, Color, etc.)
                default_val = getattr(input_socket, 'default_value', None)
                
                # Convert default values safely
                safe_default = None
                if default_val is not None:
                    try:
                        # Try to convert to list (works for Vector, Color, etc.)
                        if hasattr(default_val, '__len__'):
                            safe_default = [float(v) for v in default_val]
                        else:
                            # Single value (float, int, bool)
                            safe_default = float(default_val) if isinstance(default_val, (int, float)) else default_val
                    except (TypeError, ValueError):
                        safe_default = None
                
                input_data = {
                    "name": input_socket.name,
                    "type": input_socket.type,
                    "default_value": safe_default
                }
                node_data["inputs"].append(input_data)
        except Exception as e:
            logger.warning(f"Failed to export input sockets for node {node.name}: {e}")
    
    @staticmethod
    def _export_output_sockets(node: bpy.types.Node, node_data: Dict[str, Any]) -> None:
        """Export output sockets"""
        try:
            for output_socket in node.outputs:
                output_data = {
                    "name": output_socket.name,
                    "type": output_socket.type
                }
                node_data["outputs"].append(output_data)
        except Exception as e:
            logger.warning(f"Failed to export output sockets for node {node.name}: {e}")
    
    @staticmethod
    def _export_node_links(node_tree: bpy.types.NodeTree) -> List[Dict[str, str]]:
        """Export node links with validation"""
        links_data = []
        try:
            for link in node_tree.links:
                link_data = {
                    "from_node": link.from_node.name,
                    "from_socket": link.from_socket.name,
                    "to_node": link.to_node.name,
                    "to_socket": link.to_socket.name
                }
                links_data.append(link_data)
        except Exception as e:
            logger.warning(f"Failed to export node links: {e}")
        
        return links_data

