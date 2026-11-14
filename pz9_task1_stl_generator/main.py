"""
ОКФРС. Практика 9. Задание 1.
Минимальный валидный генератор STL.
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


def to_ascii_stl(v1, v2, v3, name="facet"):
    n = compute_normal(v1, v2, v3)
    lines = [
        f"solid {name}",
        f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}",
        f"    outer loop",
    ]
    for v in (v1, v2, v3):
        lines.append(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}")
    lines.append("    endloop")
    lines.append("  endfacet")
    lines.append(f"endsolid {name}")
    return "\n".join(lines)


def to_binary_stl(v1, v2, v3, name=b"OKFRS"):
    n = compute_normal(v1, v2, v3)
    header = (b"OKFRS STL Generator - " + name)[:80].ljust(80, b" ")
    count = struct.pack("<I", 1)
    data = struct.pack("<fff", *[float(x) for x in n])
    for v in (v1, v2, v3):
        data += struct.pack("<fff", *[float(x) for x in v])
    data += struct.pack("<H", 0)
    return header + count + data


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.v1 = [0.0, 0.0, 0.0]
        self.v2 = [1.0, 0.0, 0.0]
        self.v3 = [0.0, 1.0, 0.0]
        self.name = "triangle_okfrs"
        self.rot_z = math.radians(30)
        self.rot_x = math.radians(20)
        self.zoom = 1.0
        self.drag = None

    def get_v(self, idx):
        return [self.v1, self.v2, self.v3][idx]

    def normal(self):
        return compute_normal(tuple(self.v1), tuple(self.v2), tuple(self.v3))

    def area(self):
        a = vec_sub(self.v2, self.v1)
        b = vec_sub(self.v3, self.v1)
        return 0.5 * vec_length(vec_cross(a, b))

    def randomize(self):
        for v in (self.v1, self.v2, self.v3):
            v[0] = round(random.uniform(-2, 2), 1)
            v[1] = round(random.uniform(-2, 2), 1)
            v[2] = round(random.uniform(0, 2), 1)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("OKFRS · ПЗ9 · Задание 1 · STL Generator")
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
        self.canvas.create_text(60, 40, text="🔺",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="STL GENERATOR",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(340, 44,
                                text="· ОДИН ТРЕУГОЛЬНИК В STL",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ЛЕВАЯ ПАНЕЛЬ ----------
    def _draw_left(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ВЕРШИНЫ",
                                fill=NEON_PURP, font=FONT_LABEL)

        cy = y + 60
        # ширина колонки под одну ось
        axis_w = (w - 50) / 3

        for i, (label, color) in enumerate([
            ("V1", NEON_CYAN), ("V2", NEON_GREEN), ("V3", NEON_PINK),
        ]):
            vec = self.state.get_v(i)

            self.canvas.create_text(x + 20, cy, anchor="w",
                                    text=label, fill=color,
                                    font=("Consolas", 12, "bold"))
            cy += 24

            for j, axis in enumerate(["X", "Y", "Z"]):
                # левый угол колонки
                ax = x + 20 + j * axis_w

                # кнопка "−" (22px)
                self._tiny_btn(ax, cy, 22, 26, "−", NEON_RED,
                                f"dec_{i}_{j}")

                # поле (56px) — отступ 4px от кнопки
                key = f"v{i}_{j}"
                fx = ax + 22 + 4
                fw = axis_w - 22 - 4 - 22 - 4  # оставляем место для + и отступы
                if fw < 50:
                    fw = 50

                round_rect(self.canvas, fx, cy,
                           fx + fw, cy + 26, 4,
                           fill="#0a0d14", outline=BORDER_HL, width=1)
                self._entry(fx + 4, cy + 3, fw - 8, 20, key, f"{vec[j]:.1f}")

                # кнопка "+" справа от поля
                plus_x = fx + fw + 4
                self._tiny_btn(plus_x, cy, 22, 26, "+", NEON_GREEN,
                                f"inc_{i}_{j}")

                # подпись оси под полем
                self.canvas.create_text(fx + fw / 2, cy + 36,
                                        text=axis, fill=TEXT_DIM,
                                        font=("Consolas", 8))
            cy += 64

        # === математика ===
        cy = y + 300
        self.canvas.create_text(x + 20, cy, anchor="w",
                                text="▸ РЕЗУЛЬТАТЫ:",
                                fill=NEON_CYAN, font=FONT_LABEL)
        cy += 28

        n = self.state.normal()
        area = self.state.area()

        items = [
            ("Нормаль X", f"{n[0]:+.4f}", NEON_RED),
            ("Нормаль Y", f"{n[1]:+.4f}", NEON_GREEN),
            ("Нормаль Z", f"{n[2]:+.4f}", NEON_BLUE),
        ]
        for lbl, val, col in items:
            self.canvas.create_text(x + 30, cy, anchor="w",
                                    text=lbl, fill=TEXT_DIM,
                                    font=("Consolas", 10))
            self.canvas.create_text(x + w - 30, cy, anchor="e",
                                    text=val, fill=col,
                                    font=("Consolas", 10, "bold"))
            cy += 20

        cy += 10
        self.canvas.create_text(x + 30, cy, anchor="w",
                                text="Площадь",
                                fill=TEXT_DIM, font=("Consolas", 10))
        self.canvas.create_text(x + w - 30, cy, anchor="e",
                                text=f"{area:.4f}",
                                fill=NEON_AMBER,
                                font=("Consolas", 11, "bold"))
        cy += 22

        # === кнопки ===
        cy = y + h - 155
        self._btn(x + 20, cy, w - 40, 42,
                   "🎲 СЛУЧАЙНЫЙ", NEON_PURP, "random")
        self._btn(x + 20, cy + 50, w - 40, 42,
                   "💾 ASCII STL", NEON_CYAN, "save_ascii")
        self._btn(x + 20, cy + 100, w - 40, 42,
                   "💾 BINARY STL", NEON_GREEN, "save_binary")

    def _tiny_btn(self, x, y, w, h, label, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 4,
                   fill=lerp(color, BG_DEEP, 0.7),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Consolas", 14, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _entry(self, x, y, w, h, key, default):
        if key not in self.entries or not self.entries[key].winfo_exists():
            widget = tk.Entry(self.root, bg="#0a0d14", fg=NEON_GREEN,
                               insertbackground=NEON_CYAN,
                               font=("Consolas", 10, "bold"),
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
                    idx = int(key[1])
                    axis = int(key[3])
                    val = self.state.get_v(idx)[axis]
                    if widget.get() != f"{val:.1f}":
                        widget.delete(0, tk.END)
                        widget.insert(0, f"{val:.1f}")
                except Exception:
                    pass

        widget.place(x=x, y=y, width=w, height=h)
        widget.lift()

    def _on_entry_commit(self, key):
        try:
            widget = self.entries[key]
            val = float(widget.get().replace(",", "."))
            idx = int(key[1])
            axis = int(key[3])
            self.state.get_v(idx)[axis] = val
            self._redraw_all()
        except Exception:
            pass

    # ---------- ЦЕНТР ----------
    def _draw_center(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ 3D-ПРОЕКЦИЯ",
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
        scale = min(gw, gh) * 0.3 * self.state.zoom

        ca = math.cos(self.state.rot_z)
        sa = math.sin(self.state.rot_z)
        cb = math.cos(self.state.rot_x)
        sb = math.sin(self.state.rot_x)

        def project(v):
            x1 = v[0] * ca - v[1] * sa
            y1 = v[0] * sa + v[1] * ca
            z1 = v[2]
            y2 = y1 * cb - z1 * sb
            z2 = y1 * sb + z1 * cb
            return (cx + x1 * scale, cy - y2 * scale)

        p1 = project(self.state.v1)
        p2 = project(self.state.v2)
        p3 = project(self.state.v3)

        # оси
        o = project((0, 0, 0))
        ex = project((1, 0, 0))
        ey = project((0, 1, 0))
        ez = project((0, 0, 1))
        self.canvas.create_line(o[0], o[1], ex[0], ex[1],
                                fill=lerp(NEON_RED, BG_GRAPH, 0.5), dash=(3, 4))
        self.canvas.create_line(o[0], o[1], ey[0], ey[1],
                                fill=lerp(NEON_GREEN, BG_GRAPH, 0.5), dash=(3, 4))
        self.canvas.create_line(o[0], o[1], ez[0], ez[1],
                                fill=lerp(NEON_BLUE, BG_GRAPH, 0.5), dash=(3, 4))
        self.canvas.create_text(ex[0] + 12, ex[1], text="X",
                                fill=NEON_RED, font=("Consolas", 9, "bold"))
        self.canvas.create_text(ey[0], ey[1] + 14, text="Y",
                                fill=NEON_GREEN, font=("Consolas", 9, "bold"))
        self.canvas.create_text(ez[0], ez[1] - 10, text="Z",
                                fill=NEON_BLUE, font=("Consolas", 9, "bold"))

        # тень
        self.canvas.create_polygon(p1[0] + 6, p1[1] + 6,
                                    p2[0] + 6, p2[1] + 6,
                                    p3[0] + 6, p3[1] + 6,
                                    fill="#000000", outline="")
        # треугольник
        self.canvas.create_polygon(p1[0], p1[1],
                                    p2[0], p2[1],
                                    p3[0], p3[1],
                                    fill=lerp(NEON_PURP, BG_GRAPH, 0.6),
                                    outline=NEON_PURP, width=3)

        # вершины
        for (p, name, color) in [(p1, "V1", NEON_CYAN),
                                   (p2, "V2", NEON_GREEN),
                                   (p3, "V3", NEON_PINK)]:
            self.canvas.create_oval(p[0] - 6, p[1] - 6,
                                     p[0] + 6, p[1] + 6,
                                     fill=color, outline="#ffffff", width=2)
            self.canvas.create_text(p[0], p[1] - 16,
                                    text=name, fill=color,
                                    font=("Consolas", 10, "bold"))

        # нормаль
        vc = ((self.state.v1[0]+self.state.v2[0]+self.state.v3[0])/3,
              (self.state.v1[1]+self.state.v2[1]+self.state.v3[1])/3,
              (self.state.v1[2]+self.state.v2[2]+self.state.v3[2])/3)
        n = self.state.normal()
        vc_p = project(vc)
        n_end = project((vc[0]+n[0]*1.2, vc[1]+n[1]*1.2, vc[2]+n[2]*1.2))
        self.canvas.create_line(vc_p[0], vc_p[1],
                                n_end[0], n_end[1],
                                fill=NEON_AMBER, width=2,
                                arrow=tk.LAST, arrowshape=(10, 12, 4))
        self.canvas.create_text(n_end[0] + 15, n_end[1] - 8,
                                text="n", fill=NEON_AMBER,
                                font=("Consolas", 12, "bold"))

        self.canvas.create_text(gx + gw / 2, gy + gh - 15,
                                text=f"zoom = {self.state.zoom:.2f}×",
                                fill=TEXT_DIM,
                                font=("Consolas", 10))

    # ---------- ПРАВАЯ ----------
    def _draw_right(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ASCII STL",
                                fill=NEON_CYAN, font=FONT_LABEL)

        ascii_text = to_ascii_stl(tuple(self.state.v1),
                                   tuple(self.state.v2),
                                   tuple(self.state.v3), self.state.name)

        gx = x + 15
        gy = y + 50
        gw = w - 30
        gh = (h - 80) / 2
        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        for i, line in enumerate(ascii_text.split("\n")):
            ly = gy + 12 + i * 16
            if ly > gy + gh - 10:
                break
            self.canvas.create_text(gx + 15, ly, anchor="w",
                                    text=line, fill=NEON_GREEN,
                                    font=("Consolas", 9))

        by = gy + gh + 15
        self.canvas.create_text(x + 20, by, anchor="w",
                                text="▸ BINARY STL",
                                fill=NEON_AMBER, font=FONT_LABEL)
        by += 25

        round_rect(self.canvas, gx, by, gx + gw, by + gh - 15, 8,
                   fill=BG_GRAPH, outline="")

        bin_data = to_binary_stl(tuple(self.state.v1),
                                  tuple(self.state.v2),
                                  tuple(self.state.v3))
        self.canvas.create_text(gx + 15, by + 15, anchor="w",
                                text=f"{len(bin_data)} байт (80+4+50)",
                                fill=NEON_AMBER,
                                font=("Consolas", 10, "bold"))

        for i in range(0, min(160, len(bin_data)), 16):
            chunk = bin_data[i:i+16]
            hex_str = " ".join(f"{b:02x}" for b in chunk)
            asc_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            row = f"{i:04x}  {hex_str:<48}  {asc_str}"
            ly = by + 40 + (i // 16) * 14
            self.canvas.create_text(gx + 15, ly, anchor="w",
                                    text=row, fill=TEXT_MAIN,
                                    font=("Consolas", 8))

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

        left_w = 420
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
        self.state.zoom = max(0.3, min(4.0, self.state.zoom * delta))
        self._redraw_all()

    def _do_action(self, key):
        if key.startswith("inc_") or key.startswith("dec_"):
            parts = key.split("_")
            direction = 1 if parts[0] == "inc" else -1
            i = int(parts[1])
            j = int(parts[2])
            self.state.get_v(i)[j] = round(
                self.state.get_v(i)[j] + 0.1 * direction, 1)
        elif key == "random":
            self.state.randomize()
        elif key == "save_ascii":
            self._save_ascii()
        elif key == "save_binary":
            self._save_binary()

        self._redraw_all()

    def _save_ascii(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".stl",
            filetypes=[("STL files", "*.stl")],
            initialfile="triangle_ascii.stl")
        if not path:
            return
        try:
            text = to_ascii_stl(tuple(self.state.v1),
                                 tuple(self.state.v2),
                                 tuple(self.state.v3), self.state.name)
            with open(path, "w", encoding="ascii") as f:
                f.write(text)
            size = os.path.getsize(path)
            messagebox.showinfo("Сохранено",
                f"ASCII STL:\n{path}\n{size} байт")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _save_binary(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".stl",
            filetypes=[("STL files", "*.stl")],
            initialfile="triangle_binary.stl")
        if not path:
            return
        try:
            data = to_binary_stl(tuple(self.state.v1),
                                  tuple(self.state.v2),
                                  tuple(self.state.v3))
            with open(path, "wb") as f:
                f.write(data)
            size = os.path.getsize(path)
            messagebox.showinfo("Сохранено",
                f"Binary STL:\n{path}\n{size} байт")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()