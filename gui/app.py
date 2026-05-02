"""
Information Theory & Data Compression Tool
GUI Application - ECU Spring 2026
Algorithms: Huffman Coding + LZW
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import time
import tracemalloc
import threading
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import huffman, lzw, channel
from utils.entropy import calculate_entropy_from_file, get_file_stats


# ─── Color Palette ───────────────────────────
BG_DARK    = "#0f1117"
BG_PANEL   = "#1a1d27"
BG_CARD    = "#22263a"
ACCENT     = "#4f8ef7"
ACCENT2    = "#f7774f"
GREEN      = "#4caf7d"
YELLOW     = "#f7c44f"
TEXT_MAIN  = "#e8eaf6"
TEXT_DIM   = "#7b82a3"
BORDER     = "#2e3250"


class CompressionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ECU Compression Tool — Huffman & LZW")
        self.geometry("1100x780")
        self.minsize(900, 650)
        self.configure(bg=BG_DARK)

        self._setup_styles()
        self._build_ui()

    # ─── Style Setup ─────────────────────────
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Dark.TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("Card.TFrame", background=BG_CARD)

        style.configure("TLabel", background=BG_DARK, foreground=TEXT_MAIN,
                        font=("Consolas", 10))
        style.configure("Title.TLabel", background=BG_DARK, foreground=TEXT_MAIN,
                        font=("Consolas", 18, "bold"))
        style.configure("Sub.TLabel", background=BG_DARK, foreground=TEXT_DIM,
                        font=("Consolas", 9))
        style.configure("Card.TLabel", background=BG_CARD, foreground=TEXT_MAIN,
                        font=("Consolas", 10))
        style.configure("CardTitle.TLabel", background=BG_CARD, foreground=ACCENT,
                        font=("Consolas", 9, "bold"))
        style.configure("Panel.TLabel", background=BG_PANEL, foreground=TEXT_MAIN,
                        font=("Consolas", 10))

        style.configure("TRadiobutton", background=BG_PANEL, foreground=TEXT_MAIN,
                        font=("Consolas", 10), selectcolor=BG_CARD)
        style.configure("TCheckbutton", background=BG_PANEL, foreground=TEXT_MAIN,
                        font=("Consolas", 10), selectcolor=BG_CARD)
        style.configure("TCombobox", fieldbackground=BG_CARD, background=BG_CARD,
                        foreground=TEXT_MAIN, selectbackground=ACCENT)

        style.configure("TProgressbar", troughcolor=BG_CARD, background=ACCENT,
                        lightcolor=ACCENT, darkcolor=ACCENT)

    # ─── UI Builder ──────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_PANEL, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⚡ ECU Compression Tool", bg=BG_PANEL,
                 fg=ACCENT, font=("Consolas", 16, "bold")).pack(side=tk.LEFT, padx=20, pady=15)
        tk.Label(header, text="Huffman Coding  ·  LZW  ·  Channel Simulation",
                 bg=BG_PANEL, fg=TEXT_DIM, font=("Consolas", 9)).pack(side=tk.LEFT, padx=5, pady=15)

        # Main content
        content = tk.Frame(self, bg=BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        left = tk.Frame(content, bg=BG_DARK, width=360)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        right = tk.Frame(content, bg=BG_DARK)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent):
        # ── File Selection ──
        self._section(parent, "📂 FILE SELECTION")

        file_frame = tk.Frame(parent, bg=BG_PANEL, bd=0, relief=tk.FLAT)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_label = tk.Label(file_frame, text="No file selected",
                                   bg=BG_PANEL, fg=TEXT_DIM,
                                   font=("Consolas", 9), anchor=tk.W,
                                   wraplength=300)
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)

        tk.Button(file_frame, text="Browse", command=self._browse_file,
                  bg=ACCENT, fg="white", font=("Consolas", 9, "bold"),
                  relief=tk.FLAT, padx=12, cursor="hand2").pack(side=tk.RIGHT, padx=5, pady=5)

        # ── Algorithm ──
        self._section(parent, "⚙️  ALGORITHM")

        alg_frame = tk.Frame(parent, bg=BG_PANEL)
        alg_frame.pack(fill=tk.X, pady=(0, 10))

        self.algorithm = tk.StringVar(value="huffman")
        for text, val in [("Huffman Coding", "huffman"), ("LZW", "lzw")]:
            tk.Radiobutton(alg_frame, text=text, variable=self.algorithm,
                           value=val, bg=BG_PANEL, fg=TEXT_MAIN,
                           selectcolor=BG_CARD, activebackground=BG_PANEL,
                           font=("Consolas", 10)).pack(anchor=tk.W, padx=12, pady=3)

        # ── Mode ──
        self._section(parent, "🔄 MODE")

        mode_frame = tk.Frame(parent, bg=BG_PANEL)
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.mode = tk.StringVar(value="compress")
        for text, val in [("Compress", "compress"), ("Decompress", "decompress")]:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode,
                           value=val, bg=BG_PANEL, fg=TEXT_MAIN,
                           selectcolor=BG_CARD, activebackground=BG_PANEL,
                           font=("Consolas", 10)).pack(anchor=tk.W, padx=12, pady=3)

        # ── Bonus Channel ──
        self._section(parent, "📡 BONUS: CHANNEL SIMULATION")

        bonus_frame = tk.Frame(parent, bg=BG_PANEL)
        bonus_frame.pack(fill=tk.X, pady=(0, 10))

        self.use_channel = tk.BooleanVar(value=False)
        tk.Checkbutton(bonus_frame, text="Enable Noisy Channel + Hamming FEC",
                       variable=self.use_channel, command=self._toggle_channel,
                       bg=BG_PANEL, fg=TEXT_MAIN, selectcolor=BG_CARD,
                       activebackground=BG_PANEL,
                       font=("Consolas", 9)).pack(anchor=tk.W, padx=12, pady=3)

        self.ber_frame = tk.Frame(bonus_frame, bg=BG_PANEL)
        self.ber_frame.pack(fill=tk.X, padx=12)

        tk.Label(self.ber_frame, text="Bit Error Rate (0.0 – 0.5):",
                 bg=BG_PANEL, fg=TEXT_DIM, font=("Consolas", 9)).pack(anchor=tk.W)

        self.ber_var = tk.DoubleVar(value=0.01)
        self.ber_slider = tk.Scale(self.ber_frame, from_=0.0, to=0.5,
                                   resolution=0.001, orient=tk.HORIZONTAL,
                                   variable=self.ber_var, bg=BG_PANEL,
                                   fg=TEXT_MAIN, troughcolor=BG_CARD,
                                   highlightthickness=0, font=("Consolas", 8))
        self.ber_slider.pack(fill=tk.X, pady=2)

        self.ber_frame.pack_forget()

        # ── Run Button ──
        tk.Button(parent, text="▶  RUN", command=self._run,
                  bg=GREEN, fg="white", font=("Consolas", 13, "bold"),
                  relief=tk.FLAT, height=2, cursor="hand2").pack(fill=tk.X, pady=15)

        # Progress
        self.progress = ttk.Progressbar(parent, mode='indeterminate',
                                        style="TProgressbar")
        self.progress.pack(fill=tk.X)

    def _build_right_panel(self, parent):
        # Stats cards row
        cards_row = tk.Frame(parent, bg=BG_DARK)
        cards_row.pack(fill=tk.X, pady=(0, 10))

        self.stat_vars = {}
        stats = [
            ("Original Size", "orig_size", "bytes"),
            ("Compressed Size", "comp_size", "bytes"),
            ("Ratio", "ratio", "x"),
            ("Space Saved", "saved", "%"),
            ("Time", "time", "s"),
            ("Entropy H(X)", "entropy", "bits"),
        ]

        for i, (label, key, unit) in enumerate(stats):
            card = tk.Frame(cards_row, bg=BG_CARD, padx=10, pady=8)
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            cards_row.columnconfigure(i, weight=1)

            tk.Label(card, text=label, bg=BG_CARD, fg=TEXT_DIM,
                     font=("Consolas", 8)).pack()
            var = tk.StringVar(value="—")
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var, bg=BG_CARD, fg=ACCENT,
                     font=("Consolas", 13, "bold")).pack()
            tk.Label(card, text=unit, bg=BG_CARD, fg=TEXT_DIM,
                     font=("Consolas", 8)).pack()

        # Log output
        log_label = tk.Frame(parent, bg=BG_DARK)
        log_label.pack(fill=tk.X)
        tk.Label(log_label, text="📋 OUTPUT LOG", bg=BG_DARK, fg=TEXT_DIM,
                 font=("Consolas", 9, "bold")).pack(anchor=tk.W)

        log_frame = tk.Frame(parent, bg=BG_CARD, bd=1, relief=tk.FLAT)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, bg=BG_CARD, fg=TEXT_MAIN,
                                font=("Consolas", 10), relief=tk.FLAT,
                                wrap=tk.WORD, state=tk.DISABLED,
                                insertbackground=ACCENT,
                                selectbackground=ACCENT)
        scroll = tk.Scrollbar(log_frame, command=self.log_text.yview,
                              bg=BG_PANEL)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tag colors
        self.log_text.tag_configure("green",  foreground=GREEN)
        self.log_text.tag_configure("accent", foreground=ACCENT)
        self.log_text.tag_configure("yellow", foreground=YELLOW)
        self.log_text.tag_configure("red",    foreground=ACCENT2)
        self.log_text.tag_configure("dim",    foreground=TEXT_DIM)

    def _section(self, parent, title):
        tk.Label(parent, text=title, bg=BG_DARK, fg=TEXT_DIM,
                 font=("Consolas", 8, "bold")).pack(anchor=tk.W, pady=(8, 2))

    def _toggle_channel(self):
        if self.use_channel.get():
            self.ber_frame.pack(fill=tk.X, padx=12)
        else:
            self.ber_frame.pack_forget()

    # ─── File Browser ────────────────────────
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select a file to compress/decompress",
            filetypes=[("All files", "*.*"), ("Text files", "*.txt"),
                       ("Compressed", "*.huf *.lzw")]
        )
        if path:
            self.selected_file = path
            name = os.path.basename(path)
            size = os.path.getsize(path)
            self.file_label.config(
                text=f"{name}\n({self._fmt_size(size)})",
                fg=TEXT_MAIN
            )

    # ─── Run ─────────────────────────────────
    def _run(self):
        if not hasattr(self, 'selected_file') or not self.selected_file:
            messagebox.showerror("No File", "Please select a file first.")
            return
        self.progress.start(10)
        thread = threading.Thread(target=self._run_worker, daemon=True)
        thread.start()

    def _run_worker(self):
        try:
            self._do_run()
        except Exception as e:
            self.after(0, lambda: self._log(f"\n❌ ERROR: {e}\n", "red"))
            self.after(0, self.progress.stop)

    def _do_run(self):
        src = self.selected_file
        alg = self.algorithm.get()
        mode = self.mode.get()

        ext_map = {"huffman": ".huf", "lzw": ".lzw"}
        ext = ext_map[alg]
        alg_mod = huffman if alg == "huffman" else lzw
        alg_name = "Huffman Coding" if alg == "huffman" else "LZW"

        self._clear_log()
        self._log(f"{'═'*55}\n", "dim")
        self._log(f"  Algorithm  : {alg_name}\n", "accent")
        self._log(f"  Mode       : {mode.capitalize()}\n", "accent")
        self._log(f"  Input      : {os.path.basename(src)}\n", "accent")
        self._log(f"{'═'*55}\n\n", "dim")

        # ── Entropy of input ──
        try:
            ent = calculate_entropy_from_file(src)
            self._update_stat("entropy", f"{ent:.4f}")
            self._log(f"  H(X) Entropy        : {ent:.6f} bits/symbol\n", "yellow")
        except Exception:
            pass

        # ── Output path ──
        if mode == "compress":
            out_path = src + ext
        else:
            if src.endswith(ext):
                out_path = src[:-len(ext)] + "_decompressed" + self._original_ext(src, ext)
            else:
                out_path = src + "_decompressed"

        # ── Measure memory ──
        tracemalloc.start()
        start_time = time.perf_counter()

        if mode == "compress":
            stats = alg_mod.compress(src, out_path)
        else:
            stats = alg_mod.decompress(src, out_path)

        elapsed = time.perf_counter() - start_time
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # ── Update stat cards ──
        orig = stats.get('original_size', os.path.getsize(src))
        comp = stats.get('compressed_size', os.path.getsize(out_path))
        ratio = stats.get('compression_ratio', orig / comp if comp > 0 else 0)
        saved = stats.get('space_saved', (1 - comp / orig) * 100 if orig > 0 else 0)

        self._update_stat("orig_size", self._fmt_size(orig))
        self._update_stat("comp_size", self._fmt_size(comp))
        self._update_stat("ratio", f"{ratio:.3f}")
        self._update_stat("saved", f"{saved:.1f}")
        self._update_stat("time", f"{elapsed:.3f}")

        # ── Log details ──
        self._log(f"  Original Size       : {self._fmt_size(orig)}\n")
        self._log(f"  Output Size         : {self._fmt_size(comp)}\n")
        self._log(f"  Compression Ratio   : {ratio:.4f}x\n", "yellow")
        self._log(f"  Space Saved         : {saved:.2f}%\n", "yellow")
        self._log(f"  Execution Time      : {elapsed*1000:.2f} ms\n", "green")
        self._log(f"  Peak Memory Usage   : {peak_mem/1024:.1f} KB\n", "green")
        self._log(f"  Output File         : {os.path.basename(out_path)}\n\n")

        # ── Bonus: Channel ──
        if mode == "compress" and self.use_channel.get():
            self._run_channel_bonus(out_path, alg_mod)

        self._log(f"✅  Done!\n", "green")
        self.after(0, self.progress.stop)

    def _run_channel_bonus(self, compressed_path: str, alg_mod):
        ber = self.ber_var.get()
        self._log(f"\n{'─'*55}\n", "dim")
        self._log(f"  📡 BONUS: Noisy Channel Simulation\n", "yellow")
        self._log(f"  Bit Error Rate (BER): {ber:.4f}\n")

        enc_path    = compressed_path + ".hamming"
        noisy_path  = compressed_path + ".noisy"
        fixed_path  = compressed_path + ".fixed"
        recover_path = compressed_path + ".recovered"

        # Step 1: Hamming encode
        enc_stats = channel.encode_for_transmission(compressed_path, enc_path)
        self._log(f"  Hamming Encoded     : {self._fmt_size(enc_stats['encoded_bytes'])} "
                  f"(overhead {enc_stats['overhead_factor']}x)\n")

        # Step 2: Simulate noisy channel
        ch_stats = channel.simulate_transmission(enc_path, noisy_path, ber)
        self._log(f"  Bits Flipped        : {ch_stats['bits_flipped']} / {ch_stats['total_bits']}\n", "red")
        self._log(f"  Actual BER          : {ch_stats['actual_ber']:.6f}\n", "red")

        # Step 3: Hamming decode + correct
        fix_stats = channel.decode_after_transmission(noisy_path, fixed_path)
        self._log(f"  Errors Corrected    : {fix_stats['errors_corrected']}\n", "green")

        # Step 4: Decompress corrected file
        try:
            alg_mod.decompress(fixed_path, recover_path)
            self._log(f"  ✅ Recovery Success! File decompressed correctly.\n", "green")
        except Exception as e:
            self._log(f"  ❌ Recovery failed: {e}\n", "red")

    # ─── Helpers ─────────────────────────────
    def _log(self, text, tag=None):
        def _do():
            self.log_text.config(state=tk.NORMAL)
            if tag:
                self.log_text.insert(tk.END, text, tag)
            else:
                self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.after(0, _do)

    def _clear_log(self):
        def _do():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.after(0, _do)

    def _update_stat(self, key, val):
        def _do():
            if key in self.stat_vars:
                self.stat_vars[key].set(val)
        self.after(0, _do)

    @staticmethod
    def _fmt_size(b):
        if b < 1024:
            return f"{b} B"
        elif b < 1024**2:
            return f"{b/1024:.1f} KB"
        else:
            return f"{b/1024**2:.2f} MB"

    @staticmethod
    def _original_ext(src, comp_ext):
        base = src[:-len(comp_ext)] if src.endswith(comp_ext) else src
        _, ext = os.path.splitext(base)
        return ext if ext else ".bin"


if __name__ == "__main__":
    app = CompressionApp()
    app.mainloop()
