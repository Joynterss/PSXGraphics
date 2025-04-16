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
        model_name = os.path.splitext(os.path.basename(self.filepath))[0]
        print(f"Using model name: {model_name}")
        return export_model_to_c(self.filepath, model_name)

def scale_to_texture_space(verts, texture_width=256, texture_height=256):
    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)
    min_z = min(v[2] for v in verts)
    max_z = max(v[2] for v in verts)

    scale_x = texture_width / (max_x - min_x) if max_x != min_x else 1
    scale_y = texture_height / (max_y - min_y) if max_y != min_y else 1
    scale_z = texture_width / (max_z - min_z) if max_z != min_z else 1

    center_x = (max_x + min_x) / 2
    center_y = (max_y + min_y) / 2
    center_z = (max_z + min_z) / 2

    scaled_verts = []
    for vert in verts:
        x = (vert[0] - center_x) * scale_x
        y = (vert[1] - center_y) * scale_y
        z = (vert[2] - center_z) * scale_z
        scaled_verts.append((x, y, z))

    return scaled_verts

def export_model_to_c(filepath, model_name, scale_factor=3.5):
    print(f"Exporting model with name: {model_name}")

    TEXTURE_WIDTH = 256
    TEXTURE_HEIGHT = 256

    obj = bpy.context.active_object
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    mesh = obj_eval.to_mesh()

    # Get bounding box dimensions
    coords = [v.co for v in mesh.vertices]
    min_x = min(v.x for v in coords)
    max_x = max(v.x for v in coords)
    min_y = min(v.y for v in coords)
    max_y = max(v.y for v in coords)
    min_z = min(v.z for v in coords)
    max_z = max(v.z for v in coords)

    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    max_dim = max(size_x, size_y, size_z)

    # Compute center offset and normalization scale
    offset = mathutils.Vector((
        (min_x + max_x) / 2,
        (min_y + max_y) / 2,
        (min_z + max_z) / 2
    ))

    uniform_scale = (TEXTURE_WIDTH / 2) / max_dim * scale_factor  # Fit model into [-128, 128]

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
        if item in item_map:
            return item_map[item]
        index = len(item_list)
        item_map[item] = index
        item_list.append(item)
        return index

    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers else None

    for poly in mesh.polygons:
        v_idx = []
        n_idx = []
        uv_idx = []

        for loop_idx in poly.loop_indices:
            vert = mesh.vertices[mesh.loops[loop_idx].vertex_index].co - offset
            norm = mesh.loops[loop_idx].normal
            uv = uv_layer[loop_idx].uv if uv_layer else mathutils.Vector((0.0, 0.0))

            # Convert vertex coordinates with scaling and Y/Z swap
            v = (
                round(vert.x * uniform_scale, 2),
                round(-vert.z * uniform_scale, 2),
                round(vert.y * uniform_scale, 2)
            )

            n = (round(norm.x, 2), round(norm.y, 2), round(norm.z, 2))

            uv_px = (
                round(uv.x * TEXTURE_WIDTH, 2),
                round(uv.y * TEXTURE_HEIGHT, 2)
            )

            v_i = unique_insert(v, vertex_map, verts)
            n_i = unique_insert(n, normal_map, norms)
            uv_i = unique_insert(uv_px, uv_map, uvs)

            v_idx.append(v_i)
            n_idx.append(n_i)
            uv_idx.append(uv_i)

        if len(v_idx) == 3:
            # Convert triangle to fake quad with duplicate last index
            vertex_indices.append(f"{{{v_idx[0]},{v_idx[1]},{v_idx[2]},{v_idx[2]}}}")
            uv_indices.append(f"{{{uv_idx[0]},{uv_idx[1]},{uv_idx[2]},{uv_idx[2]}}}")
            normal_indices.extend([f"{n_idx[0]}", f"{n_idx[1]}", f"{n_idx[2]}", f"{n_idx[2]}"])
        elif len(v_idx) == 4:
            if len(v_idx) == 4:
            # Original winding (CW)
                vertex_indices.append(f"{{{v_idx[0]},{v_idx[1]},{v_idx[2]},{v_idx[3]}}}")
                uv_indices.append(f"{{{uv_idx[0]},{uv_idx[1]},{uv_idx[2]},{uv_idx[3]}}}")
                normal_indices.extend([f"{n_idx[0]}", f"{n_idx[1]}", f"{n_idx[2]}", f"{n_idx[3]}"])

                # Reversed winding (CCW)
                vertex_indices.append(f"{{{v_idx[3]},{v_idx[2]},{v_idx[1]},{v_idx[0]}}}")
                uv_indices.append(f"{{{uv_idx[3]},{uv_idx[2]},{uv_idx[1]},{uv_idx[0]}}}")
                normal_indices.extend([f"{n_idx[3]}", f"{n_idx[2]}", f"{n_idx[1]}", f"{n_idx[0]}"])



    verts_str = ',\n  '.join([f"{{{x},{y},{z}}}" for (x, y, z) in verts])
    norms_str = ',\n  '.join([f"{{{x},{y},{z}}}" for (x, y, z) in norms])
    uvs_str = ',\n  '.join([f"{{{x},{y}}}" for (x, y) in uvs])
    vertex_indices_str = ',\n  '.join(vertex_indices)
    uv_indices_str = ',\n  '.join(uv_indices)
    normal_indices_str = ',\n  '.join(normal_indices)

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
