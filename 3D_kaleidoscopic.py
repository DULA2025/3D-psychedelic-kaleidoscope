import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import noise

# Initialize Pygame and OpenGL
pygame.init()
width, height = 800, 800
display = (width, height)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

# Set up the perspective (using GLU or fallback to glFrustum)
def set_perspective(fov, aspect, near, far):
    try:
        gluPerspective(fov, aspect, near, far)
    except Exception as e:
        print(f"GLU failed: {e}. Using glFrustum fallback.")
        top = near * math.tan(math.radians(fov) / 2)
        bottom = -top
        right = top * aspect
        left = -right
        glFrustum(left, right, bottom, top, near, far)

set_perspective(45, width / height, 0.1, 50.0)
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glTranslatef(0.0, 0.0, -5)  # Move back to see the scene

# Global variables
rotate_speed = 0.01
pulse_factor = 1.0
frame_count = 0
y_rotation = 0  # For slow rotation around Y-axis
sparkles = []  # List to store sparkling particles

def hsb_to_rgb(h, s, b):
    """Convert HSB (0-360, 0-1, 0-1) to RGB (0-1, 0-1, 0-1) for OpenGL"""
    h = h % 360
    s, b = min(1.0, max(0.0, s)), min(1.0, max(0.0, b))
    if s == 0:
        return (b, b, b)
    h /= 60.0
    i = math.floor(h)
    f = h - i
    p = b * (1 - s)
    q = b * (1 - s * f)
    t = b * (1 - s * (1 - f))
    if i == 0:
        return (b, t, p)
    elif i == 1:
        return (q, b, p)
    elif i == 2:
        return (p, b, t)
    elif i == 3:
        return (p, q, b)
    elif i == 4:
        return (t, p, b)
    else:
        return (b, p, q)

def draw_sphere(x, y, z, radius, slices, stacks, color):
    """Draw a sphere at position (x, y, z) with given radius, slices, and stacks"""
    quad = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor4f(*color, 0.7)  # Semi-transparent
    gluSphere(quad, radius, slices, stacks)
    glPopMatrix()

def draw_triangle(x1, y1, z1, x2, y2, z2, x3, y3, z3, color):
    """Draw a triangle with vertices and color"""
    glBegin(GL_TRIANGLES)
    glColor4f(*color, 0.7)  # Semi-transparent
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y2, z2)
    glVertex3f(x3, y3, z3)
    glEnd()

def draw_sector():
    global frame_count, pulse_factor
    # Radial Lines (as 3D triangles)
    for k in range(4):
        angle = k * (math.pi / 8)
        length = (1.0 + 0.5 * math.sin(frame_count * 0.02 + k)) * pulse_factor
        hue = (frame_count * 5 + k * 90) % 360
        r, g, b = hsb_to_rgb(hue, 0.8, 1.0)
        color = (r, g, b)
        x1, y1 = 0, 0
        x2 = length * math.cos(angle)
        y2 = length * math.sin(angle)
        z2 = 0.2 * math.sin(frame_count * 0.01 + k)  # Depth
        draw_triangle(x1, y1, 0, x2, y2, z2, x2 * 0.9, y2 * 0.9, z2 * 0.9, color)

    # Bezier-like curves (as chains of small spheres)
    for m in range(6):
        offset = m * 0.2
        hue = (frame_count * 4 + m * 60) % 360
        r, g, b = hsb_to_rgb(hue, 0.8, 1.0)
        color = (r, g, b)
        points = []
        for t in range(0, 101, 5):
            t = t / 100.0
            x1, y1, z1 = 0.5 + offset, 0, 0
            x2 = 1.0 + offset + 0.2 * math.sin(frame_count * 0.03 + m)
            y2 = 0.5 * math.cos(frame_count * 0.02 + m)
            z2 = 0.1 * math.sin(frame_count * 0.02 + m)
            x3 = 1.5 + offset + 0.3 * math.sin(frame_count * 0.04 + m)
            y3 = 1.0 * math.cos(frame_count * 0.03 + m)
            z3 = 0.2 * math.sin(frame_count * 0.03 + m)
            x4, y4, z4 = 2.0 + offset, 0, 0
            mt = 1 - t
            x = mt**3 * x1 + 3 * mt**2 * t * x2 + 3 * mt * t**2 * x3 + t**3 * x4
            y = mt**3 * y1 + 3 * mt**2 * t * y2 + 3 * mt * t**2 * y3 + t**3 * y4
            z = mt**3 * z1 + 3 * mt**2 * t * z2 + 3 * mt * t**2 * z3 + t**3 * z4
            points.append((x, y, z))
        for i in range(len(points) - 1):
            draw_sphere(points[i][0], points[i][1], points[i][2], 0.05, 10, 10, color)

    # Ellipses (as spheres with varying sizes and positions)
    for j in range(25):
        x = 0.2 + j * 0.12
        noise_val = noise.pnoise2(x * 0.01, frame_count * 0.01)
        y = (noise_val - 0.5) * 1.8 * pulse_factor
        size = 0.15 + noise_val * 0.4
        hue = (frame_count * 3 + j * 14) % 360
        r, g, b = hsb_to_rgb(hue, 0.7, 1.0)
        z = 0.1 * math.sin(frame_count * 0.01 + j)  # Depth
        draw_sphere(x, y, z, size, 10, 10, (r, g, b))

def draw_core():
    global frame_count, pulse_factor
    core_size = 0.5 + 0.2 * math.sin(frame_count * 0.03) * pulse_factor
    core_hue = (frame_count * 6) % 360
    r, g, b = hsb_to_rgb(core_hue, 0.8, 1.0)
    draw_sphere(0, 0, 0, core_size, 20, 20, (r, g, b))

def update_sparkles():
    global sparkles, frame_count
    if len(sparkles) < 50:  # Limit number of sparkles for performance
        sparkles.append({
            'x': random.uniform(-5, 5),
            'y': random.uniform(-5, 5),
            'z': random.uniform(-1, 1),
            'size': random.uniform(0.05, 0.2),
            'lifetime': random.uniform(30, 60),
            'hue': random.uniform(0, 360)
        })
    for sparkle in sparkles[:]:
        sparkle['lifetime'] -= 1
        if sparkle['lifetime'] <= 0:
            sparkles.remove(sparkle)
        else:
            r, g, b = hsb_to_rgb(sparkle['hue'], 1.0, 1.0)
            draw_sphere(sparkle['x'], sparkle['y'], sparkle['z'], sparkle['size'], 8, 8, (r, g, b))
            sparkle['size'] *= 1.02  # Slight growth for sparkle effect
            sparkle['hue'] = (sparkle['hue'] + 1) % 360  # Color cycling

def main():
    global frame_count, rotate_speed, pulse_factor, y_rotation
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEMOTION:
                rotate_speed = map_value(event.pos[0], 0, width, 0.005, 0.02)
                pulse_factor = map_value(event.pos[1], 0, height, 0.8, 1.2)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear to black
        glPushMatrix()
        
        # Slow rotation around Y-axis
        y_rotation += 0.005  # Slow rotation speed
        glRotatef(y_rotation * 57.2958, 0, 1, 0)  # Convert radians to degrees

        # Draw 8 sectors rotated around Z-axis
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 0, 1)  # Rotate around Z for symmetry
            draw_sector()
            glPopMatrix()
        
        draw_core()

        # Draw sparkling light effects
        update_sparkles()

        glPopMatrix()
        
        pygame.display.flip()
        clock.tick(60)
        frame_count += 1

def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

if __name__ == "__main__":
    main()
