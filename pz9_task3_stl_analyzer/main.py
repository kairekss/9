"""
ОКФРС. Практика 9. Задание 3.
STL-анализатор: чтение, статистика, валидация меша.
Поиск дыр, non-manifold рёбер, вывернутых нормалей.
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

def v_add(a, b):
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])

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


class Triangle:
    def __init__(self, v1, v2, v3, normal=None):
        self.v1 = tuple(v1)
        self.v2 = tuple(v2)
        self.v3 = tuple(v3)
        self.normal = normal if normal else v_norm(v_cross(v_sub(self.v2, self.v1),
                                                            v_sub(self.v3, self.v1)))

    def area(self):
        return 0.5 * v_length(v_cross(v_sub(self.v2, self.v1),
                                       v_sub(self.v3, self.v1)))

    def centroid(self):
        return ((self.v1[0]+self.v2[0]+self.v3[0])/3,
                (self.v1[1]+self.v2[1]+self.v3[1])/3,
                (self.v1[2]+self.v2[2]+self.v3[2])/3)

    def is_degenerate(self, eps=1e-10):
        return self.area() < eps


# ============================================================
# ПАРСИНГ STL
# ============================================================
def read_ascii_stl(path):
    triangles = []
    name = "object"
    with open(path, "r", encoding="ascii", errors="replace") as f:
        content = f.read()

    import re
    m = re.search(r"solid\s+(\S+)", content)
    if m:
        name = m.group(1)

    pattern = re.compile(
        r"facet\s+normal\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)",
        re.DOTALL
    )

    for match in pattern.finditer(content):
        vals = [float(x) for x in match.groups()]
        n = vals[0:3]
        v1 = vals[3:6]
        v2 = vals[6:9]
        v3 = vals[9:12]
        triangles.append(Triangle(v1, v2, v3, n))
    return triangles, name


def read_binary_stl(path):
    with open(path, "rb") as f:
        header = f.read(80)
        cb = f.read(4)
        if len(cb) < 4:
            raise ValueError("Файл слишком маленький")
        n = struct.unpack("<I", cb)[0]
        triangles = []
        for _ in range(n):
            data = f.read(50)
            if len(data) < 50:
                break
            vals = struct.unpack("<12fH", data)
            normal = vals[0:3]
            v1 = vals[3:6]
            v2 = vals[6:9]
            v3 = vals[9:12]
            triangles.append(Triangle(v1, v2, v3, normal))
        name = header[:80].decode("ascii", errors="replace").strip() or "binary"
        return triangles, name


def detect_and_read(path):
    with open(path, "rb") as f:
        head = f.read(500)
    if b"facet normal" in head or b"endsolid" in head:
        return read_ascii_stl(path)
    # проверка размера
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


# ============================================================
# АНАЛИЗ МЕША
# ============================================================
def analyze_mesh(triangles):
    """
    Полный анализ меша. Возвращает словарь с результатами.
    """
    result = {
        "count": len(triangles),
        "area": 0.0,
        "volume": 0.0,
        "center_mass": (0, 0, 0),
        "bbox": None,
        "diagonal": 0.0,
        "degenerate": [],       # индексы вырожденных треугольников
        "non_manifold_edges": [],  # рёбра, у которых != 2 треуг
        "flipped_normals": [],     # индексы с вывернутой нормалью
        "holes_count": 0,
        "is_watertight": False,
        "is_valid": False,
    }

    if not triangles:
        return result

    # === 1. Площадь, объём, центр масс ===
    total_volume = 0.0
    total_area = 0.0
    # центр масс через signed volume тетраэдров
    # V = (1/6) * sum(dot(v1, cross(v2, v3)))
    # centroid = (1/4) * sum((v1+v2+v3) * signed_vol)
    cx = cy = cz = 0.0

    for t in triangles:
        total_area += t.area()
        vol = v_dot(t.v1, v_cross(t.v2, t.v3)) / 6.0
        total_volume += vol
        # centroid тетраэдра = (v1+v2+v3+0)/4 = (v1+v2+v3)/4
        ccx = (t.v1[0]+t.v2[0]+t.v3[0]) / 4.0
        ccy = (t.v1[1]+t.v2[1]+t.v3[1]) / 4.0
        ccz = (t.v1[2]+t.v2[2]+t.v3[2]) / 4.0
        cx += ccx * vol
        cy += ccy * vol
        cz += ccz * vol

    result["area"] = total_area
    result["volume"] = abs(total_volume)

    if abs(total_volume) > 1e-9:
        result["center_mass"] = (cx / total_volume,
                                  cy / total_volume,
                                  cz / total_volume)
    else:
        # fallback — центр bbox
        xs = [v[0] for t in triangles for v in (t.v1, t.v2, t.v3)]
        ys = [v[1] for t in triangles for v in (t.v1, t.v2, t.v3)]
        zs = [v[2] for t in triangles for v in (t.v1, t.v2, t.v3)]
        result["center_mass"] = ((min(xs)+max(xs))/2,
                                  (min(ys)+max(ys))/2,
                                  (min(zs)+max(zs))/2)

    # === 2. Bounding Box ===
    xs = [v[0] for t in triangles for v in (t.v1, t.v2, t.v3)]
    ys = [v[1] for t in triangles for v in (t.v1, t.v2, t.v3)]
    zs = [v[2] for t in triangles for v in (t.v1, t.v2, t.v3)]
    bbox_min = (min(xs), min(ys), min(zs))
    bbox_max = (max(xs), max(ys), max(zs))
    result["bbox"] = (bbox_min, bbox_max)
    result["diagonal"] = v_length(v_sub(bbox_max, bbox_min))

    # === 3. Вырожденные треугольники ===
    for i, t in enumerate(triangles):
        if t.is_degenerate():
            result["degenerate"].append(i)

    # === 4. Non-manifold рёбра ===
    # ключ — отсортированная пара вершин
    # значение — список индексов треугольников
    def vkey(v):
        # округляем до 5 знаков чтобы совпадали
        return (round(v[0], 5), round(v[1], 5), round(v[2], 5))

    edges = defaultdict(list)
    for i, t in enumerate(triangles):
        vs = [vkey(t.v1), vkey(t.v2), vkey(t.v3)]
        for a, b in [(0,1), (1,2), (2,0)]:
            k = tuple(sorted([vs[a], vs[b]]))
            edges[k].append(i)

    for edge, tris in edges.items():
        if len(tris) != 2:
            result["non_manifold_edges"].append((edge, len(tris)))

    # === 5. Дыры ===
    # отверстие — это ребро, к которому примыкает только 1 треугольник
    # (открытое ребро)
    open_edges = [e for e, t in edges.items() if len(t) == 1]
    result["holes_count"] = len(open_edges)

    # === 6. Согласованность нормалей ===
    # Проверяем, что для смежных треугольников нормали направлены в одну сторону.
    # Если у двух треугольников на одном ребре нормали «смотрят в одну сторону» —
    # значит одна из них инвертирована.
    #
    # Идея: если у треугольника A ребро (v1->v2), у соседа B должно быть (v2->v1).
    # Если у обоих (v1->v2), у одного нормаль вывернута.

    # сначала построим ориентированные рёбра
    directed = defaultdict(list)
    for i, t in enumerate(triangles):
        vs = [vkey(t.v1), vkey(t.v2), vkey(t.v3)]
        for a, b in [(0,1), (1,2), (2,0)]:
            directed[(vs[a], vs[b])].append(i)

    # ребро должно встречаться ровно 1 раз в direct (a->b) и 1 раз в direct (b->a)
    for edge, tris in directed.items():
        if len(tris) > 1:
            # два треугольника имеют одинаковое направление ребра — ошибка
            # Помечаем только один, чтобы не дублировать
            if tris[0] not in result["flipped_normals"]:
                result["flipped_normals"].append(tris[0])
            if tris[1] not in result["flipped_normals"]:
                result["flipped_normals"].append(tris[1])

    # === 7. Watertight ===
    result["is_watertight"] = (len(open_edges) == 0 and
                                len(result["non_manifold_edges"]) == 0 and
                                len(result["degenerate"]) == 0)

    # === 8. Valid ===
    result["is_valid"] = (result["is_watertight"] and
                           len(result["flipped_normals"]) == 0)

    return result


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.triangles = []
        self.analysis = None
        self.name = "object"
        self.file_path = None

        self.rot_z = math.radians(30)
        self.rot_x = math.radians(20)
        self.zoom = 1.0
        self.size = 1.0
        self.center = (0, 0, 0)
        self.drag = None

        # режим отображения
        self.show_problems = True    # показывать ошибки
        self.show_normals = False

    def load(self, path):
        triangles, name = detect_and_read(path)
        self.triangles = triangles
        self.name = name
        self.file_path = path
        self.analysis = analyze_mesh(triangles)
        # вычисляем bbox для визуализации
        if self.analysis["bbox"]:
            (mn, mx) = self.analysis["bbox"]
            self.center = ((mn[0]+mx[0])/2,
                           (mn[1]+mx[1])/2,
                           (mn[2]+mx[2])/2)
            self.size = max(mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2])
            if self.size < 0.001:
                self.size = 1.0


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 3 · STL Analyzer")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.state = AppState()
        self.btn_zones = {}
        self.scene_rect = None
        self.W, self.H = 1600, 1000

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)

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
        self.canvas.create_text(60, 40, text="🔬",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="STL ANALYZER",
                                fill=TEXT_MAIN, anchor="w",
                                font=FONT_TITLE)
        self.canvas.create_text(340, 44,
                                text="· АНАЛИЗ И ВАЛИДАЦИЯ МЕША",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ЛЕВАЯ ПАНЕЛЬ ----------
    def _draw_left(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ФАЙЛ",
                                fill=NEON_PURP, font=FONT_LABEL)

        cy = y + 55

        # путь
        if self.state.file_path:
            self.canvas.create_text(x + w / 2, cy, anchor="center",
                                    text=os.path.basename(self.state.file_path),
                                    fill=NEON_CYAN,
                                    font=("Consolas", 10, "bold"))
        else:
            self.canvas.create_text(x + w / 2, cy, anchor="center",
                                    text="(не загружен)",
                                    fill=TEXT_DIM,
                                    font=("Consolas", 10, "italic"))
        cy += 30

        # загрузка
        self._btn(x + 20, cy, w - 40, 42,
                   "📂 ЗАГРУЗИТЬ STL", NEON_BLUE, "load")
        cy += 55

        # === Статистика ===
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ СТАТИСТИКА",
                                fill=NEON_CYAN, font=FONT_LABEL)
        cy += 25

        if self.state.analysis:
            a = self.state.analysis
            bbox = a["bbox"]
            cm = a["center_mass"]

            rows = [
                ("Треугольников", f"{a['count']}", NEON_CYAN),
                ("Площадь", f"{a['area']:.3f}", NEON_GREEN),
                ("Объём", f"{a['volume']:.3f}", NEON_AMBER),
                ("Диагональ BBox", f"{a['diagonal']:.2f}", NEON_PURP),
            ]

            for lbl, val, col in rows:
                self.canvas.create_text(x + 30, cy, anchor="w",
                                        text=lbl, fill=TEXT_DIM,
                                        font=("Consolas", 10))
                self.canvas.create_text(x + w - 30, cy, anchor="e",
                                        text=val, fill=col,
                                        font=("Consolas", 11, "bold"))
                cy += 22

            cy += 8
            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text="Центр масс:",
                                    fill=TEXT_DIM, font=("Consolas", 9))
            cy += 18
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=f"({cm[0]:.2f}, {cm[1]:.2f}, {cm[2]:.2f})",
                                    fill=NEON_CYAN,
                                    font=("Consolas", 9, "bold"))
            cy += 25

            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text="Габариты (min/max):",
                                    fill=TEXT_DIM, font=("Consolas", 9))
            cy += 18
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=f"X: {bbox[0][0]:.2f} … {bbox[1][0]:.2f}",
                                    fill=TEXT_MAIN,
                                    font=("Consolas", 9))
            cy += 16
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=f"Y: {bbox[0][1]:.2f} … {bbox[1][1]:.2f}",
                                    fill=TEXT_MAIN,
                                    font=("Consolas", 9))
            cy += 16
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=f"Z: {bbox[0][2]:.2f} … {bbox[1][2]:.2f}",
                                    fill=TEXT_MAIN,
                                    font=("Consolas", 9))
            cy += 25
        else:
            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text="Загрузи файл",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 10, "italic"))
            cy += 30

        # === Кнопки отображения ===
        cy = y + h - 180
        self._btn(x + 20, cy, w - 40, 38,
                   "🔴 ПРОБЛЕМЫ: " + ("ВКЛ" if self.state.show_problems else "ВЫКЛ"),
                   NEON_RED if self.state.show_problems else TEXT_DIM,
                   "toggle_problems")
        cy += 46
        self._btn(x + 20, cy, w - 40, 38,
                   "➡ НОРМАЛИ: " + ("ВКЛ" if self.state.show_normals else "ВЫКЛ"),
                   NEON_AMBER if self.state.show_normals else TEXT_DIM,
                   "toggle_normals")
        cy += 46

    def _btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    # ---------- ЦЕНТР — 3D ----------
    def _draw_center(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ 3D-СЦЕНА",
                                fill=NEON_CYAN, font=FONT_LABEL)
        self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                text="тяни — вращение · колесо — масштаб",
                                fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        gx = x + 20
        gy = y + 50
        gw = w - 40
        gh = h - 70
        self.scene_rect = (gx, gy, gw, gh)

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        if not self.state.triangles or not self.state.analysis:
            self.canvas.create_text(gx + gw / 2, gy + gh / 2,
                                    text="Загрузи STL-файл",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 14, "italic"))
            return

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
            z2 = y1 * sb + z1 * cb
            return (cx + x1 * scale, cy - y2 * scale, y2 * cb + z2 * sb)

        # проблемные индексы
        problem_ids = set()
        a = self.state.analysis
        if self.state.show_problems:
            problem_ids.update(a["degenerate"])
            problem_ids.update(a["flipped_normals"])

        # сортировка по глубине
        tris_with_depth = []
        for idx, t in enumerate(self.state.triangles):
            c = t.centroid()
            vx = c[0] - center[0]
            vy = c[1] - center[1]
            vz = c[2] - center[2]
            x1 = vx * ca - vy * sa
            y1 = vx * sa + vy * ca
            depth = y1 * cb - vz * sb
            tris_with_depth.append((depth, idx, t))
        tris_with_depth.sort(key=lambda x: x[0])

        for depth, idx, t in tris_with_depth:
            p1 = project(t.v1)
            p2 = project(t.v2)
            p3 = project(t.v3)

            is_problem = idx in problem_ids

            if is_problem:
                col = NEON_RED
                outline = "#ffffff"
                width = 2
            else:
                n = t.normal
                light = 0.4 + 0.6 * abs(n[2])
                col = "#{:02x}{:02x}{:02x}".format(
                    min(255, int(100 * light + 50)),
                    min(255, int(100 * light + 50)),
                    min(255, int(200 * light + 50)))
                outline = col
                width = 1

            self.canvas.create_polygon(p1[0], p1[1],
                                        p2[0], p2[1],
                                        p3[0], p3[1],
                                        fill=col,
                                        outline=outline,
                                        width=width)

            # нормали
            if self.state.show_normals:
                c = t.centroid()
                n = t.normal
                n_end = (c[0] + n[0] * 0.1, c[1] + n[1] * 0.1,
                          c[2] + n[2] * 0.1)
                pc = project(c)
                pn = project(n_end)
                self.canvas.create_line(pc[0], pc[1], pn[0], pn[1],
                                        fill=NEON_AMBER, width=1,
                                        arrow=tk.LAST, arrowshape=(4, 5, 2))

        # подпись
        info = f"{a['count']} треуг. · {a['area']:.2f} площ. · {a['volume']:.2f} объём"
        self.canvas.create_text(gx + gw / 2, gy + gh - 15,
                                text=info, fill=TEXT_DIM,
                                font=("Consolas", 10))

    # ---------- ПРАВАЯ — ОТЧЁТ ----------
    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ОТЧЁТ О ВАЛИДНОСТИ",
                                fill=NEON_CYAN, font=FONT_LABEL)

        if not self.state.analysis:
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text="Загрузи файл для анализа",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 12, "italic"))
            return

        a = self.state.analysis
        cy = y + 55

        # Итоговый статус
        if a["is_valid"]:
            status = "✓ ВАЛИДНЫЙ (готов к печати)"
            scol = NEON_GREEN
        elif a["is_watertight"]:
            status = "⚠ ЕСТЬ ВЫВЕРНУТЫЕ НОРМАЛИ"
            scol = NEON_AMBER
        else:
            status = "✗ НЕВАЛИДНЫЙ (есть ошибки)"
            scol = NEON_RED

        round_rect(self.canvas, x + 15, cy, x + w - 15, cy + 50, 8,
                   fill=lerp(scol, BG_DEEP, 0.75),
                   outline=scol, width=2)
        self.canvas.create_text(x + w / 2, cy + 25,
                                text=status, fill=scol,
                                font=("Segoe UI", 14, "bold"))
        cy += 65

        # Проверки
        checks = [
            ("Замкнутость (Watertight)",
             a["is_watertight"],
             f"открытых рёбер: {a['holes_count']}"),
            ("Non-manifold рёбра",
             len(a["non_manifold_edges"]) == 0,
             f"найдено: {len(a['non_manifold_edges'])}"),
            ("Вырожденные треугольники",
             len(a["degenerate"]) == 0,
             f"найдено: {len(a['degenerate'])}"),
            ("Согласованность нормалей",
             len(a["flipped_normals"]) == 0,
             f"вывернутых: {len(a['flipped_normals'])}"),
        ]

        for lbl, ok, detail in checks:
            col = NEON_GREEN if ok else NEON_RED
            icon = "✓" if ok else "✗"

            round_rect(self.canvas, x + 15, cy, x + w - 15, cy + 46, 6,
                       fill=BG_PANEL)
            self.canvas.create_text(x + 30, cy + 23,
                                    text=icon, fill=col,
                                    font=("Consolas", 16, "bold"))
            self.canvas.create_text(x + 55, cy + 15, anchor="w",
                                    text=lbl, fill=TEXT_MAIN,
                                    font=("Segoe UI", 10, "bold"))
            self.canvas.create_text(x + 55, cy + 33, anchor="w",
                                    text=detail, fill=col,
                                    font=("Consolas", 9))
            cy += 52

        # Список проблемных треугольников
        cy += 10
        problems = []
        if a["degenerate"]:
            problems.append(("Вырожденные", a["degenerate"], NEON_RED))
        if a["flipped_normals"]:
            problems.append(("Вывернутые", a["flipped_normals"], NEON_AMBER))

        if problems:
            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text="▸ ПРОБЛЕМНЫЕ ТРЕУГОЛЬНИКИ",
                                    fill=NEON_RED, font=FONT_LABEL)
            cy += 25

            for name, ids, col in problems:
                self.canvas.create_text(x + 25, cy, anchor="w",
                                        text=f"{name} ({len(ids)}):",
                                        fill=col,
                                        font=("Consolas", 10, "bold"))
                cy += 18
                # выводим первые 10
                ids_str = ", ".join(str(i+1) for i in ids[:10])
                if len(ids) > 10:
                    ids_str += f" ... (ещё {len(ids)-10})"
                self.canvas.create_text(x + 35, cy, anchor="w",
                                        text=ids_str, fill=TEXT_DIM,
                                        font=("Consolas", 9))
                cy += 24
        else:
            self.canvas.create_text(x + w / 2, cy + 20,
                                    text="✓ Проблем не найдено",
                                    fill=NEON_GREEN,
                                    font=("Segoe UI", 12, "bold"))
            cy += 50

        # non-manifold рёбра — список
        if a["non_manifold_edges"]:
            cy += 10
            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text="▸ NON-MANIFOLD РЁБРА",
                                    fill=NEON_PINK, font=FONT_LABEL)
            cy += 25
            for (edge, count) in a["non_manifold_edges"][:5]:
                edge_str = f"({edge[0][0]:.1f},{edge[0][1]:.1f},{edge[0][2]:.1f})–" \
                          f"({edge[1][0]:.1f},{edge[1][1]:.1f},{edge[1][2]:.1f})"
                self.canvas.create_text(x + 25, cy, anchor="w",
                                        text=f"{edge_str} → {count} треуг.",
                                        fill=TEXT_DIM,
                                        font=("Consolas", 8))
                cy += 16
            if len(a["non_manifold_edges"]) > 5:
                self.canvas.create_text(x + 25, cy, anchor="w",
                                        text=f"... ещё {len(a['non_manifold_edges'])-5}",
                                        fill=TEXT_DIM,
                                        font=("Consolas", 8, "italic"))

    # ---------- ПЕРЕРИСОВКА ----------
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

        left_w = 380
        self._draw_left(50, 90, left_w, h - 110)

        c_x = 50 + left_w + 20
        c_w = (w - c_x - 50) * 0.55
        self._draw_center(c_x, 90, c_w, h - 110)

        r_x = c_x + c_w + 15
        r_w = w - r_x - 50
        self._draw_right(r_x, 90, r_w, h - 110)

    # ---------- СОБЫТИЯ ----------
    def _on_click(self, event):
        x, y = event.x, event.y
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return
        if self.scene_rect:
            gx, gy, gw, gh = self.scene_rect
            if gx <= x <= gx + gw and gy <= y <= gy + gh:
                self.state.drag = (x, y, self.state.rot_z, self.state.rot_x)

    def _on_drag(self, event):
        if not self.state.drag:
            return
        x0, y0, rz0, rx0 = self.state.drag
        dx = event.x - x0
        dy = event.y - y0
        self.state.rot_z = rz0 + dx * 0.01
        self.state.rot_x = max(-math.pi/2, min(math.pi/2, rx0 + dy * 0.01))
        self._redraw_all()

    def _on_release(self, event):
        self.state.drag = None

    def _on_wheel(self, event):
        if not self.scene_rect:
            return
        gx, gy, gw, gh = self.scene_rect
        if not (gx <= event.x <= gx + gw and gy <= event.y <= gy + gh):
            return
        delta = 1.1 if event.delta > 0 else 0.9
        self.state.zoom = max(0.3, min(10.0, self.state.zoom * delta))
        self._redraw_all()

    def _do_action(self, key):
        if key == "load":
            self._load()
        elif key == "toggle_problems":
            self.state.show_problems = not self.state.show_problems
        elif key == "toggle_normals":
            self.state.show_normals = not self.state.show_normals

        self._redraw_all()

    def _load(self):
        path = filedialog.askopenfilename(
            title="Открыть STL",
            filetypes=[("STL files", "*.stl"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.state.load(path)
            a = self.state.analysis
            messagebox.showinfo("Готово",
                f"Файл проанализирован.\n\n"
                f"Треугольников: {a['count']}\n"
                f"Площадь: {a['area']:.3f}\n"
                f"Объём: {a['volume']:.3f}\n"
                f"Валидность: {'✓ да' if a['is_valid'] else '✗ нет'}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать STL:\n{e}")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()