"""
アニメーション効果とカスタムウィジェット
"""

import customtkinter as ctk
from typing import Callable, Optional
import math


class AnimatedButton(ctk.CTkButton):
    """ホバー時にアニメーションするボタン"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.default_size = kwargs.get('width', 100), kwargs.get('height', 40)
        self.is_animating = False

        # ホバーイベントのバインド
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)

    def on_hover_enter(self, event):
        """ホバー開始時のアニメーション"""
        if not self.is_animating:
            self.is_animating = True
            self.animate_scale(1.0, 1.05, 150)

    def on_hover_leave(self, event):
        """ホバー終了時のアニメーション"""
        if self.is_animating:
            self.is_animating = False
            self.animate_scale(1.05, 1.0, 150)

    def animate_scale(self, start_scale, end_scale, duration):
        """スケールアニメーション"""
        steps = 10
        step_duration = duration // steps
        scale_diff = end_scale - start_scale

        for i in range(steps + 1):
            scale = start_scale + (scale_diff * (i / steps))
            new_width = int(self.default_size[0] * scale)
            new_height = int(self.default_size[1] * scale)

            self.after(i * step_duration, lambda w=new_width, h=new_height:
                      self.configure(width=w, height=h))


class PulsingProgressBar(ctk.CTkProgressBar):
    """脈動するプログレスバー"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.is_pulsing = False
        self.pulse_value = 0

    def start_pulse(self):
        """脈動アニメーションの開始"""
        self.is_pulsing = True
        self.pulse_animation()

    def stop_pulse(self):
        """脈動アニメーションの停止"""
        self.is_pulsing = False

    def pulse_animation(self):
        """脈動アニメーションの実行"""
        if not self.is_pulsing:
            return

        # サイン波を使用した滑らかな脈動
        self.pulse_value = (self.pulse_value + 0.05) % (2 * math.pi)
        progress = (math.sin(self.pulse_value) + 1) / 2
        self.set(progress)

        # 次のフレーム
        self.after(50, self.pulse_animation)


