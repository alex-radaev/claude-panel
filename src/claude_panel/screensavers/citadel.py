from rich.text import Text
import random
import math

# Citadel — true 3D fantasy world with orbiting camera
# Perspective projection, z-buffer, diffuse shading, atmospheric fog

random.seed(42)

# ── 3D Engine ──
CAM_R = 24.0       # orbit radius
CAM_H = 10.0       # camera height
LOOK_Y = 3.5       # look-at Y
FOV = 65.0          # field of view degrees
CHAR_AR = 0.48      # char width/height aspect ratio

focal = width / (2.0 * math.tan(math.radians(FOV / 2)))
pitch = math.atan2(CAM_H - LOOK_Y, CAM_R)
cos_p, sin_p = math.cos(pitch), math.sin(pitch)

# ── Helpers ──
def lc(a, b, t):
    t = max(0.0, min(1.0, t))
    return (int(a[0]+(b[0]-a[0])*t), int(a[1]+(b[1]-a[1])*t), int(a[2]+(b[2]-a[2])*t))

def rgb(c):
    return f"rgb({max(0,min(255,c[0]))},{max(0,min(255,c[1]))},{max(0,min(255,c[2]))})"

def fog_mix(c, d):
    f = 1.0 - math.exp(-d * 0.016)
    return lc(c, (80, 68, 100), f)

def shade_color(base, normal, light, dist):
    diff = max(0.0, normal[0]*light[0] + normal[1]*light[1] + normal[2]*light[2])
    b = 0.28 + 0.72 * diff
    c = (int(base[0]*b), int(base[1]*b), int(base[2]*b))
    return fog_mix(c, dist)

# ── Projection ──
def proj(wx, wy, wz, cc, sc, cx, cz):
    """Project world point to (screen_x, screen_y, depth) or None"""
    dx, dy, dz = wx - cx, wy - CAM_H, wz - cz
    # Yaw rotation
    ex = dx * cc - dz * sc
    ey = dy
    ez = dx * sc + dz * cc
    # Pitch rotation
    ey2 = ey * cos_p - ez * sin_p
    ez2 = ey * sin_p + ez * cos_p
    if ez2 > -0.5:
        return None
    sx = ex / (-ez2) * focal + width / 2
    sy = -ey2 / (-ez2) * focal * CHAR_AR + height / 2
    return (sx, sy, -ez2)

# ── Scene: Boxes [cx, cy_base, cz, half_w, h, half_d, color] ──
boxes = [
    # Central keep
    [0, 0, 0, 2.0, 12, 2.0, (148, 128, 102)],
    # Corner towers
    [-6, 0, -6, 1.4, 8.5, 1.4, (138, 120, 95)],
    [6, 0, -6, 1.4, 8.5, 1.4, (138, 120, 95)],
    [-6, 0, 6, 1.4, 8.5, 1.4, (138, 120, 95)],
    [6, 0, 6, 1.4, 8.5, 1.4, (138, 120, 95)],
    # Walls
    [0, 0, -6, 6, 5.5, 0.5, (128, 110, 88)],
    [0, 0, 6, 6, 5.5, 0.5, (128, 110, 88)],
    [-6, 0, 0, 0.5, 5.5, 6, (128, 110, 88)],
    [6, 0, 0, 0.5, 5.5, 6, (128, 110, 88)],
    # Gate tower
    [0, 0, -6.5, 1.2, 7, 1.0, (142, 122, 98)],
    # Houses
    [-11, 0, 3, 1.8, 3.8, 2.2, (158, 138, 110)],
    [-10, 0, -9, 2.2, 3.2, 1.8, (152, 132, 105)],
    [11, 0, -4, 2.0, 4.2, 1.8, (162, 142, 112)],
    [10, 0, 10, 1.8, 3.2, 2.2, (150, 130, 104)],
    [14, 0, 6, 1.4, 2.8, 1.4, (145, 125, 98)],
    [-14, 0, -5, 2.0, 3.8, 1.8, (155, 135, 108)],
    # Market stall
    [8, 0, -10, 1.5, 2.5, 1.0, (160, 140, 100)],
    # Well
    [-3, 0, -10, 0.6, 1.5, 0.6, (120, 110, 95)],
]

