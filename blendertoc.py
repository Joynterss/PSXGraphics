import bpy
import os
import mathutils
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

class ExportPSXModel(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.psxmodel"
    bl_label = "Export PSX Model (.c)"
    filename_ext = ".c"
    filter_glob: StringProperty(default='*.c', options={'HIDDEN'})

    model_name: StringProperty(
        name="Model Name",
        description="Name to use for arrays inside the .c file",
        default="mymodel"
    )

    def execute(self, context):
        # Extract model name from the chosen file path
        model_name = os.path.splitext(os.path.basename(self.filepath))[0]
        print(f"Using model name: {model_name}")
        return export_model_to_c(self.filepath, model_name)


def export_model_to_c(filepath, model_name, scale_factor=200.0):
    # First, explicitly set the model_name to ensure it's properly passed and used
    print(f"Exporting model with name: {model_name}")  # Debug print to verify the model_name
    
    obj = bpy.context.active_object
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()

    # Initialize maps and lists for storing the vertices, normals, and UVs
    vertex_map = {}
    normal_map = {}
    uv_map = {}

    verts = []
    norms = []
    uvs = []
    vertex_indices = []
    uv_indices = []
    normal_indices = []

    def unique_insert(item, item_map, item_list):
        """Helper function to insert unique items and return their index"""
        if item in item_map:
            return item_map[item]
        index = len(item_list)
        item_map[item] = index
        item_list.append(item)
        return index

    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers else None

    # Loop through each polygon in the mesh
    for poly in mesh.polygons:
        v_idx = []
        n_idx = []
        uv_idx = []

        # Loop through each vertex of the polygon
        for loop_idx in poly.loop_indices:
            vert = mesh.vertices[mesh.loops[loop_idx].vertex_index].co
            norm = mesh.loops[loop_idx].normal
            uv = uv_layer[loop_idx].uv if uv_layer else mathutils.Vector((0.0, 0.0))

            # Scale the vertices and normalize the normal vectors
            # Swap Y and Z, and invert the new Y (to turn Blender +Y into PSX -Z)
            v = (
                round(vert.x * scale_factor, 2),
                round(-vert.z * scale_factor, 2),
                round(vert.y * scale_factor, 2)
            )

            n = (round(norm.x, 2), round(norm.y, 2), round(norm.z, 2))
            uv_int = (round(uv.x, 2), round(uv.y, 2))

            # Insert the vertices, normals, and UVs into the respective lists
            v_i = unique_insert(v, vertex_map, verts)
            n_i = unique_insert(n, normal_map, norms)
            uv_i = unique_insert(uv_int, uv_map, uvs)

            v_idx.append(v_i)
            n_idx.append(n_i)
            uv_idx.append(uv_i)

            # After collecting v_idx, n_idx, uv_idx (CCW)
            # Reverse the winding order for PS1 (CW)
            v_idx = v_idx[::-1]
            n_idx = n_idx[::-1]
            uv_idx = uv_idx[::-1]



        # Adjust for quads by copying the last vertex, normal, and UV
        if len(v_idx) == 3:
            v_idx.append(v_idx[2])
            n_idx.append(n_idx[2])
            uv_idx.append(uv_idx[2])

        # Store the indices for the vertices, normals, and UVs
        vertex_indices.append(f"{{{v_idx[0]},{v_idx[1]},{v_idx[2]},{v_idx[3]}}}")
        uv_indices.append(f"{{{uv_idx[0]},{uv_idx[1]},{uv_idx[2]},{uv_idx[3]}}}")
        normal_indices.append(f"{n_idx[0]}")

    # Convert lists of vertices, normals, UVs, and indices to string format for C
    verts_str = ',\n  '.join([f"{{{x},{y},{z}}}" for (x, y, z) in verts])
    norms_str = ',\n  '.join([f"{{{x},{y},{z}}}" for (x, y, z) in norms])
    uvs_str = ',\n  '.join([f"{{{x},{y}}}" for (x, y) in uvs])
    vertex_indices_str = ',\n  '.join(vertex_indices)
    uv_indices_str = ',\n  '.join(uv_indices)
    normal_indices_str = ',\n  '.join(normal_indices)

    # Use the model_name for all variables in the C content
    c_content = f"""#include <psxgte.h>
#include "../display.h"

int {model_name}_num_faces = {len(vertex_indices)};  // {model_name} face count

SVECTOR {model_name}_verts[] = {{
  {verts_str}
}}; 

SVECTOR {model_name}_norms[] = {{
  {norms_str}
}}; 

INDEX {model_name}_vertex_indices[] = {{
  {vertex_indices_str}
}}; 

INDEX {model_name}_uv_indices[] = {{
  {uv_indices_str}
}}; 

int {model_name}_normal_indices[] = {{
  {normal_indices_str}
}}; 

SVECTOR {model_name}_uv[] = {{
  {uvs_str}
}}; 
"""

    # Write the C content to the file
    try:
        with open(filepath, "w") as file:
            file.write(c_content)
        print(f"Exported {model_name}.c to {filepath}")
        return {'FINISHED'}
    except Exception as e:
        print(f"Error while saving the file: {e}")
        return {'CANCELLED'}

def menu_func_export(self, context):
    self.layout.operator(ExportPSXModel.bl_idname, text="PlayStation Model (.c)")

def register():
    bpy.utils.register_class(ExportPSXModel)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportPSXModel)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