class AnimatedCard(ctk.CTkFrame):
    """アニメーション付きカード"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.default_color = self._fg_color
        self.hover_color = ("gray85", "gray25")
        self.is_hovering = False

        # ホバーイベントのバインド
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)

        # 全子ウィジェットにもイベントを伝播
        self.bind_children()

    def bind_children(self):
        """子ウィジェットにイベントをバインド"""
        for child in self.winfo_children():
            child.bind("<Enter>", lambda e: self.on_hover_enter(e))
            child.bind("<Leave>", lambda e: self.on_hover_leave(e))

    def on_hover_enter(self, event):
        """ホバー開始時"""
        if not self.is_hovering:
            self.is_hovering = True
            self.animate_color(self.default_color, self.hover_color, 200)

    def on_hover_leave(self, event):
        """ホバー終了時"""
        # マウスがカード内にあるかチェック
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)

        if not self.is_widget_child(widget):
            self.is_hovering = False
            self.animate_color(self.hover_color, self.default_color, 200)

    def is_widget_child(self, widget):
        """ウィジェットがこのカードの子要素かチェック"""
        while widget:
            if widget == self:
                return True
            try:
                widget = widget.master
            except:
                break
        return False

    def animate_color(self, start_color, end_color, duration):
        """色のアニメーション"""
        steps = 10
        step_duration = duration // steps

        for i in range(steps + 1):
            ratio = i / steps
            # 簡易的な色の補間（実際の実装ではより高度な補間が必要）
            self.after(i * step_duration, lambda: self.configure(fg_color=end_color))


class SlideInNotification(ctk.CTkToplevel):
    """スライドイン通知"""

    def __init__(self, master, message: str, type: str = "info", duration: int = 3000):
        super().__init__(master)

        self.master_window = master
        self.duration = duration

        # ウィンドウ設定
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # 透明度の設定（Windows）
        if master.tk.call('tk', 'windowingsystem') == 'win32':
            self.attributes("-alpha", 0.0)

        # 色の設定
        colors = {
            "success": ("#10B981", "white"),
            "error": ("#EF4444", "white"),
            "warning": ("#F59E0B", "white"),
            "info": ("#3B82F6", "white")
        }
        bg_color, text_color = colors.get(type, colors["info"])

        # アイコンの設定
        icons = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ"
        }
        icon = icons.get(type, "ℹ")

        # フレーム
        self.notification_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=bg_color,
            border_width=0
        )
        self.notification_frame.pack(padx=5, pady=5)

        # コンテンツ
        content_frame = ctk.CTkFrame(
            self.notification_frame,
            fg_color="transparent"
        )
        content_frame.pack(padx=15, pady=12)

        # アイコン
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icon,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=text_color
        )
        icon_label.pack(side="left", padx=(0, 10))

        # メッセージ
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=text_color
        )
        message_label.pack(side="left")

        # 閉じるボタン
        close_button = ctk.CTkButton(
            content_frame,
            text="✕",
            width=20,
            height=20,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=text_color,
            hover_color=(bg_color[0], bg_color[0]),
            command=self.close_notification
        )
        close_button.pack(side="right", padx=(20, 0))

        # アニメーション開始
        self.slide_in()

    def slide_in(self):
        """スライドインアニメーション"""
        self.update_idletasks()

        # 最終位置の計算
        final_x = self.master_window.winfo_x() + self.master_window.winfo_width() - self.winfo_width() - 20
        final_y = self.master_window.winfo_y() + 80

        # 初期位置（画面外右側）
        start_x = self.master_window.winfo_x() + self.master_window.winfo_width() + 10
        self.geometry(f"+{start_x}+{final_y}")

        # アニメーション
        steps = 15
        duration = 300  # ミリ秒
        step_duration = duration // steps

        for i in range(steps + 1):
            ratio = self.ease_out_cubic(i / steps)
            x = int(start_x - (start_x - final_x) * ratio)
            alpha = i / steps

            self.after(i * step_duration, lambda x=x, a=alpha: self.update_position(x, final_y, a))

        # 自動クローズ
        self.after(duration + self.duration, self.slide_out)

    def slide_out(self):
        """スライドアウトアニメーション"""
        if not self.winfo_exists():
            return

        current_x = self.winfo_x()
        current_y = self.winfo_y()
        final_x = self.master_window.winfo_x() + self.master_window.winfo_width() + 10

        steps = 15
        duration = 300
        step_duration = duration // steps

        for i in range(steps + 1):
            ratio = self.ease_in_cubic(i / steps)
            x = int(current_x + (final_x - current_x) * ratio)
            alpha = 1 - (i / steps)

            self.after(i * step_duration, lambda x=x, a=alpha: self.update_position(x, current_y, a))

        self.after(duration, self.destroy)

    def update_position(self, x, y, alpha):
        """位置と透明度の更新"""
        if self.winfo_exists():
            self.geometry(f"+{x}+{y}")
            if self.tk.call('tk', 'windowingsystem') == 'win32':
                self.attributes("-alpha", alpha)

    def close_notification(self):
        """通知を閉じる"""
        self.slide_out()

    @staticmethod
    def ease_out_cubic(t):
        """イーズアウトカービック関数"""
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_cubic(t):
        """イーズインカービック関数"""
        return t * t * t


class CircularProgressBar(ctk.CTkCanvas):
    """円形プログレスバー"""

    def __init__(self, master, size=100, thickness=10, **kwargs):
        super().__init__(master, width=size, height=size, **kwargs)

        self.size = size
        self.thickness = thickness
        self.progress = 0

        # 背景色の設定
        self.configure(bg=master.cget("fg_color")[1] if isinstance(master.cget("fg_color"), tuple) else master.cget("fg_color"))
        self.configure(highlightthickness=0)

        # 色の設定
        self.bg_color = "#E5E5E5"
        self.fg_color = "#3B82F6"

        self.draw()

    def set_progress(self, value: float):
        """プログレスの設定（0.0 ~ 1.0）"""
        self.progress = max(0, min(1, value))
        self.draw()

    def draw(self):
        """プログレスバーの描画"""
        self.delete("all")

        # センター座標と半径
        center = self.size // 2
        radius = (self.size - self.thickness) // 2

        # 背景の円
        self.create_oval(
            center - radius, center - radius,
            center + radius, center + radius,
            outline=self.bg_color,
            width=self.thickness,
            fill=""
        )

        # プログレスの円弧
        if self.progress > 0:
            extent = -360 * self.progress  # 負の値で時計回り
            self.create_arc(
                center - radius, center - radius,
                center + radius, center + radius,
                outline=self.fg_color,
                width=self.thickness,
                fill="",
                start=90,
                extent=extent,
                style="arc"
            )

        # パーセンテージテキスト
        percentage = int(self.progress * 100)
        self.create_text(
            center, center,
            text=f"{percentage}%",
            font=("Arial", int(self.size * 0.2), "bold"),
            fill=self.fg_color
        )