# ── Roofs: [cx, cz, half_w, half_d, base_y, peak_y, color] ──
roofs = [
    [0, 0, 2.3, 2.3, 12, 17, (88, 50, 38)],       # keep spire
    [-6, -6, 1.6, 1.6, 8.5, 12, (92, 52, 38)],     # tower roofs
    [6, -6, 1.6, 1.6, 8.5, 12, (92, 52, 38)],
    [-6, 6, 1.6, 1.6, 8.5, 12, (92, 52, 38)],
    [6, 6, 1.6, 1.6, 8.5, 12, (92, 52, 38)],
    [0, -6.5, 1.4, 1.2, 7, 10, (90, 50, 36)],      # gate tower
    [-11, 3, 2.1, 2.5, 3.8, 6.2, (108, 58, 32)],   # house roofs
    [-10, -9, 2.5, 2.1, 3.2, 5.4, (105, 55, 34)],
    [11, -4, 2.3, 2.1, 4.2, 6.8, (110, 58, 32)],
    [10, 10, 2.1, 2.5, 3.2, 5.5, (106, 56, 33)],
    [14, 6, 1.7, 1.7, 2.8, 4.5, (102, 54, 32)],
    [-14, -5, 2.3, 2.1, 3.8, 6.2, (108, 56, 34)],
    [8, -10, 1.8, 1.3, 2.5, 4.0, (115, 60, 30)],
]

# ── Trees: [cx, cz, trunk_h, crown_h, crown_r] ──
trees_data = []
for _ in range(22):
    tx = random.uniform(-22, 22)
    tz = random.uniform(-22, 22)
    if abs(tx) < 8.5 and abs(tz) < 8.5:
        continue
    trees_data.append([tx, tz, random.uniform(1.0, 2.0), random.uniform(1.5, 3.0), random.uniform(0.6, 1.4)])

# ── Embers ──
embers = []
for _ in range(30):
    embers.append({"x": random.uniform(-8, 8), "z": random.uniform(-8, 8),
                   "y": random.uniform(3, 12), "ph": random.uniform(0, 6.28),
                   "spd": random.uniform(0.02, 0.06)})

# ── Windows — mix of lit and dark for realism ──
lights = []      # lit windows (warm glow)
dark_windows = []  # unlit windows (dark rectangles)
for b in boxes:
    bx, by, bz, hw, bh, hd = b[0], b[1], b[2], b[3], b[4], b[5]
    if bh < 2.5:
        continue
    n_rows = max(1, int(bh / 3.0))
    all_sides = [
        (hw + 0.15, 0),    # +X face
        (-hw - 0.15, 0),   # -X face
        (0, hd + 0.15),    # +Z face
        (0, -hd - 0.15),   # -Z face
    ]
    for side in all_sides:
        for row in range(n_rows):
            wy = by + bh * (0.3 + 0.45 * row / max(1, n_rows - 1)) if n_rows > 1 else by + bh * 0.45
            win = {"x": bx + side[0], "y": wy, "z": bz + side[1],
                   "ph": random.uniform(0, 6.28)}
            # ~45% of windows are lit, rest are dark
            if random.random() < 0.45:
                win["glow"] = random.uniform(0.6, 1.0)
                lights.append(win)
            else:
                dark_windows.append(win)

random.seed()

# ── Sun direction (normalized) ──
sun_raw = (0.5, 0.7, -0.3)
sun_len = math.sqrt(sum(x*x for x in sun_raw))
SUN = tuple(x/sun_len for x in sun_raw)

def vis_x(x):
    return 0 <= x < width

# ── Face normals for axis-aligned boxes ──
FACE_NORMALS = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]

