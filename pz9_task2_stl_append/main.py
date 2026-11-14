"""
ОКФРС. Практика 9. Задание 2.
Дописывание треугольников в существующий STL-файл.
Чтение ASCII и Binary, добавление нового треугольника,
сохранение обновлённого файла.
Премиум-стиль 2026.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import sys, os, math, struct, random

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
def vec_sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def vec_cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])

def vec_length(v):
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def vec_normalize(v):
    l = vec_length(v)
    if l < 1e-12:
        return (0, 0, 0)
    return (v[0]/l, v[1]/l, v[2]/l)

def compute_normal(v1, v2, v3):
    a = vec_sub(v2, v1)
    b = vec_sub(v3, v1)
    return vec_normalize(vec_cross(a, b))

def triangle_area(v1, v2, v3):
    a = vec_sub(v2, v1)
    b = vec_sub(v3, v1)
    return 0.5 * vec_length(vec_cross(a, b))


# ============================================================
# ФОРМАТ STL
# ============================================================
class Triangle:
    def __init__(self, v1, v2, v3):
        self.v1 = tuple(v1)
        self.v2 = tuple(v2)
        self.v3 = tuple(v3)
        self.normal = compute_normal(self.v1, self.v2, self.v3)

    def area(self):
        return triangle_area(self.v1, self.v2, self.v3)

    def centroid(self):
        return ((self.v1[0]+self.v2[0]+self.v3[0])/3,
                (self.v1[1]+self.v2[1]+self.v3[1])/3,
                (self.v1[2]+self.v2[2]+self.v3[2])/3)


def read_ascii_stl(path):
    """Парсит ASCII STL. Возвращает (list_of_triangles, name)."""
    triangles = []
    name = "object"
    with open(path, "r", encoding="ascii", errors="replace") as f:
        content = f.read()

    # имя объекта
    import re
    m = re.search(r"solid\s+(\S+)", content)
    if m:
        name = m.group(1)

    # все треугольники
    pattern = re.compile(
        r"facet\s+normal\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)",
        re.DOTALL
    )

    for match in pattern.finditer(content):
        coords = [float(x) for x in match.groups()]
        v1 = coords[3:6]
        v2 = coords[6:9]
        v3 = coords[9:12]
        triangles.append(Triangle(v1, v2, v3))

    return triangles, name


def read_binary_stl(path):
    """Парсит Binary STL."""
    with open(path, "rb") as f:
        header = f.read(80)
        count_bytes = f.read(4)
        if len(count_bytes) < 4:
            raise ValueError("Файл слишком маленький")

        n_tri = struct.unpack("<I", count_bytes)[0]
        triangles = []

        for _ in range(n_tri):
            data = f.read(50)
            if len(data) < 50:
                break
            # nx, ny, nz
            # v1 (3 float)
            # v2 (3 float)
            # v3 (3 float)
            # 2 байта атрибутов
            vals = struct.unpack("<12fH", data)
            # vals: 12 floats (normal + 3 вершины), H — атрибуты
            v1 = vals[3:6]
            v2 = vals[6:9]
            v3 = vals[9:12]
            triangles.append(Triangle(v1, v2, v3))

        name = header[:80].decode("ascii", errors="replace").strip()
        if not name:
            name = "binary_object"

        return triangles, name


def detect_and_read_stl(path):
    """Авто-определение ASCII или Binary."""
    with open(path, "rb") as f:
        head = f.read(80)

    # ASCII начинается с "solid"
    is_ascii = head.startswith(b"solid")

    # но некоторые бинарные тоже начинаются с "solid"
    # проверяем — если в первых 200 байтах есть "facet normal", это ASCII
    with open(path, "rb") as f:
        content = f.read(500)
    if b"facet normal" in content:
        is_ascii = True
    elif b"endsolid" in content:
        is_ascii = True
    else:
        # проверим размер: binary STL = 84 + 50 * n
        try:
            size = os.path.getsize(path)
            if size >= 84:
                with open(path, "rb") as f:
                    f.seek(80)
                    n_bytes = f.read(4)
                    if len(n_bytes) == 4:
                        n = struct.unpack("<I", n_bytes)[0]
                        if size == 84 + 50 * n:
                            is_ascii = False
        except Exception:
            pass

    if is_ascii:
        return read_ascii_stl(path)
    return read_binary_stl(path)


def save_ascii_stl(path, triangles, name="object"):
    with open(path, "w", encoding="ascii") as f:
        f.write(f"solid {name}\n")
        for t in triangles:
            n = t.normal
            f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
            f.write(f"    outer loop\n")
            for v in (t.v1, t.v2, t.v3):
                f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        f.write(f"endsolid {name}\n")


def save_binary_stl(path, triangles, name="object"):
    with open(path, "wb") as f:
        header = (f"OKFRS STL - {name}").encode("ascii")[:80].ljust(80, b" ")
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))

        for t in triangles:
            n = t.normal
            f.write(struct.pack("<fff", *[float(x) for x in n]))
            for v in (t.v1, t.v2, t.v3):
                f.write(struct.pack("<fff", *[float(x) for x in v]))
            f.write(struct.pack("<H", 0))


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.triangles = []
        self.model_name = "object"
        self.file_path = None

        # текущий 3D вид
        self.rot_z = math.radians(30)
        self.rot_x = math.radians(20)
        self.zoom = 1.0
        self.drag = None

        # новый треугольник
        self.new_tri = [[0.5, 0.0, 0.0],
                         [0.0, 0.5, 0.0],
                         [0.0, 0.0, 0.5]]

        # текущий выбранный треугольник для подсветки
        self.selected = None

        # границы
        self.update_bounds()

    def update_bounds(self):
        """Пересчитывает bounding box и центр."""
        if not self.triangles:
            self.bbox = ((-1, -1, -1), (1, 1, 1))
            self.center = (0, 0, 0)
            self.size = 2
            return
        xs = []
        ys = []
        zs = []
        for t in self.triangles:
            for v in (t.v1, t.v2, t.v3):
                xs.append(v[0])
                ys.append(v[1])
                zs.append(v[2])
        self.bbox = ((min(xs), min(ys), min(zs)),
                      (max(xs), max(ys), max(zs)))
        self.center = (sum(xs) / len(xs),
                       sum(ys) / len(ys),
                       sum(zs) / len(zs))
        size = max(
            self.bbox[1][0] - self.bbox[0][0],
            self.bbox[1][1] - self.bbox[0][1],
            self.bbox[1][2] - self.bbox[0][2],
        )
        self.size = size if size > 0.001 else 1.0

    def stats(self):
        n = len(self.triangles)
        area = sum(t.area() for t in self.triangles)
        return {"count": n, "area": area}

    def load(self, path):
        triangles, name = detect_and_read_stl(path)
        self.triangles = triangles
        self.model_name = name
        self.file_path = path
        self.update_bounds()

    def add_triangle(self, v1, v2, v3):
        self.triangles.append(Triangle(v1, v2, v3))
        self.update_bounds()

    def remove_triangle(self, idx):
        if 0 <= idx < len(self.triangles):
            self.triangles.pop(idx)
            self.update_bounds()

    def save(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".stl":
            # смотрим на расширение — нет, используем флаг
            pass

    def randomize_new(self):
        self.new_tri = [
            [round(random.uniform(-1, 1), 2),
             round(random.uniform(-1, 1), 2),
             round(random.uniform(-1, 1), 2)] for _ in range(3)
        ]


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 2 · STL Append")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.state = AppState()
        self.btn_zones = {}
        self.entries = {}
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
        self.canvas.create_text(60, 40, text="➕",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="STL EDITOR",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(300, 44,
                                text="· ЗАГРУЗКА · ДОБАВЛЕНИЕ · СОХРАНЕНИЕ",
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

        # файл
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="Путь:",
                                fill=TEXT_DIM, font=("Consolas", 9))
        cy += 18
        round_rect(self.canvas, x + 20, cy, x + w - 20, cy + 26, 4,
                   fill=BG_PANEL, outline=BORDER_HL, width=1)
        path_text = self.state.file_path or "(не загружен)"
        path_short = os.path.basename(path_text) if self.state.file_path else path_text
        self.canvas.create_text(x + w / 2, cy + 13,
                                text=path_short[:40],
                                fill=NEON_CYAN if self.state.file_path else TEXT_DIM,
                                font=("Consolas", 9))
        cy += 40

        # кнопки файла
        self._btn(x + 20, cy, w - 40, 40,
                   "📂 ЗАГРУЗИТЬ STL", NEON_BLUE, "load")
        cy += 50
        self._btn(x + 20, cy, w - 40, 40,
                   "💾 СОХРАНИТЬ STL", NEON_GREEN, "save")
        cy += 50

        # === статистика ===
        st = self.state.stats()
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ СТАТИСТИКА",
                                fill=NEON_CYAN, font=FONT_LABEL)
        cy += 25

        stats = [
            ("Треугольников", f"{st['count']}", NEON_CYAN),
            ("Суммарная площадь", f"{st['area']:.3f}", NEON_AMBER),
        ]
        for lbl, val, col in stats:
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=lbl, fill=TEXT_DIM,
                                    font=("Consolas", 10))
            self.canvas.create_text(x + w - 30, cy, anchor="e",
                                    text=val, fill=col,
                                    font=("Consolas", 11, "bold"))
            cy += 22

        # === новый треугольник ===
        cy += 10
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ НОВЫЙ ТРЕУГОЛЬНИК",
                                fill=NEON_PINK, font=FONT_LABEL)
        cy += 25

        axis_w = (w - 60) / 3
        for i, (label, color) in enumerate([
            ("V1", NEON_CYAN), ("V2", NEON_GREEN), ("V3", NEON_PINK),
        ]):
            vec = self.state.new_tri[i]
            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text=label, fill=color,
                                    font=("Consolas", 11, "bold"))
            cy += 20

            for j, axis in enumerate(["X", "Y", "Z"]):
                ax = x + 20 + j * axis_w
                key = f"new_{i}_{j}"
                round_rect(self.canvas, ax, cy, ax + axis_w - 5, cy + 24, 4,
                           fill="#0a0d14", outline=BORDER_HL, width=1)
                self._entry(ax + 4, cy + 2, axis_w - 15, 20,
                             key, f"{vec[j]:.2f}")
                self.canvas.create_text(ax + (axis_w - 5) / 2, cy + 32,
                                        text=axis, fill=TEXT_DIM,
                                        font=("Consolas", 8))
            cy += 50

        # кнопки управления
        cy += 5
        self._btn(x + 20, cy, w - 40, 36,
                   "🎲 СЛУЧАЙНЫЙ ТРЕУГОЛЬНИК", NEON_PURP, "random_new")
        cy += 44
        self._btn(x + 20, cy, w - 40, 40,
                   "➕ ДОБАВИТЬ ТРЕУГОЛЬНИК", NEON_PINK, "add_tri")

    def _btn(self, x, y, w, h, text, color, key, active=True):
        c = color if active else TEXT_DIM
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(c, BG_DEEP, 0.8),
                   outline=c, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=c,
                                font=("Segoe UI", 10, "bold"))
        if active:
            self.btn_zones[key] = (x, y, x + w, y + h)

    def _entry(self, x, y, w, h, key, default):
        if key not in self.entries or not self.entries[key].winfo_exists():
            widget = tk.Entry(self.root, bg="#0a0d14", fg=NEON_GREEN,
                               insertbackground=NEON_CYAN,
                               font=("Consolas", 9, "bold"),
                               bd=0, highlightthickness=0,
                               justify="center")
            widget.insert(0, default)
            widget.bind("<Return>", lambda e, k=key: self._on_entry_commit(k))
            widget.bind("<FocusOut>", lambda e, k=key: self._on_entry_commit(k))
            self.entries[key] = widget
        else:
            widget = self.entries[key]
            if self.root.focus_get() != widget:
                try:
                    parts = key.split("_")
                    if parts[0] == "new":
                        i = int(parts[1])
                        j = int(parts[2])
                        val = self.state.new_tri[i][j]
                        if widget.get() != f"{val:.2f}":
                            widget.delete(0, tk.END)
                            widget.insert(0, f"{val:.2f}")
                except Exception:
                    pass
        widget.place(x=x, y=y, width=w, height=h)
        widget.lift()

    def _on_entry_commit(self, key):
        try:
            widget = self.entries[key]
            val = float(widget.get().replace(",", "."))
            parts = key.split("_")
            if parts[0] == "new":
                i = int(parts[1])
                j = int(parts[2])
                self.state.new_tri[i][j] = val
        except Exception:
            pass

    # ---------- ЦЕНТР — 3D СЦЕНА ----------
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

        cx = gx + gw / 2
        cy = gy + gh / 2
        scale = min(gw, gh) * 0.35 / self.state.size * self.state.zoom

        ca = math.cos(self.state.rot_z)
        sa = math.sin(self.state.rot_z)
        cb = math.cos(self.state.rot_x)
        sb = math.sin(self.state.rot_x)

        center = self.state.center

        def project(v):
            # относительно центра
            vx = v[0] - center[0]
            vy = v[1] - center[1]
            vz = v[2] - center[2]
            x1 = vx * ca - vy * sa
            y1 = vx * sa + vy * ca
            z1 = vz
            y2 = y1 * cb - z1 * sb
            z2 = y1 * sb + z1 * cb
            return (cx + x1 * scale, cy - y2 * scale)

        # все треугольники
        if not self.state.triangles:
            self.canvas.create_text(cx, cy,
                                    text="Загрузи STL-файл\nили добавь треугольник",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 14, "italic"),
                                    justify="center")
        else:
            # сортировка по глубине — по центроиду
            tris_with_depth = []
            for idx, t in enumerate(self.state.triangles):
                c = t.centroid()
                # глубина = vx*cb + vz*sb (приблизительно)
                vx = c[0] - center[0]
                vy = c[1] - center[1]
                vz = c[2] - center[2]
                x1 = vx * ca - vy * sa
                y1 = vx * sa + vy * ca
                depth = y1 * cb - vz * sb
                tris_with_depth.append((depth, idx, t))

            tris_with_depth.sort(key=lambda x: x[0])  # дальние первыми

            for depth, idx, t in tris_with_depth:
                p1 = project(t.v1)
                p2 = project(t.v2)
                p3 = project(t.v3)

                # цвет по нормали
                n = t.normal
                # просто светлота
                light = 0.4 + 0.6 * abs(n[2])
                base_col = (int(100 * light + 50),
                             int(100 * light + 50),
                             int(200 * light + 50))
                col = "#{:02x}{:02x}{:02x}".format(
                    min(255, base_col[0]),
                    min(255, base_col[1]),
                    min(255, base_col[2]))

                outline_col = col
                if idx == self.state.selected:
                    outline_col = "#ffffff"
                    col = NEON_AMBER

                self.canvas.create_polygon(p1[0], p1[1],
                                            p2[0], p2[1],
                                            p3[0], p3[1],
                                            fill=col,
                                            outline=outline_col,
                                            width=2 if idx == self.state.selected else 1)

        # подпись
        info = f"{self.state.stats()['count']} треуг. · zoom {self.state.zoom:.1f}×"
        self.canvas.create_text(gx + gw / 2, gy + gh - 15,
                                text=info, fill=TEXT_DIM,
                                font=("Consolas", 10))

    # ---------- ПРАВАЯ — СПИСОК ТРЕУГОЛЬНИКОВ ----------
    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ СПИСОК ТРЕУГОЛЬНИКОВ",
                                fill=NEON_CYAN, font=FONT_LABEL)
        self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                text=f"{len(self.state.triangles)} шт.",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        gx = x + 15
        gy = y + 50
        gw = w - 30
        gh = h - 70

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        if not self.state.triangles:
            self.canvas.create_text(gx + gw / 2, gy + gh / 2,
                                    text="Пусто\nЗагрузите STL",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 11, "italic"),
                                    justify="center")
            return

        # шапка
        header_h = 26
        round_rect(self.canvas, gx + 4, gy + 4, gx + gw - 4,
                   gy + header_h + 4, 4,
                   fill=lerp(NEON_BLUE, BG_DEEP, 0.7))

        cols = [(20, "#"), (55, "V1 (X Y Z)"),
                (gx + gw * 0.5, "V2"), (gx + gw * 0.75, "V3")]

        # заголовки
        self.canvas.create_text(gx + 20, gy + 17, text="#",
                                fill=NEON_CYAN, font=("Consolas", 9, "bold"))
        self.canvas.create_text(gx + 50, gy + 17, anchor="w",
                                text="V1", fill=NEON_CYAN,
                                font=("Consolas", 9, "bold"))
        self.canvas.create_text(gx + 200, gy + 17, anchor="w",
                                text="V2", fill=NEON_GREEN,
                                font=("Consolas", 9, "bold"))
        self.canvas.create_text(gx + 350, gy + 17, anchor="w",
                                text="V3", fill=NEON_PINK,
                                font=("Consolas", 9, "bold"))

        # строки
        line_h = 20
        max_rows = int((gh - header_h - 10) / line_h)
        start_y = gy + header_h + 14

        for i, t in enumerate(self.state.triangles[:max_rows]):
            ry = start_y + i * line_h
            # зебра
            if i % 2 == 0:
                self.canvas.create_rectangle(gx + 4, ry - 8,
                                              gx + gw - 4, ry + 12,
                                              fill=BG_CELL, outline="")

            # подсветка выбранного
            if i == self.state.selected:
                self.canvas.create_rectangle(gx + 4, ry - 8,
                                              gx + gw - 4, ry + 12,
                                              fill=lerp(NEON_AMBER, BG_CELL, 0.7),
                                              outline="")

            def fmt_vec(v):
                return f"{v[0]:+.1f} {v[1]:+.1f} {v[2]:+.1f}"

            self.canvas.create_text(gx + 20, ry, text=f"{i+1}",
                                    fill=TEXT_DIM, font=("Consolas", 9))
            self.canvas.create_text(gx + 50, ry, anchor="w",
                                    text=fmt_vec(t.v1),
                                    fill=NEON_CYAN, font=("Consolas", 9))
            self.canvas.create_text(gx + 200, ry, anchor="w",
                                    text=fmt_vec(t.v2),
                                    fill=NEON_GREEN, font=("Consolas", 9))
            self.canvas.create_text(gx + 350, ry, anchor="w",
                                    text=fmt_vec(t.v3),
                                    fill=NEON_PINK, font=("Consolas", 9))

        if len(self.state.triangles) > max_rows:
            self.canvas.create_text(gx + gw / 2, gy + gh - 12,
                                    text=f"... ещё {len(self.state.triangles) - max_rows}",
                                    fill=TEXT_DIM,
                                    font=("Consolas", 9, "italic"))

    # ---------- ОБЩАЯ ПЕРЕРИСОВКА ----------
    def _redraw_all(self):
        for widget in self.entries.values():
            try:
                if widget.winfo_exists():
                    widget.place_forget()
            except Exception:
                pass

        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = self.W, self.H
        self.W, self.H = w, h

        self.btn_zones = {}

        self._draw_bg(w, h)
        self._draw_header(w)

        left_w = 400
        self._draw_left(50, 90, left_w, h - 110)

        c_x = 50 + left_w + 20
        c_w = (w - c_x - 50) * 0.5
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

        # клик по 3D — вращение
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
        elif key == "save":
            self._save()
        elif key == "random_new":
            self.state.randomize_new()
        elif key == "add_tri":
            self._add_triangle()

        self._redraw_all()

    def _load(self):
        path = filedialog.askopenfilename(
            title="Открыть STL",
            filetypes=[("STL files", "*.stl"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.state.load(path)
            messagebox.showinfo("Загружено",
                f"Файл: {os.path.basename(path)}\n"
                f"Треугольников: {len(self.state.triangles)}\n"
                f"Имя модели: {self.state.model_name}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать STL:\n{e}")

    def _save(self):
        if not self.state.triangles:
            messagebox.showwarning("Пусто", "Нет треугольников для сохранения")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить STL",
            defaultextension=".stl",
            filetypes=[("ASCII STL", "*.stl"), ("Binary STL", "*.stl")])
        if not path:
            return

        # Спросим формат
        answer = messagebox.askyesno("Формат",
            "Сохранить как Binary STL?\n\n"
            "Да = Binary (компактный)\n"
            "Нет = ASCII (текстовый)")
        try:
            if answer:
                save_binary_stl(path, self.state.triangles,
                                 self.state.model_name)
            else:
                save_ascii_stl(path, self.state.triangles,
                                self.state.model_name)
            size = os.path.getsize(path)
            messagebox.showinfo("Сохранено",
                f"Файл сохранён:\n{path}\n\n"
                f"Размер: {size} байт\n"
                f"Треугольников: {len(self.state.triangles)}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _add_triangle(self):
        try:
            v1 = self.state.new_tri[0]
            v2 = self.state.new_tri[1]
            v3 = self.state.new_tri[2]
            # проверка: не вырожденный
            normal = compute_normal(tuple(v1), tuple(v2), tuple(v3))
            if normal == (0, 0, 0):
                messagebox.showerror("Ошибка",
                    "Треугольник вырожденный.\n"
                    "Вершины на одной прямой или совпадают.")
                return
            self.state.add_triangle(v1, v2, v3)
            self.state.selected = len(self.state.triangles) - 1
            messagebox.showinfo("Добавлено",
                f"Треугольник добавлен.\n"
                f"Всего: {len(self.state.triangles)}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()