
"""
ОКФРС. Практика 9. Задание 5.
Интерактивный 3D-редактор меша с автоматическим склеиванием граней.
Премиум-стиль 2026.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import sys, os, math, struct, random
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# ПАЛИТРА
# ============================================================
BG_DEEP    = "#08090f"
BG_GLASS   = "#131823"
BG_GRAPH   = "#050810"
BG_PANEL   = "#0f141c"
BG_CELL    = "#0e1218"
BORDER     = "#232a3d"
BORDER_HL  = "#2f3648"

NEON_CYAN  = "#00f0ff"
NEON_GREEN = "#39ff88"
NEON_PINK  = "#ff3ea5"
NEON_PURP  = "#a066ff"
NEON_AMBER = "#ffb830"
NEON_RED   = "#ff4d5e"
NEON_BLUE  = "#4d8dff"

TEXT_MAIN  = "#e8f0ff"
TEXT_DIM   = "#5a6780"

FONT_MONO  = ("Consolas", 13, "bold")
FONT_MONO_S= ("Consolas", 10)
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_LABEL_S = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 20, "bold")


def lerp(c1, c2, t):
    t = max(0.0, min(1.0, float(t)))
    try:
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    except Exception:
        return c1
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(r1 + (r2 - r1) * t))),
        max(0, min(255, int(g1 + (g2 - g1) * t))),
        max(0, min(255, int(b1 + (b2 - b1) * t))))


def round_rect(canvas, x1, y1, x2, y2, r,
               fill=None, outline=None, width=1, tags=""):
    pts = []
    steps = 8
    for i in range(steps + 1):
        a = math.pi + (math.pi / 2) * (i / steps)
        pts.extend([x1 + r + r * math.cos(a), y1 + r + r * math.sin(a)])
    for i in range(steps + 1):
        a = -math.pi/2 + (math.pi / 2) * (i / steps)
        pts.extend([x2 - r + r * math.cos(a), y1 + r + r * math.sin(a)])
    for i in range(steps + 1):
        a = 0 + (math.pi / 2) * (i / steps)
        pts.extend([x2 - r + r * math.cos(a), y2 - r + r * math.sin(a)])
    for i in range(steps + 1):
        a = math.pi/2 + (math.pi / 2) * (i / steps)
        pts.extend([x1 + r + r * math.cos(a), y2 - r + r * math.sin(a)])
    return canvas.create_polygon(pts, fill=fill or "", outline=outline or "",
                                 width=width, smooth=False, tags=tags)


# ============================================================
# МАТЕМАТИКА
# ============================================================
def v_sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def v_cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])

def v_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def v_length(v):
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def v_norm(v):
    l = v_length(v)
    if l < 1e-12:
        return (0, 0, 0)
    return (v[0]/l, v[1]/l, v[2]/l)

def v_dist(a, b):
    return v_length(v_sub(a, b))


class Triangle:
    def __init__(self, v1, v2, v3):
        self.v1 = tuple(v1)
        self.v2 = tuple(v2)
        self.v3 = tuple(v3)
        self.normal = v_norm(v_cross(v_sub(self.v2, self.v1),
                                       v_sub(self.v3, self.v1)))

    def area(self):
        return 0.5 * v_length(v_cross(v_sub(self.v2, self.v1),
                                       v_sub(self.v3, self.v1)))

    def centroid(self):
        return ((self.v1[0]+self.v2[0]+self.v3[0])/3,
                (self.v1[1]+self.v2[1]+self.v3[1])/3,
                (self.v1[2]+self.v2[2]+self.v3[2])/3)


# ============================================================
# СТРУКТУРА МЕША
# ============================================================
class Mesh:
    def __init__(self):
        self.vertices = []
        self.triangles = []

    def add_vertex(self, v):
        self.vertices.append(tuple(v))
        return len(self.vertices) - 1

    def add_triangle(self, i1, i2, i3):
        if i1 == i2 or i2 == i3 or i1 == i3:
            return False
        self.triangles.append((i1, i2, i3))
        return True

    def get_tri_coords(self):
        out = []
        for (i1, i2, i3) in self.triangles:
            if i1 < len(self.vertices) and i2 < len(self.vertices) and i3 < len(self.vertices):
                out.append(Triangle(self.vertices[i1],
                                     self.vertices[i2],
                                     self.vertices[i3]))
        return out

    def count_edges(self):
        edges = set()
        for (i1, i2, i3) in self.triangles:
            for a, b in [(i1,i2), (i2,i3), (i3,i1)]:
                edges.add(tuple(sorted([a, b])))
        return len(edges)

    def find_hanging_vertices(self):
        used = set()
        for (i1, i2, i3) in self.triangles:
            used.add(i1); used.add(i2); used.add(i3)
        return [i for i in range(len(self.vertices)) if i not in used]

    def weld(self, eps=0.001):
        n = len(self.vertices)
        if n == 0:
            return 0, 0

        groups = defaultdict(list)
        for i, v in enumerate(self.vertices):
            key = (round(v[0] / eps), round(v[1] / eps), round(v[2] / eps))
            groups[key].append(i)

        cluster_map = {}
        new_vertices = []
        cluster_keys = list(groups.keys())

        for key in cluster_keys:
            idxs = groups[key]
            mx = sum(self.vertices[i][0] for i in idxs) / len(idxs)
            my = sum(self.vertices[i][1] for i in idxs) / len(idxs)
            mz = sum(self.vertices[i][2] for i in idxs) / len(idxs)
            new_idx = len(new_vertices)
            new_vertices.append((mx, my, mz))
            for i in idxs:
                cluster_map[i] = new_idx

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dx == 0 and dy == 0 and dz == 0:
                        continue
                    for key in cluster_keys:
                        neighbor_key = (key[0]+dx, key[1]+dy, key[2]+dz)
                        if neighbor_key in groups:
                            idx_new = new_vertices[cluster_map[groups[key][0]]]
                            n_idxs = groups[neighbor_key]
                            mx2 = sum(self.vertices[i][0] for i in n_idxs) / len(n_idxs)
                            my2 = sum(self.vertices[i][1] for i in n_idxs) / len(n_idxs)
                            mz2 = sum(self.vertices[i][2] for i in n_idxs) / len(n_idxs)
                            if v_dist(idx_new, (mx2, my2, mz2)) < eps:
                                for i in n_idxs:
                                    cluster_map[i] = cluster_map[groups[key][0]]

        new_triangles = []
        seen = set()
        for (i1, i2, i3) in self.triangles:
            a = cluster_map[i1]
            b = cluster_map[i2]
            c = cluster_map[i3]
            if a == b or b == c or a == c:
                continue
            key = tuple(sorted([a, b, c]))
            if key in seen:
                continue
            seen.add(key)
            new_triangles.append((a, b, c))

        n_merged = n - len(new_vertices)
        n_removed_tris = len(self.triangles) - len(new_triangles)

        self.vertices = new_vertices
        self.triangles = new_triangles
        return n_merged, n_removed_tris


# ============================================================
# ЧТЕНИЕ / ЗАПИСЬ STL
# ============================================================
def read_ascii_stl(path):
    import re
    triangles = []
    name = "object"
    with open(path, "r", encoding="ascii", errors="replace") as f:
        content = f.read()
    m = re.search(r"solid\s+(\S+)", content)
    if m: name = m.group(1)
    pattern = re.compile(
        r"facet\s+normal\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)",
        re.DOTALL)
    for match in pattern.finditer(content):
        vals = [float(x) for x in match.groups()]
        triangles.append((tuple(vals[3:6]), tuple(vals[6:9]), tuple(vals[9:12])))
    return triangles, name


def read_binary_stl(path):
    with open(path, "rb") as f:
        header = f.read(80)
        cb = f.read(4)
        if len(cb) < 4:
            raise ValueError("Маленький файл")
        n = struct.unpack("<I", cb)[0]
        triangles = []
        for _ in range(n):
            data = f.read(50)
            if len(data) < 50: break
            vals = struct.unpack("<12fH", data)
            triangles.append((tuple(vals[3:6]), tuple(vals[6:9]), tuple(vals[9:12])))
        name = header[:80].decode("ascii", errors="replace").strip() or "binary"
        return triangles, name


def detect_and_read(path):
    with open(path, "rb") as f:
        head = f.read(500)
    if b"facet normal" in head or b"endsolid" in head:
        return read_ascii_stl(path)
    try:
        size = os.path.getsize(path)
        if size >= 84:
            with open(path, "rb") as f:
                f.seek(80)
                n = struct.unpack("<I", f.read(4))[0]
                if size == 84 + 50 * n:
                    return read_binary_stl(path)
    except Exception:
        pass
    if head.startswith(b"solid"):
        return read_ascii_stl(path)
    return read_binary_stl(path)


def save_binary_stl(path, triangles, name="object"):
    with open(path, "wb") as f:
        f.write((f"OKFRS STL - {name}").encode("ascii")[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(triangles)))
        for (v1, v2, v3) in triangles:
            n = v_norm(v_cross(v_sub(v2, v1), v_sub(v3, v1)))
            f.write(struct.pack("<fff", *n))
            for v in (v1, v2, v3):
                f.write(struct.pack("<fff", *v))
            f.write(struct.pack("<H", 0))


def save_ascii_stl(path, triangles, name="object"):
    with open(path, "w", encoding="ascii") as f:
        f.write(f"solid {name}\n")
        for (v1, v2, v3) in triangles:
            n = v_norm(v_cross(v_sub(v2, v1), v_sub(v3, v1)))
            f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
            f.write(f"    outer loop\n")
            for v in (v1, v2, v3):
                f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        f.write(f"endsolid {name}\n")


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.mesh = Mesh()
        self.name = "custom"
        self.loaded_file = None
        self.rot_z = math.radians(30)
        self.rot_x = math.radians(20)
        self.zoom = 1.0
        self.size = 1.0
        self.center = (0, 0, 0)
        self.drag_view = None
        self.snap_enabled = True
        self.snap_step = 0.1
        self.weld_eps = 0.001
        self.selected_vertex = None
        self.show_grid = True

    def update_center(self):
        if not self.mesh.vertices:
            self.center = (0, 0, 0)
            self.size = 2
            return
        xs = [v[0] for v in self.mesh.vertices]
        ys = [v[1] for v in self.mesh.vertices]
        zs = [v[2] for v in self.mesh.vertices]
        self.center = ((min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2)
        self.size = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
        if self.size < 0.001:
            self.size = 1.0

    def snap(self, v):
        if not self.snap_enabled:
            return v
        s = self.snap_step
        return (round(v[0]/s)*s, round(v[1]/s)*s, round(v[2]/s)*s)

    def load_stl(self, path):
        tris, name = detect_and_read(path)
        self.mesh = Mesh()
        self.name = name
        self.loaded_file = path
        vert_map = {}
        def get_v_idx(v):
            key = (round(v[0], 5), round(v[1], 5), round(v[2], 5))
            if key not in vert_map:
                vert_map[key] = self.mesh.add_vertex(v)
            return vert_map[key]

        for (v1, v2, v3) in tris:
            i1 = get_v_idx(v1)
            i2 = get_v_idx(v2)
            i3 = get_v_idx(v3)
            self.mesh.add_triangle(i1, i2, i3)
        self.update_center()
        self.selected_vertex = None

    def load_sample_cube(self):
        self.mesh = Mesh()
        self.name = "cube_sample"
        v = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
        for p in v:
            self.mesh.add_vertex(p)
        faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                 (0, 1, 5), (0, 5, 4), (2, 3, 7), (2, 7, 6),
                 (0, 4, 7), (0, 7, 3), (1, 2, 6), (1, 6, 5)]
        for f in faces:
            self.mesh.add_triangle(*f)
        self.update_center()

    def add_vertex_at_center(self):
        cx, cy, cz = self.center
        v = self.snap((cx, cy, cz))
        idx = self.mesh.add_vertex(v)
        self.selected_vertex = idx
        return idx

    def weld(self, eps=None):
        if eps is None:
            eps = self.weld_eps
        return self.mesh.weld(eps)

    def stats(self):
        if not self.mesh.vertices:
            return None
        xs = [v[0] for v in self.mesh.vertices]
        ys = [v[1] for v in self.mesh.vertices]
        zs = [v[2] for v in self.mesh.vertices]
        tris = self.mesh.get_tri_coords()
        area = sum(t.area() for t in tris)
        return {
            "n_vertices": len(self.mesh.vertices),
            "n_triangles": len(self.mesh.triangles),
            "n_edges": self.mesh.count_edges(),
            "area": area,
            "hanging": len(self.mesh.find_hanging_vertices()),
            "bbox_min": (min(xs), min(ys), min(zs)),
            "bbox_max": (max(xs), max(ys), max(zs)),
        }


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 5 · Mesh Editor")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.state = AppState()
        self.state.load_sample_cube()
        self.btn_zones = {}
        self.scene_rect = None
        self.W, self.H = 1600, 1000
        self.dragging_vertex = False

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-3>", self._on_right_click)

        self.root.update_idletasks()
        self._redraw_all()

    def _on_resize(self, event):
        self._redraw_all()

    def _draw_bg(self, w, h):
        for i in range(40):
            y0 = int(i * h / 40)
            y1 = int((i + 1) * h / 40)
            col = lerp(BG_DEEP, "#0a0e18", i / 40)
            self.canvas.create_rectangle(0, y0, w, y1, fill=col, outline="")

    def _draw_header(self, w):
        self.canvas.create_text(60, 40, text="✂", fill=NEON_CYAN, font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="MESH EDITOR", fill=TEXT_MAIN, anchor="w", font=FONT_TITLE)
        self.canvas.create_text(340, 44, text="· РЕДАКТОР СО СКЛЕЙКОЙ ВЕРШИН", fill=NEON_CYAN, anchor="w", font=("Segoe UI", 11, "bold"))
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    def _draw_left(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14, fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5), width=2)
        
        cy = y + 25
        self.canvas.create_text(x + 20, cy, anchor="w", text="▸ ФАЙЛ", fill=NEON_PURP, font=FONT_LABEL)
        cy += 25
        self._btn(x + 20, cy, w - 40, 40, "📂 ЗАГРУЗИТЬ STL", NEON_BLUE, "load")
        cy += 50
        self._btn(x + 20, cy, w - 40, 40, "🎲 КУБ (ПРИМЕР)", NEON_PURP, "cube")
        
        cy += 50
        self.canvas.create_text(x + 20, cy, anchor="w", text="▸ СТАТИСТИКА", fill=NEON_CYAN, font=FONT_LABEL)
        cy += 20
        stats = self.state.stats()
        if stats:
            rows = [
                ("Вершин", f"{stats['n_vertices']}", NEON_CYAN),
                ("Рёбер", f"{stats['n_edges']}", NEON_GREEN),
                ("Треугольников", f"{stats['n_triangles']}", NEON_PINK),
                ("Площадь", f"{stats['area']:.2f}", NEON_AMBER),
                ("Висящих", f"{stats['hanging']}", NEON_RED if stats['hanging'] else NEON_GREEN),
            ]
            for lbl, val, col in rows:
                self.canvas.create_text(x + 30, cy, anchor="w", text=lbl, fill=TEXT_DIM, font=("Consolas", 10))
                self.canvas.create_text(x + w - 30, cy, anchor="e", text=val, fill=col, font=("Consolas", 11, "bold"))
                cy += 20

        cy += 20
        self.canvas.create_text(x + 20, cy, anchor="w", text="▸ ИНСТРУМЕНТЫ", fill=NEON_CYAN, font=FONT_LABEL)
        cy += 20
        self._btn(x + 20, cy, w - 40, 38, "➕ ДОБАВИТЬ ВЕРШИНУ", NEON_GREEN, "add_vertex")
        cy += 45
        self._btn(x + 20, cy, w - 40, 38, "✂ СКЛЕИТЬ ВЕРШИНЫ", NEON_PINK, "weld")
        cy += 45
        self._btn(x + 20, cy, w - 40, 38, "⚙ SNAP: " + ("ВКЛ" if self.state.snap_enabled else "ВЫКЛ"), NEON_GREEN if self.state.snap_enabled else TEXT_DIM, "toggle_snap")
        
        cy += 45
        self.canvas.create_text(x + 20, cy, anchor="w", text=f"SNAP ШАГ: {self.state.snap_step:.2f}", fill=TEXT_DIM, font=("Consolas", 10))
        cy += 20
        steps = [0.01, 0.05, 0.1, 0.25, 0.5]
        bw = (w - 40 - 4 * 4) / 5
        for i, s in enumerate(steps):
            active = (abs(self.state.snap_step - s) < 1e-6)
            self._tiny_btn(x + 20 + i * (bw + 4), cy, bw, 26, f"{s}", s, active)

        # Низ панели
        vy = y + h - 170
        self.canvas.create_text(x + 20, vy, anchor="w", text="▸ ВЫБРАННАЯ ВЕРШИНА", fill=NEON_AMBER, font=FONT_LABEL)
        vy += 20
        if self.state.selected_vertex is not None and self.state.selected_vertex < len(self.state.mesh.vertices):
            v = self.state.mesh.vertices[self.state.selected_vertex]
            self.canvas.create_text(x + 30, vy, anchor="w", text=f"#{self.state.selected_vertex+1}", fill=NEON_AMBER, font=("Consolas", 11, "bold"))
            vy += 18
            for axis, val in zip(["X", "Y", "Z"], v):
                self.canvas.create_text(x + 30, vy, anchor="w", text=f"{axis}: {val:+.3f}", fill=TEXT_MAIN, font=("Consolas", 10))
                vy += 16
        else:
            self.canvas.create_text(x + 30, vy, anchor="w", text="(клик по вершине)", fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        cy = y + h - 55
        bw = (w - 50) / 2
        self._btn(x + 20, cy, bw, 36, "💾 ASCII", NEON_CYAN, "save_ascii")
        self._btn(x + 30 + bw, cy, bw, 36, "💾 BINARY", NEON_GREEN, "save_binary")

    def _btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8, fill=lerp(color, BG_DEEP, 0.8), outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2, text=text, fill=color, font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _tiny_btn(self, x, y, w, h, label, val, active):
        color = NEON_CYAN
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 4, fill=lerp(color, BG_DEEP, 0.5), outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2, text=label, fill=color, font=("Consolas", 9, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 4, fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2, text=label, fill=TEXT_DIM, font=("Consolas", 9, "bold"))
        self.btn_zones[f"snap_{val}"] = (x, y, x + w, y + h)

    def _draw_center(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14, fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w", text="▸ 3D-СЦЕНА", fill=NEON_CYAN, font=FONT_LABEL)
        self.canvas.create_text(x + w - 20, y + 25, anchor="e", text="тяни — вращение · колесо — масштаб · ПКМ — удалить", fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        gx = x + 20
        gy = y + 50
        gw = w - 40
        gh = h - 70
        self.scene_rect = (gx, gy, gw, gh)
        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8, fill=BG_GRAPH, outline="")

        cx = gx + gw / 2
        cy = gy + gh / 2
        scale = min(gw, gh) * 0.35 / self.state.size * self.state.zoom

        ca = math.cos(self.state.rot_z)
        sa = math.sin(self.state.rot_z)
        cb = math.cos(self.state.rot_x)
        sb = math.sin(self.state.rot_x)
        center = self.state.center

        def project(v):
            vx = v[0] - center[0]
            vy = v[1] - center[1]
            vz = v[2] - center[2]
            x1 = vx * ca - vy * sa
            y1 = vx * sa + vy * ca
            z1 = vz
            y2 = y1 * cb - z1 * sb
            return (cx + x1 * scale, cy - y2 * scale)

        if self.state.show_grid:
            grid_step = 0.5
            for i in range(-10, 11):
                p1 = project((i * grid_step, -5, 0))
                p2 = project((i * grid_step, 5, 0))
                if (gx <= p1[0] <= gx+gw and gy <= p1[1] <= gy+gh and gx <= p2[0] <= gx+gw and gy <= p2[1] <= gy+gh):
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#101820", width=1)
                
                p1 = project((-5, i * grid_step, 0))
                p2 = project((5, i * grid_step, 0))
                if (gx <= p1[0] <= gx+gw and gy <= p1[1] <= gy+gh and gx <= p2[0] <= gx+gw and gy <= p2[1] <= gy+gh):
                    self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="#101820", width=1)

        tris = self.state.mesh.get_tri_coords()
        items = []
        for t in tris:
            depth = (t.v1[0]+t.v2[0]+t.v3[0]) * 0.01 + (t.v1[1]+t.v2[1]+t.v3[1]) * 0.01
            items.append((depth, t))
        items.sort(key=lambda x: x[0])

        for _, t in items:
            p1 = project(t.v1)
            p2 = project(t.v2)
            p3 = project(t.v3)
            n = t.normal
            light = 0.4 + 0.6 * abs(n[2])
            col = "#{:02x}{:02x}{:02x}".format(min(255, int(100 * light + 50)), min(255, int(100 * light + 50)), min(255, int(200 * light + 50)))
            self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], fill=col, outline="#5566aa", width=1)

        for i, v in enumerate(self.state.mesh.vertices):
            p = project(v)
            is_selected = (i == self.state.selected_vertex)
            r = 5 if is_selected else 3
            col = NEON_AMBER if is_selected else NEON_CYAN
            self.canvas.create_oval(p[0] - r, p[1] - r, p[0] + r, p[1] + r, fill=col, outline="#ffffff", width=2 if is_selected else 1)

        info = f"вершин: {len(self.state.mesh.vertices)} · треуг.: {len(self.state.mesh.triangles)} · zoom {self.state.zoom:.1f}×"
        self.canvas.create_text(gx + gw / 2, gy + gh - 15, text=info, fill=TEXT_DIM, font=("Consolas", 10))

    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14, fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w", text="▸ УГЛЫ И ГЕОМЕТРИЯ", fill=NEON_CYAN, font=FONT_LABEL)

        cy = y + 55
        if self.state.selected_vertex is None or self.state.selected_vertex >= len(self.state.mesh.vertices):
            self.canvas.create_text(x + w / 2, y + h / 2, text="Выбери вершину\n(клик по точке в сцене)", fill=TEXT_DIM, font=("Segoe UI", 12, "italic"), justify="center")
            return

        idx = self.state.selected_vertex
        used_in = []
        for ti, (i1, i2, i3) in enumerate(self.state.mesh.triangles):
            if idx in (i1, i2, i3):
                used_in.append(ti)

        self.canvas.create_text(x + 20, cy, anchor="w", text=f"Вершина #{idx+1}", fill=NEON_AMBER, font=FONT_LABEL)
        cy += 22
        self.canvas.create_text(x + 20, cy, anchor="w", text=f"Используется в {len(used_in)} треугольниках", fill=TEXT_DIM, font=("Consolas", 10))
        cy += 30

        for ti in used_in[:5]:
            i1, i2, i3 = self.state.mesh.triangles[ti]
            t = Triangle(self.state.mesh.vertices[i1], self.state.mesh.vertices[i2], self.state.mesh.vertices[i3])
            verts = [(i1, t.v1), (i2, t.v2), (i3, t.v3)]
            for (i, v) in verts:
                if i == idx:
                    others = [t.v1, t.v2, t.v3]
                    others.remove(v)
                    if len(others) >= 2:
                        a = v_sub(others[0], v)
                        b = v_sub(others[1], v)
                        cos_a = v_dot(a, b) / (v_length(a) * v_length(b) + 1e-12)
                        cos_a = max(-1, min(1, cos_a))
                        angle = math.degrees(math.acos(cos_a))
                        self.canvas.create_text(x + 30, cy, anchor="w", text=f"Треуг #{ti+1}: {angle:.1f}°", fill=NEON_CYAN, font=("Consolas", 11))
                        cy += 22
                    break

        cy += 15
        self.canvas.create_text(x + 20, cy, anchor="w", text="▸ ПОИСК БЛИЖАЙШИХ", fill=NEON_GREEN, font=FONT_LABEL)
        cy += 22

        v_self = self.state.mesh.vertices[idx]
        dists = []
        for i, v in enumerate(self.state.mesh.vertices):
            if i == idx: continue
            dists.append((v_dist(v_self, v), i))
        
        dists.sort()
        for d, i in dists[:5]:
            self.canvas.create_text(x + 30, cy, anchor="w", text=f"#{i+1}: {d:.4f}", fill=TEXT_DIM, font=("Consolas", 10))
            cy += 18

        near_weld = sum(1 for d, _ in dists if d < self.state.weld_eps)
        cy += 10
        self.canvas.create_text(x + 20, cy, anchor="w", text=f"Ближе eps ({self.state.weld_eps}): {near_weld}", fill=NEON_AMBER, font=("Consolas", 10, "bold"))

    def _redraw_all(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = self.W, self.H
        self.W, self.H = w, h

        self.btn_zones = {}
        self._draw_bg(w, h)
        self._draw_header(w)

        left_w = 340
        self._draw_left(50, 90, left_w, h - 110)

        c_x = 50 + left_w + 20
        c_w = (w - c_x - 50) * 0.6
        self._draw_center(c_x, 90, c_w, h - 110)

        r_x = c_x + c_w + 15
        r_w = w - r_x - 50
        self._draw_right(r_x, 90, r_w, h - 110)

    def _on_click(self, event):
        x, y = event.x, event.y
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return

        if self.scene_rect:
            gx, gy, gw, gh = self.scene_rect
            if gx <= x <= gx + gw and gy <= y <= gy + gh:
                hit = self._pick_vertex(x, y)
                if hit is not None:
                    self.state.selected_vertex = hit
                    self.dragging_vertex = True
                    self._redraw_all()
                else:
                    self.state.drag_view = (x, y, self.state.rot_z, self.state.rot_x)

    def _pick_vertex(self, mx, my):
        if not self.scene_rect:
            return None
        gx, gy, gw, gh = self.scene_rect
        cx = gx + gw / 2
        cy = gy + gh / 2
        scale = min(gw, gh) * 0.35 / self.state.size * self.state.zoom

        ca = math.cos(self.state.rot_z)
        sa = math.sin(self.state.rot_z)
        cb = math.cos(self.state.rot_x)
        sb = math.sin(self.state.rot_x)
        center = self.state.center

        best = None
        best_dist = 15
        for i, v in enumerate(self.state.mesh.vertices):
            vx = v[0] - center[0]
            vy = v[1] - center[1]
            vz = v[2] - center[2]
            x1 = vx * ca - vy * sa
            y1 = vx * sa + vy * ca
            z1 = vz
            y2 = y1 * cb - z1 * sb
            z2 = y1 * sb + z1 * cb
            px = cx + x1 * scale
            py = cy - y2 * scale
            d = math.hypot(mx - px, my - py)
            if d < best_dist:
                best_dist = d
                best = i
        return best

    def _on_drag(self, event):
        if self.dragging_vertex and self.state.selected_vertex is not None:
            if self.scene_rect:
                gx, gy, gw, gh = self.scene_rect
                cx = gx + gw / 2
                cy = gy + gh / 2
                scale = min(gw, gh) * 0.35 / self.state.size * self.state.zoom

                ca = math.cos(self.state.rot_z)
                sa = math.sin(self.state.rot_z)
                cb = math.cos(self.state.rot_x)
                sb = math.sin(self.state.rot_x)

                dx = (event.x - cx) / scale
                dy = -(event.y - cy) / scale
                
                vx = dx * ca + (dy + 0) * sa / cb if abs(cb) > 1e-6 else dx
                vy = -dx * sa + (dy + 0) * ca / cb if abs(cb) > 1e-6 else dy

                idx = self.state.selected_vertex
                if idx < len(self.state.mesh.vertices):
                    v = list(self.state.mesh.vertices[idx])
                    v[0] = vx + self.state.center[0]
                    v[1] = vy + self.state.center[1]
                    new_v = self.state.snap(tuple(v))
                    self.state.mesh.vertices[idx] = new_v
                    self._redraw_all()
            return

        if self.state.drag_view:
            x0, y0, rz0, rx0 = self.state.drag_view
            dx = event.x - x0
            dy = event.y - y0
            self.state.rot_z = rz0 + dx * 0.01
            self.state.rot_x = max(-math.pi/2, min(math.pi/2, rx0 + dy * 0.01))
            self._redraw_all()

    def _on_release(self, event):
        self.dragging_vertex = False
        self.state.drag_view = None

    def _on_right_click(self, event):
        hit = self._pick_vertex(event.x, event.y)
        if hit is None: return
        self.state.mesh.triangles = [(i1, i2, i3) for (i1, i2, i3) in self.state.mesh.triangles if hit not in (i1, i2, i3)]
        if self.state.selected_vertex == hit:
            self.state.selected_vertex = None
        self._redraw_all()

    def _on_wheel(self, event):
        if self.scene_rect:
            gx, gy, gw, gh = self.scene_rect
            if gx <= event.x <= gx + gw and gy <= event.y <= gy + gh:
                delta = 1.1 if event.delta > 0 else 0.9
                self.state.zoom = max(0.3, min(10.0, self.state.zoom * delta))
                self._redraw_all()

    def _do_action(self, key):
        if key == "load":
            self._load()
        elif key == "cube":
            self.state.load_sample_cube()
            self._redraw_all()
        elif key == "add_vertex":
            self.state.add_vertex_at_center()
            self._redraw_all()
        elif key == "weld":
            n_v, n_t = self.state.weld()
            messagebox.showinfo("Склейка", f"Склеено вершин: {n_v}\nУдалено дубликатов треугольников: {n_t}")
            self._redraw_all()
        elif key == "toggle_snap":
            self.state.snap_enabled = not self.state.snap_enabled
            self._redraw_all()
        elif key.startswith("snap_"):
            self.state.snap_step = float(key[5:])
            self._redraw_all()
        elif key == "save_ascii":
            self._save("ascii")
        elif key == "save_binary":
            self._save("binary")

    def _load(self):
        path = filedialog.askopenfilename(title="Открыть STL", filetypes=[("STL files", "*.stl")])
        if not path: return
        try:
            self.state.load_stl(path)
            messagebox.showinfo("Загружено", f"Файл: {os.path.basename(path)}\nВершин: {len(self.state.mesh.vertices)}\nТреугольников: {len(self.state.mesh.triangles)}")
            self._redraw_all()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _save(self, kind):
        if not self.state.mesh.triangles:
            messagebox.showwarning("Пусто", "Нет треугольников")
            return
        path = filedialog.asksaveasfilename(defaultextension=".stl", initialfile=f"edited_{self.state.name}.stl", filetypes=[("STL files", "*.stl")])
        if not path: return
        try:
            tris = [(t.v1, t.v2, t.v3) for t in self.state.mesh.get_tri_coords()]
            if kind == "ascii":
                save_ascii_stl(path, tris, self.state.name)
            else:
                save_binary_stl(path, tris, self.state.name)
            size = os.path.getsize(path)
            messagebox.showinfo("Сохранено", f"Файл сохранён:\n{path}\n\nТреугольников: {len(tris)}\nРазмер: {size} байт")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
