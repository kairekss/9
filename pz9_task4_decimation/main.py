"""
ОКФРС. Практика 9. Задание 4.
Контролируемая децимация STL-модели.
Упрощение сетки с контролем качества (площадь, объём, габариты).
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
        triangles.append(Triangle(vals[3:6], vals[6:9], vals[9:12]))
    return triangles, name


def read_binary_stl(path):
    with open(path, "rb") as f:
        header = f.read(80)
        cb = f.read(4)
        if len(cb) < 4:
            raise ValueError("Слишком маленький файл")
        n = struct.unpack("<I", cb)[0]
        triangles = []
        for _ in range(n):
            data = f.read(50)
            if len(data) < 50: break
            vals = struct.unpack("<12fH", data)
            triangles.append(Triangle(vals[3:6], vals[6:9], vals[9:12]))
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
        for t in triangles:
            f.write(struct.pack("<fff", *t.normal))
            for v in (t.v1, t.v2, t.v3):
                f.write(struct.pack("<fff", *v))
            f.write(struct.pack("<H", 0))


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


# ============================================================
# СТАТИСТИКА МЕША
# ============================================================
def mesh_stats(triangles):
    if not triangles:
        return None
    total_vol = 0.0
    total_area = 0.0
    xs, ys, zs = [], [], []
    for t in triangles:
        total_area += t.area()
        total_vol += v_dot(t.v1, v_cross(t.v2, t.v3)) / 6.0
        for v in (t.v1, t.v2, t.v3):
            xs.append(v[0]); ys.append(v[1]); zs.append(v[2])
    bbox_min = (min(xs), min(ys), min(zs))
    bbox_max = (max(xs), max(ys), max(zs))
    diag = v_length(v_sub(bbox_max, bbox_min))
    return {
        "count": len(triangles),
        "area": total_area,
        "volume": abs(total_vol),
        "bbox": (bbox_min, bbox_max),
        "diag": diag,
    }


# ============================================================
# ДЕЦИМАЦИЯ (УПРОЩЕНИЕ)
# ============================================================
def decimate_by_ratio(triangles, keep_ratio):
    """
    Простая децимация: случайным образом убираем треугольники.
    Оставшиеся — сохраняем пропорционально площади (убираем мелкие).
    """
    if not triangles:
        return []
    n_keep = max(1, int(len(triangles) * keep_ratio))
    if n_keep >= len(triangles):
        return list(triangles)

    # сортируем по площади — оставляем крупные (важные для формы)
    indexed = [(t.area(), i, t) for i, t in enumerate(triangles)]
    indexed.sort(key=lambda x: -x[0])  # крупные первыми
    return [t for (_, _, t) in indexed[:n_keep]]


def decimate_by_target(triangles, target_count):
    if target_count >= len(triangles):
        return list(triangles)
    ratio = target_count / len(triangles)
    return decimate_by_ratio(triangles, ratio)


def decimate_uniform(triangles, keep_ratio):
    """
    Равномерное удаление — каждый n-й треугольник.
    Более предсказуемо по форме.
    """
    if not triangles:
        return []
    n_keep = max(1, int(len(triangles) * keep_ratio))
    if n_keep >= len(triangles):
        return list(triangles)
    step = len(triangles) / n_keep
    result = []
    for i in range(n_keep):
        idx = int(i * step)
        if idx < len(triangles):
            result.append(triangles[idx])
    return result


def decimate_smart(triangles, keep_ratio):
    """
    Умная децимация: удаляем треугольники с самой маленькой площадью,
    пока не достигнем нужного количества. Сохраняет крупные грани.
    """
    if not triangles:
        return []
    n_keep = max(1, int(len(triangles) * keep_ratio))
    if n_keep >= len(triangles):
        return list(triangles)
    # сортируем индексы по площади — маленькие в начале
    indexed = [(t.area(), i) for i, t in enumerate(triangles)]
    indexed.sort(key=lambda x: x[0])  # маленькие первыми
    keep_indices = set(idx for _, idx in indexed[n_keep:])
    return [t for i, t in enumerate(triangles) if i in keep_indices]


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.original = []
        self.decimated = []
        self.original_stats = None
        self.decimated_stats = None
        self.name = "object"

        self.method = "smart"       # smart | uniform | random
        self.keep_percent = 50      # 5% .. 100%

        self.rot_z = math.radians(30)
        self.rot_x = math.radians(20)
        self.zoom = 1.0
        self.size = 1.0
        self.center = (0, 0, 0)
        self.drag = None

        self.view_mode = "both"     # both | original | decimated

    def load(self, path):
        self.original, self.name = detect_and_read(path)
        self.original_stats = mesh_stats(self.original)
        self.decimated = []
        self.decimated_stats = None
        if self.original_stats:
            bbox = self.original_stats["bbox"]
            self.center = ((bbox[0][0]+bbox[1][0])/2,
                           (bbox[0][1]+bbox[1][1])/2,
                           (bbox[0][2]+bbox[1][2])/2)
            self.size = max(bbox[1][0]-bbox[0][0],
                            bbox[1][1]-bbox[0][1],
                            bbox[1][2]-bbox[0][2])
            if self.size < 0.001: self.size = 1.0

    def decimate(self):
        if not self.original:
            return
        ratio = self.keep_percent / 100.0
        if self.method == "smart":
            self.decimated = decimate_smart(self.original, ratio)
        elif self.method == "uniform":
            self.decimated = decimate_uniform(self.original, ratio)
        else:
            self.decimated = decimate_by_ratio(self.original, ratio)
        self.decimated_stats = mesh_stats(self.decimated)

    def quality_check(self):
        """Проверяет качество децимации."""
        if not self.original_stats or not self.decimated_stats:
            return None
        o = self.original_stats
        d = self.decimated_stats

        # Проценты отклонений
        def pct_diff(a, b):
            if a < 1e-9: return 0
            return abs(b - a) / a * 100

        return {
            "count_orig": o["count"],
            "count_dec": d["count"],
            "ratio": d["count"] / o["count"] if o["count"] else 0,
            "area_diff": pct_diff(o["area"], d["area"]),
            "volume_diff": pct_diff(o["volume"], d["volume"]),
            "diag_diff": pct_diff(o["diag"], d["diag"]),
            "area_ok": pct_diff(o["area"], d["area"]) <= 2.0,
            "volume_ok": pct_diff(o["volume"], d["volume"]) <= 5.0,
            "diag_ok": pct_diff(o["diag"], d["diag"]) <= 1.0,
        }


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 4 · Decimation")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.state = AppState()
        self.btn_zones = {}
        self.slider_zone = None
        self.slider_drag = False
        self.scene_left = None
        self.scene_right = None
        self.drag_view = None
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
        self.canvas.create_text(60, 40, text="🔪",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="DECIMATION",
                                fill=TEXT_MAIN, anchor="w",
                                font=FONT_TITLE)
        self.canvas.create_text(310, 44,
                                text="· УПРОЩЕНИЕ МЕША С КОНТРОЛЕМ КАЧЕСТВА",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ЛЕВАЯ ----------
    def _draw_left(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ПАРАМЕТРЫ",
                                fill=NEON_PURP, font=FONT_LABEL)

        cy = y + 55

        # Загрузка
        if self.state.original:
            self.canvas.create_text(x + w / 2, cy, anchor="center",
                                    text=f"{self.state.name[:30]}",
                                    fill=NEON_CYAN,
                                    font=("Consolas", 10, "bold"))
            cy += 18
            self.canvas.create_text(x + w / 2, cy, anchor="center",
                                    text=f"{len(self.state.original)} треугольников",
                                    fill=TEXT_DIM,
                                    font=("Consolas", 9))
        else:
            self.canvas.create_text(x + w / 2, cy, anchor="center",
                                    text="(файл не загружен)",
                                    fill=TEXT_DIM,
                                    font=("Consolas", 10, "italic"))
        cy += 30

        self._btn(x + 20, cy, w - 40, 40,
                   "📂 ЗАГРУЗИТЬ STL", NEON_BLUE, "load")
        cy += 55

        # Метод
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="МЕТОД ДЕЦИМАЦИИ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        cy += 22

        methods = [
            ("smart",   "SMART (по площади)", NEON_GREEN),
            ("uniform", "РАВНОМЕРНЫЙ",        NEON_CYAN),
            ("random",  "СЛУЧАЙНЫЙ",          NEON_AMBER),
        ]
        for i, (key, label, col) in enumerate(methods):
            bx = x + 20
            by = cy + i * 42
            active = (self.state.method == key)
            self._method_btn(bx, by, w - 40, 36, key, label, col, active)
        cy += 3 * 42 + 10

        # Ползунок процента
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text=f"ОСТАВИТЬ: {self.state.keep_percent}%",
                                fill=NEON_AMBER, font=FONT_LABEL)
        cy += 22

        bar_x0 = x + 20
        bar_x1 = x + w - 20
        bar_y = cy
        bar_h = 14

        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x1, bar_y + bar_h/2, bar_h//2,
                   fill="#0f141c", outline="")

        k = (self.state.keep_percent - 5) / (100 - 5)
        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x0 + (bar_x1 - bar_x0) * k, bar_y + bar_h/2,
                   bar_h//2, fill=NEON_AMBER, outline="")
        cx_ = bar_x0 + (bar_x1 - bar_x0) * k
        self.canvas.create_oval(cx_ - 10, bar_y - 10, cx_ + 10, bar_y + 10,
                                fill="#ffffff", outline=NEON_AMBER, width=2)
        self.slider_zone = (bar_x0, bar_y - 16, bar_x1, bar_y + 16)
        cy += 40

        # Кнопки быстрого выбора
        percents = [10, 25, 50, 75, 90]
        bw = (w - 40 - 4 * 5) / 5
        for i, p in enumerate(percents):
            bx = x + 20 + i * (bw + 5)
            active = (self.state.keep_percent == p)
            self._tiny_btn(bx, cy, bw, 28, f"{p}%", p, active)
        cy += 50

        # Кнопка «Применить»
        self._btn(x + 20, cy, w - 40, 44,
                   "✂ ПРИМЕНИТЬ ДЕЦИМАЦИЮ", NEON_PINK, "apply")
        cy += 55

        # Информация
        if self.state.decimated_stats:
            d = self.state.decimated_stats
            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text="РЕЗУЛЬТАТ:",
                                    fill=NEON_CYAN, font=FONT_LABEL_S)
            cy += 22
            info = [
                ("Треугольников", f"{d['count']}", NEON_CYAN),
                ("Площадь", f"{d['area']:.3f}", NEON_GREEN),
                ("Объём", f"{d['volume']:.3f}", NEON_AMBER),
            ]
            for lbl, val, col in info:
                self.canvas.create_text(x + 30, cy, anchor="w",
                                        text=lbl, fill=TEXT_DIM,
                                        font=("Consolas", 10))
                self.canvas.create_text(x + w - 30, cy, anchor="e",
                                        text=val, fill=col,
                                        font=("Consolas", 10, "bold"))
                cy += 20

    def _method_btn(self, x, y, w, h, key, label, color, active):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(color, BG_DEEP, 0.6),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Segoe UI", 9, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
        self.btn_zones[f"method_{key}"] = (x, y, x + w, y + h)

    def _tiny_btn(self, x, y, w, h, label, val, active):
        color = NEON_AMBER
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 4,
                       fill=lerp(color, BG_DEEP, 0.5),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Consolas", 10, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 4,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Consolas", 10, "bold"))
        self.btn_zones[f"pct_{val}"] = (x, y, x + w, y + h)

    def _btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    # ---------- ЦЕНТР — 2 СЦЕНЫ ----------
    def _draw_centers(self, x, y, w, h):
        # две колонки
        gap = 15
        col_w = (w - gap) / 2

        self._draw_scene(x, y, col_w, h, "original")
        self._draw_scene(x + col_w + gap, y, col_w, h, "decimated")

    def _draw_scene(self, x, y, w, h, kind):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        title = "▸ ОРИГИНАЛ" if kind == "original" else "▸ ПОСЛЕ ДЕЦИМАЦИИ"
        color = NEON_CYAN if kind == "original" else NEON_PINK
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text=title, fill=color,
                                font=FONT_LABEL)

        tris = self.state.original if kind == "original" else self.state.decimated
        count = len(tris)
        self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                text=f"{count} треуг.",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        gx = x + 15
        gy = y + 50
        gw = w - 30
        gh = h - 70

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        if not tris:
            self.canvas.create_text(gx + gw / 2, gy + gh / 2,
                                    text="(пусто)",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 12, "italic"))
            if kind == "original":
                self.scene_left = (gx, gy, gw, gh)
            else:
                self.scene_right = (gx, gy, gw, gh)
            return

        if kind == "original":
            self.scene_left = (gx, gy, gw, gh)
        else:
            self.scene_right = (gx, gy, gw, gh)

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
            return (cx + x1 * scale, cy - y2 * scale)

        # сортировка по глубине
        items = []
        for t in tris:
            c = t.v1  # условно
            depth = (t.v1[0]+t.v2[0]+t.v3[0]) * 0.01 + (t.v1[1]+t.v2[1]+t.v3[1]) * 0.01
            items.append((depth, t))
        items.sort(key=lambda x: x[0])

        for _, t in items:
            p1 = project(t.v1)
            p2 = project(t.v2)
            p3 = project(t.v3)
            n = t.normal
            light = 0.4 + 0.6 * abs(n[2])
            col = "#{:02x}{:02x}{:02x}".format(
                min(255, int(100 * light + 50)),
                min(255, int(100 * light + 50)),
                min(255, int(200 * light + 50)))
            self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1],
                                        fill=col, outline=col, width=1)

    # ---------- ПРАВАЯ — ОТЧЁТ ----------
    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ СРАВНИТЕЛЬНЫЙ ОТЧЁТ",
                                fill=NEON_CYAN, font=FONT_LABEL)

        q = self.state.quality_check() if self.state.decimated_stats else None
        if not q:
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text="Загрузи файл\nи примени децимацию",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 12, "italic"),
                                    justify="center")
            return

        cy = y + 55

        # Треугольники
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="ТРЕУГОЛЬНИКИ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        cy += 22
        self.canvas.create_text(x + 30, cy, anchor="w",
                                text=f"{q['count_orig']} → {q['count_dec']}",
                                fill=NEON_CYAN,
                                font=("Consolas", 14, "bold"))
        cy += 25
        self.canvas.create_text(x + 30, cy, anchor="w",
                                text=f"(сохранено {q['ratio']*100:.1f}%)",
                                fill=TEXT_DIM,
                                font=("Consolas", 9))
        cy += 30

        # Площадь
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="ПЛОЩАДЬ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        cy += 20
        self.canvas.create_text(x + 30, cy, anchor="w",
                                text=f"{self.state.original_stats['area']:.3f} → {self.state.decimated_stats['area']:.3f}",
                                fill=NEON_GREEN,
                                font=("Consolas", 12, "bold"))
        cy += 20
        self._status_row(x, cy, w, "отклонение", f"{q['area_diff']:.2f}%",
                          "OK" if q['area_ok'] else "FAIL", q['area_ok'])
        cy += 30

        # Объём
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="ОБЪЁМ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        cy += 20
        self.canvas.create_text(x + 30, cy, anchor="w",
                                text=f"{self.state.original_stats['volume']:.3f} → {self.state.decimated_stats['volume']:.3f}",
                                fill=NEON_AMBER,
                                font=("Consolas", 12, "bold"))
        cy += 20
        self._status_row(x, cy, w, "отклонение", f"{q['volume_diff']:.2f}%",
                          "OK" if q['volume_ok'] else "FAIL", q['volume_ok'])
        cy += 30

        # Габариты
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="ДИАГОНАЛЬ BBOX:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        cy += 20
        self.canvas.create_text(x + 30, cy, anchor="w",
                                text=f"{self.state.original_stats['diag']:.2f} → {self.state.decimated_stats['diag']:.2f}",
                                fill=NEON_PURP,
                                font=("Consolas", 12, "bold"))
        cy += 20
        self._status_row(x, cy, w, "отклонение", f"{q['diag_diff']:.2f}%",
                          "OK" if q['diag_ok'] else "FAIL", q['diag_ok'])
        cy += 35

        # Итог
        all_ok = q['area_ok'] and q['volume_ok'] and q['diag_ok']
        if all_ok:
            status = "✓ КАЧЕСТВО ДОПУСТИМО"
            scol = NEON_GREEN
        else:
            status = "⚠ КАЧЕСТВО СНИЖЕНО"
            scol = NEON_AMBER
        round_rect(self.canvas, x + 15, cy, x + w - 15, cy + 50, 8,
                   fill=lerp(scol, BG_DEEP, 0.7), outline=scol, width=2)
        self.canvas.create_text(x + w / 2, cy + 25,
                                text=status, fill=scol,
                                font=("Segoe UI", 14, "bold"))
        cy += 65

        # Кнопки сохранения
        bw = (w - 50) / 2
        self._btn(x + 20, cy, bw, 40, "💾 ASCII", NEON_CYAN, "save_ascii")
        self._btn(x + 20 + bw + 10, cy, bw, 40, "💾 BINARY", NEON_GREEN, "save_binary")

    def _status_row(self, x, y, w, label, value, tag, ok):
        col = NEON_GREEN if ok else NEON_RED
        self.canvas.create_text(x + 30, y, anchor="w",
                                text=label, fill=TEXT_DIM,
                                font=("Consolas", 9))
        self.canvas.create_text(x + w - 80, y, anchor="e",
                                text=value, fill=col,
                                font=("Consolas", 10, "bold"))
        self.canvas.create_text(x + w - 25, y, anchor="e",
                                text=tag, fill=col,
                                font=("Consolas", 9, "bold"))

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

        left_w = 340
        self._draw_left(50, 90, left_w, h - 110)

        c_x = 50 + left_w + 20
        c_w = (w - c_x - 50) * 0.7
        self._draw_centers(c_x, 90, c_w, h - 110)

        r_x = c_x + c_w + 15
        r_w = w - r_x - 50
        self._draw_right(r_x, 90, r_w, h - 110)

    # ---------- СОБЫТИЯ ----------
    def _on_click(self, event):
        x, y = event.x, event.y

        # слайдер
        if self.slider_zone:
            sx0, sy0, sx1, sy1 = self.slider_zone
            if sx0 <= x <= sx1 and sy0 <= y <= sy1:
                self.slider_drag = True
                self._set_slider(x)
                return

        # кнопки
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return

        # вращение — клик в любой сцене
        for rect in (self.scene_left, self.scene_right):
            if rect:
                gx, gy, gw, gh = rect
                if gx <= x <= gx + gw and gy <= y <= gy + gh:
                    self.drag_view = (x, y, self.state.rot_z, self.state.rot_x)
                    return

    def _on_drag(self, event):
        if self.slider_drag:
            self._set_slider(event.x)
            return
        if self.drag_view:
            x0, y0, rz0, rx0 = self.drag_view
            dx = event.x - x0
            dy = event.y - y0
            self.state.rot_z = rz0 + dx * 0.01
            self.state.rot_x = max(-math.pi/2, min(math.pi/2, rx0 + dy * 0.01))
            self._redraw_all()

    def _on_release(self, event):
        self.slider_drag = False
        self.drag_view = None

    def _on_wheel(self, event):
        # zoom по колесу на любой сцене
        for rect in (self.scene_left, self.scene_right):
            if rect:
                gx, gy, gw, gh = rect
                if gx <= event.x <= gx + gw and gy <= event.y <= gy + gh:
                    delta = 1.1 if event.delta > 0 else 0.9
                    self.state.zoom = max(0.3, min(10.0, self.state.zoom * delta))
                    self._redraw_all()
                    return

    def _set_slider(self, mouse_x):
        if not self.slider_zone:
            return
        x0, y0, x1, y1 = self.slider_zone
        k = (mouse_x - x0) / max(1, x1 - x0)
        k = max(0.0, min(1.0, k))
        val = int(5 + k * (100 - 5))
        self.state.keep_percent = val
        self._redraw_all()

    def _do_action(self, key):
        if key == "load":
            self._load()
        elif key.startswith("method_"):
            self.state.method = key[7:]
            self._redraw_all()
        elif key.startswith("pct_"):
            self.state.keep_percent = int(key[4:])
            self._redraw_all()
        elif key == "apply":
            self._apply()
        elif key == "save_ascii":
            self._save("ascii")
        elif key == "save_binary":
            self._save("binary")

    def _load(self):
        path = filedialog.askopenfilename(
            title="Открыть STL",
            filetypes=[("STL files", "*.stl")])
        if not path: return
        try:
            self.state.load(path)
            self.state.decimated = []
            self.state.decimated_stats = None
            messagebox.showinfo("Загружено",
                f"Файл: {os.path.basename(path)}\n"
                f"Треугольников: {len(self.state.original)}")
            self._redraw_all()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _apply(self):
        if not self.state.original:
            messagebox.showwarning("Нет файла", "Загрузите STL")
            return
        self.state.decimate()
        self._redraw_all()

    def _save(self, kind):
        if not self.state.decimated:
            messagebox.showwarning("Пусто", "Сначала примените децимацию")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".stl",
            initialfile=f"decimated_{self.state.keep_percent}pct.stl",
            filetypes=[("STL files", "*.stl")])
        if not path: return
        try:
            if kind == "ascii":
                save_ascii_stl(path, self.state.decimated, self.state.name)
            else:
                save_binary_stl(path, self.state.decimated, self.state.name)
            size = os.path.getsize(path)
            messagebox.showinfo("Сохранено",
                f"Сохранено:\n{path}\n\n"
                f"Треугольников: {len(self.state.decimated)}\n"
                f"Размер: {size} байт")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()