"""
ОКФРС. Практика 9. Задание 8.
Конвертер STL в SVG: ортографическая проекция и векторный чертёж.
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
BG_DEEP = "#08090f"
BG_GLASS = "#131823"
BG_GRAPH = "#050810"
BG_PANEL = "#0f141c"
BG_CELL = "#0e1218"
BORDER = "#232a3d"

NEON_CYAN = "#00f0ff"
NEON_GREEN = "#39ff88"
NEON_PINK = "#ff3ea5"
NEON_PURP = "#a066ff"
NEON_AMBER = "#ffb830"
NEON_RED = "#ff4d5e"
NEON_BLUE = "#4d8dff"

TEXT_MAIN = "#e8f0ff"
TEXT_DIM = "#5a6780"

FONT_MONO = ("Consolas", 13, "bold")
FONT_MONO_S = ("Consolas", 10)
FONT_LABEL = ("Segoe UI", 10, "bold")
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
        a = -math.pi / 2 + (math.pi / 2) * (i / steps)
        pts.extend([x2 - r + r * math.cos(a), y1 + r + r * math.sin(a)])
    for i in range(steps + 1):
        a = 0 + (math.pi / 2) * (i / steps)
        pts.extend([x2 - r + r * math.cos(a), y2 - r + r * math.sin(a)])
    for i in range(steps + 1):
        a = math.pi / 2 + (math.pi / 2) * (i / steps)
        pts.extend([x1 + r + r * math.cos(a), y2 - r + r * math.sin(a)])
    return canvas.create_polygon(pts, fill=fill or "", outline=outline or "",
                                 width=width, smooth=False, tags=tags)


# ============================================================
# МАТЕМАТИКА
# ============================================================
def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def v_length(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def v_norm(v):
    l = v_length(v)
    if l < 1e-12: return (0, 0, 0)
    return (v[0] / l, v[1] / l, v[2] / l)


class Triangle:
    def __init__(self, v1, v2, v3):
        self.v1 = tuple(v1)
        self.v2 = tuple(v2)
        self.v3 = tuple(v3)
        self.normal = v_norm(v_cross(v_sub(self.v2, self.v1), v_sub(self.v3, self.v1)))


# ============================================================
# ПАРСИНГ STL
# ============================================================
def read_ascii_stl(path):
    import re
    triangles = []
    with open(path, "r", encoding="ascii", errors="replace") as f:
        content = f.read()
    pattern = re.compile(
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+).*?"
        r"vertex\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)\s+([\-\deE\.\+]+)",
        re.DOTALL)
    for match in pattern.finditer(content):
        vals = [float(x) for x in match.groups()]
        triangles.append(Triangle(vals[0:3], vals[3:6], vals[6:9]))
    return triangles


def read_binary_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        cb = f.read(4)
        if len(cb) < 4: raise ValueError("Ошибка чтения")
        n = struct.unpack("<I", cb)[0]
        triangles = []
        for _ in range(n):
            data = f.read(50)
            if len(data) < 50: break
            vals = struct.unpack("<12fH", data)
            triangles.append(Triangle(vals[3:6], vals[6:9], vals[9:12]))
    return triangles


def detect_and_read(path):
    with open(path, "rb") as f:
        head = f.read(500)
    if b"facet normal" in head or b"endsolid" in head:
        return read_ascii_stl(path)
    return read_binary_stl(path)


# ============================================================
# ГЕНЕРАЦИЯ SVG
# ============================================================
def generate_svg(triangles, view="top", mode="silhouette"):
    """
    view: top | front | side
    mode: wireframe | silhouette
    """
    if not triangles: return ""

    # Выбор оси проекции
    if view == "top":
        # вид сверху (XY)
        proj = lambda v: (v[0], v[1])
        depth = lambda v: v[2]
    elif view == "front":
        # вид спереди (XZ)
        proj = lambda v: (v[0], v[2])
        depth = lambda v: v[1]
    else:
        # вид сбоку (YZ)
        proj = lambda v: (v[1], v[2])
        depth = lambda v: v[0]

    # 1. Собираем все 2D-грани
    faces = []
    for t in triangles:
        p1, p2, p3 = proj(t.v1), proj(t.v2), proj(t.v3)

        # Проверка backface culling (если нужно) - здесь пропускаем,
        # так как для чертежа нужны все линии (включая невидимые)

        # Вычисляем площадь проекции для отсечения вырожденных
        area = 0.5 * abs(p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]))
        if area > 1e-6:
            faces.append((p1, p2, p3))

    # Находим Bounding Box
    xs = [p[0] for f in faces for p in f]
    ys = [p[1] for f in faces for p in f]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x
    h = max_y - min_y

    # Отступы 10%
    pad = max(w, h) * 0.1
    svg_w = w + pad * 2
    svg_h = h + pad * 2

    # Координаты в SVG (Y инвертирован)
    def to_svg(x, y):
        return (x - min_x + pad, max_y - y + pad)

    # Формируем SVG
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.2f} {svg_h:.2f}">']
    svg.append('<rect width="100%" height="100%" fill="#1a1a24" />')

    if mode == "silhouette":
        # Для получения силуэта используем заливку без обводки.
        # Чтобы не было лишних линий, заливаем все полигоны.
        svg.append('<g fill="#00e5ff" stroke="none">')
        for p1, p2, p3 in faces:
            sx1, sy1 = to_svg(*p1)
            sx2, sy2 = to_svg(*p2)
            sx3, sy3 = to_svg(*p3)
            svg.append(f'<polygon points="{sx1:.2f},{sy1:.2f} {sx2:.2f},{sy2:.2f} {sx3:.2f},{sy3:.2f}" />')
        svg.append('</g>')
    else:
        # Wireframe (без дубликатов)
        edges = set()
        for p1, p2, p3 in faces:
            for a, b in [(p1, p2), (p2, p3), (p3, p1)]:
                # Ключ ребра (сортируем, чтобы (A,B) и (B,A) были одинаковыми)
                key = tuple(sorted([(round(a[0], 4), round(a[1], 4)),
                                    (round(b[0], 4), round(b[1], 4))]))
                edges.add(key)

        svg.append('<g fill="none" stroke="#00e5ff" stroke-width="1.5">')
        for (p1, p2) in edges:
            sx1, sy1 = to_svg(*p1)
            sx2, sy2 = to_svg(*p2)
            svg.append(f'<line x1="{sx1:.2f}" y1="{sy1:.2f}" x2="{sx2:.2f}" y2="{sy2:.2f}" />')
        svg.append('</g>')

    svg.append('</svg>')
    return "\n".join(svg)


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.triangles = []
        self.svg_string = ""

        self.view = "top"  # top | front | side
        self.mode = "wireframe"  # wireframe | silhouette

        self.rot_z = math.radians(30)
        self.rot_x = math.radians(20)
        self.size = 2.0
        self.center = (0, 0, 0)
        self.drag_view = None

    def load_stl(self, path):
        self.triangles = detect_and_read(path)
        self.update_bounds()
        self.rebuild_svg()

    def update_bounds(self):
        if not self.triangles: return
        xs = [v[0] for t in self.triangles for v in (t.v1, t.v2, t.v3)]
        ys = [v[1] for t in self.triangles for v in (t.v1, t.v2, t.v3)]
        zs = [v[2] for t in self.triangles for v in (t.v1, t.v2, t.v3)]
        self.center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
        self.size = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 0.1)

    def rebuild_svg(self):
        self.svg_string = generate_svg(self.triangles, self.view, self.mode)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 8 · STL to SVG")
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
        self.canvas.create_text(60, 40, text="✒️",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="STL → SVG CONVERTER",
                                fill=TEXT_MAIN, anchor="w",
                                font=FONT_TITLE)
        self.canvas.create_text(410, 44,
                                text="· 3D МЕШ → 2D ВЕКТОРНЫЙ ЧЕРТЁЖ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ЛЕВАЯ ПАНЕЛЬ ----------
    def _draw_left(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        cy = y + 25
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ ИСХОДНАЯ МОДЕЛЬ", fill=NEON_PURP, font=FONT_LABEL)
        cy += 25

        if self.state.triangles:
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=f"Треугольников: {len(self.state.triangles)}",
                                    fill=NEON_GREEN, font=("Consolas", 10))
        else:
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text="(файл не загружен)",
                                    fill=TEXT_DIM, font=("Consolas", 10))
        cy += 25

        self._btn(x + 20, cy, w - 40, 40,
                  "📂 ЗАГРУЗИТЬ STL", NEON_BLUE, "load")
        cy += 60

        # === ВИД ПРОЕКЦИИ ===
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ ПРОЕКЦИЯ", fill=NEON_CYAN, font=FONT_LABEL)
        cy += 25

        views = [
            ("top", "СВЕРХУ (XY)", NEON_GREEN),
            ("front", "СПЕРЕДИ (XZ)", NEON_PINK),
            ("side", "СБОКУ (YZ)", NEON_AMBER),
        ]
        for i, (key, label, col) in enumerate(views):
            active = (self.state.view == key)
            self._btn(x + 20, cy + i * 38, w - 40, 32, label,
                      col if active else TEXT_DIM, f"view_{key}")
        cy += 3 * 38 + 20

        # === РЕЖИМ ===
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ РЕЖИМ ЧЕРТЕЖА", fill=NEON_CYAN, font=FONT_LABEL)
        cy += 25

        modes = [
            ("wireframe", "КАРКАС (ВСЕ РЁБРА)", NEON_CYAN),
            ("silhouette", "СИЛУЭТ (КОНТУР)", NEON_GREEN),
        ]
        for i, (key, label, col) in enumerate(modes):
            active = (self.state.mode == key)
            self._btn(x + 20, cy + i * 38, w - 40, 32, label,
                      col if active else TEXT_DIM, f"mode_{key}")
        cy += 2 * 38 + 30

        # === КНОПКИ СОХРАНЕНИЯ ===
        self._btn(x + 20, cy, w - 40, 44, "💾 ЭКСПОРТ SVG", NEON_PINK, "save_svg")

    def _btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    # ---------- ЦЕНТР — 3D ОРИГИНАЛ ----------
    def _draw_center(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ 3D МОДЕЛЬ (ОРИГИНАЛ)",
                                fill=NEON_CYAN, font=FONT_LABEL)

        gx = x + 20
        gy = y + 50
        gw = w - 40
        gh = h - 70
        self.scene_rect = (gx, gy, gw, gh)

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        if not self.state.triangles: return

        cx = gx + gw / 2
        cy = gy + gh / 2
        scale = min(gw, gh) * 0.35 / self.state.size

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
            return (cx + x1 * scale, cy - y2 * scale, y2 * cb + z1 * sb)

        tris = self.state.triangles
        items = []
        for t in tris:
            depth = (t.v1[0] + t.v1[1] + t.v1[2])
            items.append((depth, t))
        items.sort(key=lambda x: x[0])

        for _, t in items:
            p1 = project(t.v1)
            p2 = project(t.v2)
            p3 = project(t.v3)
            n = t.normal
            light = 0.3 + 0.7 * abs(n[2])
            col = "#{:02x}{:02x}{:02x}".format(
                min(255, int(100 * light + 30)),
                min(255, int(150 * light + 40)),
                min(255, int(200 * light + 50)))
            self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1],
                                       fill=col, outline="#222", width=1)

    # ---------- ПРАВАЯ — SVG ПРЕВЬЮ ----------
    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ПРЕДПРОСМОТР ЧЕРТЕЖА (SVG)",
                                fill=NEON_GREEN, font=FONT_LABEL)

        mode_txt = "СИЛУЭТ" if self.state.mode == "silhouette" else "КАРКАС"
        view_txt = {"top": "СВЕРХУ", "front": "СПЕРЕДИ", "side": "СБОКУ"}.get(self.state.view, "")
        self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                text=f"{view_txt} · {mode_txt}",
                                fill=TEXT_DIM, font=("Consolas", 10))

        gx = x + 20
        gy = y + 50
        gw = w - 40
        gh = h - 80

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill="#1a1a24", outline="")

        if not self.state.triangles:
            return

        # Рисуем то же самое, что и в SVG, только на Canvas
        if self.state.view == "top":
            proj = lambda v: (v[0], v[1])
        elif self.state.view == "front":
            proj = lambda v: (v[0], v[2])
        else:
            proj = lambda v: (v[1], v[2])

        faces_2d = []
        for t in self.state.triangles:
            p1, p2, p3 = proj(t.v1), proj(t.v2), proj(t.v3)
            faces_2d.append((p1, p2, p3))

        # BBox
        xs = [p[0] for f in faces_2d for p in f]
        ys = [p[1] for f in faces_2d for p in f]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        bw = max_x - min_x
        bh = max_y - min_y
        if bw == 0: bw = 1
        if bh == 0: bh = 1

        pad = max(bw, bh) * 0.1
        scale = min(gw / (bw + pad * 2), gh / (bh + pad * 2))

        cx = gx + gw / 2
        cy = gy + gh / 2

        def to_screen(p):
            px = (p[0] - min_x) * scale + cx - (bw * scale) / 2
            py = -(p[1] - min_y) * scale + cy + (bh * scale) / 2
            return px, py

        if self.state.mode == "silhouette":
            for p1, p2, p3 in faces_2d:
                sx1, sy1 = to_screen(p1)
                sx2, sy2 = to_screen(p2)
                sx3, sy3 = to_screen(p3)
                self.canvas.create_polygon(sx1, sy1, sx2, sy2, sx3, sy3,
                                           fill=NEON_CYAN, outline="")
        else:
            edges = set()
            for p1, p2, p3 in faces_2d:
                for a, b in [(p1, p2), (p2, p3), (p3, p1)]:
                    key = tuple(sorted([(round(a[0], 4), round(a[1], 4)),
                                        (round(b[0], 4), round(b[1], 4))]))
                    edges.add(key)

            for p1, p2 in edges:
                sx1, sy1 = to_screen(p1)
                sx2, sy2 = to_screen(p2)
                self.canvas.create_line(sx1, sy1, sx2, sy2,
                                        fill=NEON_CYAN, width=2)

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

        left_w = 280
        self._draw_left(50, 90, left_w, h - 110)

        c_x = 50 + left_w + 20
        c_w = (w - c_x - 50) * 0.45
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
                self.state.drag_view = (x, y, self.state.rot_z, self.state.rot_x)

    def _on_drag(self, event):
        if self.state.drag_view:
            x0, y0, rz0, rx0 = self.state.drag_view
            self.state.rot_z = rz0 + (event.x - x0) * 0.01
            self.state.rot_x = max(-math.pi / 2, min(math.pi / 2, rx0 + (event.y - y0) * 0.01))
            self._redraw_all()

    def _on_release(self, event):
        self.state.drag_view = None

    def _on_wheel(self, event):
        pass  # Зум не нужен для этой сцены

    def _do_action(self, key):
        if key == "load":
            path = filedialog.askopenfilename(title="Открыть STL", filetypes=[("STL", "*.stl")])
            if not path: return
            try:
                self.state.load_stl(path)
                self._redraw_all()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        elif key.startswith("view_"):
            self.state.view = key[5:]
            self.state.rebuild_svg()
            self._redraw_all()

        elif key.startswith("mode_"):
            self.state.mode = key[5:]
            self.state.rebuild_svg()
            self._redraw_all()

        elif key == "save_svg":
            if not self.state.svg_string:
                messagebox.showwarning("Пусто", "Сначала загрузите модель")
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".svg",
                filetypes=[("SVG Image", "*.svg")],
                initialfile=f"projection_{self.state.view}.svg"
            )
            if not path: return
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.state.svg_string)
                size = os.path.getsize(path)
                messagebox.showinfo("Сохранено",
                                    f"Векторный чертёж сохранён:\n{path}\n\n"
                                    f"Размер: {size} байт\n\n"
                                    f"Можно открыть в браузере, Inkscape или Illustrator.")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()