import pygame
import math
import numpy as np
from pygame.locals import QUIT, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
import os

def load_obj_c_model(base_name, base_path):
    obj_c_path = os.path.join(base_path, "cout", f"{base_name}.c")
    if not os.path.exists(obj_c_path):
        raise FileNotFoundError(f"Could not find {obj_c_path}")

    vertices = []
    normals = []
    uvs = []
    vertex_indices = []  # Keep this as a list of lists
    uv_indices = []
    normal_indices = []

    with open(obj_c_path, "r") as file:
        in_vertex_array = False
        in_normal_array = False
        in_uv_array = False
        in_vertex_indices = False
        in_uv_indices = False
        in_normal_indices = False

        for line in file:
            line = line.strip()

            # Vertex array
            if "SVECTOR" in line and "_verts" in line:
                in_vertex_array = True
                continue
            if in_vertex_array:
                if line.startswith("};"):
                    in_vertex_array = False
                elif "{" in line and "}" in line:
                    parts = line.strip("{} ,").split(",")
                    if len(parts) >= 3:
                        x, y, z = map(float, parts[:3])
                        vertices.append((x, y, z))

            # Normal array
            if "SVECTOR" in line and "_norms" in line:
                in_normal_array = True
                continue
            if in_normal_array:
                if line.startswith("};"):
                    in_normal_array = False
                elif "{" in line and "}" in line:
                    parts = line.strip("{} ,").split(",")
                    if len(parts) >= 3:
                        x, y, z = map(float, parts[:3])
                        normals.append((x, y, z))

            # UV array
            if "SVECTOR" in line and "_uv" in line:
                in_uv_array = True
                continue
            if in_uv_array:
                if line.startswith("};"):
                    in_uv_array = False
                elif "{" in line and "}" in line:
                    parts = line.strip("{} ,").split(",")
                    if len(parts) >= 2:
                        u, v = map(float, parts[:2])
                        uvs.append((u, v))

            # Vertex indices array
            if "INDEX" in line and "_vertex_indices" in line:
                in_vertex_indices = True
                continue
            if in_vertex_indices:
                if line.startswith("};"):
                    in_vertex_indices = False
                elif "{" in line and "}" in line:
                    parts = line.strip("{} ,").split(",")
                    vertex_indices.append([int(i) for i in parts])

            # UV indices array
            if "INDEX" in line and "_uv_indices" in line:
                in_uv_indices = True
                continue
            if in_uv_indices:
                if line.startswith("};"):
                    in_uv_indices = False
                elif "{" in line and "}" in line:
                    parts = line.strip("{} ,").split(",")
                    uv_indices.append([int(i) for i in parts])

            # Normal indices array
  
            if "int" in line and "_normal_indices" in line:
                in_normal_indices = True
                continue
            if in_normal_indices:
                if line.startswith("};"):
                    in_normal_indices = False
                elif "{" in line and "}" in line:
                    parts = line.strip("{} ,").split(",")
                    try:
                        normal_indices.extend([int(i) for i in parts])
                    except ValueError:
                        print(f"Skipping invalid line in normal_indices: {line}")


    # Convert the lists to numpy arrays for mathematical operations
    vertices = np.array(vertices, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    uvs = np.array(uvs, dtype=np.float32)

    # No need to convert vertex_indices to numpy array since it’s a list of lists
    vertex_indices = [list(map(int, idx)) for idx in vertex_indices]  # Ensure all indices are integers
    uv_indices = [list(map(int, idx)) for idx in uv_indices]
    normal_indices = np.array(normal_indices, dtype=np.int32)

    return vertices, normals, uvs, vertex_indices, uv_indices, normal_indices

def render_model(base_name, base_path):
    screen_width, screen_height = 800, 600

    try:
        vertices, _, _, vertex_indices, _, _ = load_obj_c_model(base_name, base_path)
    except FileNotFoundError as e:
        print(str(e))
        return

    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("Joynters - Wireframe")

    vertices = np.array(vertices, dtype=np.float32)

    # Center the model at the origin and adjust scale
    center = vertices.mean(axis=0)
    vertices -= center  # Shift all vertices to make the center the origin

    # Scale down to fit within the screen view
    scale_factor = 10  # Adjust scale for better viewing
    vertices *= scale_factor

    # Initialize rotation angles and momentum
    angle_x, angle_y = 0, 0
    angular_velocity = np.array([0.0, 0.3], dtype=np.float32)  # Angular velocity for X and Y

    # Define the camera's position relative to the object (fixed position along the Z-axis)
    camera_position = np.array([0.0, 0.0, 5000.0], dtype=np.float32)  # Camera at Z = 500, looking at the object
    camera_distance = 500  # Set the camera's "view distance" from the object

    clock = pygame.time.Clock()

    is_dragging = False
    last_mouse_pos = (0, 0)
    rotation_speed = 0.1  # Adjust rotation speed for responsiveness

    dt = clock.tick(60) / 1000.0  # Delta time for smoother rotation
    friction = .99  # Momentum friction to slow down over time
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                is_dragging = True
                last_mouse_pos = event.pos
                
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                is_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if is_dragging:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]

                    # Update rotation angles
                    angle_y -= dx * rotation_speed  # Horizontal movement (left/right spin)
                    angle_x += dy * rotation_speed  # Vertical movement (up/down spin)

                    # Update angular velocity for momentum (horizontal and vertical)
                    angular_velocity[1] = -dx * rotation_speed  # Left/right spin
                    angular_velocity[0] = dy * rotation_speed  # Up/down spin

                    last_mouse_pos = event.pos

        # Apply momentum if not dragging
        if not is_dragging:
            # Always apply angular velocity to keep the spin going
            angle_x += angular_velocity[0] * dt
            angle_y += angular_velocity[1] * dt
            angular_velocity *= friction  # Friction slows it over time

            # Ensure it keeps spinning indefinitely while flattening
            if np.linalg.norm(angular_velocity) < 0.2:
                angular_velocity[1] = 0.3  # Maintain a small constant spin around Y-axis

        # Gradually flatten to the horizontal position while keeping the spin
        if abs(angle_x) > 0.1:
            # Speed up the flattening process
            angle_x -= np.sign(angle_x) * 0.1  # Faster flattening speed (was 0.05)

        else:
            angle_x = 0  # Make sure it's exactly flat

        # If the momentum slows down below a threshold, start to flatten the object
        if np.linalg.norm(angular_velocity) < 0.05:  # Threshold for stopping the spin
            if abs(angle_x) > 0.1:
                angle_x -= np.sign(angle_x) * 0.1  # Faster flattening (was 0.05)
            else:
                angle_x = 0  # Completely flatten
                angular_velocity = np.array([0.0, 0.0], dtype=np.float32)  # Stop the spin

        # Wrap rotation angles to keep them within a range (-180 to 180)
        angle_y %= 360
        if angle_y > 180:
            angle_y -= 360

        # Rotate and render
        rotated_vertices = rotate_vertices(vertices, angle_x, angle_y)

        # Now apply the camera position for proper perspective view
        projected_vertices = prepare_vertices(rotated_vertices, screen_width, screen_height, camera_position, camera_distance)


        screen.fill((0, 0, 0))  # Clear screen

        # In render_model(), replace the face drawing code with the following:
        
        for face in vertex_indices:
            pts = [projected_vertices[i] for i in face if i < len(projected_vertices)]
    

            if len(pts) > 1:
                for i in range(len(pts)):
                    start = pts[i]
                    end = pts[(i + 1) % len(pts)]
                    pygame.draw.line(screen, (0, 255, 0), start, end, width=1)



        font = pygame.font.SysFont(None, 24)

        lines = [
            "Joynters  Modeling  Machine",
            " -  For  PSX  Development  -"
        ]

        for i, line in enumerate(lines):
            label_surface = font.render(line, True, (0, 240, 0))
            screen.blit(label_surface, (10, 10 + i * 20))  # Adjust 20 for line spacing

        pygame.display.flip()

    pygame.quit()  # Quit after the loop is done

