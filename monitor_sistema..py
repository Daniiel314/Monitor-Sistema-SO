import tkinter as tk
from tkinter import ttk
import psutil
import time

# Configuración de Matplotlib con Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class Monitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Sistema Basico")
        self.root.geometry("950x750")

        # ======== ESTADO DEL SISTEMA ========
        self.monitor_activo = True
        self.last_process_update = 0

        # RED (Inicialización de variables anteriores)
        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()

        # ======== TEMA OSCURO ========
        style = ttk.Style()
        style.theme_use("clam")

        self.colors = {
            "bg": "#1e1e1e",
            "fg": "#ffffff",
            "panel": "#2b2b2b",
            "cpu": "#00ffff",      # Cyan
            "down": "#00ff00",     # Verde Matrix
            "up": "#ff00ff"        # Magenta
        }

        # Configuración de estilos
        style.configure("Treeview",
                        background=self.colors["panel"],
                        fieldbackground=self.colors["panel"],
                        foreground=self.colors["fg"],
                        borderwidth=0)
        style.map('Treeview', background=[('selected', self.colors["cpu"])], foreground=[('selected', 'black')])

        style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"], fieldbackground=self.colors["panel"])
        style.configure("TNotebook", background=self.colors["bg"])
        style.configure("TNotebook.Tab", padding=[10, 5], font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", self.colors["panel"])], foreground=[("selected", self.colors["fg"])])
        style.configure("TProgressbar", thickness=15, troughcolor=self.colors["panel"], background=self.colors["cpu"])

        root.config(bg=self.colors["bg"])

        # ======== CABECERA ========
        header_frame = tk.Frame(root, bg=self.colors["bg"])
        header_frame.pack(fill="x", padx=10, pady=5)

        title = tk.Label(header_frame, text="Monitor de Sistema", font=("Segoe UI", 16, "bold"),
                         bg=self.colors["bg"], fg=self.colors["fg"])
        title.pack(side="left")

        self.btn_toggle = tk.Button(header_frame, text="⏸ Pausar", font=("Segoe UI", 9),
                                    bg="#444", fg="white", relief="flat",
                                    command=self.toggle_monitor)
        self.btn_toggle.pack(side="right")

        # ======== PESTAÑAS ========
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.tab_general = ttk.Frame(self.notebook)
        self.tab_cores = ttk.Frame(self.notebook)
        self.tab_procesos = ttk.Frame(self.notebook)
        self.tab_graficas = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_general, text="Resumen General")
        self.notebook.add(self.tab_cores, text="CPU por Núcleo")
        self.notebook.add(self.tab_procesos, text="Top Procesos")
        self.notebook.add(self.tab_graficas, text="Gráficas (CPU y Red)")

        # Inicializar Pestañas
        self.setup_general_tab()
        self.setup_cores_tab()
        self.setup_procesos_tab()
        self.setup_graficas_tab()

        # Precalentamiento: procesos (evita CPU%=0 en la primera actualización)
        for p in psutil.process_iter():
            try:
                p.cpu_percent()
            except Exception:
                pass

        # Iniciar loop
        self.actualizar_metricas()

    # ----------------------------------------------------
    def toggle_monitor(self):
        self.monitor_activo = not self.monitor_activo
        if self.monitor_activo:
            self.btn_toggle.config(text="⏸ Pausar", bg="#444")
        else:
            self.btn_toggle.config(text="▶ Reanudar", bg="#228b22")

    def get_size(self, bytes):
        for unit in ["", "K", "M", "G", "T"]:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}B"
            bytes /= 1024
        return f"{bytes:.1f} TB"

    # ===========================================================
    # PESTAÑA 1: GENERAL
    # ===========================================================
    def setup_general_tab(self):
        frame = tk.Frame(self.tab_general, bg=self.colors["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # RAM
        tk.Label(frame, text="Memoria RAM", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor="w")
        self.prog_ram = ttk.Progressbar(frame, length=400, mode='determinate')
        self.prog_ram.pack(fill="x", pady=5)
        self.txt_ram = tk.Label(frame, text="Calculando...", bg=self.colors["bg"], fg=self.colors["fg"])
        self.txt_ram.pack(anchor="e")

        tk.Frame(frame, height=20, bg=self.colors["bg"]).pack()

        # DISCO
        tk.Label(frame, text="Disco Raíz (/)", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor="w")
        self.prog_disk = ttk.Progressbar(frame, length=400)
        self.prog_disk.pack(fill="x", pady=5)
        self.txt_disk = tk.Label(frame, text="Calculando...", bg=self.colors["bg"], fg=self.colors["fg"])
        self.txt_disk.pack(anchor="e")

        tk.Frame(frame, height=30, bg=self.colors["bg"]).pack()

        # RED (TEXTO)
        panel_red = tk.Frame(frame, bg=self.colors["panel"], padx=10, pady=10)
        panel_red.pack(fill="x")

        tk.Label(panel_red, text="Velocidad Actual", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["panel"], fg=self.colors["fg"]).pack()

        self.txt_net_down = tk.Label(panel_red, text="Bajada: 0 KB/s", font=("Consolas", 14),
                                     fg=self.colors["down"], bg=self.colors["panel"])
        self.txt_net_down.pack(pady=5)

        self.txt_net_up = tk.Label(panel_red, text="Subida: 0 KB/s", font=("Consolas", 14),
                                   fg=self.colors["up"], bg=self.colors["panel"])
        self.txt_net_up.pack(pady=5)

    # ===========================================================
    # PESTAÑA 2: NÚCLEOS
    # ===========================================================
    def setup_cores_tab(self):
        canvas = tk.Canvas(self.tab_cores, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_cores, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.colors["bg"])
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.core_widgets = []
        num_cores = psutil.cpu_count(logical=True)
        for i in range(num_cores):
            box = tk.Frame(self.scrollable_frame, bg=self.colors["bg"])
            box.pack(fill="x", pady=2)
            tk.Label(box, text=f"Core {i}:", width=8, bg=self.colors["bg"], fg=self.colors["fg"]).pack(side="left")
            bar = ttk.Progressbar(box, length=200)
            bar.pack(side="left", padx=10, expand=True, fill="x")
            pct = tk.Label(box, text="0%", width=5, bg=self.colors["bg"], fg=self.colors["fg"])
            pct.pack(side="left")
            self.core_widgets.append((bar, pct))

    # ===========================================================
    # PESTAÑA 3: PROCESOS
    # ===========================================================
    def setup_procesos_tab(self):
        columns = ("pid", "nombre", "cpu", "ram")
        self.tree = ttk.Treeview(self.tab_procesos, columns=columns, show="headings")
        self.tree.heading("pid", text="PID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("cpu", text="CPU %")
        self.tree.heading("ram", text="RAM %")
        self.tree.column("pid", width=70, anchor="center")
        self.tree.column("nombre", width=260)
        self.tree.column("cpu", width=80, anchor="center")
        self.tree.column("ram", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(self.tab_procesos, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ===========================================================
    # PESTAÑA 4: GRÁFICAS (CPU + RED)
    # ===========================================================
    def setup_graficas_tab(self):
        plt_bg = self.colors["bg"]
        plot_area = self.colors["panel"]
        text_color = self.colors["fg"]

        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor=plt_bg)

        # --- SUBPLOT 1: CPU ---
        self.ax_cpu = self.fig.add_subplot(211)
        self.ax_cpu.set_facecolor(plot_area)
        self.ax_cpu.set_title("Uso de CPU (%)", color=text_color, fontsize=10)
        self.ax_cpu.tick_params(colors=text_color)
        for s in self.ax_cpu.spines.values(): s.set_edgecolor(text_color)
        self.ax_cpu.set_ylim(0, 100)

        # --- SUBPLOT 2: RED (MB/s) ---
        self.ax_net = self.fig.add_subplot(212)
        self.ax_net.set_facecolor(plot_area)
        self.ax_net.set_title("Velocidad de Red (MB/s)", color=text_color, fontsize=10)
        self.ax_net.tick_params(colors=text_color)
        for s in self.ax_net.spines.values(): s.set_edgecolor(text_color)

        # Datos iniciales (60 segundos)
        self.cpu_data = [0] * 60
        self.net_down_data = [0] * 60
        self.net_up_data = [0] * 60

        # Líneas
        self.line_cpu, = self.ax_cpu.plot(self.cpu_data, color=self.colors["cpu"], label="CPU")

        # Dos líneas para red: Bajada (Verde) y Subida (Magenta)
        self.line_down, = self.ax_net.plot(self.net_down_data, color=self.colors["down"], label="Bajada", linewidth=1.5)
        self.line_up, = self.ax_net.plot(self.net_up_data, color=self.colors["up"], label="Subida", linewidth=1.5)

        # Leyenda pequeña
        self.ax_net.legend(loc="upper left", facecolor=plot_area, edgecolor=text_color, labelcolor=text_color, fontsize=8)

        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_graficas)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ===========================================================
    # BUCLE PRINCIPAL
    # ===========================================================
    def actualizar_metricas(self):
        if self.monitor_activo:
            # Se obtiene la lista completa de nucleos UNA vez
            cpu_list = psutil.cpu_percent(percpu=True)
            cpu_global = 0.0

            # Calculo aritmetico del promedio global
            # Evita llamar de nuevo a psutil.cpu_percent()
            if cpu_list:
                cpu_global = sum(cpu_list) / len(cpu_list)
            else:
                cpu_global = psutil.cpu_percent()  # fallback

            # CPU & RAM
            ram = psutil.virtual_memory()
            self.prog_ram["value"] = ram.percent
            self.txt_ram.config(text=f"{ram.percent}% ({self.get_size(ram.used)}/{self.get_size(ram.total)})")

            # DISCO
            try:
                disk = psutil.disk_usage("/")
                self.prog_disk["value"] = disk.percent
                self.txt_disk.config(text=f"{disk.percent}% ({self.get_size(disk.free)} libres)")
            except:
                pass

            # RED (Calculo diferencial)
            now = time.time()
            io = psutil.net_io_counters()
            dt = now - self.last_time

            down_mbs = 0.0
            up_mbs = 0.0

            if dt > 0:
                # Convertimos bytes a MB (bytes / 1024 / 1024)
                down_speed_bytes = (io.bytes_recv - self.last_net_io.bytes_recv) / dt
                up_speed_bytes = (io.bytes_sent - self.last_net_io.bytes_sent) / dt

                down_mbs = down_speed_bytes / 1024 / 1024
                up_mbs = up_speed_bytes / 1024 / 1024

                self.txt_net_down.config(text=f"Bajada: {self.get_size(down_speed_bytes)}/s")
                self.txt_net_up.config(text=f"Subida: {self.get_size(up_speed_bytes)}/s")

            self.last_net_io = io
            self.last_time = now

            # CORES: actualizar barras usando cpu_list
            for i, (bar, lbl) in enumerate(self.core_widgets):
                if i < len(cpu_list):
                    bar["value"] = cpu_list[i]
                    lbl.config(text=f"{cpu_list[i]}%")

            # GRÁFICAS (Actualización)
            # 1. CPU (usar cpu_global calculado arriba)
            self.cpu_data.append(cpu_global)
            self.cpu_data.pop(0)
            self.line_cpu.set_ydata(self.cpu_data)

            # 2. RED
            self.net_down_data.append(down_mbs)
            self.net_down_data.pop(0)
            self.net_up_data.append(up_mbs)
            self.net_up_data.pop(0)

            self.line_down.set_ydata(self.net_down_data)
            self.line_up.set_ydata(self.net_up_data)

            # Re-escalado dinámico para la red (porque la velocidad varía mucho)
            try:
                self.ax_net.relim()
                self.ax_net.autoscale_view(True, True, True)
            except Exception:
                pass

            self.canvas.draw()

            # PROCESOS (Throttle 3s)
            if time.time() - self.last_process_update > 3:
                for item in self.tree.get_children():
                    self.tree.delete(item)

                procs = []
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        # evitar procesos sin nombre o sin cpu info
                        if p.info.get('cpu_percent') is not None and p.info.get('name'):
                            procs.append(p.info)
                    except Exception:
                        pass

                for p in sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:15]:
                    self.tree.insert("", "end", values=(p['pid'], p['name'], f"{p['cpu_percent']}%", f"{p['memory_percent']:.1f}%"))

                self.last_process_update = time.time()

        self.root.after(1000, self.actualizar_metricas)

if __name__ == "__main__":
    root = tk.Tk()
    app = Monitor(root)
    root.mainloop()