# ── Get visible faces of a box from camera ──
def box_faces(cx, cy, cz, hw, h, hd, cam_x, cam_z):
    """Returns list of (vertices_4, normal) for visible faces"""
    x0, x1 = cx - hw, cx + hw
    y0, y1 = cy, cy + h
    z0, z1 = cz - hd, cz + hd
    faces = []
    # +X face: visible if camera is on +X side
    if cam_x > cx:
        faces.append(([(x1,y0,z0),(x1,y0,z1),(x1,y1,z1),(x1,y1,z0)], (1,0,0)))
    # -X face
    if cam_x < cx:
        faces.append(([(x0,y0,z1),(x0,y0,z0),(x0,y1,z0),(x0,y1,z1)], (-1,0,0)))
    # +Z face
    if cam_z > cz:
        faces.append(([(x1,y0,z1),(x0,y0,z1),(x0,y1,z1),(x1,y1,z1)], (0,0,1)))
    # -Z face
    if cam_z < cz:
        faces.append(([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)], (0,0,-1)))
    # Top face: always visible (camera is above)
    faces.append(([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)], (0,1,0)))
    return faces

# ── Scanline fill a projected quad ──
def fill_face(verts_3d, normal, base_col, cc, sc, camx, camz, buf, cbuf, zbuf):
    projected = []
    for v in verts_3d:
        p = proj(v[0], v[1], v[2], cc, sc, camx, camz)
        if p is None:
            return
        projected.append(p)

    # Shade the face
    diff = max(0, normal[0]*SUN[0] + normal[1]*SUN[1] + normal[2]*SUN[2])
    b = 0.25 + 0.75 * diff
    sc_color = (int(base_col[0]*b), int(base_col[1]*b), int(base_col[2]*b))

    min_y = max(0, int(min(p[1] for p in projected)))
    max_y = min(height - 1, int(max(p[1] for p in projected)))

    for y in range(min_y, max_y + 1):
        xs = []
        n = len(projected)
        for i in range(n):
            j = (i + 1) % n
            y0, y1p = projected[i][1], projected[j][1]
            if (y0 <= y < y1p) or (y1p <= y < y0):
                if abs(y1p - y0) > 0.001:
                    t = (y - y0) / (y1p - y0)
                    x = projected[i][0] + t * (projected[j][0] - projected[i][0])
                    z = projected[i][2] + t * (projected[j][2] - projected[i][2])
                    xs.append((x, z))
        if len(xs) < 2:
            continue
        xs.sort()
        x_left, z_left = xs[0]
        x_right, z_right = xs[-1]
        ix0 = max(0, int(x_left))
        ix1 = min(width - 1, int(x_right))
        for x in range(ix0, ix1 + 1):
            t = (x - x_left) / max(0.001, x_right - x_left)
            z = z_left + t * (z_right - z_left)
            if z < zbuf[y][x]:
                zbuf[y][x] = z
                fc = fog_mix(sc_color, z)
                # Brick texture
                tx = ((y * 7 + x * 13) % 17)
                if normal[1] > 0.5:  # top face
                    ch = "░"
                elif tx < 2:
                    ch = "▓"
                else:
                    ch = "█"
                buf[y][x] = ch
                cbuf[y][x] = rgb(fc)

# ── Fill a triangle (for roofs) ──
def fill_tri(v0, v1, v2, normal, base_col, cc, sc, camx, camz, buf, cbuf, zbuf):
    projected = []
    for v in [v0, v1, v2]:
        p = proj(v[0], v[1], v[2], cc, sc, camx, camz)
        if p is None:
            return
        projected.append(p)

    diff = max(0, normal[0]*SUN[0] + normal[1]*SUN[1] + normal[2]*SUN[2])
    b = 0.25 + 0.75 * diff
    sc_col = (int(base_col[0]*b), int(base_col[1]*b), int(base_col[2]*b))

    min_y = max(0, int(min(p[1] for p in projected)))
    max_y = min(height - 1, int(max(p[1] for p in projected)))

    for y in range(min_y, max_y + 1):
        xs = []
        for i in range(3):
            j = (i + 1) % 3
            y0, y1p = projected[i][1], projected[j][1]
            if (y0 <= y < y1p) or (y1p <= y < y0):
                if abs(y1p - y0) > 0.001:
                    t = (y - y0) / (y1p - y0)
                    x = projected[i][0] + t * (projected[j][0] - projected[i][0])
                    z = projected[i][2] + t * (projected[j][2] - projected[i][2])
                    xs.append((x, z))
        if len(xs) < 2:
            continue
        xs.sort()
        x_left, z_left = xs[0]
        x_right, z_right = xs[-1]
        for x in range(max(0, int(x_left)), min(width - 1, int(x_right)) + 1):
            t = (x - x_left) / max(0.001, x_right - x_left)
            z = z_left + t * (z_right - z_left)
            if z < zbuf[y][x]:
                zbuf[y][x] = z
                fc = fog_mix(sc_col, z)
                buf[y][x] = "▓"
                cbuf[y][x] = rgb(fc)

