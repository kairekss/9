"""
ОКФРС. Практика 9. Задание 7.
Генератор 3D-моделей методом экструзии (выдавливания 2D-профиля).
Создание полигона -> выдавливание в 3D -> проверка валидности.
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
BORDER_HL = "#2f3648"

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
    if l < 1e-12:
        return (0, 0, 0)
    return (v[0] / l, v[1] / l, v[2] / l)


def compute_normal(v1, v2, v3):
    return v_norm(v_cross(v_sub(v2, v1), v_sub(v3, v1)))


class Triangle:
    def __init__(self, v1, v2, v3):
        self.v1 = tuple(v1)
        self.v2 = tuple(v2)
        self.v3 = tuple(v3)
        self.normal = compute_normal(self.v1, self.v2, self.v3)

    def area(self):
        return 0.5 * v_length(v_cross(v_sub(self.v2, self.v1), v_sub(self.v3, self.v1)))


# ============================================================
# ЯДРО ЭКСТРУЗИИ
# ============================================================
def extrude_profile(points_2d, height):
    """
    Принимает список 2D-точек [(x,y), ...] и высоту H.
    Возвращает список треугольников (в виде списков вершин).
    1. Триангуляция нижней крышки.
    2. Триангуляция верхней крышки (с обратным обходом).
    3. Боковые грани (2 треугольника на каждое ребро).
    """
    n = len(points_2d)
    if n < 3:
        return []

    # Если пользователь нарисовал по часовой стрелке, развернем для корректных нормалей
    area2d = sum(points_2d[i][0] * points_2d[(i + 1) % n][1] - points_2d[(i + 1) % n][0] * points_2d[i][1] for i in
                 range(n)) / 2.0
    if area2d < 0:
        points_2d = list(reversed(points_2d))
        n = len(points_2d)

    tris = []

    z0 = 0
    z1 = height

    # Верхние и нижние вершины
    bot_verts = [(p[0], p[1], z0) for p in points_2d]
    top_verts = [(p[0], p[1], z1) for p in points_2d]

    # 1. Нижняя крышка (нормали вниз, обход по часовой)
    # Простая триангуляция "веером" от нулевой вершины
    for i in range(1, n - 1):
        tris.append((bot_verts[0], bot_verts[i + 1], bot_verts[i]))

    # 2. Верхняя крышка (нормали вверх, обход против часовой)
    for i in range(1, n - 1):
        tris.append((top_verts[0], top_verts[i], top_verts[i + 1]))

    # 3. Боковые стенки (4 вершины, разбиваем на 2 треугольника)
    for i in range(n):
        j = (i + 1) % n
        b1, b2 = bot_verts[i], bot_verts[j]
        t1, t2 = top_verts[i], top_verts[j]

        # Внешняя нормаль должна смотреть наружу.
        # Треугольник 1: b1 -> t1 -> b2
        # Треугольник 2: t1 -> t2 -> b2
        # В зависимости от обхода (CCW) нормали будут правильные.
        tris.append((b1, b2, t2))
        tris.append((b1, t2, t1))

    return tris


# ============================================================
# ВАЛИДАТОР (ИЗ ЗАДАНИЯ 3)
# ============================================================
def check_mesh_validity(triangles):
    """Проверяет, замкнут ли меш (watertight) и нет ли вывернутых нормалей."""

    def vkey(v):
        return (round(v[0], 5), round(v[1], 5), round(v[2], 5))

    edges = defaultdict(list)
    for i, t in enumerate(triangles):
        vs = [vkey(t.v1), vkey(t.v2), vkey(t.v3)]
        for a, b in [(0, 1), (1, 2), (2, 0)]:
            k = tuple(sorted([vs[a], vs[b]]))
            edges[k].append(i)

    open_edges = sum(1 for e, t in edges.items() if len(t) == 1)
    non_manifold = sum(1 for e, t in edges.items() if len(t) > 2)

    # Проверка нормалей
    directed = defaultdict(list)
    for i, t in enumerate(triangles):
        vs = [vkey(t.v1), vkey(t.v2), vkey(t.v3)]
        for a, b in [(0, 1), (1, 2), (2, 0)]:
            directed[(vs[a], vs[b])].append(i)

    flipped = 0
    for edge, t_list in directed.items():
        if len(t_list) > 1:
            flipped += 1

    is_valid = (open_edges == 0 and non_manifold == 0 and flipped == 0)

    return {
        "count": len(triangles),
        "open_edges": open_edges,
        "non_manifold": non_manifold,
        "flipped": flipped,
        "valid": is_valid
    }


# ============================================================
# STL
# ============================================================
def save_binary_stl(path, triangles):
    with open(path, "wb") as f:
        f.write(b"OKFRS Extrusion Model".ljust(80, b" "))
        f.write(struct.pack("<I", len(triangles)))
        for t in triangles:
            f.write(struct.pack("<fff", *t.normal))
            for v in (t.v1, t.v2, t.v3):
                f.write(struct.pack("<fff", *v))
            f.write(struct.pack("<H", 0))


def save_ascii_stl(path, triangles):
    with open(path, "w", encoding="ascii") as f:
        f.write("solid extruded_model\n")
        for t in triangles:
            f.write(f"  facet normal {t.normal[0]:.6e} {t.normal[1]:.6e} {t.normal[2]:.6e}\n")
            f.write("    outer loop\n")
            for v in (t.v1, t.v2, t.v3):
                f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
            f.write("    endloop\n  endfacet\n")
        f.write("endsolid extruded_model\n")


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        # Точки 2D-профиля в координатах от -2 до 2
        self.profile = [
            [-1.0, -1.0],
            [1.0, -1.0],
            [1.0, 1.0],
            [-1.0, 1.0]
        ]
        self.height = 1.5

        # Сгенерированные треугольники
        self.triangles = []
        self.validation = None

        # 3D камера
        self.rot_z = math.radians(30)
        self.rot_x = math.radians(20)
        self.zoom = 1.0
        self.size = 3.0
        self.center = (0, 0, 0)
        self.drag_view = None

        # Взаимодействие с профилем
        self.drag_point = None
        self.hover_point = None

        self.rebuild()

    def rebuild(self):
        tris_pts = extrude_profile(self.profile, self.height)
        self.triangles = [Triangle(*t) for t in tris_pts]
        self.validation = check_mesh_validity(self.triangles)

        # Центр и размер для камеры
        if self.triangles:
            xs = [v[0] for t in self.triangles for v in (t.v1, t.v2, t.v3)]
            ys = [v[1] for t in self.triangles for v in (t.v1, t.v2, t.v3)]
            zs = [v[2] for t in self.triangles for v in (t.v1, t.v2, t.v3)]
            self.center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
            self.size = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 0.1)

    def add_point(self):
        if len(self.profile) < 20:
            # Добавляем в конец со сдвигом
            if self.profile:
                last = self.profile[-1]
                self.profile.append([last[0] + 0.5, last[1] + 0.5])
            else:
                self.profile.append([0, 0])
            self.rebuild()

    def reset_square(self):
        self.profile = [[-1, -1], [1, -1], [1, 1], [-1, 1]]
        self.rebuild()

    def reset_triangle(self):
        self.profile = [[0, -1], [1, 1], [-1, 1]]
        self.rebuild()

    def reset_circle(self, steps=12):
        self.profile = []
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.profile.append([math.cos(a), math.sin(a)])
        self.rebuild()


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 7 · Extrusion")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.state = AppState()
        self.btn_zones = {}
        self.scene_2d_rect = None
        self.scene_3d_rect = None
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
        self.canvas.create_text(60, 40, text="🧊",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="EXTRUSION GENERATOR",
                                fill=TEXT_MAIN, anchor="w",
                                font=FONT_TITLE)
        self.canvas.create_text(390, 44,
                                text="· 2D-ПРОФИЛЬ → 3D-МЕШ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ЛЕВАЯ ----------
    def _draw_left(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        cy = y + 25
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ ШАБЛОНЫ", fill=NEON_PURP, font=FONT_LABEL)
        cy += 25

        self._btn(x + 20, cy, w - 40, 32, "⬛ КВАДРАТ", NEON_CYAN, "shape_square")
        cy += 38
        self._btn(x + 20, cy, w - 40, 32, "🔺 ТРЕУГОЛЬНИК", NEON_GREEN, "shape_triangle")
        cy += 38
        self._btn(x + 20, cy, w - 40, 32, "⭕ КРУГ (12)", NEON_AMBER, "shape_circle")
        cy += 45

        # === Точки профиля ===
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text=f"▸ ТОЧКИ ({len(self.state.profile)})",
                                fill=NEON_PINK, font=FONT_LABEL)
        cy += 20

        # Список точек
        for i, p in enumerate(self.state.profile[:12]):
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=f"{i}: ({p[0]:.2f}, {p[1]:.2f})",
                                    fill=TEXT_DIM if i != self.state.drag_point else NEON_AMBER,
                                    font=("Consolas", 9))
            cy += 16
        if len(self.state.profile) > 12:
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=f"... (+{len(self.state.profile) - 12})",
                                    fill=TEXT_DIM, font=("Consolas", 8))

        cy += 15
        self._btn(x + 20, cy, w - 40, 32, "➕ ДОБАВИТЬ ТОЧКУ", NEON_PURP, "add_point")
        cy += 40

        # Высота
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text=f"ВЫСОТА: {self.state.height:.2f}",
                                fill=NEON_AMBER, font=("Consolas", 10))
        cy += 20
        k = self.state.height / 5.0
        round_rect(self.canvas, x + 20, cy - 5, x + w - 20, cy + 5, 5, fill="#0f141c")
        round_rect(self.canvas, x + 20, cy - 5, x + 20 + (w - 40) * k, cy + 5, 5, fill=NEON_AMBER)
        self.canvas.create_oval(x + 20 + (w - 40) * k - 8, cy - 8, x + 20 + (w - 40) * k + 8, cy + 8, fill="#fff",
                                outline=NEON_AMBER, width=2)
        self.btn_zones["slider_height"] = (x + 20, cy - 10, x + w - 20, cy + 10)

        # === Кнопки сохранения ===
        cy = y + h - 100
        bw = (w - 50) / 2
        self._btn(x + 20, cy, bw, 36, "💾 ASCII", NEON_CYAN, "save_ascii")
        self._btn(x + 30 + bw, cy, bw, 36, "💾 BINARY", NEON_GREEN, "save_binary")

    def _btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    # ---------- ЦЕНТР — 2D ПРОФИЛЬ ----------
    def _draw_center(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ 2D-ПРОФИЛЬ (редактор)",
                                fill=NEON_CYAN, font=FONT_LABEL)
        self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                text="тяни точки мышью",
                                fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        gx = x + 20
        gy = y + 50
        gw = w - 40
        gh = h - 70
        self.scene_2d_rect = (gx, gy, gw, gh)

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        cx = gx + gw / 2
        cy = gy + gh / 2
        scale = min(gw, gh) * 0.25 * self.state.zoom

        # Сетка
        for i in range(-4, 5):
            xx = cx + i * scale
            yy = cy - i * scale
            self.canvas.create_line(xx, gy, xx, gy + gh, fill="#101820")
            self.canvas.create_line(gx, yy, gx + gw, yy, fill="#101820")

        # Оси
        self.canvas.create_line(cx, gy, cx, gy + gh, fill="#2a3040")
        self.canvas.create_line(gx, cy, gx + gw, cy, fill="#2a3040")

        # Полигон
        pts = []
        for p in self.state.profile:
            pts.append((cx + p[0] * scale, cy - p[1] * scale))

        if len(pts) >= 3:
            flat = [coord for pt in pts for coord in pt]
            self.canvas.create_polygon(flat, fill=lerp(NEON_CYAN, BG_GRAPH, 0.8),
                                       outline=NEON_CYAN, width=2)
        elif len(pts) > 1:
            flat = [coord for pt in pts for coord in pt]
            self.canvas.create_line(flat, fill=NEON_CYAN, width=2)

        # Точки
        for i, (px, py) in enumerate(pts):
            r = 6 if i == self.state.hover_point else 4
            col = NEON_AMBER if i == self.state.drag_point else NEON_PINK
            self.canvas.create_oval(px - r, py - r, px + r, py + r, fill=col, outline="#fff")
            self.canvas.create_text(px, py - 12, text=str(i), fill=NEON_PINK, font=("Consolas", 8))

    # ---------- ПРАВО — 3D РЕЗУЛЬТАТ ----------
    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ 3D-РЕЗУЛЬТАТ",
                                fill=NEON_GREEN, font=FONT_LABEL)

        # Валидатор
        v = self.state.validation
        if v:
            stat_col = NEON_GREEN if v["valid"] else NEON_RED
            stat_txt = "✓ ВАЛИДНЫЙ (watertight)" if v["valid"] else "✗ ОШИБКИ В МЕШЕ"
            self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                    text=stat_txt, fill=stat_col,
                                    font=("Segoe UI", 10, "bold"))

        gx = x + 20
        gy = y + 50
        gw = w - 40
        gh = h - 120
        self.scene_3d_rect = (gx, gy, gw, gh)

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        if not self.state.triangles: return

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
            # Перспектива
            z = z2 + self.state.size * 2.5
            if z < 0.1: z = 0.1
            f = (self.state.size * 2.5) / z
            return (cx + x1 * scale * f, cy - y2 * scale * f, y2 * cb + z2 * sb)

        tris = self.state.triangles
        items = []
        for t in tris:
            c = t.v1
            depth = (c[0] + c[1] + c[2])
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

            # Если невалидно, подсвечиваем
            if not self.state.validation["valid"]:
                col = lerp(col, NEON_RED, 0.3)

            self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1],
                                       fill=col, outline="#5566aa", width=1)

        # Статистика внизу
        if v:
            info = f"{v['count']} треуг. · дыр: {v['open_edges']} · вывернуто: {v['flipped']}"
            self.canvas.create_text(gx + gw / 2, gy + gh - 15, text=info,
                                    fill=TEXT_DIM, font=("Consolas", 10))

    def _redraw_all(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100: w, h = self.W, self.H
        self.W, self.H = w, h
        self.btn_zones = {}

        self._draw_bg(w, h)
        self._draw_header(w)

        left_w = 280
        self._draw_left(50, 90, left_w, h - 110)

        c_x = 50 + left_w + 15
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
                if key == "slider_height":
                    self.state.height = max(0.1, (x - x0) / (x1 - x0) * 5.0)
                    self.state.rebuild()
                    return
                self._do_action(key)
                return

        # Клик в 2D-сцене
        if self.scene_2d_rect:
            gx, gy, gw, gh = self.scene_2d_rect
            if gx <= x <= gx + gw and gy <= y <= gy + gh:
                hit = self._pick_point_2d(x, y)
                if hit is not None:
                    self.state.drag_point = hit
                    return

        # Клик в 3D-сцене
        if self.scene_3d_rect:
            gx, gy, gw, gh = self.scene_3d_rect
            if gx <= x <= gx + gw and gy <= y <= gy + gh:
                self.state.drag_view = (x, y, self.state.rot_z, self.state.rot_x)

    def _pick_point_2d(self, mx, my):
        gx, gy, gw, gh = self.scene_2d_rect
        cx = gx + gw / 2;
        cy = gy + gh / 2
        scale = min(gw, gh) * 0.25 * self.state.zoom
        for i, p in enumerate(self.state.profile):
            px = cx + p[0] * scale
            py = cy - p[1] * scale
            if math.hypot(mx - px, my - py) < 15:
                return i
        return None

    def _on_drag(self, event):
        if self.state.drag_point is not None:
            gx, gy, gw, gh = self.scene_2d_rect
            cx = gx + gw / 2;
            cy = gy + gh / 2
            scale = min(gw, gh) * 0.25 * self.state.zoom
            nx = (event.x - cx) / scale
            ny = -(event.y - cy) / scale
            self.state.profile[self.state.drag_point] = [round(nx, 2), round(ny, 2)]
            self.state.rebuild()
            self._redraw_all()
            return

        if self.state.drag_view:
            x0, y0, rz0, rx0 = self.state.drag_view
            self.state.rot_z = rz0 + (event.x - x0) * 0.01
            self.state.rot_x = max(-math.pi / 2, min(math.pi / 2, rx0 + (event.y - y0) * 0.01))
            self._redraw_all()

    def _on_release(self, event):
        self.state.drag_point = None
        self.state.drag_view = None

    def _on_wheel(self, event):
        delta = 1.1 if event.delta > 0 else 0.9
        self.state.zoom = max(0.3, min(10.0, self.state.zoom * delta))
        self._redraw_all()

    def _do_action(self, key):
        if key == "shape_square":
            self.state.reset_square()
        elif key == "shape_triangle":
            self.state.reset_triangle()
        elif key == "shape_circle":
            self.state.reset_circle()
        elif key == "add_point":
            self.state.add_point()
        elif key == "save_ascii":
            path = filedialog.asksaveasfilename(defaultextension=".stl", filetypes=[("STL", "*.stl")])
            if path: save_ascii_stl(path, self.state.triangles); messagebox.showinfo("ОК", path)
        elif key == "save_binary":
            path = filedialog.asksaveasfilename(defaultextension=".stl", filetypes=[("STL", "*.stl")])
            if path: save_binary_stl(path, self.state.triangles); messagebox.showinfo("ОК", path)
        self._redraw_all()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()