# passai/ui/animations.py — Animation Library

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, Qt, QObject, QTimer, QPoint, QRect,
    pyqtSignal
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsColorizeEffect
from PyQt6.QtGui import QColor


class AnimationHelper:
    """Helper class for smooth animations and micro-interactions."""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 200, on_finished=None):
        """Fade a widget in from transparent to opaque."""
        if not isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect = widget.graphicsEffect()
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        if on_finished:
            anim.finished.connect(on_finished)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        widget._fade_anim = anim
        return anim

    @staticmethod
    def fade_out(widget: QWidget, duration: int = 160, on_finished=None):
        """Fade a widget out."""
        if not isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect = widget.graphicsEffect()
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        if on_finished:
            anim.finished.connect(on_finished)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        widget._fade_anim = anim
        return anim

    @staticmethod
    def scale_in(widget: QWidget, duration: int = 200, on_finished=None):
        """Scale + fade in — dialog/popup entrance."""
        if not isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect = widget.graphicsEffect()

        opacity_anim = QPropertyAnimation(effect, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        original_geo = widget.geometry()
        shrink = 0.04
        start_geo = original_geo.adjusted(
            int(original_geo.width()  * shrink),
            int(original_geo.height() * shrink),
            int(-original_geo.width()  * shrink),
            int(-original_geo.height() * shrink)
        )
        start_geo.moveCenter(original_geo.center())

        geo_anim = QPropertyAnimation(widget, b"geometry")
        geo_anim.setDuration(duration)
        geo_anim.setStartValue(start_geo)
        geo_anim.setEndValue(original_geo)
        geo_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        group = QParallelAnimationGroup(widget)
        group.addAnimation(opacity_anim)
        group.addAnimation(geo_anim)
        if on_finished:
            group.finished.connect(on_finished)
        group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)
        widget._scale_anim = group
        return group

    @staticmethod
    def slide_in_from_bottom(widget: QWidget, distance: int = 18,
                             duration: int = 240, on_finished=None):
        """Slide + fade in from slightly below — content reveal."""
        if not isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect = widget.graphicsEffect()

        opacity_anim = QPropertyAnimation(effect, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        pos = widget.pos()
        pos_anim = QPropertyAnimation(widget, b"pos")
        pos_anim.setDuration(duration)
        pos_anim.setStartValue(QPoint(pos.x(), pos.y() + distance))
        pos_anim.setEndValue(pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(widget)
        group.addAnimation(opacity_anim)
        group.addAnimation(pos_anim)
        if on_finished:
            group.finished.connect(on_finished)
        group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)
        widget._slide_anim = group
        return group

    @staticmethod
    def shake(widget: QWidget, intensity: int = 10, duration: int = 380):
        """Horizontal shake — wrong PIN / validation error feedback.

        Safe to call repeatedly (spam-proof): tracks the widget's true
        origin so repeated rapid calls never accumulate positional drift.
        """
        # ── Stop any running shake cleanly (stop() does NOT emit finished) ──
        existing = getattr(widget, '_shake_anim', None)
        if existing is not None:
            try:
                existing.stop()
            except RuntimeError:
                pass
            widget._shake_anim = None

        # ── Capture origin only on the first call; reuse it for rapid repeats ─
        # This is the fix: without this, each call captures the mid-animation
        # offset position, causing the widget to drift further on every spam.
        if getattr(widget, '_shake_origin', None) is None:
            widget._shake_origin = QPoint(widget.pos())
        pos = widget._shake_origin

        # Snap back to the true origin before starting the new animation,
        # so there is no discontinuity between the stopped and new anim.
        try:
            widget.move(pos)
        except RuntimeError:
            return None

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.Linear)

        steps = 8
        for i in range(steps + 1):
            t = i / steps
            if i == 0 or i == steps:
                offset = 0
            else:
                sign   = 1 if i % 2 == 0 else -1
                offset = int(sign * intensity * (1.0 - t))
            anim.setKeyValueAt(t, QPoint(pos.x() + offset, pos.y()))

        def _on_done(p=pos):
            try:
                widget.move(p)
            except RuntimeError:
                pass
            widget._shake_origin = None
            widget._shake_anim   = None

        anim.finished.connect(_on_done)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        widget._shake_anim = anim
        return anim

    @staticmethod
    def stagger_fade_in(widgets: list, base_delay: int = 35, duration: int = 200):
        """Staggered fade-in for a list of widgets."""
        for i, widget in enumerate(widgets):
            if not isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)
            else:
                effect = widget.graphicsEffect()
            effect.setOpacity(0.0)

            def _start(w=widget, eff=effect):
                try:
                    a = QPropertyAnimation(eff, b"opacity")
                    a.setDuration(duration)
                    a.setStartValue(0.0)
                    a.setEndValue(1.0)
                    a.setEasingCurve(QEasingCurve.Type.OutCubic)
                    a.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
                    w._stagger_anim = a
                except RuntimeError:
                    pass

            QTimer.singleShot(i * base_delay, _start)

    @staticmethod
    def stagger_slide_in(widgets: list, base_delay: int = 40,
                         duration: int = 240, distance: int = 14):
        """Staggered slide+fade — richer than plain fade."""
        for i, widget in enumerate(widgets):
            if not isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)
            else:
                effect = widget.graphicsEffect()
            effect.setOpacity(0.0)

            def _start(w=widget, eff=effect):
                try:
                    pos = w.pos()
                    w.move(pos.x(), pos.y() + distance)

                    op_a = QPropertyAnimation(eff, b"opacity")
                    op_a.setDuration(duration)
                    op_a.setStartValue(0.0)
                    op_a.setEndValue(1.0)
                    op_a.setEasingCurve(QEasingCurve.Type.OutCubic)

                    pos_a = QPropertyAnimation(w, b"pos")
                    pos_a.setDuration(duration)
                    pos_a.setStartValue(QPoint(pos.x(), pos.y() + distance))
                    pos_a.setEndValue(pos)
                    pos_a.setEasingCurve(QEasingCurve.Type.OutCubic)

                    grp = QParallelAnimationGroup(w)
                    grp.addAnimation(op_a)
                    grp.addAnimation(pos_a)
                    grp.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)
                    w._stagger_anim = grp
                except RuntimeError:
                    pass

            QTimer.singleShot(i * base_delay, _start)

    @staticmethod
    def button_press_effect(button: QWidget, duration: int = 90):
        """Micro spring press animation on a button."""
        original_geo = button.geometry()
        shrink_geo   = original_geo.adjusted(1, 1, -1, -1)
        shrink_geo.moveCenter(original_geo.center())

        shrink = QPropertyAnimation(button, b"geometry")
        shrink.setDuration(duration // 2)
        shrink.setStartValue(original_geo)
        shrink.setEndValue(shrink_geo)
        shrink.setEasingCurve(QEasingCurve.Type.OutCubic)

        grow = QPropertyAnimation(button, b"geometry")
        grow.setDuration(duration // 2)
        grow.setStartValue(shrink_geo)
        grow.setEndValue(original_geo)
        grow.setEasingCurve(QEasingCurve.Type.OutBack)

        shrink.finished.connect(grow.start)
        shrink.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        button._press_shrink = shrink
        button._press_grow   = grow

    @staticmethod
    def window_fade_in(window: QWidget, duration: int = 220):
        """Fade the entire window in on show — smooth startup feel."""
        window.setWindowOpacity(0.0)
        anim = QPropertyAnimation(window, b"windowOpacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        window._win_fade = anim
        return anim

    @staticmethod
    def cross_fade(old_widget: QWidget, new_widget: QWidget,
                   duration: int = 160, on_finished=None):
        """Fade out old, fade in new simultaneously."""
        if not isinstance(new_widget.graphicsEffect(), QGraphicsOpacityEffect):
            eff = QGraphicsOpacityEffect(new_widget)
            new_widget.setGraphicsEffect(eff)
            eff.setOpacity(0.0)
        new_widget.show()
        AnimationHelper.fade_out(old_widget, duration)
        return AnimationHelper.fade_in(new_widget, duration, on_finished)


class DetailsPanelAnimator(QObject):
    """Manages smooth content transitions in the details panel."""

    animation_finished = pyqtSignal()

    def __init__(self, details_widget: QWidget):
        super().__init__()
        self.details_widget = details_widget
        self.is_animating   = False

    def animate_content_change(self, on_content_changed):
        """Fade out → update → fade in."""
        if self.is_animating:
            on_content_changed()
            return

        self.is_animating = True

        if not isinstance(self.details_widget.graphicsEffect(), QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self.details_widget)
            self.details_widget.setGraphicsEffect(effect)
        effect = self.details_widget.graphicsEffect()

        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(100)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

        def on_out_done():
            on_content_changed()
            fade_in = QPropertyAnimation(effect, b"opacity")
            fade_in.setDuration(160)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
            fade_in.finished.connect(self._finish)
            fade_in.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            self.details_widget._fade_in = fade_in

        fade_out.finished.connect(on_out_done)
        fade_out.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self.details_widget._fade_out = fade_out

    def _finish(self):
        self.is_animating = False
        self.animation_finished.emit()
