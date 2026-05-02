"""
ECU Information Theory & Data Compression Tool
Modern PyQt6 GUI — Spring 2026
Algorithms: Huffman Coding + LZW + Bonus Channel
"""

import sys
import os
import time
import tracemalloc
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QRadioButton, QButtonGroup,
    QCheckBox, QSlider, QTextEdit, QFrame, QProgressBar,
    QTabWidget, QGridLayout, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QLinearGradient, QPainter

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from algorithms import huffman, lzw, channel
from utils.entropy import calculate_entropy_from_file, get_file_stats

# ─── Theme Colors ─────────────────────────────────────
C = {
    'bg':       '#0D1117',
    'surface':  '#161B22',
    'card':     '#21262D',
    'border':   '#30363D',
    'accent':   '#58A6FF',
    'accent2':  '#3FB950',
    'warning':  '#F78166',
    'yellow':   '#E3B341',
    'text':     '#E6EDF3',
    'text_dim': '#8B949E',
    'hover':    '#2D333B',
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
}}

QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    background: {C['surface']};
}}

QTabBar::tab {{
    background: {C['card']};
    color: {C['text_dim']};
    padding: 10px 24px;
    border: 1px solid {C['border']};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    font-size: 13px;
    font-weight: 500;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {C['surface']};
    color: {C['accent']};
    border-bottom: 2px solid {C['accent']};
}}

QPushButton {{
    background-color: {C['accent']};
    color: #0D1117;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 700;
}}

QPushButton:hover {{
    background-color: #79C0FF;
}}

QPushButton:pressed {{
    background-color: #388BFD;
}}

QPushButton#secondary {{
    background-color: {C['card']};
    color: {C['text']};
    border: 1px solid {C['border']};
}}

QPushButton#secondary:hover {{
    background-color: {C['hover']};
    border-color: {C['accent']};
}}

QPushButton#danger {{
    background-color: transparent;
    color: {C['warning']};
    border: 1px solid {C['warning']};
}}

QPushButton#run_btn {{
    background-color: {C['accent2']};
    color: #0D1117;
    font-size: 15px;
    padding: 14px;
    border-radius: 10px;
}}

QPushButton#run_btn:hover {{
    background-color: #56D364;
}}

QRadioButton, QCheckBox {{
    color: {C['text']};
    font-size: 13px;
    spacing: 8px;
    padding: 4px 0;
}}

QRadioButton::indicator, QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid {C['border']};
    background: {C['card']};
}}

QRadioButton::indicator:checked {{
    background: {C['accent']};
    border-color: {C['accent']};
}}

QCheckBox::indicator {{
    border-radius: 4px;
}}

QCheckBox::indicator:checked {{
    background: {C['accent']};
    border-color: {C['accent']};
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {C['border']};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {C['accent']};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background: {C['accent']};
    border-radius: 2px;
}}

QTextEdit {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: {C['accent']};
}}

QProgressBar {{
    background-color: {C['card']};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {C['accent']};
    border-radius: 4px;
}}

