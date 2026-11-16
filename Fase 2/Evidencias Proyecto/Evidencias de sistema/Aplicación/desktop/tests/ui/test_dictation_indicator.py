from PySide6.QtCore import Qt

from ergosense.ui.dictation_indicator import DictationIndicator


def test_indicator_stays_above_apps_and_cannot_take_focus_or_clicks(qapp):
    indicator = DictationIndicator()
    flags = indicator.windowFlags()
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert flags & Qt.WindowType.WindowTransparentForInput
    assert flags & Qt.WindowType.WindowDoesNotAcceptFocus
    assert indicator.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    assert indicator.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert indicator.width() == indicator.height() == 44
    assert 0.5 < indicator.windowOpacity() < 1
    indicator.set_active(True)
    assert indicator.isVisible()
    indicator.set_state("listening")
    assert indicator._state == "listening"
    indicator.set_state("processing")
    assert indicator._state == "processing"
    indicator.set_active(False)
    assert not indicator.isVisible()
    indicator.close()
