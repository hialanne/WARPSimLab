# gui_scaling.py


class ScalableClientMixin:
    """Reusable runtime scaling support for WARPSimLab GUI components."""

    def _initialize_scaling(self, scaling_root):
        self._scaling_root = scaling_root
        self._scalable_fonts = []
        self._scale_bind_id = scaling_root.bind("<<WARPSimLabScaleChanged>>", self._on_gui_scale_changed, add="+")


    def _register_scalable_font(self, font, base_size=None):
        if base_size is None:
            base_size = abs(int(font.cget("size")))

        self._scalable_fonts.append((font, base_size))


    def _get_gui_scale(self):
        return float(getattr(self._scaling_root, "_warpsimlab_gui_scale", 1.0))


    def _apply_gui_scale(self):
        scale = self._get_gui_scale()

        for font, base_size in self._scalable_fonts:
            font.configure(size=max(1, round(base_size * scale)))

        self._apply_scaled_styles()


    def _apply_scaled_styles(self):
        pass


    def _on_gui_scale_changed(self, *_):
        self._apply_gui_scale()


    def _stop_scaling(self):
        if self._scale_bind_id is not None:
            self._scaling_root.unbind("<<WARPSimLabScaleChanged>>", self._scale_bind_id)
            self._scale_bind_id = None


class ScalableFrameMixin(ScalableClientMixin):
    """Runtime scaling support for temporary WARPSimLab frames."""

    def _initialize_frame_scaling(self):
        self._initialize_scaling(self.winfo_toplevel())
        self.bind("<Destroy>", self._on_scaling_destroy, add="+")


    def _on_scaling_destroy(self, event):
        if event.widget is not self:
            return

        self._stop_scaling()