QScrollBar:vertical {{
    background: {C['surface']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QFrame#card {{
    background-color: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 10px;
}}

QFrame#divider {{
    background-color: {C['border']};
    max-height: 1px;
}}
"""


# ─── Worker Thread ────────────────────────────────────
class WorkerThread(QThread):
    log_signal      = pyqtSignal(str, str)   # (text, color)
    stat_signal     = pyqtSignal(str, str)   # (key, value)
    done_signal     = pyqtSignal(bool)       # success
    chart_signal    = pyqtSignal(dict)       # chart data

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            self._execute()
        except Exception as e:
            self.log_signal.emit(f"\n❌  ERROR: {e}\n", C['warning'])
            self.done_signal.emit(False)

    def _execute(self):
        p = self.params
        src      = p['file']
        alg_name = p['algorithm']   # 'huffman' or 'lzw'
        mode     = p['mode']
        use_ch   = p['use_channel']
        ber      = p['ber']

        alg_mod  = huffman if alg_name == 'huffman' else lzw
        alg_label = 'Huffman Coding' if alg_name == 'huffman' else 'LZW'
        ext       = '.huf' if alg_name == 'huffman' else '.lzw'

        self._log('━' * 52, C['border'])
        self._log(f'  Algorithm  :  {alg_label}', C['accent'])
        self._log(f'  Mode       :  {mode.capitalize()}', C['accent'])
        self._log(f'  File       :  {os.path.basename(src)}', C['accent'])
        self._log('━' * 52 + '\n', C['border'])

        # Entropy
        try:
            ent = calculate_entropy_from_file(src)
            self._log(f'  H(X) Entropy        :  {ent:.6f} bits/symbol', C['yellow'])
            self.stat_signal.emit('entropy', f'{ent:.4f}')
        except:
            pass

        # Output path
        if mode == 'compress':
            out_path = src + ext
        else:
            base = src[:-len(ext)] if src.endswith(ext) else src
            _, orig_ext = os.path.splitext(base)
            out_path = base + '_decompressed' + (orig_ext or '.bin')

        # Run with memory profiling
        tracemalloc.start()
        t0 = time.perf_counter()

        if mode == 'compress':
            stats = alg_mod.compress(src, out_path)
        else:
            stats = alg_mod.decompress(src, out_path)

        elapsed = time.perf_counter() - t0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if mode == 'compress':
            orig  = stats.get('original_size',    os.path.getsize(src))
            comp  = stats.get('compressed_size',  os.path.getsize(out_path))
            ratio = stats.get('compression_ratio', orig / comp if comp > 0 else 0)
            saved = stats.get('space_saved', (1 - comp / orig) * 100 if orig > 0 else 0)

            self.stat_signal.emit('orig',  self._fmt(orig))
            self.stat_signal.emit('comp',  self._fmt(comp))
            self.stat_signal.emit('ratio', f'{ratio:.3f}x')
            self.stat_signal.emit('saved', f'{saved:.1f}%')
            self.stat_signal.emit('time',  f'{elapsed*1000:.1f} ms')
            self.stat_signal.emit('mem',   f'{peak_mem/1024:.0f} KB')

            self._log(f'\n  Compressed Size     :  {self._fmt(comp)}', C['text'])
            self._log(f'  Original Size       :  {self._fmt(orig)}', C['text'])
            self._log(f'  Compression Ratio   :  {ratio:.4f}x', C['yellow'])
            self._log(f'  Space Saved         :  {saved:.2f}%', C['yellow'])
            self._log(f'  Execution Time      :  {elapsed*1000:.2f} ms', C['accent2'])
            self._log(f'  Peak Memory         :  {peak_mem/1024:.1f} KB', C['accent2'])
            self._log(f'  Output File         :  {os.path.basename(out_path)}\n', C['text_dim'])

        else:  # decompress
            comp_size   = os.path.getsize(src)
            decomp_size = stats.get('decompressed_size', os.path.getsize(out_path))
            ratio = decomp_size / comp_size if comp_size > 0 else 0
            saved = (1 - comp_size / decomp_size) * 100 if decomp_size > 0 else 0
            success = stats.get('success', True)

            self.stat_signal.emit('orig',  self._fmt(comp_size))
            self.stat_signal.emit('comp',  self._fmt(decomp_size))
            self.stat_signal.emit('ratio', f'{ratio:.3f}x')
            self.stat_signal.emit('saved', f'{saved:.1f}%')
            self.stat_signal.emit('time',  f'{elapsed*1000:.1f} ms')
            self.stat_signal.emit('mem',   f'{peak_mem/1024:.0f} KB')

            self._log(f'\n  Compressed File     :  {self._fmt(comp_size)}', C['text'])
            self._log(f'  Decompressed Size   :  {self._fmt(decomp_size)}', C['text'])
            self._log(f'  Expansion Ratio     :  {ratio:.4f}x', C['yellow'])
            self._log(f'  Space Recovered     :  {saved:.2f}%', C['yellow'])
            self._log(f'  Execution Time      :  {elapsed*1000:.2f} ms', C['accent2'])
            self._log(f'  Peak Memory         :  {peak_mem/1024:.1f} KB', C['accent2'])
            self._log(f'  Lossless Check      :  {"✅ PASS" if success else "❌ FAIL"}', C['accent2'] if success else C['warning'])
            self._log(f'  Output File         :  {os.path.basename(out_path)}\n', C['text_dim'])

            orig  = decomp_size
            comp  = comp_size

        # Chart data
        self.chart_signal.emit({
            'algorithm': alg_label,
            'orig': orig, 'comp': comp,
            'ratio': ratio, 'saved': saved,
            'time': elapsed * 1000,
            'mem': peak_mem / 1024,
            'entropy': ent if 'ent' in dir() else 0
        })

        # Bonus
        if mode == 'compress' and use_ch:
            self._run_bonus(out_path, alg_mod, ber)

        self._log('✅  Completed successfully!\n', C['accent2'])
        self.done_signal.emit(True)

    def _run_bonus(self, comp_path, alg_mod, ber):
        self._log('\n' + '─' * 52, C['border'])
        self._log('  📡  BONUS: Noisy Channel + Hamming FEC', C['yellow'])
        self._log(f'  Bit Error Rate (BER) : {ber:.4f}\n', C['text'])

        enc_path     = comp_path + '.hamming'
        noisy_path   = comp_path + '.noisy'
        fixed_path   = comp_path + '.fixed'
        recover_path = comp_path + '.recovered'

        enc_s = channel.encode_for_transmission(comp_path, enc_path)
        self._log(f'  [1] Hamming Encoded  :  {self._fmt(enc_s["encoded_bytes"])}  '
                  f'(overhead {enc_s["overhead_factor"]}x)', C['text'])

        ch_s = channel.simulate_transmission(enc_path, noisy_path, ber, seed=42)
        self._log(f'  [2] Bits Flipped     :  {ch_s["bits_flipped"]} / {ch_s["total_bits"]}', C['warning'])
        self._log(f'      Actual BER       :  {ch_s["actual_ber"]:.6f}', C['warning'])

        fix_s = channel.decode_after_transmission(noisy_path, fixed_path)
        self._log(f'  [3] Errors Corrected :  {fix_s["errors_corrected"]}', C['accent2'])

        try:
            alg_mod.decompress(fixed_path, recover_path)
            self._log('  [4] Recovery         :  ✅ SUCCESS — File decompressed!', C['accent2'])
        except Exception as e:
            if ber > 0.05:
                self._log(f'  [4] Recovery         :  ⚠️  BER تعالي جداً — Hamming(7,4) بيصلح bit واحدة بس في كل codeword', C['warning'])
                self._log(f'       جرب BER أقل من 0.05 للحصول على recovery كامل', C['yellow'])
            else:
                self._log(f'  [4] Recovery         :  ❌ FAILED ({e})', C['warning'])

    def _log(self, text, color=None):
        self.log_signal.emit(text + '\n', color or C['text'])

    @staticmethod
    def _fmt(b):
        if b < 1024: return f'{b} B'
        if b < 1024**2: return f'{b/1024:.1f} KB'
        return f'{b/1024**2:.2f} MB'


# ─── Stat Card ────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, label, key, unit=''):
        super().__init__()
        self.setObjectName('card')
        self.setMinimumHeight(90)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(f'color: {C["text_dim"]}; font-size: 11px; font-weight: 500; background: transparent; border: none;')
        layout.addWidget(self.lbl)

        self.val = QLabel('—')
        self.val.setStyleSheet(f'color: {C["accent"]}; font-size: 20px; font-weight: 700; background: transparent; border: none;')
        layout.addWidget(self.val)

        if unit:
            u = QLabel(unit)
            u.setStyleSheet(f'color: {C["text_dim"]}; font-size: 10px; background: transparent; border: none;')
            layout.addWidget(u)

    def set_value(self, v):
        self.val.setText(str(v))


# ─── Chart Widget ─────────────────────────────────────
class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.fig = Figure(figsize=(8, 4), facecolor=C['surface'])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet(f'background: {C["surface"]};')
        layout.addWidget(self.canvas)

        self.results = []
        self._draw_empty()

    def _draw_empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor=C['surface'])
        ax.text(0.5, 0.5, 'Run compression to see charts',
                ha='center', va='center', color=C['text_dim'], fontsize=13,
                transform=ax.transAxes)
        ax.set_axis_off()
        self.canvas.draw()

    def update_chart(self, data):
        self.results.append(data)
        self.fig.clear()

        if len(self.results) == 0:
            return

        # Layout: 2x2 subplots
        axes = self.fig.subplots(1, 3)
        self.fig.patch.set_facecolor(C['surface'])

        labels   = [r['algorithm'] for r in self.results]
        origs    = [r['orig'] / 1024 for r in self.results]
        comps    = [r['comp'] / 1024 for r in self.results]
        ratios   = [r['ratio'] for r in self.results]
        times    = [r['time'] for r in self.results]

        colors_orig = [C['text_dim']] * len(labels)
        colors_comp = [C['accent']] * len(labels)

        # ── Chart 1: Size comparison ──
        ax1 = axes[0]
        ax1.set_facecolor(C['card'])
        x = range(len(labels))
        w = 0.35
        bars1 = ax1.bar([i - w/2 for i in x], origs, w, label='Original', color=C['text_dim'], alpha=0.8)
        bars2 = ax1.bar([i + w/2 for i in x], comps, w, label='Compressed', color=C['accent'], alpha=0.9)
        ax1.set_title('File Size (KB)', color=C['text'], fontsize=11, pad=10)
        ax1.set_xticks(list(x))
        ax1.set_xticklabels(labels, color=C['text'], fontsize=9)
        ax1.tick_params(colors=C['text_dim'])
        ax1.spines[:].set_color(C['border'])
        ax1.yaxis.label.set_color(C['text_dim'])
        ax1.legend(facecolor=C['card'], edgecolor=C['border'],
                   labelcolor=C['text'], fontsize=9)
        for spine in ax1.spines.values():
            spine.set_edgecolor(C['border'])
        ax1.set_ylabel('KB', color=C['text_dim'], fontsize=9)

        # ── Chart 2: Compression Ratio ──
        ax2 = axes[1]
        ax2.set_facecolor(C['card'])
        bar_colors = [C['accent2'] if r >= 1 else C['warning'] for r in ratios]
        bars = ax2.bar(labels, ratios, color=bar_colors, alpha=0.9)
        ax2.axhline(y=1, color=C['warning'], linestyle='--', linewidth=1, alpha=0.7)
        ax2.set_title('Compression Ratio', color=C['text'], fontsize=11, pad=10)
        ax2.tick_params(colors=C['text_dim'])
        ax2.set_ylabel('Ratio (x)', color=C['text_dim'], fontsize=9)
        for spine in ax2.spines.values():
            spine.set_edgecolor(C['border'])
        ax2.set_xticklabels(labels, color=C['text'], fontsize=9)
        for bar, val in zip(bars, ratios):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                     f'{val:.2f}x', ha='center', va='bottom', color=C['text'], fontsize=9)

        # ── Chart 3: Execution Time ──
        ax3 = axes[2]
        ax3.set_facecolor(C['card'])
        bars3 = ax3.bar(labels, times, color=C['yellow'], alpha=0.9)
        ax3.set_title('Execution Time (ms)', color=C['text'], fontsize=11, pad=10)
        ax3.tick_params(colors=C['text_dim'])
        ax3.set_ylabel('ms', color=C['text_dim'], fontsize=9)
        for spine in ax3.spines.values():
            spine.set_edgecolor(C['border'])
        ax3.set_xticklabels(labels, color=C['text'], fontsize=9)
        for bar, val in zip(bars3, times):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f'{val:.1f}', ha='center', va='bottom', color=C['text'], fontsize=9)

        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()


# ─── Main Window ─────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ECU Compression Tool — Spring 2026')
        self.setMinimumSize(1150, 750)
        self.resize(1250, 820)
        self.setStyleSheet(STYLESHEET)

        self.selected_file = None
        self.worker = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f'background: {C["surface"]}; border-bottom: 1px solid {C["border"]};')
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)

        title = QLabel('⚡  ECU Compression Tool')
        title.setStyleSheet(f'color: {C["accent"]}; font-size: 18px; font-weight: 700; background: transparent;')
        h_lay.addWidget(title)

        sub = QLabel('Huffman Coding  ·  LZW  ·  Noisy Channel  ·  Hamming FEC')
        sub.setStyleSheet(f'color: {C["text_dim"]}; font-size: 11px; background: transparent;')
        h_lay.addWidget(sub)
        h_lay.addStretch()

        badge = QLabel('Spring 2026')
        badge.setStyleSheet(f'''
            color: {C["accent"]}; background: rgba(88,166,255,0.1);
            border: 1px solid rgba(88,166,255,0.3);
            border-radius: 12px; padding: 4px 12px; font-size: 11px;
        ''')
        h_lay.addWidget(badge)
        root.addWidget(header)

        # ── Body ──
        body = QHBoxLayout()
        body.setContentsMargins(20, 16, 20, 16)
        body.setSpacing(16)

        # Left panel
        left = QFrame()
        left.setFixedWidth(320)
        left.setObjectName('card')
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(16, 16, 16, 16)
        left_lay.setSpacing(12)
        self._build_left(left_lay)
        body.addWidget(left)

        # Right panel
        right_lay = QVBoxLayout()
        right_lay.setSpacing(12)
        self._build_right(right_lay)
        body.addLayout(right_lay)

        root.addLayout(body)

    # ── Left Panel ──────────────────────────────────
    def _build_left(self, layout):
        def section(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(f'color: {C["text_dim"]}; font-size: 10px; font-weight: 600; '
                              f'letter-spacing: 1px; background: transparent;')
            layout.addWidget(lbl)

        # File
        section('📂  FILE')
        file_frame = QFrame()
        file_frame.setStyleSheet(f'background: {C["bg"]}; border: 1px solid {C["border"]}; '
                                  f'border-radius: 8px;')
        ff_lay = QHBoxLayout(file_frame)
        ff_lay.setContentsMargins(10, 8, 8, 8)

        self.file_lbl = QLabel('No file selected')
        self.file_lbl.setStyleSheet(f'color: {C["text_dim"]}; font-size: 11px; background: transparent; border: none;')
        self.file_lbl.setWordWrap(True)
        ff_lay.addWidget(self.file_lbl, 1)

        browse_btn = QPushButton('Browse')
        browse_btn.setObjectName('secondary')
        browse_btn.setFixedWidth(75)
        browse_btn.clicked.connect(self._browse)
        ff_lay.addWidget(browse_btn)
        layout.addWidget(file_frame)

        self._div(layout)

        # Algorithm
        section('⚙️  ALGORITHM')
        self.alg_group = QButtonGroup()
        for text, val in [('Huffman Coding', 'huffman'), ('LZW', 'lzw')]:
            rb = QRadioButton(text)
            rb.setProperty('value', val)
            if val == 'huffman':
                rb.setChecked(True)
            self.alg_group.addButton(rb)
            layout.addWidget(rb)

        self._div(layout)

        # Mode
        section('🔄  MODE')
        self.mode_group = QButtonGroup()
        for text, val in [('Compress', 'compress'), ('Decompress', 'decompress')]:
            rb = QRadioButton(text)
            rb.setProperty('value', val)
            if val == 'compress':
                rb.setChecked(True)
            self.mode_group.addButton(rb)
            layout.addWidget(rb)

        self._div(layout)

        # Bonus
        section('📡  BONUS: CHANNEL SIMULATION')
        self.ch_check = QCheckBox('Enable Noisy Channel + Hamming FEC')
        self.ch_check.toggled.connect(self._toggle_channel)
        layout.addWidget(self.ch_check)

        self.ch_frame = QFrame()
        ch_lay = QVBoxLayout(self.ch_frame)
        ch_lay.setContentsMargins(0, 4, 0, 0)
        ch_lay.setSpacing(6)

        self.ber_lbl = QLabel('Bit Error Rate: 0.010')
        self.ber_lbl.setStyleSheet(f'color: {C["text_dim"]}; font-size: 11px; background: transparent;')
        ch_lay.addWidget(self.ber_lbl)

        self.ber_slider = QSlider(Qt.Orientation.Horizontal)
        self.ber_slider.setRange(0, 100)   # max 0.1 — Hamming(7,4) limit
        self.ber_slider.setValue(10)       # default 0.01
        self.ber_slider.valueChanged.connect(self._ber_changed)
        ch_lay.addWidget(self.ber_slider)

        self.ber_warn = QLabel('⚠️  BER > 0.05: double-bit errors may occur')
        self.ber_warn.setStyleSheet(f'color: {C["warning"]}; font-size: 10px; background: transparent;')
        self.ber_warn.setVisible(False)
        ch_lay.addWidget(self.ber_warn)

        layout.addWidget(self.ch_frame)
        self.ch_frame.setVisible(False)

        layout.addStretch()

        # Run button
        self.run_btn = QPushButton('▶   RUN')
        self.run_btn.setObjectName('run_btn')
        self.run_btn.clicked.connect(self._run)
        layout.addWidget(self.run_btn)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(5)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    # ── Right Panel ─────────────────────────────────
    def _build_right(self, layout):
        # Stat cards
        cards_frame = QFrame()
        cards_lay = QHBoxLayout(cards_frame)
        cards_lay.setContentsMargins(0, 0, 0, 0)
        cards_lay.setSpacing(10)

        self.cards = {}
        card_defs = [
            ('Original', 'orig', ''),
            ('Compressed', 'comp', ''),
            ('Ratio', 'ratio', ''),
            ('Saved', 'saved', ''),
            ('Time', 'time', ''),
            ('Memory', 'mem', ''),
            ('Entropy H(X)', 'entropy', 'bits/sym'),
        ]
        for label, key, unit in card_defs:
            card = StatCard(label, key, unit)
            self.cards[key] = card
            cards_lay.addWidget(card)

        layout.addWidget(cards_frame)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Log
        log_widget = QWidget()
        log_lay = QVBoxLayout(log_widget)
        log_lay.setContentsMargins(10, 10, 10, 10)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont('Consolas', 11))
        log_lay.addWidget(self.log)

        clear_btn = QPushButton('Clear Log')
        clear_btn.setObjectName('secondary')
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.log.clear)
        log_lay.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignRight)

        tabs.addTab(log_widget, '📋  Output Log')

        # Tab 2: Charts
        self.chart = ChartWidget()
        tabs.addTab(self.chart, '📊  Analysis Charts')

        # Tab 3: Info
        info_widget = QWidget()
        info_lay = QVBoxLayout(info_widget)
        info_lay.setContentsMargins(16, 16, 16, 16)
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml(self._info_html())
        info_lay.addWidget(info_text)
        tabs.addTab(info_widget, 'ℹ️  Algorithm Info')

        layout.addWidget(tabs, 1)

    # ── Helpers ──────────────────────────────────────
    def _div(self, layout):
        div = QFrame()
        div.setObjectName('divider')
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f'background: {C["border"]}; border: none;')
        layout.addWidget(div)

    def _toggle_channel(self, checked):
        self.ch_frame.setVisible(checked)

    def _ber_changed(self, val):
        ber = val / 1000
        self.ber_lbl.setText(f'Bit Error Rate: {ber:.3f}')
        self.ber_warn.setVisible(ber > 0.05)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select File', '',
            'All Files (*);;Text (*.txt);;Compressed (*.huf *.lzw)'
        )
        if path:
            self.selected_file = path
            name = os.path.basename(path)
            size = os.path.getsize(path)
            self.file_lbl.setText(f'{name}\n{self._fmt(size)}')
            self.file_lbl.setStyleSheet(f'color: {C["text"]}; font-size: 11px; background: transparent; border: none;')

    def _run(self):
        if not self.selected_file:
            self._append_log('⚠️  Please select a file first.\n', C['warning'])
            return

        alg = next((b.property('value') for b in self.alg_group.buttons() if b.isChecked()), 'huffman')
        mode = next((b.property('value') for b in self.mode_group.buttons() if b.isChecked()), 'compress')
        ber  = self.ber_slider.value() / 1000

        # Reset cards
        for card in self.cards.values():
            card.set_value('…')

        self.run_btn.setEnabled(False)
        self.progress.setVisible(True)

        self.worker = WorkerThread({
            'file': self.selected_file,
            'algorithm': alg,
            'mode': mode,
            'use_channel': self.ch_check.isChecked(),
            'ber': ber
        })
        self.worker.log_signal.connect(self._append_log)
        self.worker.stat_signal.connect(self._update_stat)
        self.worker.chart_signal.connect(self.chart.update_chart)
        self.worker.done_signal.connect(self._done)
        self.worker.start()

    def _append_log(self, text, color):
        color = color or C['text']
        self.log.moveCursor(self.log.textCursor().MoveOperation.End)
        self.log.setTextColor(QColor(color))
        self.log.insertPlainText(text)
        self.log.moveCursor(self.log.textCursor().MoveOperation.End)

    def _update_stat(self, key, val):
        if key in self.cards:
            self.cards[key].set_value(val)

    def _done(self, success):
        self.run_btn.setEnabled(True)
        self.progress.setVisible(False)

    @staticmethod
    def _fmt(b):
        if b < 1024: return f'{b} B'
        if b < 1024**2: return f'{b/1024:.1f} KB'
        return f'{b/1024**2:.2f} MB'

    def _info_html(self):
        return f"""
        <style>
            body {{ background: {C['surface']}; color: {C['text']}; font-family: 'Segoe UI'; font-size: 13px; }}
            h2 {{ color: {C['accent']}; }}
            h3 {{ color: {C['yellow']}; margin-top: 16px; }}
            p {{ color: {C['text_dim']}; line-height: 1.6; }}
            code {{ background: {C['card']}; padding: 2px 6px; border-radius: 4px; color: {C['accent2']}; }}
        </style>
        <h2>⚡ ECU Compression Tool — Algorithm Reference</h2>

        <h3>Huffman Coding</h3>
        <p>A lossless compression algorithm that assigns shorter binary codes to more frequent symbols.
        Builds a binary tree using a min-heap. The tree is serialized into the compressed file header
        so decompression is completely independent from compression.</p>
        <p>Best for: <code>text files</code>, files with skewed symbol frequencies</p>

        <h3>LZW (Lempel-Ziv-Welch)</h3>
        <p>A dictionary-based algorithm that replaces repeated patterns with short codes.
        The dictionary is rebuilt algorithmically during decompression — it does NOT need to be stored.
        Uses 16-bit codes (max dictionary size: 65,536 entries).</p>
        <p>Best for: <code>repetitive data</code>, structured binary files</p>

        <h3>Shannon Entropy H(X)</h3>
        <p>H(X) = -Σ p(x) · log₂(p(x)) — measures the theoretical minimum bits per symbol needed.
        High entropy (≈8 bits) means data is incompressible. Low entropy means high redundancy.</p>

        <h3>📡 BONUS: Noisy Channel + Hamming(7,4)</h3>
        <p>Simulates a Binary Symmetric Channel (BSC) that randomly flips bits with probability <i>p</i>.
        Hamming(7,4) encodes 4 data bits into 7-bit codewords — can detect and correct any single-bit error per codeword.</p>
        """


# ─── Entry Point ──────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