def barycentric(p, a, b, c):
    # Barycentric interpolation function to calculate texture coordinates inside the triangle
    detT = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if detT == 0:
        return (0, 0, 0)
    alpha = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / detT
    beta = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / detT
    gamma = 1 - alpha - beta
    return alpha, beta, gamma

def parse_normal_indices(file_content):
    normal_indices = []
    in_normal_indices = False
    
    for line in file_content:
        # Check if we're in the _normal_indices section
        if "int _normal_indices" in line:
            in_normal_indices = True
            continue
        
        # Parse the normal indices only if we are in the relevant section
        if in_normal_indices:
            if line.startswith("};"):
                in_normal_indices = False  # End of the section
            elif "{" in line and "}" in line:
                # Clean the line and parse integers
                line = line.strip("{} \n")
                indices = line.split(",")
                try:
                    normal_indices.extend([int(i.strip()) for i in indices])
                except ValueError:
                    print(f"Skipping invalid line in normal_indices: {line}")
    
    return normal_indices


def prepare_vertices(vertices, screen_width, screen_height, camera_position, camera_distance):
    projected_vertices = []
    for v in vertices:
        x, y, z = v - camera_position  # Shift vertices based on the camera position
        # Ensure no division by zero
        if z + camera_distance != 0:  
            projected_x = int(x / (z + camera_distance) * screen_width / 2 + screen_width / 2)
            projected_y = int(-y / (z + camera_distance) * screen_height / 2 + screen_height / 2)
            projected_vertices.append((projected_x, projected_y))
    return projected_vertices



def rotate_vertices(verts, angle_x, angle_y):
    cosx, sinx = math.cos(angle_x), math.sin(angle_x)
    cosy, siny = math.cos(angle_y), math.sin(angle_y)

    rotated = []
    for x, y, z in verts:
        # Rotate around Y-axis (yaw) first (left/right)
        x1 = x * cosy + z * siny
        z1 = -x * siny + z * cosy

        # Then rotate around X-axis (pitch) (up/down)
        y2 = y * cosx - z1 * sinx
        z2 = y * sinx + z1 * cosx

        rotated.append((x1, y2, z2))

    return np.array(rotated, dtype=np.float32)

if __name__ == "__main__":
    base_path = "C:\\thing\\thing\\thing\\PSXGraphics"
    base_name = input("Enter the base name (without extension): ").strip()
    render_model(base_name, base_path)
