from __future__ import annotations


def build_stylesheet(theme: str = "dark") -> str:
    if theme == "light":
        return """
        QWidget { background: #f5f7fb; color: #1f2937; font-size: 13px; }
        QMainWindow, QDialog { background: #edf2f7; }
        QGroupBox { border: 1px solid #cbd5e1; border-radius: 16px; margin-top: 12px; padding-top: 14px; font-weight: 600; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        QTextEdit, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 8px; }
        QTabWidget::pane { border: 1px solid #cbd5e1; border-radius: 14px; padding: 8px; }
        QTabBar::tab { background: #ffffff; border: 1px solid #cbd5e1; border-bottom: none; border-top-left-radius: 10px; border-top-right-radius: 10px; padding: 9px 14px; }
        QTabBar::tab:selected { background: #e2e8f0; }
        QPushButton { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 14px; padding: 10px 14px; }
        QPushButton:hover { background: #e2e8f0; }
        QPushButton:pressed { background: #cbd5e1; }
        QPushButton:disabled { color: #94a3b8; background: #e5e7eb; }
        QProgressBar { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; height: 18px; text-align: center; }
        QProgressBar::chunk { background: #60a5fa; border-radius: 9px; }
        QLabel#titleLabel { font-size: 22px; font-weight: 700; }
        QLabel#subtitleLabel { color: #64748b; }
        QStatusBar { background: #ffffff; border-top: 1px solid #cbd5e1; }
        """
    return """
    QWidget { background: #111827; color: #e5e7eb; font-size: 13px; }
    QMainWindow, QDialog { background: #0f172a; }
    QGroupBox { border: 1px solid #334155; border-radius: 16px; margin-top: 12px; padding-top: 14px; font-weight: 600; }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
    QTextEdit, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget { background: #111827; border: 1px solid #334155; border-radius: 12px; padding: 8px; }
    QTabWidget::pane { border: 1px solid #334155; border-radius: 14px; padding: 8px; }
    QTabBar::tab { background: #111827; border: 1px solid #334155; border-bottom: none; border-top-left-radius: 10px; border-top-right-radius: 10px; padding: 9px 14px; }
    QTabBar::tab:selected { background: #1e293b; }
    QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 10px 14px; }
    QPushButton:hover { background: #334155; }
    QPushButton:pressed { background: #475569; }
    QPushButton:disabled { color: #64748b; background: #111827; }
    QProgressBar { background: #111827; border: 1px solid #334155; border-radius: 10px; height: 18px; text-align: center; }
    QProgressBar::chunk { background: #38bdf8; border-radius: 9px; }
    QLabel#titleLabel { font-size: 22px; font-weight: 700; }
    QLabel#subtitleLabel { color: #94a3b8; }
    QStatusBar { background: #0b1220; border-top: 1px solid #334155; }
    """
