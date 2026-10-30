from types import SimpleNamespace
from unittest.mock import Mock

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


def test_scaling_uses_base_size_and_unbinds_only_on_frame_destroy():
    client = ScalableFrameMixin()
    root = Mock()
    root._warpsimlab_gui_scale = 1.5
    root.bind.return_value = "binding-id"
    client.winfo_toplevel = lambda: root
    client.bind = Mock()
    client._initialize_frame_scaling()
    font = Mock()
    font.cget.return_value = -10
    client._register_scalable_font(font)
    client._apply_gui_scale()
    font.configure.assert_called_with(size=15)
    root._warpsimlab_gui_scale = .01
    client._on_gui_scale_changed()
    font.configure.assert_called_with(size=1)
    root._warpsimlab_gui_scale = 2
    client._on_gui_scale_changed()
    font.configure.assert_called_with(size=20)
    client._on_scaling_destroy(SimpleNamespace(widget=object()))
    root.unbind.assert_not_called()
    client._on_scaling_destroy(SimpleNamespace(widget=client))
    client._stop_scaling()
    root.unbind.assert_called_once_with("<<WARPSimLabScaleChanged>>", "binding-id")


def test_default_scale_and_explicit_font_size():
    client = ScalableFrameMixin()
    root = SimpleNamespace(bind=lambda *a, **k: "id")
    client._initialize_scaling(root)
    font = Mock()
    client._register_scalable_font(font, base_size=12)
    client._apply_gui_scale()
    font.configure.assert_called_once_with(size=12)