# ══════════════════════════════════════════
# MAIN RENDER LOOP
# ══════════════════════════════════════════
for frame in range(3000):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    cbuf = [[""] * width for _ in range(height)]
    zbuf = [[999.0] * width for _ in range(height)]

    # Exactly 10 full orbits over 3000 frames → seamless loop restart
    cam_angle = frame * (20.0 * math.pi / 3000.0)
    cos_c = math.cos(cam_angle)
    sin_c = math.sin(cam_angle)
    cam_x = CAM_R * math.sin(cam_angle)
    cam_z = CAM_R * math.cos(cam_angle)

    # ═══ SKY ═══
    horizon = height // 2 - 2
    for y in range(height):
        t = y / max(1, height - 1)
        if t < 0.20:
            sky = lc((40, 65, 170), (70, 100, 190), t / 0.20)
        elif t < 0.38:
            sky = lc((70, 100, 190), (140, 110, 160), (t - 0.20) / 0.18)
        elif t < 0.50:
            sky = lc((140, 110, 160), (230, 140, 50), (t - 0.38) / 0.12)
        else:
            sky = lc((230, 140, 50), (255, 180, 60), min(1, (t - 0.50) / 0.10))
        for x in range(width):
            cbuf[y][x] = rgb(sky)

    # ═══ STARS ═══
    random.seed(7)
    for _ in range(50):
        sx = random.randint(0, width - 1)
        sy = random.randint(0, int(height * 0.35))
        br = random.uniform(0.3, 1.0)
        tw = 0.5 + 0.5 * math.sin(frame * 0.12 + sx * 0.3 + sy * 0.7)
        if tw * br > 0.4:
            v = int(130 + 125 * tw * br)
            buf[sy][sx] = random.choice(["·", "∗", "✦", "·"])
            cbuf[sy][sx] = f"rgb({v},{v},{min(255, v + 20)})"
    random.seed()

    # ═══ GROUND PLANE (optimized per-row raycasting) ═══
    for py in range(max(0, horizon - 3), height):
        dir_cy = (height / 2 - py) / (focal * CHAR_AR)
        dir_cz_cam = -1.0
        # Undo pitch (row-level, shared across all columns)
        dir_wy = dir_cy * cos_p + dir_cz_cam * sin_p
        dir_wz_p = -dir_cy * sin_p + dir_cz_cam * cos_p
        if dir_wy >= -0.001:
            continue
        t_ground = -CAM_H / dir_wy
        if t_ground < 0 or t_ground > 80:
            continue
        dist = t_ground
        fog_t = 1.0 - math.exp(-dist * 0.016)
        # Pre-compute yaw components for this row
        dwzp_sin = dir_wz_p * sin_c
        dwzp_cos = dir_wz_p * cos_c
        inv_focal = 1.0 / focal
        half_w = width / 2

        for px in range(width):
            if dist > zbuf[py][px]:
                continue
            dir_cx = (px - half_w) * inv_focal
            gx = cam_x + t_ground * (dir_cx * cos_c + dwzp_sin)
            gz = cam_z + t_ground * (-dir_cx * sin_c + dwzp_cos)

            # Fast texture — checkerboard + distance-based detail
            gxi = int(gx * 0.5 + 1000) # offset to avoid negative floor issues
            gzi = int(gz * 0.5 + 1000)
            on_grid = (gxi + gzi) % 2

            # Fast moat/path check
            d2 = gx * gx + gz * gz
            if 42 < d2 < 56:  # moat ring (r≈6.5-7.5)
                c = lc((25, 40, 75), (80, 68, 100), fog_t)
                ch = "≈"
            elif d2 > 49:  # outside moat
                # Simplified road check: 4 cardinal directions
                agx, agz = abs(gx), abs(gz)
                on_path = (agx < 0.8 and agz > 7) or (agz < 0.8 and agx > 7)
                if on_path:
                    c = lc((95, 82, 65), (80, 68, 100), fog_t)
                    ch = "░"
                elif on_grid:
                    c = lc((32, 52, 20), (80, 68, 100), fog_t)
                    ch = "," if dist < 15 else " "
                else:
                    c = lc((24, 42, 16), (80, 68, 100), fog_t)
                    ch = "'" if dist < 15 else " "
            else:  # inside castle walls — cobblestone
                c = lc((85, 75, 60), (80, 68, 100), fog_t)
                ch = "░" if on_grid else "▪"

            zbuf[py][px] = dist
            buf[py][px] = ch
            cbuf[py][px] = rgb(c)

    # ═══ BOXES (buildings, walls, towers) ═══
    # Sort by distance (painter's algorithm backup - z-buffer handles it)
    for b in boxes:
        bx, by, bz, hw, h, hd, col = b
        faces = box_faces(bx, by, bz, hw, h, hd, cam_x, cam_z)
        for verts, normal in faces:
            fill_face(verts, normal, col, cos_c, sin_c, cam_x, cam_z, buf, cbuf, zbuf)

    # ═══ ROOFS (pyramids as 4 triangles) ═══
    for r in roofs:
        rx, rz, rhw, rhd, rby, rpy, rcol = r
        # Peak point
        peak = (rx, rpy, rz)
        # Base corners
        c0 = (rx - rhw, rby, rz - rhd)
        c1 = (rx + rhw, rby, rz - rhd)
        c2 = (rx + rhw, rby, rz + rhd)
        c3 = (rx - rhw, rby, rz + rhd)
        # 4 triangular faces
        tri_faces = [
            (c0, c1, peak, (0, 0.5, -0.87)),   # front (-Z)
            (c1, c2, peak, (0.87, 0.5, 0)),     # right (+X)
            (c2, c3, peak, (0, 0.5, 0.87)),     # back (+Z)
            (c3, c0, peak, (-0.87, 0.5, 0)),    # left (-X)
        ]
        for v0, v1, v2, n in tri_faces:
            # Backface culling
            face_cx = (v0[0] + v1[0] + v2[0]) / 3
            face_cz = (v0[2] + v1[2] + v2[2]) / 3
            to_cam = (cam_x - face_cx, 0, cam_z - face_cz)
            dot = n[0] * to_cam[0] + n[2] * to_cam[2]
            if dot > 0:
                fill_tri(v0, v1, v2, n, rcol, cos_c, sin_c, cam_x, cam_z, buf, cbuf, zbuf)

    # ═══ TREES (billboard sprites) ═══
    for tr in trees_data:
        tx, tz, trunk_h, crown_h, crown_r = tr
        # Project trunk base and top
        p_base = proj(tx, 0, tz, cos_c, sin_c, cam_x, cam_z)
        p_trunk_top = proj(tx, trunk_h, tz, cos_c, sin_c, cam_x, cam_z)
        p_crown_top = proj(tx, trunk_h + crown_h, tz, cos_c, sin_c, cam_x, cam_z)
        if not p_base or not p_trunk_top or not p_crown_top:
            continue
        depth = p_base[2]
        if depth > 50:
            continue

        # Trunk
        tsx = int(p_base[0])
        for y in range(max(0, int(p_crown_top[1])), min(height, int(p_base[1]) + 1)):
            if vis_x(tsx) and depth < zbuf[y][tsx]:
                if y >= int(p_trunk_top[1]):
                    # Trunk
                    zbuf[y][tsx] = depth
                    buf[y][tsx] = "│"
                    cbuf[y][tsx] = rgb(fog_mix((80, 55, 28), depth))
                else:
                    # Crown
                    crown_frac = (y - int(p_crown_top[1])) / max(1, int(p_trunk_top[1]) - int(p_crown_top[1]))
                    crown_w = int(crown_r / depth * focal * (0.3 + crown_frac * 0.7))
                    for dx in range(-crown_w, crown_w + 1):
                        cx_s = tsx + dx
                        if vis_x(cx_s) and depth < zbuf[y][cx_s]:
                            zbuf[y][cx_s] = depth
                            g = 40 + int(crown_frac * 30) + random.randint(-5, 5)
                            buf[y][cx_s] = "█" if abs(dx) < crown_w else "▓"
                            cbuf[y][cx_s] = rgb(fog_mix((18, max(30, min(120, g)), 15), depth))

    # ═══ WINDOW LIGHTS ═══
    for light in lights:
        p = proj(light["x"], light["y"], light["z"], cos_c, sin_c, cam_x, cam_z)
        if not p:
            continue
        sx, sy, dep = int(p[0]), int(p[1]), p[2]
        if not vis_x(sx) or not (0 <= sy < height):
            continue
        if dep > zbuf[sy][sx] + 1.0:
            continue  # behind something far away
        fl = 0.65 + 0.35 * math.sin(frame * 0.18 + light["ph"])
        g = light["glow"] * fl
        wc = (int(255 * g), int(195 * g), int(55 * g))
        # Bright center
        buf[sy][sx] = "▪"
        cbuf[sy][sx] = f"bold rgb({wc[0]},{wc[1]},{wc[2]})"
        # Warm glow on adjacent stone (small radius for performance)
        for gdx in [-1, 0, 1]:
            for gdy in [-1, 0, 1]:
                if gdx == 0 and gdy == 0:
                    continue
                gx_s, gy_s = sx + gdx, sy + gdy
                if vis_x(gx_s) and 0 <= gy_s < height:
                    if buf[gy_s][gx_s] in ("█", "▓", "│", "▀", "░"):
                        ga = g * (0.3 if abs(gdx) + abs(gdy) < 2 else 0.15)
                        cbuf[gy_s][gx_s] = rgb(lc((110, 95, 75), (255, 180, 60), ga))

    # ═══ DARK WINDOWS ═══
    for dw in dark_windows:
        p = proj(dw["x"], dw["y"], dw["z"], cos_c, sin_c, cam_x, cam_z)
        if not p:
            continue
        sx, sy, dep = int(p[0]), int(p[1]), p[2]
        if not vis_x(sx) or not (0 <= sy < height):
            continue
        if dep > zbuf[sy][sx] + 1.0:
            continue
        buf[sy][sx] = "▫"
        cbuf[sy][sx] = "rgb(35,30,28)"

    # ═══ EMBERS ═══
    for e in embers:
        e["y"] += e["spd"]
        if e["y"] > 15:
            e["y"] = random.uniform(2, 5)
            e["x"] = random.uniform(-6, 6)
            e["z"] = random.uniform(-6, 6)
        ex = e["x"] + math.sin(frame * 0.06 + e["ph"]) * 1.5
        ez = e["z"] + math.cos(frame * 0.05 + e["ph"] * 1.3) * 1.5
        p = proj(ex, e["y"], ez, cos_c, sin_c, cam_x, cam_z)
        if not p:
            continue
        sx, sy, dep = int(p[0]), int(p[1]), p[2]
        if not vis_x(sx) or not (0 <= sy < height):
            continue
        br = 0.5 + 0.5 * math.sin(frame * 0.14 + e["ph"])
        if br > 0.4 and dep < zbuf[sy][sx]:
            r = int(255 * br)
            g = int(130 * br + 30)
            buf[sy][sx] = "✦" if br > 0.65 else "·"
            cbuf[sy][sx] = f"bold rgb({r},{g},15)"

    # ═══ RENDER ═══
    for y in range(height):
        line = Text()
        for x in range(width):
            c = cbuf[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.07)
