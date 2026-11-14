"""
ОКФРС. Практика 9. Задание 6.
Каркасный 3D-рендер в стиле Elite:
матрицы поворота, перспектива, backface culling.
Премиум-стиль 2026.
"""
import tkinter as tk
from tkinter import messagebox
import sys, os, math, random, time

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
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_BOLD  = ("Segoe UI", 10, "bold")


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
# МАТРИЦЫ ПОВОРОТА
# ============================================================
def mat_mul(m1, m2):
    return [
        [sum(m1[i][k] * m2[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def mat_vec(m, v):
    return (
        m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
        m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
        m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
    )


def mat_rot_x(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def mat_rot_y(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def mat_rot_z(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


# ============================================================
# МОДЕЛИ
# ============================================================
def make_cube(size=1.0):
    """Куб: 8 вершин, 12 треугольников."""
    s = size / 2
    verts = [
        (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),
        (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2),  # bottom
        (4, 5, 6), (4, 6, 7),  # top
        (0, 1, 5), (0, 5, 4),  # front
        (2, 3, 7), (2, 7, 6),  # back
        (0, 4, 7), (0, 7, 3),  # left
        (1, 2, 6), (1, 6, 5),  # right
    ]
    return verts, faces


def make_pyramid(size=1.0):
    """Пирамида: 5 вершин, 6 граней."""
    s = size / 2
    verts = [
        (0, -s, 0),         # верх
        (-s, s, -s), (s, s, -s), (s, s, s), (-s, s, s),
    ]
    faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
        (1, 3, 2), (1, 4, 3),
    ]
    return verts, faces


def make_octahedron(size=1.0):
    """Октаэдр: 6 вершин, 8 треугольников."""
    s = size
    verts = [
        (s, 0, 0), (-s, 0, 0),
        (0, s, 0), (0, -s, 0),
        (0, 0, s), (0, 0, -s),
    ]
    faces = [
        (0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2),
        (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5),
    ]
    return verts, faces


def make_tetrahedron(size=1.0):
    s = size / math.sqrt(3)
    verts = [
        (s, s, s), (s, -s, -s), (-s, s, -s), (-s, -s, s),
    ]
    faces = [
        (0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2),
    ]
    return verts, faces


def make_spaceship():
    """Космический корабль — 10 вершин, 16 граней."""
    verts = [
        (0, 0, 1.5),       # 0 нос
        (0.8, 0, 0.5),     # 1 правый бок
        (-0.8, 0, 0.5),    # 2 левый бок
        (0, 0.6, 0.3),     # 3 верх
        (0, -0.6, 0.3),    # 4 низ
        (1.0, 0, -1.0),    # 5 правый хвост
        (-1.0, 0, -1.0),   # 6 левый хвост
        (0, 0.4, -1.0),    # 7 верхний хвост
        (0, -0.4, -1.0),   # 8 нижний хвост
    ]
    faces = [
        (0, 1, 3), (0, 3, 2), (0, 2, 4), (0, 4, 1),
        (1, 5, 7), (1, 7, 3), (3, 7, 6), (3, 6, 2),
        (2, 6, 8), (2, 8, 4), (4, 8, 5), (4, 5, 1),
        (5, 6, 7), (5, 8, 6), (7, 8, 5), (6, 8, 7),
    ]
    return verts, faces


MODELS = {
    "КУБ":        make_cube,
    "ПИРАМИДА":   make_pyramid,
    "ОКТАЭДР":    make_octahedron,
    "ТЕТРАЭДР":   make_tetrahedron,
    "КОРАБЛЬ":    make_spaceship,
}


# ============================================================
# РЕНДЕР
# ============================================================
class Renderer3D:
    def __init__(self, cx, cy, scale=150.0):
        self.cx = cx
        self.cy = cy
        self.scale = scale
        self.fov = 3.0       # чем больше — тем меньше перспективных искажений

    def project(self, v):
        """Перспективная проекция."""
        z = v[2] + 3.0      # сдвигаем камеру назад
        if z < 0.1:
            z = 0.1
        factor = self.fov / z
        return (self.cx + v[0] * self.scale * factor,
                self.cy - v[1] * self.scale * factor)

    def transform(self, verts, mat):
        """Применяем матрицу поворота ко всем вершинам."""
        return [mat_vec(mat, v) for v in verts]

    def normal(self, v1, v2, v3):
        """Нормаль по трём точкам."""
        ax = v2[0] - v1[0]; ay = v2[1] - v1[1]; az = v2[2] - v1[2]
        bx = v3[0] - v1[0]; by = v3[1] - v1[1]; bz = v3[2] - v1[2]
        nx = ay*bz - az*by
        ny = az*bx - ax*bz
        nz = ax*by - ay*bx
        l = math.sqrt(nx*nx + ny*ny + nz*nz)
        if l < 1e-9: return (0, 0, 0)
        return (nx/l, ny/l, nz/l)

    def is_visible(self, v1, v2, v3):
        """Backface culling: нормаль направлена на камеру?"""
        n = self.normal(v1, v2, v3)
        # центр грани
        c = ((v1[0]+v2[0]+v3[0])/3,
             (v1[1]+v2[1]+v3[1])/3,
             (v1[2]+v2[2]+v3[2])/3)
        # вектор от грани к камере (камера в (0,0,-3))
        cx = 0 - c[0]
        cy = 0 - c[1]
        cz = -3 - c[2]
        # скалярное произведение
        return n[0]*cx + n[1]*cy + n[2]*cz > 0


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.model_name = "КУБ"
        self.verts, self.faces = MODELS[self.model_name]()
        self.rot_x = math.radians(20)
        self.rot_y = math.radians(30)
        self.rot_z = math.radians(0)
        self.scale = 180.0
        self.fov = 3.0
        self.auto_rotate = True
        self.auto_speed = 0.4

        # режим
        self.mode = "filled"   # filled | wireframe | wireframe_filled
        self.show_hidden = True   # показывать скрытые линии пунктиром
        self.show_vertices = True
        self.show_normals = False

    def load_model(self, name):
        if name in MODELS:
            self.model_name = name
            self.verts, self.faces = MODELS[name]()

    def get_rotation_matrix(self):
        mx = mat_rot_x(self.rot_x)
        my = mat_rot_y(self.rot_y)
        mz = mat_rot_z(self.rot_z)
        return mat_mul(mat_mul(mx, my), mz)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 6 · Elite Wireframe")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.state = AppState()
        self.btn_zones = {}
        self.scene_rect = None
        self.W, self.H = 1600, 1000
        self.dragging = None

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)

        self.root.update_idletasks()
        self._redraw_all()
        self._animate()

    def _on_resize(self, event):
        self._redraw_all()

    def _draw_bg(self, w, h):
        for i in range(40):
            y0 = int(i * h / 40)
            y1 = int((i + 1) * h / 40)
            col = lerp(BG_DEEP, "#0a0e18", i / 40)
            self.canvas.create_rectangle(0, y0, w, y1, fill=col, outline="")

    def _draw_header(self, w):
        self.canvas.create_text(60, 40, text="🚀",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="ELITE WIREFRAME",
                                fill=TEXT_MAIN, anchor="w",
                                font=FONT_TITLE)
        self.canvas.create_text(370, 44,
                                text="· КАРКАСНЫЙ 3D-РЕНДЕР",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ПАНЕЛЬ ----------
    def _draw_left(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        cy = y + 25
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ МОДЕЛЬ", fill=NEON_PURP, font=FONT_LABEL)
        cy += 25

        # модели — 5 кнопок
        models = list(MODELS.keys())
        for i, name in enumerate(models):
            bx = x + 20
            by = cy + i * 38
            active = (self.state.model_name == name)
            self._btn(bx, by, w - 40, 32, name,
                       NEON_CYAN if active else TEXT_DIM, f"model_{name}")

        cy += len(models) * 38 + 15

        # === Режим ===
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ РЕЖИМ", fill=NEON_PURP, font=FONT_LABEL)
        cy += 25

        modes = [
            ("filled", "ЗАЛИВКА", NEON_AMBER),
            ("wireframe", "КАРКАС", NEON_GREEN),
            ("wireframe_filled", "КАРКАС+ЗАЛИВКА", NEON_CYAN),
        ]
        for i, (key, label, col) in enumerate(modes):
            active = (self.state.mode == key)
            self._btn(x + 20, cy + i * 38, w - 40, 32, label,
                       col if active else TEXT_DIM, f"mode_{key}")
        cy += len(modes) * 38 + 15

        # === Кнопки показа ===
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ ОТОБРАЖЕНИЕ", fill=NEON_PURP, font=FONT_LABEL)
        cy += 25

        toggles = [
            ("show_hidden", "СКРЫТЫЕ ЛИНИИ", NEON_PINK,
             self.state.show_hidden),
            ("show_vertices", "ВЕРШИНЫ", NEON_CYAN,
             self.state.show_vertices),
            ("show_normals", "НОРМАЛИ", NEON_AMBER,
             self.state.show_normals),
            ("auto_rotate", "АВТО-ВРАЩЕНИЕ", NEON_GREEN,
             self.state.auto_rotate),
        ]
        for i, (key, label, col, active) in enumerate(toggles):
            self._toggle_btn(x + 20, cy + i * 34, w - 40, 30,
                              key, label, col, active)

        # === Слайдеры ===
        cy = y + h - 320
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ ПАРАМЕТРЫ", fill=NEON_PURP, font=FONT_LABEL)
        cy += 25

        # Scale
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text=f"МАСШТАБ: {self.state.scale:.0f}",
                                fill=TEXT_DIM, font=("Consolas", 10))
        cy += 20
        self._slider(x + 20, cy, w - 40, (self.state.scale - 50) / 250.0,
                      "scale", 50, 300, NEON_CYAN)
        cy += 35

        # FOV
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text=f"ПЕРСПЕКТИВА: {self.state.fov:.1f}",
                                fill=TEXT_DIM, font=("Consolas", 10))
        cy += 20
        self._slider(x + 20, cy, w - 40, (self.state.fov - 1.0) / 9.0,
                      "fov", 1.0, 10.0, NEON_PINK)
        cy += 35

        # Скорость авто-вращения
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text=f"СКОРОСТЬ: {self.state.auto_speed:.2f}",
                                fill=TEXT_DIM, font=("Consolas", 10))
        cy += 20
        self._slider(x + 20, cy, w - 40, self.state.auto_speed / 2.0,
                      "speed", 0.0, 2.0, NEON_GREEN)

    def _btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 6,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=FONT_BOLD)
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _toggle_btn(self, x, y, w, h, key, label, color, active):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(color, BG_DEEP, 0.5),
                       outline=color, width=2)
            self.canvas.create_text(x + 15, y + h / 2, text="✓",
                                    fill=color, font=("Consolas", 12, "bold"))
            self.canvas.create_text(x + 35, y + h / 2, anchor="w",
                                    text=label, fill=color,
                                    font=FONT_BOLD)
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + 35, y + h / 2, anchor="w",
                                    text=label, fill=TEXT_DIM,
                                    font=FONT_BOLD)
        self.btn_zones[f"toggle_{key}"] = (x, y, x + w, y + h)

    def _slider(self, x, y, w, k, key, vmin, vmax, color):
        round_rect(self.canvas, x, y - 5, x + w, y + 5, 5,
                   fill="#0f141c", outline="")
        k = max(0.0, min(1.0, k))
        if k > 0.005:
            round_rect(self.canvas, x, y - 5, x + w * k, y + 5, 5,
                       fill=color, outline="")
        cx_ = x + w * k
        self.canvas.create_oval(cx_ - 9, y - 9, cx_ + 9, y + 9,
                                fill="#ffffff", outline=color, width=2)
        self.btn_zones[f"slider_{key}"] = (x, y - 10, x + w, y + 10)

    # ---------- СЦЕНА ----------
    def _draw_scene(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text=f"▸ {self.state.model_name}  ·  {self.state.mode}",
                                fill=NEON_CYAN, font=FONT_LABEL)

        self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                text="тяни мышью — вращение · колесо — масштаб",
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

        renderer = Renderer3D(cx, cy, self.state.scale)
        renderer.fov = self.state.fov

        # трансформируем вершины
        mat = self.state.get_rotation_matrix()
        transformed = renderer.transform(self.state.verts, mat)

        # проектируем
        projected = [renderer.project(v) for v in transformed]

        # === Разделяем грани на видимые и скрытые ===
        visible_faces = []
        hidden_faces = []
        for face in self.state.faces:
            v1, v2, v3 = (transformed[face[0]],
                          transformed[face[1]],
                          transformed[face[2]])
            if renderer.is_visible(v1, v2, v3):
                visible_faces.append(face)
            else:
                hidden_faces.append(face)

        mode = self.state.mode

        # === Скрытые грани (если включены) ===
        if self.state.show_hidden and mode in ("wireframe", "wireframe_filled"):
            for face in hidden_faces:
                p1 = projected[face[0]]
                p2 = projected[face[1]]
                p3 = projected[face[2]]
                self._draw_triangle_outline(p1, p2, p3,
                                             color=lerp(NEON_BLUE, BG_GRAPH, 0.5),
                                             dash=(3, 4))

        # === Видимые грани ===
        for face in visible_faces:
            p1 = projected[face[0]]
            p2 = projected[face[1]]
            p3 = projected[face[2]]

            if mode == "filled":
                # заливка
                n = renderer.normal(transformed[face[0]],
                                     transformed[face[1]],
                                     transformed[face[2]])
                light = 0.3 + 0.7 * abs(n[2])
                col = "#{:02x}{:02x}{:02x}".format(
                    int(50 * light + 30),
                    int(150 * light + 50),
                    int(220 * light + 35))
                self.canvas.create_polygon(p1[0], p1[1],
                                            p2[0], p2[1],
                                            p3[0], p3[1],
                                            fill=col, outline=col, width=1)

            elif mode == "wireframe":
                # только контур
                self._draw_triangle_outline(p1, p2, p3,
                                             color=NEON_GREEN, width=2)

            elif mode == "wireframe_filled":
                # заливка + контур
                n = renderer.normal(transformed[face[0]],
                                     transformed[face[1]],
                                     transformed[face[2]])
                light = 0.3 + 0.7 * abs(n[2])
                col = "#{:02x}{:02x}{:02x}".format(
                    int(50 * light + 30),
                    int(150 * light + 50),
                    int(220 * light + 35))
                self.canvas.create_polygon(p1[0], p1[1],
                                            p2[0], p2[1],
                                            p3[0], p3[1],
                                            fill=col, outline=NEON_GREEN,
                                            width=2)

        # === Вершины ===
        if self.state.show_vertices:
            for i, p in enumerate(projected):
                r = 4
                self.canvas.create_oval(p[0] - r, p[1] - r,
                                         p[0] + r, p[1] + r,
                                         fill=NEON_AMBER, outline="#ffffff", width=1)
                self.canvas.create_text(p[0] + 8, p[1] - 8,
                                        text=str(i), fill=NEON_AMBER,
                                        font=("Consolas", 8, "bold"))

        # === Нормали ===
        if self.state.show_normals:
            for face in self.state.faces:
                v1, v2, v3 = (transformed[face[0]],
                              transformed[face[1]],
                              transformed[face[2]])
                n = renderer.normal(v1, v2, v3)
                c = ((v1[0]+v2[0]+v3[0])/3,
                     (v1[1]+v2[1]+v3[1])/3,
                     (v1[2]+v2[2]+v3[2])/3)
                p_c = renderer.project(c)
                n_end = (c[0] + n[0] * 0.3,
                          c[1] + n[1] * 0.3,
                          c[2] + n[2] * 0.3)
                p_n = renderer.project(n_end)
                self.canvas.create_line(p_c[0], p_c[1],
                                        p_n[0], p_n[1],
                                        fill=NEON_AMBER, width=1,
                                        arrow=tk.LAST, arrowshape=(5, 6, 2))

        # подпись
        info = f"видимых: {len(visible_faces)} · скрытых: {len(hidden_faces)}"
        self.canvas.create_text(gx + gw / 2, gy + gh - 15,
                                text=info, fill=TEXT_DIM,
                                font=("Consolas", 10))

    def _draw_triangle_outline(self, p1, p2, p3, color, width=2, dash=None):
        for a, b in [(p1, p2), (p2, p3), (p3, p1)]:
            self.canvas.create_line(a[0], a[1], b[0], b[1],
                                    fill=color, width=width,
                                    dash=dash if dash else ())

    # ---------- ПРАВАЯ ----------
    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ИНФО",
                                fill=NEON_CYAN, font=FONT_LABEL)

        cy = y + 55

        # модель
        rows = [
            ("Модель",     self.state.model_name,         NEON_CYAN),
            ("Вершин",     f"{len(self.state.verts)}",    NEON_GREEN),
            ("Граней",     f"{len(self.state.faces)}",    NEON_PINK),
            ("Режим",      self.state.mode,               NEON_AMBER),
        ]
        for lbl, val, col in rows:
            self.canvas.create_text(x + 25, cy, anchor="w",
                                    text=lbl, fill=TEXT_DIM,
                                    font=("Consolas", 10))
            self.canvas.create_text(x + w - 25, cy, anchor="e",
                                    text=val, fill=col,
                                    font=("Consolas", 11, "bold"))
            cy += 22

        cy += 15
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ УГЛЫ ПОВОРОТА",
                                fill=NEON_PURP, font=FONT_LABEL)
        cy += 22

        angles = [
            ("X", math.degrees(self.state.rot_x), NEON_RED),
            ("Y", math.degrees(self.state.rot_y), NEON_GREEN),
            ("Z", math.degrees(self.state.rot_z), NEON_BLUE),
        ]
        for axis, deg, col in angles:
            self.canvas.create_text(x + 25, cy, anchor="w",
                                    text=f"∠{axis}:", fill=col,
                                    font=("Consolas", 10, "bold"))
            self.canvas.create_text(x + w - 25, cy, anchor="e",
                                    text=f"{deg:+.0f}°", fill=col,
                                    font=("Consolas", 11, "bold"))
            cy += 20

        cy += 20
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ ПРОИЗВОДИТЕЛЬНОСТЬ",
                                fill=NEON_CYAN, font=FONT_LABEL)
        cy += 22

        # FPS-метрика
        info = [
            ("Сцена", f"{len(self.state.faces)} полигонов", NEON_CYAN),
            ("Режим", self.state.mode, NEON_AMBER),
        ]
        for lbl, val, col in info:
            self.canvas.create_text(x + 25, cy, anchor="w",
                                    text=lbl, fill=TEXT_DIM,
                                    font=("Consolas", 10))
            cy += 18
            self.canvas.create_text(x + 35, cy, anchor="w",
                                    text=val, fill=col,
                                    font=("Consolas", 10, "bold"))
            cy += 20

        # Кнопки
        cy = y + h - 100
        bw = (w - 50) / 2
        self._btn(x + 20, cy, bw, 40,
                   "⟲ СБРОС", NEON_PINK, "reset")
        self._btn(x + 30 + bw, cy, bw, 40,
                   "📷 СКРИНШОТ", NEON_CYAN, "screenshot")

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

        left_w = 300
        self._draw_left(50, 90, left_w, h - 110)

        c_x = 50 + left_w + 20
        c_w = w - c_x - 50 - 260
        self._draw_scene(c_x, 90, c_w, h - 110)

        r_x = c_x + c_w + 15
        r_w = 250
        self._draw_right(r_x, 90, r_w, h - 110)

    # ---------- СОБЫТИЯ ----------
    def _on_click(self, event):
        x, y = event.x, event.y

        # слайдеры
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                if key.startswith("slider_"):
                    # клик по слайдеру — сдвинуть
                    name = key[7:]
                    k = (x - x0) / max(1, x1 - x0)
                    self._set_slider(name, k)
                    return
                else:
                    self._do_action(key)
                    return

        # клик в сцене — drag
        if self.scene_rect:
            gx, gy, gw, gh = self.scene_rect
            if gx <= x <= gx + gw and gy <= y <= gy + gh:
                self.dragging = (x, y, self.state.rot_x, self.state.rot_y)

    def _on_drag(self, event):
        if not self.dragging:
            return
        x0, y0, rx0, ry0 = self.dragging
        dx = event.x - x0
        dy = event.y - y0
        self.state.rot_y = ry0 + dx * 0.01
        self.state.rot_x = max(-math.pi/2, min(math.pi/2, rx0 + dy * 0.01))
        self._redraw_all()

    def _on_release(self, event):
        self.dragging = None

    def _on_wheel(self, event):
        delta = 10 if event.delta > 0 else -10
        self.state.scale = max(50, min(300, self.state.scale + delta))
        self._redraw_all()

    def _set_slider(self, name, k):
        if name == "scale":
            self.state.scale = 50 + k * 250
        elif name == "fov":
            self.state.fov = 1.0 + k * 9.0
        elif name == "speed":
            self.state.auto_speed = k * 2.0
        self._redraw_all()

    def _do_action(self, key):
        if key.startswith("model_"):
            self.state.load_model(key[6:])
        elif key.startswith("mode_"):
            self.state.mode = key[5:]
        elif key.startswith("toggle_"):
            name = key[7:]
            if name == "show_hidden":
                self.state.show_hidden = not self.state.show_hidden
            elif name == "show_vertices":
                self.state.show_vertices = not self.state.show_vertices
            elif name == "show_normals":
                self.state.show_normals = not self.state.show_normals
            elif name == "auto_rotate":
                self.state.auto_rotate = not self.state.auto_rotate
        elif key == "reset":
            self.state.rot_x = math.radians(20)
            self.state.rot_y = math.radians(30)
            self.state.rot_z = 0
            self.state.scale = 180
            self.state.fov = 3.0
        elif key == "screenshot":
            try:
                from PIL import ImageGrab
                from tkinter import filedialog
                path = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG", "*.png")],
                    initialfile="elite_render.png")
                if not path: return
                if self.scene_rect:
                    gx, gy, gw, gh = self.scene_rect
                    x1 = self.root.winfo_rootx() + self.canvas.winfo_x() + gx
                    y1 = self.root.winfo_rooty() + self.canvas.winfo_y() + gy
                    x2 = x1 + gw
                    y2 = y1 + gh
                    ImageGrab.grab().crop((x1, y1, x2, y2)).save(path)
                    messagebox.showinfo("Сохранено", path)
            except ImportError:
                messagebox.showerror("Ошибка", "pip install pillow")
        self._redraw_all()

    # ---------- АНИМАЦИЯ ----------
    def _animate(self):
        if self.state.auto_rotate:
            self.state.rot_y += 0.015 * self.state.auto_speed
            self.state.rot_x += 0.007 * self.state.auto_speed
            self._redraw_all()
        self.root.after(50, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()