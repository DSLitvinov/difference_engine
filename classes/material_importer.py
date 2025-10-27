"""
Material and texture import functionality
"""
import bpy
import json
import os
import logging
from typing import Optional, Dict, Any, List

# Setup logging
logger = logging.getLogger(__name__)


class DFM_MaterialImporter:
    """Class for importing materials and textures"""
    
    # Node type mapping for special cases where simple conversion doesn't work
    NODE_TYPE_MAP = {
        # Common node types that don't follow the simple pattern
        'CURVE_FLOAT': 'ShaderNodeFloatCurve',
        'CURVE_RGB': 'ShaderNodeRGBCurve',
        'CURVE_VEC': 'ShaderNodeVectorCurve',
        'MAP_RANGE': 'ShaderNodeMapRange',
        'RGB': 'ShaderNodeRGB',
        'VALUE': 'ShaderNodeValue',
        'VALTORGB': 'ShaderNodeValToRGB',  # ColorRamp
        'RGBTOBW': 'ShaderNodeRGBToBW',
        # Add more special cases as needed
    }
    
    @staticmethod
    def import_material(material_file: str, import_path: str) -> Optional[bpy.types.Material]:
        """
        Import material from JSON and load textures.
        
        Reuses existing materials if found, otherwise creates new ones.
        
        Args:
            material_file: Path to material JSON file
            import_path: Base path for texture files
            
        Returns:
            Material object or None if import fails
        """
        try:
            logger.info(f"Importing material from: {material_file}")
            with open(material_file, 'r') as f:
                material_data = json.load(f)
            
            logger.debug(f"Material data keys: {material_data.keys()}")
            logger.debug(f"use_nodes: {material_data.get('use_nodes')}")
            logger.debug(f"nodes count: {len(material_data.get('nodes', []))}")
            logger.debug(f"links count: {len(material_data.get('links', []))}")
            
            # Create material with tmp_ prefix for imported materials
            original_name = material_data.get('name', 'ImportedMaterial')
            material_name = f"tmp_{original_name}"
            material = bpy.data.materials.get(material_name)
            
            if material:
                logger.info(f"Reusing existing imported material: {material_name}")
            else:
                material = bpy.data.materials.new(name=material_name)
                logger.info(f"Created new imported material: {material_name}")
            
            # Set basic properties with safe conversion
            if 'diffuse_color' in material_data:
                color = material_data['diffuse_color']
                # Ensure we only use RGB values (first 3 elements)
                if isinstance(color, (list, tuple)) and len(color) >= 3:
                    material.diffuse_color = color[:4]  # RGBA (4 values in Blender)
                    
            if 'specular_color' in material_data:
                color = material_data['specular_color']
                # Ensure we only use RGB values (first 3 elements)
                if isinstance(color, (list, tuple)) and len(color) >= 3:
                    material.specular_color = color[:3]  # RGB (3 values)
                    
            if 'roughness' in material_data:
                roughness = material_data['roughness']
                if isinstance(roughness, (int, float)):
                    material.roughness = float(roughness)
                    
            if 'metallic' in material_data:
                metallic = material_data['metallic']
                if isinstance(metallic, (int, float)):
                    material.metallic = float(metallic)
            
            # Setup node-based materials
            use_nodes = material_data.get('use_nodes', False)
            if use_nodes and 'nodes' in material_data:
                material.use_nodes = True
                DFM_MaterialImporter.import_node_tree(
                    material.node_tree, 
                    material_data['nodes'],
                    material_data.get('links', []),  # Add links parameter
                    import_path
                )
            
            return material
            
        except Exception as e:
            logger.error(f"Failed to import material: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def import_node_tree(node_tree: bpy.types.NodeTree, nodes_data: List[Dict[str, Any]], links_data: List[Dict[str, str]], import_path: str) -> None:
        """
        Import node tree structure with links.
        
        Args:
            node_tree: Blender node tree to populate
            nodes_data: List of node data dictionaries
            links_data: List of link data dictionaries
            import_path: Base path for texture files
        """
        # Clear existing nodes
        node_tree.nodes.clear()
        
        # Track created nodes for linking
        created_nodes = {}
        
        textures_dir = os.path.join(import_path, "textures")
        
        for node_data in nodes_data:
            # Create node with proper type conversion
            original_type = node_data.get('type', 'BSDF_PRINCIPLED')
            
            logger.debug(f"Processing node: {node_data.get('name', 'unnamed')} of type: {original_type}")
            
            # Convert node type from internal format to class name
            if original_type.startswith('ShaderNode'):
                # Already in correct format
                node_type = original_type
            elif original_type in DFM_MaterialImporter.NODE_TYPE_MAP:
                # Use explicit mapping for special cases
                node_type = DFM_MaterialImporter.NODE_TYPE_MAP[original_type]
                logger.debug(f"Mapped {original_type} → {node_type}")
            else:
                # Convert using simple pattern: BSDF_PRINCIPLED → ShaderNodeBsdfPrincipled
                parts = original_type.split('_')
                formatted_name = ''.join(word.capitalize() for word in parts)
                node_type = f'ShaderNode{formatted_name}'
                logger.debug(f"Converted {original_type} → {node_type}")
            
            try:
                node = node_tree.nodes.new(type=node_type)
                logger.debug(f"✓ Created node: {node.name}")
            except Exception as e:
                logger.error(f"✗ Failed to create node type '{node_type}' (from '{original_type}'): {e}")
                logger.error(f"  Hint: Add mapping for '{original_type}' in NODE_TYPE_MAP")
                continue
            
            # Set node properties safely
            if 'name' in node_data:
                node.name = node_data['name']
                
            if 'location' in node_data:
                loc = node_data['location']
                if isinstance(loc, (list, tuple)) and len(loc) >= 2:
                    node.location = [float(loc[0]), float(loc[1])]  # Only use X, Y
                    
            if 'width' in node_data:
                width = node_data['width']
                if isinstance(width, (int, float)):
                    node.width = float(width)
            
            # Handle image texture nodes FIRST (before other properties that depend on image being loaded)
            if node_data.get('type') == 'TEX_IMAGE':
                texture_file = node_data.get('copied_texture')
                if texture_file:
                    texture_path = os.path.join(textures_dir, texture_file)
                    if os.path.exists(texture_path):
                        try:
                            # Check if image is already loaded (texture caching)
                            image = bpy.data.images.get(texture_file)
                            if image:
                                logger.debug(f"Reusing cached texture: {texture_file}")
                                # Ensure the image filepath is set correctly
                                image.filepath = texture_path
                                # Reload the image data to ensure it's valid
                                image.reload()
                            else:
                                image = bpy.data.images.load(texture_path)
                                logger.debug(f"Loaded new texture: {texture_file} from {texture_path}")
                            
                            # Assign image to node
                            if hasattr(node, 'image'):
                                node.image = image
                                logger.debug(f"✓ Assigned texture {texture_file} to node {node.name}")
                                logger.debug(f"  Image size: {image.size[0]}x{image.size[1]}, Filepath: {image.filepath}")
                            else:
                                logger.error(f"✗ Node {node.name} doesn't have 'image' attribute!")
                        except Exception as e:
                            logger.error(f"Failed to load texture {texture_path}: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                    else:
                        logger.warning(f"Texture file not found: {texture_path}")
            
            # Restore node properties (AFTER image is loaded for TEX_IMAGE nodes)
            if 'properties' in node_data:
                props = node_data['properties']
                
                # Common properties
                if 'operation' in props and hasattr(node, 'operation'):
                    node.operation = props['operation']
                if 'blend_type' in props and hasattr(node, 'blend_type'):
                    node.blend_type = props['blend_type']
                if 'interpolation' in props and hasattr(node, 'interpolation'):
                    try:
                        node.interpolation = props['interpolation']
                    except Exception as e:
                        logger.warning(f"Failed to set interpolation: {e}")
                if 'extension' in props and hasattr(node, 'extension'):
                    try:
                        node.extension = props['extension']
                    except Exception as e:
                        logger.warning(f"Failed to set extension: {e}")
                if 'color_space' in props and hasattr(node, 'color_space'):
                    try:
                        node.color_space = props['color_space']
                    except Exception as e:
                        logger.warning(f"Failed to set color_space: {e}")
                if 'label' in props:
                    node.label = props['label']
                if 'hide' in props:
                    node.hide = props['hide']
                if 'mute' in props:
                    node.mute = props['mute']
                
                # Node Group restoration
                if 'node_tree_name' in props and hasattr(node, 'node_tree'):
                    node_tree_name = props['node_tree_name']
                    # Try to find the node group in the blend file
                    if node_tree_name in bpy.data.node_groups:
                        node.node_tree = bpy.data.node_groups[node_tree_name]
                        logger.info(f"Restored Group node reference: {node_tree_name}")
                    else:
                        logger.warning(f"Node group '{node_tree_name}' not found in blend file - Group node will be empty")
                
                # ColorRamp restoration
                if 'color_ramp' in props and hasattr(node, 'color_ramp'):
                    ramp_data = props['color_ramp']
                    ramp = node.color_ramp
                    
                    # Set ramp properties
                    if 'color_mode' in ramp_data:
                        ramp.color_mode = ramp_data['color_mode']
                    if 'interpolation' in ramp_data:
                        ramp.interpolation = ramp_data['interpolation']
                    
                    # Restore color stops
                    if 'elements' in ramp_data:
                        # Clear existing elements (keep at least 2)
                        while len(ramp.elements) > 2:
                            ramp.elements.remove(ramp.elements[0])
                        
                        # Add new elements
                        elements_data = ramp_data['elements']
                        for i, elem_data in enumerate(elements_data):
                            if i < len(ramp.elements):
                                # Update existing
                                elem = ramp.elements[i]
                            else:
                                # Create new
                                elem = ramp.elements.new(elem_data['position'])
                            
                            elem.position = elem_data['position']
                            if 'color' in elem_data:
                                elem.color = elem_data['color']
                
                # Curve restoration (Float, RGB, Vector)
                if 'mapping' in props and hasattr(node, 'mapping'):
                    curves_data = props['mapping']
                    mapping = node.mapping
                    
                    if 'use_clip' in curves_data and hasattr(mapping, 'use_clip'):
                        mapping.use_clip = curves_data['use_clip']
                    
                    if 'curves' in curves_data:
                        for curve_idx, curve_points in enumerate(curves_data['curves']):
                            if curve_idx < len(mapping.curves):
                                curve = mapping.curves[curve_idx]
                                
                                # Clear existing points
                                while len(curve.points) > 0:
                                    curve.points.remove(curve.points[0])
                                
                                # Add points
                                for point_data in curve_points:
                                    point = curve.points.new(point_data['location'][0], 
                                                            point_data['location'][1])
                                    if 'handle_type' in point_data:
                                        point.handle_type = point_data['handle_type']
                        
                        # Update the mapping
                        mapping.update()
            
            # Set input default values
            if 'inputs' in node_data:
                for i, input_data in enumerate(node_data['inputs']):
                    if i < len(node.inputs):
                        default_value = input_data.get('default_value')
                        if default_value is not None:
                            try:
                                node.inputs[i].default_value = default_value
                            except (TypeError, AttributeError, ValueError) as e:
                                # Some sockets might not accept the value or wrong size
                                logger.debug(f"Skipped setting default_value for {node.name}.{node.inputs[i].name}: {e}")
                                pass
            
            created_nodes[node_data['name']] = node
        
        # Create node links (connections between nodes)
        for link_data in links_data:
            try:
                from_node = created_nodes.get(link_data['from_node'])
                to_node = created_nodes.get(link_data['to_node'])
                
                if from_node and to_node:
                    from_socket = None
                    to_socket = None
                    
                    # Find the output socket
                    for output in from_node.outputs:
                        if output.name == link_data['from_socket']:
                            from_socket = output
                            break
                    
                    # Find the input socket
                    for input in to_node.inputs:
                        if input.name == link_data['to_socket']:
                            to_socket = input
                            break
                    
                    # Create the link
                    if from_socket and to_socket:
                        node_tree.links.new(from_socket, to_socket)
                        logger.debug(f"Linked {from_node.name}.{from_socket.name} to {to_node.name}.{to_socket.name}")
                    else:
                        if not from_socket:
                            logger.warning(f"Socket not found: {link_data['from_node']}.{link_data['from_socket']}")
                        if not to_socket:
                            logger.warning(f"Socket not found: {link_data['to_node']}.{link_data['to_socket']}")
                else:
                    if not from_node:
                        logger.warning(f"Node not found: {link_data['from_node']}")
                    if not to_node:
                        logger.warning(f"Node not found: {link_data['to_node']}")
            except Exception as e:
                logger.warning(f"Failed to create link: {e}")

