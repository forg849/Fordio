import os
import sys
import json
import random
import traceback
from dataclasses import dataclass, asdict

from PyQt6 import QtCore, QtGui, QtWidgets, QtMultimedia


APP_NAME = "Fordio"


def _get_base_dir() -> str:
    """Возвращает папку, в которой нужно хранить данные приложения.

    - В обычном запуске .py — это папка со скриптом (как и раньше).
    - В собранном PyInstaller .exe (особенно --onefile) __file__ указывает
      во временную папку распаковки, которая создаётся заново при каждом
      запуске и удаляется после закрытия программы. Поэтому для .exe берём
      папку, где лежит сам исполняемый файл — она постоянна между запусками.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _get_base_dir()
DATA_DIR = os.path.join(BASE_DIR, "fordio_data")
LIB_FILE = os.path.join(DATA_DIR, "library.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

LANGUAGES = ("en", "ru")
THEME_IDS = ("graphite", "coal", "dimka", "paper", "halloween", "christmas", "system")

TEXTS = {
    "en": {
        "subtitle": "Your music, all in one place",
        "settings": "Settings",
        "library": "Library",
        "add_music": "＋  Add music",
        "search": "Search by title or artist",
        "favorites": "★ Favorites",
        "favorites_tooltip": "Add or remove selected tracks from favorites",
        "remove_selected": "Remove selected",
        "now_playing": "Now playing",
        "select_track": "Choose a track from your library",
        "loop_track": "Repeat track",
        "loop_playlist": "Repeat playlist",
        "volume": "Volume",
        "playlist": "Playlist",
        "add_to_playlist": "Add to playlist",
        "clear": "Clear",
        "shuffle": "Shuffle",
        "settings_title": "Settings",
        "settings_intro": "Set the language and look that suit you.",
        "appearance": "Appearance",
        "theme_help": "Choose a color theme. Your choice is saved for next time.",
        "language": "Interface language",
        "language_help": "Choose the language used throughout Fordio.",
        "done": "Done",
        "add_error_title": "Could not add music",
        "english": "English",
        "russian": "Русский",
        "theme_graphite": "Graphite",
        "theme_coal": "Coal",
        "theme_dimka": "Dimka",
        "theme_paper": "Paper",
        "theme_halloween": "Halloween",
        "theme_christmas": "Christmas",
        "theme_system": "System",
        "choose_music": "Choose music",
        "audio_files": "Audio files",
        "add_failed": "Could not add {name}:\n\n{error}",
        "unsupported_format": "Unsupported audio format: {extension}",
        "remove_title": "Remove tracks",
        "remove_confirm": "Remove {count} selected track(s)?",
        "yes": "Remove",
        "no": "Cancel",
        "player_error": "Player error",
        "unknown_artist": "Unknown artist",
        "track": "track",
        "tracks": "tracks",
        "settings_load_error": "Could not read settings. Default settings will be used.\n\n{error}",
        "settings_save_error": "Could not save settings.\n\n{error}",
        "crash_title": "Fordio crashed",
        "crash_message": "The app could not start.\n\n{error}",
    },
    "ru": {
        "subtitle": "Ваша музыка — в одном месте",
        "settings": "Настройки",
        "library": "Медиатека",
        "add_music": "＋  Добавить музыку",
        "search": "Поиск по названию или исполнителю",
        "favorites": "★ Избранное",
        "favorites_tooltip": "Добавить или убрать выбранные треки из избранного",
        "remove_selected": "Удалить выбранное",
        "now_playing": "Сейчас играет",
        "select_track": "Выберите трек из медиатеки",
        "loop_track": "Повторять трек",
        "loop_playlist": "Повторять плейлист",
        "volume": "Громкость",
        "playlist": "Плейлист",
        "add_to_playlist": "Добавить в плейлист",
        "clear": "Очистить",
        "shuffle": "Перемешать",
        "settings_title": "Настройки",
        "settings_intro": "Выберите язык и оформление по своему вкусу.",
        "appearance": "Оформление",
        "theme_help": "Выберите цветовую тему. Настройка сохранится для следующего запуска.",
        "language": "Язык интерфейса",
        "language_help": "Выберите язык интерфейса Fordio.",
        "done": "Готово",
        "add_error_title": "Ошибка добавления",
        "english": "English",
        "russian": "Русский",
        "theme_graphite": "Графит",
        "theme_coal": "Уголь",
        "theme_dimka": "Димка",
        "theme_paper": "Бумага",
        "theme_halloween": "Хэллоуин",
        "theme_christmas": "Новогодняя",
        "theme_system": "Как в системе",
        "choose_music": "Выберите музыку",
        "audio_files": "Аудиофайлы",
        "add_failed": "Не удалось добавить {name}:\n\n{error}",
        "unsupported_format": "Формат аудио не поддерживается: {extension}",
        "remove_title": "Удаление треков",
        "remove_confirm": "Удалить выбранные треки ({count})?",
        "yes": "Удалить",
        "no": "Отмена",
        "player_error": "Ошибка плеера",
        "unknown_artist": "Неизвестный исполнитель",
        "track": "трек",
        "tracks": "треков",
        "track_one": "трек",
        "track_few": "трека",
        "track_many": "треков",
        "settings_load_error": "Не удалось прочитать настройки. Будут использованы стандартные.\n\n{error}",
        "settings_save_error": "Не удалось сохранить настройки.\n\n{error}",
        "crash_title": "Ошибка Fordio",
        "crash_message": "Не удалось запустить приложение.\n\n{error}",
    },
}

THEMES = {
    "graphite": {
        "window": "#121720", "panel": "#1a2230", "field": "#151c27",
        "border": "#2b3545", "text": "#ecf0f6", "subtle": "#b6c0cf",
        "muted": "#8290a4", "accent": "#8cb8f8", "accent_hover": "#a4c8ff",
        "accent_text": "#152237", "selected": "#28364b", "selected_text": "#d8e7ff",
    },
    "coal": {
        "window": "#151515", "panel": "#1e1e1e", "field": "#181818",
        "border": "#363636", "text": "#eeeeee", "subtle": "#c4c4c4",
        "muted": "#929292", "accent": "#c8cdd4", "accent_hover": "#e1e4e9",
        "accent_text": "#202020", "selected": "#303238", "selected_text": "#f4f4f4",
    },
    "dimka": {
        "window": "#191720", "panel": "#221f2b", "field": "#1c1924",
        "border": "#393342", "text": "#f0edf5", "subtle": "#c8c0d3",
        "muted": "#968da2", "accent": "#c1a6ed", "accent_hover": "#d2bbf6",
        "accent_text": "#281e34", "selected": "#393044", "selected_text": "#eee4ff",
    },
    "paper": {
        "window": "#f0eee8", "panel": "#fbfaf7", "field": "#ffffff",
        "border": "#d8d4ca", "text": "#292a28", "subtle": "#50524d",
        "muted": "#777a72", "accent": "#8c6748", "accent_hover": "#a37b58",
        "accent_text": "#ffffff", "selected": "#e9ded0", "selected_text": "#342719",
    },
    "halloween": {
        "window": "#17111b", "panel": "#211827", "field": "#1a1321",
        "border": "#3a2b42", "text": "#f4edf7", "subtle": "#ccb9d4",
        "muted": "#9985a3", "accent": "#ff9b53", "accent_hover": "#ffb477",
        "accent_text": "#2b1608", "selected": "#392639", "selected_text": "#ffe0c5",
    },
    "christmas": {
        "window": "#121914", "panel": "#1b241d", "field": "#151d17",
        "border": "#34473a", "text": "#f1f3eb", "subtle": "#c7d2c7",
        "muted": "#91a195", "accent": "#c9525a", "accent_hover": "#dda65e",
        "accent_text": "#fff7ee", "selected": "#293b30", "selected_text": "#f6e8d9",
    },
}


class AppSettings:
    def __init__(self):
        self.language = "en"
        self.theme = "graphite"
        self.load_error: str | None = None

        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            self.load_error = str(error)
            return

        if not isinstance(saved, dict):
            self.load_error = "The settings file must contain a JSON object."
            return
        language = saved.get("language")
        if language in LANGUAGES:
            self.language = language
        elif "language" in saved:
            self.load_error = f"Unknown language setting: {language!r}"

        theme = saved.get("theme")
        if theme in THEME_IDS:
            self.theme = theme
        elif "theme" in saved:
            self.load_error = f"Unknown theme setting: {theme!r}"

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        temporary_file = SETTINGS_FILE + ".tmp"
        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(
                {"language": self.language, "theme": self.theme},
                file,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(temporary_file, SETTINGS_FILE)


@dataclass
class Track:
    id: str
    title: str
    artist: str
    filename: str  # stored in data dir
    duration_ms: int = 0
    added_at: float = 0.0
    favorite: bool = False

    @property
    def path(self) -> str:
        return os.path.join(DATA_DIR, "tracks", self.filename)


class Library:
    def __init__(self):
        self.tracks_dir = os.path.join(DATA_DIR, "tracks")
        os.makedirs(self.tracks_dir, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.tracks: list[Track] = []
        self._load()

    def _load(self):
        if not os.path.exists(LIB_FILE):
            self.tracks = []
            return
        try:
            with open(LIB_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            tracks = []
            for t in raw.get("tracks", []):
                # На случай старых файлов библиотеки без поля "favorite"
                # и прочих неожиданных/отсутствующих ключей.
                try:
                    tracks.append(Track(
                        id=t["id"],
                        title=t.get("title", ""),
                        artist=t.get("artist", ""),
                        filename=t["filename"],
                        duration_ms=t.get("duration_ms", 0),
                        added_at=t.get("added_at", 0.0),
                        favorite=bool(t.get("favorite", False)),
                    ))
                except Exception:
                    continue
            self.tracks = tracks
        except Exception:
            self.tracks = []

    def _save(self):
        raw = {"tracks": [asdict(t) for t in self.tracks]}
        tmp = LIB_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
        os.replace(tmp, LIB_FILE)

    def add_track_from_file(self, src_path: str) -> Track:
        if not os.path.exists(src_path):
            raise FileNotFoundError(src_path)

        base = os.path.basename(src_path)
        name, ext = os.path.splitext(base)
        ext = ext.lower()
        if ext not in {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".mp4"}:
            raise ValueError("Unsupported audio format: " + ext)

        # generate id and safe filename
        track_id = QtCore.QUuid.createUuid().toString()
        safe_filename = f"{track_id}{ext}"
        dst_path = os.path.join(self.tracks_dir, safe_filename)

        # copy
        import shutil
        shutil.copy2(src_path, dst_path)

        # title heuristics
        title = name
        artist = ""

        t = Track(
            id=track_id,
            title=title,
            artist=artist,
            filename=safe_filename,
            duration_ms=0,
            added_at=QtCore.QDateTime.currentSecsSinceEpoch(),
            favorite=False,
        )
        self.tracks.append(t)
        self._save()
        return t

    def remove_track(self, track_id: str):
        track = next((x for x in self.tracks if x.id == track_id), None)
        if not track:
            return
        # delete file
        try:
            if os.path.exists(track.path):
                os.remove(track.path)
        except Exception:
            pass
        self.tracks = [x for x in self.tracks if x.id != track_id]
        self._save()

    def toggle_favorite(self, track_id: str) -> bool:
        track = next((x for x in self.tracks if x.id == track_id), None)
        if not track:
            return False
        track.favorite = not track.favorite
        self._save()
        return track.favorite

    def set_favorite(self, track_id: str, value: bool):
        track = next((x for x in self.tracks if x.id == track_id), None)
        if not track:
            return
        track.favorite = bool(value)
        self._save()


class Player(QtCore.QObject):

    positionChanged = QtCore.pyqtSignal("qint64")
    durationChanged = QtCore.pyqtSignal("qint64")
    stateChanged = QtCore.pyqtSignal(object)

    trackChanged = QtCore.pyqtSignal(str)
    ended = QtCore.pyqtSignal()
    errorOccured = QtCore.pyqtSignal(str)


    def __init__(self):
        super().__init__()
        self.audio = QtMultimedia.QMediaPlayer()
        # Keep QAudioOutput referenced, otherwise some Qt builds may not route audio correctly.
        self._output = QtMultimedia.QAudioOutput()
        self.audio.setAudioOutput(self._output)


        self.audio.positionChanged.connect(self.positionChanged)
        self.audio.durationChanged.connect(self.durationChanged)
        self.audio.playbackStateChanged.connect(self.stateChanged.emit)
        self.audio.mediaStatusChanged.connect(self._on_media_status)
        self.audio.errorOccurred.connect(self._on_error)

        self.playlist: list[str] = []  # track ids
        self.current_index = -1
        self.loop_one = False
        self.loop_playlist = False

        # For repeat logic
        self._was_playing = False

    def _on_error(self, _):
        err = self.audio.errorString()
        self.errorOccured.emit(err)

    def _on_media_status(self, status):
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            self.ended.emit()

    def set_playlist(self, track_ids: list[str], start_id: str | None = None):
        self.playlist = list(track_ids)
        if not self.playlist:
            self.current_index = -1
            return
        if start_id and start_id in self.playlist:
            self.current_index = self.playlist.index(start_id)
        else:
            self.current_index = 0

    def load_current(self, tracks_by_id: dict[str, Track]):
        if self.current_index < 0 or self.current_index >= len(self.playlist):
            return
        tid = self.playlist[self.current_index]
        t = tracks_by_id.get(tid)
        if not t:
            return
        url = QtCore.QUrl.fromLocalFile(t.path)

        # Use Qt6/PyQt6 supported API. QMediaContent may be missing in some builds.
        self.audio.setSource(url)

        # Update UI immediately.
        self.trackChanged.emit(tid)

        # If media fails to load, Qt will call _on_error via errorOccurred.
        # Also set up a simple sanity check: if it ends up with an error, we'll show it.
        # (Some backends may report nothing until playback starts.)
        # Keep auto-play behavior in caller.


    def play(self):
        self.audio.play()

    def pause(self):
        self.audio.pause()

    def stop(self):
        self.audio.stop()

    def seek(self, ms: int):
        self.audio.setPosition(ms)

    def set_volume(self, vol: int):
        # QMediaPlayer.setVolume may be missing depending on Qt backend.
        # Use audio output volume if available.
        v = max(0, min(100, int(vol)))
        try:
            self.audio.setVolume(v)
        except Exception:
            try:
                self.audio.audioOutput().setVolume(v)
            except Exception:
                pass


    def volume(self) -> int:
        # QMediaPlayer in some Qt builds uses audio output volume
        try:
            return int(self.audio.audioOutput().volume())
        except Exception:
            return 50


    def position(self) -> int:
        return int(self.audio.position())

    def duration(self) -> int:
        return int(self.audio.duration())

    def state(self):
        # playbackState() returns a Qt enum (PlaybackState). Casting to int may fail
        # depending on PyQt/Qt build.
        return self.audio.playbackState()


    def next(self, tracks_by_id: dict[str, Track], auto_play: bool = True):
        if not self.playlist:
            return
        if self.current_index < 0:
            self.current_index = 0
        else:
            self.current_index += 1
        if self.current_index >= len(self.playlist):
            if self.loop_playlist:
                self.current_index = 0
            else:
                # end
                self.stop()
                return
        self.load_current(tracks_by_id)
        if auto_play:
            self.play()

    def previous(self, tracks_by_id: dict[str, Track], auto_play: bool = True):
        if not self.playlist:
            return
        if self.current_index < 0:
            self.current_index = 0
        else:
            self.current_index -= 1
        if self.current_index < 0:
            if self.loop_playlist:
                self.current_index = len(self.playlist) - 1
            else:
                self.current_index = 0
        self.load_current(tracks_by_id)
        if auto_play:
            self.play()


def fmt_time(ms: int) -> str:
    if ms < 0:
        ms = 0
    s = ms // 1000
    m, sec = divmod(s, 60)
    h, m2 = divmod(m, 60)
    if h > 0:
        return f"{h:d}:{m2:02d}:{sec:02d}"
    return f"{m:d}:{sec:02d}"


class VisualizerBars(QtWidgets.QWidget):
    """Декоративный сегментный эквалайзер без анализа аудиопотока."""

    def __init__(self, bars: int = 24, segments: int = 10, parent=None):
        super().__init__(parent)
        self.bars_count = max(4, bars)
        self.segments = max(3, segments)

        self.levels = [0.0 for _ in range(self.bars_count)]
        self.targets = [0.0 for _ in range(self.bars_count)]

        self._playing = False
        self._active_color = QtGui.QColor("#8cb8f8")
        self._inactive_color = QtGui.QColor("#2b3545")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setMinimumHeight(66)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )

    def set_playing(self, playing: bool):
        self._playing = bool(playing)
        if not self._playing:
            self.targets = [0.0 for _ in range(self.bars_count)]

    def set_colors(self, active: str, inactive: str):
        self._active_color = QtGui.QColor(active)
        self._inactive_color = QtGui.QColor(inactive)
        self.update()

    def tick(self):
        if self._playing:
            for i in range(self.bars_count):
                if random.random() < 0.18 or abs(self.levels[i] - self.targets[i]) < 0.02:
                    self.targets[i] = random.uniform(0.12, 1.0)
                self.levels[i] += (self.targets[i] - self.levels[i]) * 0.35
        else:
            for i in range(self.bars_count):
                self.levels[i] += (0.0 - self.levels[i]) * 0.18
                if self.levels[i] < 0.002:
                    self.levels[i] = 0.0

        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = self.bars_count
        segs = self.segments
        if n <= 0 or w <= 0 or h <= 0:
            p.end()
            return

        gap = 4.0
        bar_w = (w - gap * (n - 1)) / n
        if bar_w <= 0:
            bar_w = 1.0

        seg_gap = 3.0
        seg_h = (h - seg_gap * (segs - 1)) / segs
        if seg_h <= 0:
            seg_h = 1.0

        active_colors = [
            self._active_color.lighter(100 + int(30 * s / max(1, segs - 1)))
            for s in range(segs)
        ]
        p.setPen(QtCore.Qt.PenStyle.NoPen)

        for i, level in enumerate(self.levels):
            level = max(0.0, min(1.0, level))
            lit = int(round(level * segs))

            x = i * (bar_w + gap)

            for s in range(segs):
                y = h - (s + 1) * seg_h - s * seg_gap
                rect = QtCore.QRectF(x, y, bar_w, seg_h)

                if s < lit:
                    p.setBrush(active_colors[s])
                else:
                    p.setBrush(self._inactive_color)

                p.drawRoundedRect(rect, 2.0, 2.0)

        p.end()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 760)
        self.setMinimumSize(900, 680)

        self.preferences = AppSettings()
        self._text_widgets = []
        self._placeholder_widgets = []
        self._settings_ui = None

        self.library = Library()
        self.tracks_by_id = {t.id: t for t in self.library.tracks}

        self.player = Player()
        self.player.ended.connect(self._on_ended)
        self.player.trackChanged.connect(self._on_track_changed)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.errorOccured.connect(self._on_error)
        self.player.stateChanged.connect(self._on_state_changed)

        self.playlist_ids: list[str] = []

        self._build_ui()
        self._apply_theme()
        self._apply_language()
        self._refresh_library_list()
        self._sync_player_from_playlist()
        self._apply_brand_icon()
        if self.preferences.load_error:
            QtCore.QTimer.singleShot(0, self._show_settings_load_warning)

        self._animTimer = QtCore.QTimer(self)
        self._animTimer.setInterval(30)
        self._animTimer.timeout.connect(self._tick_playing_animation)
        self._playing = False
        self._animTimer.start()

    def _text(self, key: str) -> str:
        return TEXTS[self.preferences.language][key]

    def _register_text(self, widget, key: str):
        self._set_widget_text(widget, key)
        self._text_widgets.append((widget, key))
        return widget

    def _set_widget_text(self, widget, key: str):
        if isinstance(widget, QtWidgets.QGroupBox):
            widget.setTitle(self._text(key))
        else:
            widget.setText(self._text(key))

    def _colors_for_theme(self, theme_id: str):
        if theme_id != "system":
            return THEMES[theme_id]
        palette = QtWidgets.QApplication.palette()
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        field = palette.color(QtGui.QPalette.ColorRole.Base)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        accent = palette.color(QtGui.QPalette.ColorRole.Highlight)
        dark = window.lightness() < 128
        muted = text.lighter(140) if dark else text.darker(140)
        border = field.lighter(135) if dark else field.darker(115)
        hover = accent.lighter(115) if dark else accent.darker(110)
        selected_text = palette.color(QtGui.QPalette.ColorRole.HighlightedText)

        return {
            "window": window.name(),
            "panel": palette.color(QtGui.QPalette.ColorRole.Button).name(),
            "field": field.name(),
            "border": border.name(),
            "text": text.name(),
            "subtle": text.name(),
            "muted": muted.name(),
            "accent": accent.name(),
            "accent_hover": hover.name(),
            "accent_text": selected_text.name(),
            "selected": accent.name(),
            "selected_text": selected_text.name(),
        }

    def _theme_colors(self):
        return self._colors_for_theme(self.preferences.theme)

    def _apply_theme(self):
        colors = self._theme_colors()
        stylesheet = """
            QWidget {
                color: @text;
                font-family: "Segoe UI", Arial;
                font-size: 10pt;
            }
            QMainWindow, QDialog, QWidget#root { background-color: @window; }
            QGroupBox {
                background-color: @panel;
                border: 1px solid @border;
                border-radius: 14px;
                margin-top: 20px;
                padding: 18px 14px 14px;
            }
            QGroupBox::title {
                color: @subtle;
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px;
            }
            QListWidget {
                background-color: @field;
                border: 1px solid @border;
                border-radius: 10px;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                min-height: 34px;
                padding: 5px 9px;
                border-radius: 7px;
            }
            QListWidget::item:hover { background-color: @panel; }
            QListWidget::item:selected {
                background-color: @selected;
                color: @selected_text;
            }
            QPushButton, QToolButton {
                background-color: @panel;
                border: 1px solid @border;
                border-radius: 9px;
                padding: 9px 12px;
                color: @text;
            }
            QPushButton:hover, QToolButton:hover { background-color: @selected; }
            QPushButton:pressed, QToolButton:pressed { background-color: @border; }
            QPushButton#primaryButton, QToolButton#playButton {
                background-color: @accent;
                border-color: @accent;
                color: @accent_text;
                font-weight: 700;
            }
            QPushButton#primaryButton:hover, QToolButton#playButton:hover {
                background-color: @accent_hover;
            }
            QToolButton {
                min-width: 40px;
                min-height: 38px;
                font-size: 13pt;
                font-weight: 600;
            }
            QToolButton#playButton {
                min-width: 54px;
                min-height: 48px;
                border-radius: 14px;
                font-size: 16pt;
            }
            QLineEdit {
                background-color: @field;
                border: 1px solid @border;
                border-radius: 9px;
                padding: 10px 12px;
                selection-background-color: @selected;
            }
            QLineEdit:focus { border-color: @accent; }
            QSlider { background: transparent; }
            QSlider::groove:horizontal {
                height: 5px;
                background: @border;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal { background: @accent; border-radius: 2px; }
            QSlider::handle:horizontal {
                width: 13px;
                height: 13px;
                margin: -5px 0;
                background: @accent_hover;
                border: 2px solid @accent;
                border-radius: 7px;
            }
            QCheckBox { spacing: 8px; color: @subtle; }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid @border;
                border-radius: 5px;
                background: @field;
            }
            QCheckBox::indicator:checked {
                background: @accent;
                border-color: @accent;
            }
            QLabel#appTitle {
                color: @accent;
                font-size: 22pt;
                font-weight: 700;
                letter-spacing: 2px;
            }
            QLabel#libraryCount, QLabel#mutedLabel, QLabel#settingsDescription {
                color: @muted;
            }
            QLabel#trackTitle {
                color: @text;
                font-size: 19pt;
                font-weight: 600;
            }
            QLabel#trackArtist { color: @subtle; font-size: 11pt; }
            QLabel#albumArt {
                background-color: @selected;
                border: 1px solid @border;
                border-radius: 14px;
                color: @accent;
                font-size: 42pt;
            }
            QLabel#settingsTitle { font-size: 15pt; font-weight: 600; }
            QPushButton#languageOption:checked {
                background-color: @selected;
                border-color: @accent;
                color: @selected_text;
            }
            QPushButton#themeCard {
                padding: 6px;
                border-radius: 8px;
            }
            QPushButton#themeCard:checked {
                background-color: @selected;
                border: 2px solid @accent;
            }
            QScrollBar:vertical {
                width: 8px;
                margin: 3px 1px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                min-height: 24px;
                background: @border;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """
        for key in sorted(colors, key=len, reverse=True):
            value = colors[key]
            stylesheet = stylesheet.replace(f"@{key}", value)
        self.setStyleSheet(stylesheet)
        self.visualizer.set_colors(colors["accent"], colors["border"])

    def _apply_language(self):
        for widget, key in self._text_widgets:
            self._set_widget_text(widget, key)
        for widget, key in self._placeholder_widgets:
            widget.setPlaceholderText(self._text(key))

        self.favorite_button.setToolTip(self._text("favorites_tooltip"))
        index = self.player.current_index
        track_id = self.player.playlist[index] if 0 <= index < len(self.player.playlist) else None
        track = self.tracks_by_id.get(track_id) if track_id else None
        if track is None:
            self.lblNowTitle.setText("—")
            self.lblNowArtist.setText(self._text("select_track"))
        else:
            self.lblNowTitle.setText(track.title)
            self.lblNowArtist.setText(track.artist or self._text("unknown_artist"))
        self._refresh_library_list()
        self._update_settings_language()

    def _format_track_count(self, count: int) -> str:
        if self.preferences.language == "en":
            noun = self._text("track") if count == 1 else self._text("tracks")
        else:
            last_two = count % 100
            last_digit = count % 10
            if 11 <= last_two <= 14:
                noun = self._text("track_many")
            elif last_digit == 1:
                noun = self._text("track_one")
            elif 2 <= last_digit <= 4:
                noun = self._text("track_few")
            else:
                noun = self._text("track_many")
        return f"{count} {noun}"

    def _show_settings_load_warning(self):
        message = self._text("settings_load_error").format(error=self.preferences.load_error)
        QtWidgets.QMessageBox.warning(self, self._text("settings_title"), message)

    def _open_settings(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setMinimumWidth(500)
        dialog_layout = QtWidgets.QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(20, 18, 20, 16)
        dialog_layout.setSpacing(10)

        title = QtWidgets.QLabel()
        title.setObjectName("settingsTitle")
        description = QtWidgets.QLabel()
        description.setObjectName("settingsDescription")
        description.setWordWrap(True)
        language_title = QtWidgets.QLabel()
        language_title.setObjectName("settingsTitle")
        language_help = QtWidgets.QLabel()
        language_help.setObjectName("settingsDescription")
        language_help.setWordWrap(True)
        appearance_title = QtWidgets.QLabel()
        appearance_title.setObjectName("settingsTitle")
        theme_help = QtWidgets.QLabel()
        theme_help.setObjectName("settingsDescription")
        theme_help.setWordWrap(True)

        dialog_layout.addWidget(title)
        dialog_layout.addWidget(description)
        dialog_layout.addSpacing(6)
        dialog_layout.addWidget(language_title)
        dialog_layout.addWidget(language_help)

        language_row = QtWidgets.QHBoxLayout()
        language_row.setSpacing(10)
        language_group = QtWidgets.QButtonGroup(dialog)
        language_group.setExclusive(True)
        language_buttons = {}
        for language in LANGUAGES:
            button = QtWidgets.QPushButton()
            button.setObjectName("languageOption")
            button.setCheckable(True)
            button.setMinimumWidth(130)
            button.setChecked(self.preferences.language == language)
            language_group.addButton(button)
            language_row.addWidget(button)
            language_buttons[language] = button
            button.clicked.connect(
                lambda checked, value=language: (
                    self._set_preference("language", value) if checked else None
                )
            )
        language_row.addStretch(1)
        dialog_layout.addLayout(language_row)
        dialog_layout.addSpacing(8)

        dialog_layout.addWidget(appearance_title)
        dialog_layout.addWidget(theme_help)
        theme_grid = QtWidgets.QGridLayout()
        theme_grid.setHorizontalSpacing(10)
        theme_grid.setVerticalSpacing(10)
        theme_cards = {}
        for index, theme_id in enumerate(THEME_IDS):
            button, label = self._create_theme_card(theme_id)
            button.setChecked(self.preferences.theme == theme_id)
            theme_grid.addWidget(button, index // 3, index % 3)
            theme_cards[theme_id] = (button, label)
            button.clicked.connect(
                lambda checked, value=theme_id: (
                    self._set_preference("theme", value) if checked else None
                )
            )
        dialog_layout.addLayout(theme_grid)

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        close_button = QtWidgets.QPushButton()
        close_button.clicked.connect(dialog.accept)
        footer.addWidget(close_button)
        dialog_layout.addLayout(footer)

        self._settings_ui = {
            "dialog": dialog,
            "title": title,
            "description": description,
            "language_title": language_title,
            "language_help": language_help,
            "appearance_title": appearance_title,
            "theme_help": theme_help,
            "language_buttons": language_buttons,
            "theme_cards": theme_cards,
            "close_button": close_button,
        }
        self._update_settings_language()
        dialog.exec()
        self._settings_ui = None

    def _create_theme_card(self, theme_id: str):
        colors = self._colors_for_theme(theme_id)
        button = QtWidgets.QPushButton()
        button.setObjectName("themeCard")
        button.setCheckable(True)
        button.setFixedSize(136, 104)
        button.setAccessibleName(self._text(f"theme_{theme_id}"))

        card_layout = QtWidgets.QVBoxLayout(button)
        card_layout.setContentsMargins(7, 7, 7, 5)
        card_layout.setSpacing(5)

        preview = QtWidgets.QFrame()
        preview.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        preview.setFixedHeight(54)
        preview.setStyleSheet(
            f"background-color: {colors['window']}; border: 1px solid {colors['border']};"
            "border-radius: 4px;"
        )
        preview_layout = QtWidgets.QHBoxLayout(preview)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        preview_layout.setSpacing(5)

        sidebar = QtWidgets.QFrame()
        sidebar.setFixedWidth(12)
        sidebar.setStyleSheet(f"background-color: {colors['panel']}; border: none;")
        preview_layout.addWidget(sidebar)

        sample = QtWidgets.QVBoxLayout()
        sample.setContentsMargins(0, 0, 0, 0)
        sample.setSpacing(4)
        accent_line = QtWidgets.QFrame()
        accent_line.setFixedHeight(8)
        accent_line.setStyleSheet(f"background-color: {colors['accent']}; border: none;")
        secondary_line = QtWidgets.QFrame()
        secondary_line.setFixedHeight(5)
        secondary_line.setStyleSheet(f"background-color: {colors['muted']}; border: none;")
        sample.addWidget(accent_line)
        sample.addWidget(secondary_line)
        sample.addStretch(1)
        preview_layout.addLayout(sample, 1)
        card_layout.addWidget(preview)

        label = QtWidgets.QLabel()
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        card_layout.addWidget(label)
        return button, label

    def _update_settings_language(self):
        if not self._settings_ui:
            return
        ui = self._settings_ui
        ui["dialog"].setWindowTitle(self._text("settings_title"))
        labels = (
            ("title", "settings_title"),
            ("description", "settings_intro"),
            ("language_title", "language"),
            ("language_help", "language_help"),
            ("appearance_title", "appearance"),
            ("theme_help", "theme_help"),
        )
        for widget_key, text_key in labels:
            ui[widget_key].setText(self._text(text_key))
        ui["close_button"].setText(self._text("done"))
        for language, button in ui["language_buttons"].items():
            text_key = "english" if language == "en" else "russian"
            button.setText(self._text(text_key))
            button.setChecked(self.preferences.language == language)
        for theme_id, (button, label) in ui["theme_cards"].items():
            label.setText(self._text(f"theme_{theme_id}"))
            button.setAccessibleName(label.text())
            button.setChecked(self.preferences.theme == theme_id)

    def _set_preference(self, key: str, value: str):
        old_value = getattr(self.preferences, key)
        if old_value == value:
            return
        setattr(self.preferences, key, value)
        try:
            self.preferences.save()
        except OSError as error:
            setattr(self.preferences, key, old_value)
            self._apply_theme()
            self._apply_language()
            message = self._text("settings_save_error").format(error=error)
            QtWidgets.QMessageBox.warning(self, self._text("settings_title"), message)
            return

        if key == "theme":
            self._apply_theme()
        else:
            self._apply_language()
        self._update_settings_language()

    def _apply_brand_icon(self):
        # Optional icons if exists
        for fname in ("foto.ico", "logos.ico", "root.png"):
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
            if os.path.exists(p):
                try:
                    if fname.endswith('.ico'):
                        self.setWindowIcon(QtGui.QIcon(p))
                    else:
                        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(p)))
                except Exception:
                    pass
                break

    def _build_ui(self):
        cw = QtWidgets.QWidget()
        cw.setObjectName("root")
        self.setCentralWidget(cw)

        layout = QtWidgets.QVBoxLayout(cw)
        layout.setContentsMargins(24, 20, 24, 22)
        layout.setSpacing(16)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(12)
        layout.addLayout(top)

        logo = QtWidgets.QLabel("FORDIO")
        logo.setObjectName("appTitle")
        top.addWidget(logo)
        subtitle = self._register_text(QtWidgets.QLabel(), "subtitle")
        subtitle.setObjectName("mutedLabel")
        top.addWidget(subtitle)
        top.addStretch(1)

        self.settings_button = self._register_text(QtWidgets.QPushButton(), "settings")
        self.settings_button.clicked.connect(self._open_settings)
        top.addWidget(self.settings_button)

        grid = QtWidgets.QHBoxLayout()
        grid.setSpacing(16)
        layout.addLayout(grid, 1)

        lib_box = self._register_text(QtWidgets.QGroupBox(), "library")
        lib_layout = QtWidgets.QVBoxLayout(lib_box)
        lib_layout.setSpacing(10)

        btn_add = self._register_text(QtWidgets.QPushButton(), "add_music")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self._add_music)
        lib_layout.addWidget(btn_add)

        self.searchLibrary = QtWidgets.QLineEdit()
        self.searchLibrary.setPlaceholderText(self._text("search"))
        self.searchLibrary.textChanged.connect(self._filter_library)
        lib_layout.addWidget(self.searchLibrary)
        self._placeholder_widgets.append((self.searchLibrary, "search"))

        self.lblLibraryCount = QtWidgets.QLabel()
        self.lblLibraryCount.setObjectName("libraryCount")
        lib_layout.addWidget(self.lblLibraryCount)

        self.listLibrary = QtWidgets.QListWidget()
        self.listLibrary.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listLibrary.itemDoubleClicked.connect(self._play_selected_as_playlist)
        lib_layout.addWidget(self.listLibrary, 1)

        lib_buttons = QtWidgets.QHBoxLayout()
        lib_layout.addLayout(lib_buttons)

        btn_favorite = self._register_text(QtWidgets.QPushButton(), "favorites")
        btn_favorite.setToolTip(self._text("favorites_tooltip"))
        btn_favorite.clicked.connect(self._toggle_favorite_selected)
        lib_buttons.addWidget(btn_favorite)
        self.favorite_button = btn_favorite

        btn_remove = self._register_text(QtWidgets.QPushButton(), "remove_selected")
        btn_remove.clicked.connect(self._remove_selected)
        lib_buttons.addWidget(btn_remove)

        grid.addWidget(lib_box, 5)

        right = QtWidgets.QVBoxLayout()
        right.setSpacing(14)
        grid.addLayout(right, 7)

        now = self._register_text(QtWidgets.QGroupBox(), "now_playing")
        now_layout = QtWidgets.QVBoxLayout(now)
        now_layout.setSpacing(14)

        track_info = QtWidgets.QHBoxLayout()
        track_info.setSpacing(16)
        self.lblAlbumArt = QtWidgets.QLabel("♫")
        self.lblAlbumArt.setObjectName("albumArt")
        self.lblAlbumArt.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblAlbumArt.setFixedSize(104, 104)
        track_info.addWidget(self.lblAlbumArt)

        track_text = QtWidgets.QVBoxLayout()
        track_text.addStretch(1)
        self.lblNowTitle = QtWidgets.QLabel("—")
        self.lblNowTitle.setObjectName("trackTitle")
        self.lblNowTitle.setWordWrap(True)
        track_text.addWidget(self.lblNowTitle)

        self.lblNowArtist = QtWidgets.QLabel("")
        self.lblNowArtist.setObjectName("trackArtist")
        self.lblNowArtist.setText(self._text("select_track"))
        track_text.addWidget(self.lblNowArtist)
        track_text.addStretch(1)
        track_info.addLayout(track_text, 1)
        now_layout.addLayout(track_info)

        self.visualizer = VisualizerBars(bars=22, segments=8)
        now_layout.addWidget(self.visualizer)

        controls = QtWidgets.QHBoxLayout()
        controls.addStretch(1)
        now_layout.addLayout(controls)

        btn_previous = QtWidgets.QToolButton()
        btn_previous.setText("⏮")
        btn_previous.clicked.connect(self._prev)
        controls.addWidget(btn_previous)

        btn_play = QtWidgets.QToolButton()
        btn_play.setText("▶")
        btn_play.setObjectName("playButton")
        btn_play.clicked.connect(self._toggle_play)
        self.tbPlay = btn_play
        controls.addWidget(btn_play)

        btn_next = QtWidgets.QToolButton()
        btn_next.setText("⏭")
        btn_next.clicked.connect(self._next)
        controls.addWidget(btn_next)
        controls.addStretch(1)

        repeat_controls = QtWidgets.QHBoxLayout()
        repeat_controls.addStretch(1)
        now_layout.addLayout(repeat_controls)

        self.cbLoopOne = self._register_text(QtWidgets.QCheckBox(), "loop_track")
        self.cbLoopOne.stateChanged.connect(self._loop_one_changed)
        repeat_controls.addWidget(self.cbLoopOne)

        self.cbLoopPlaylist = self._register_text(QtWidgets.QCheckBox(), "loop_playlist")
        self.cbLoopPlaylist.stateChanged.connect(self._loop_playlist_changed)
        repeat_controls.addWidget(self.cbLoopPlaylist)
        repeat_controls.addStretch(1)

        timeline = QtWidgets.QVBoxLayout()
        now_layout.addLayout(timeline)

        time_row = QtWidgets.QHBoxLayout()
        timeline.addLayout(time_row)

        self.lblPos = QtWidgets.QLabel("0:00")
        self.lblPos.setObjectName("mutedLabel")
        time_row.addWidget(self.lblPos)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setSingleStep(1000)
        self.slider.sliderPressed.connect(self._seek_start)
        self.slider.sliderReleased.connect(self._seek_end)
        timeline.addWidget(self.slider, 1)

        self.lblDur = QtWidgets.QLabel("0:00")
        self.lblDur.setObjectName("mutedLabel")
        time_row.addWidget(self.lblDur)

        volume_row = QtWidgets.QHBoxLayout()
        timeline.addLayout(volume_row)

        volume_label = self._register_text(QtWidgets.QLabel(), "volume")
        volume_label.setObjectName("mutedLabel")
        volume_row.addWidget(volume_label)

        self.volSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volSlider.setMinimum(0)
        self.volSlider.setMaximum(100)
        self.volSlider.setValue(self.player.volume())
        self.volSlider.valueChanged.connect(self.player.set_volume)
        volume_row.addWidget(self.volSlider, 1)

        try:
            self.player.set_volume(self.volSlider.value())
        except Exception:
            pass

        playlist_box = self._register_text(QtWidgets.QGroupBox(), "playlist")
        playlist_layout = QtWidgets.QVBoxLayout(playlist_box)
        playlist_layout.setSpacing(10)

        self.listPlaylist = QtWidgets.QListWidget()
        self.listPlaylist.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.listPlaylist.itemDoubleClicked.connect(self._play_playlist_item)
        playlist_layout.addWidget(self.listPlaylist, 1)

        playlist_buttons = QtWidgets.QHBoxLayout()
        playlist_layout.addLayout(playlist_buttons)

        btn_add_to_playlist = self._register_text(QtWidgets.QPushButton(), "add_to_playlist")
        btn_add_to_playlist.clicked.connect(self._add_selected_to_playlist)
        playlist_buttons.addWidget(btn_add_to_playlist)

        btn_clear = self._register_text(QtWidgets.QPushButton(), "clear")
        btn_clear.clicked.connect(self._clear_playlist)
        playlist_buttons.addWidget(btn_clear)

        btn_shuffle = self._register_text(QtWidgets.QPushButton(), "shuffle")
        btn_shuffle.clicked.connect(self._shuffle_playlist)
        playlist_buttons.addWidget(btn_shuffle)

        right.addWidget(now, 3)
        right.addWidget(playlist_box, 2)

        self._seek_dragging = False
        self._seek_value = 0

    # ---------- UI actions ----------
    def _add_music(self):
        file_types = "(*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma *.mp4)"
        dlg = QtWidgets.QFileDialog(
            self,
            self._text("choose_music"),
            "",
            f"{self._text('audio_files')} {file_types}",
        )
        dlg.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)
        dlg.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog, True)
        if dlg.exec():
            files = dlg.selectedFiles()
            if not files:
                return
            for f in files:
                try:
                    t = self.library.add_track_from_file(f)
                    self.tracks_by_id[t.id] = t
                except Exception as e:
                    error = str(e)
                    if error.startswith("Unsupported audio format:"):
                        extension = error.partition(":")[2].strip()
                        error = self._text("unsupported_format").format(extension=extension)
                    message = self._text("add_failed").format(name=os.path.basename(f), error=error)
                    QtWidgets.QMessageBox.warning(self, self._text("add_error_title"), message)
            self._refresh_library_list()

    def _remove_selected(self):
        items = self.listLibrary.selectedItems()
        if not items:
            return
        ids = []
        for it in items:
            ids.append(it.data(QtCore.Qt.ItemDataRole.UserRole))
        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle(self._text("remove_title"))
        dialog.setText(self._text("remove_confirm").format(count=len(ids)))
        remove_button = dialog.addButton(
            self._text("yes"),
            QtWidgets.QMessageBox.ButtonRole.AcceptRole,
        )
        dialog.addButton(self._text("no"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        if dialog.clickedButton() != remove_button:
            return

        for tid in ids:
            try:
                self.library.remove_track(tid)
                self.tracks_by_id.pop(tid, None)
            except Exception:
                pass

        # also remove from playlist
        self.playlist_ids = [x for x in self.playlist_ids if x in self.tracks_by_id]
        self._sync_player_from_playlist()
        self._refresh_library_list()
        self._refresh_playlist_list()

    def _toggle_favorite_selected(self):
        items = self.listLibrary.selectedItems()
        if not items:
            return
        for it in items:
            tid = it.data(QtCore.Qt.ItemDataRole.UserRole)
            if tid in self.tracks_by_id:
                new_val = self.library.toggle_favorite(tid)
                self.tracks_by_id[tid].favorite = new_val
        self._refresh_library_list()

    def _refresh_library_list(self, query: str | None = None):
        self.listLibrary.clear()
        if query is None:
            query = self.searchLibrary.text()
        query = query.strip().casefold()
        tracks = sorted(
            self.library.tracks,
            key=lambda t: (0 if t.favorite else 1, -t.added_at),
        )
        for t in tracks:
            searchable = f"{t.title} {t.artist}".casefold()
            if query and query not in searchable:
                continue
            title = t.title
            artist = (t.artist or "").strip()
            if artist:
                text = f"{title} — {artist}"
            else:
                text = title
            if t.favorite:
                text = "★ " + text
            it = QtWidgets.QListWidgetItem(text)
            it.setData(QtCore.Qt.ItemDataRole.UserRole, t.id)
            self.listLibrary.addItem(it)
        self.lblLibraryCount.setText(self._format_track_count(len(self.library.tracks)))

    def _filter_library(self, query: str):
        self._refresh_library_list(query)

    def _refresh_playlist_list(self):
        self.listPlaylist.clear()
        for tid in self.playlist_ids:
            t = self.tracks_by_id.get(tid)
            if not t:
                continue
            artist = (t.artist or "").strip()
            text = f"{t.title}" + (f" — {artist}" if artist else "")
            if t.favorite:
                text = "★ " + text
            it = QtWidgets.QListWidgetItem(text)
            it.setData(QtCore.Qt.ItemDataRole.UserRole, tid)
            self.listPlaylist.addItem(it)

    def _add_selected_to_playlist(self):
        items = self.listLibrary.selectedItems()
        if not items:
            return
        for it in items:
            tid = it.data(QtCore.Qt.ItemDataRole.UserRole)
            if tid in self.tracks_by_id and tid not in self.playlist_ids:
                self.playlist_ids.append(tid)
        self._sync_player_from_playlist()
        self._refresh_playlist_list()

    def _clear_playlist(self):
        self.playlist_ids = []
        self.player.stop()
        self.player.set_playlist([])
        self.player.current_index = -1
        self.lblNowTitle.setText("—")
        self.lblNowArtist.setText(self._text("select_track"))
        self.slider.setValue(0)
        self.lblPos.setText("0:00")
        self.lblDur.setText("0:00")
        self._refresh_playlist_list()

    def _shuffle_playlist(self):
        import random as _random
        _random.shuffle(self.playlist_ids)
        # try to keep current track as start
        current_tid = None
        if 0 <= self.player.current_index < len(self.player.playlist):
            current_tid = self.player.playlist[self.player.current_index]
        self._sync_player_from_playlist(start_tid=current_tid)
        self._refresh_playlist_list()

    # ---------- Player logic ----------
    def _sync_player_from_playlist(self, start_tid: str | None = None):
        # Build playlist from self.playlist_ids
        self.player.loop_one = self.cbLoopOne.isChecked()
        self.player.loop_playlist = self.cbLoopPlaylist.isChecked()

        self.player.set_playlist(self.playlist_ids, start_id=start_tid)
        self.player.load_current(self.tracks_by_id)

    def _play_selected_as_playlist(self, _item: QtWidgets.QListWidgetItem):
        items = self.listLibrary.selectedItems()
        if not items:
            items = [_item]
        ids = []
        for it in items:
            tid = it.data(QtCore.Qt.ItemDataRole.UserRole)
            ids.append(tid)


        # Unique keep order
        seen = set()
        ids2 = []
        for tid in ids:
            if tid in self.tracks_by_id and tid not in seen:
                seen.add(tid)
                ids2.append(tid)

        self.playlist_ids = ids2
        self._sync_player_from_playlist(start_tid=ids2[0] if ids2 else None)
        self._refresh_playlist_list()
        self.player.play()

    def _play_playlist_item(self, it: QtWidgets.QListWidgetItem):
        tid = it.data(QtCore.Qt.ItemDataRole.UserRole)
        if not tid:
            return
        if tid not in self.playlist_ids:
            return
        self._sync_player_from_playlist(start_tid=tid)
        # After setting start index, play
        self.player.play()

    def _on_track_changed(self, tid: str):
        t = self.tracks_by_id.get(tid)
        if not t:
            self.lblNowTitle.setText("—")
            self.lblNowArtist.setText(self._text("select_track"))
            return
        self.lblNowTitle.setText(t.title)
        self.lblNowArtist.setText(t.artist or self._text("unknown_artist"))
        # update selection in playlist
        self._select_playlist_track(tid)
        self.slider.setValue(0)
        self.lblPos.setText("0:00")

    def _select_playlist_track(self, tid: str):
        for i in range(self.listPlaylist.count()):
            it = self.listPlaylist.item(i)
            if it.data(QtCore.Qt.ItemDataRole.UserRole) == tid:
                self.listPlaylist.setCurrentRow(i)
                break

    def _toggle_play(self):
        st = self.player.state()
        if st == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_position(self, ms: int):
        if self._seek_dragging:
            return
        self.slider.setValue(ms)
        self.lblPos.setText(fmt_time(ms))

    def _on_duration(self, ms: int):
        if ms <= 0:
            self.lblDur.setText("0:00")
            self.slider.setMaximum(0)
            return
        self.lblDur.setText(fmt_time(ms))
        self.slider.setMaximum(ms)

    def _on_ended(self):
        # loop one
        if self.cbLoopOne.isChecked() and self.player.playlist:
            self.player.seek(0)
            self.player.play()
            return
        # next track
        if self.player.playlist:
            self.player.next(self.tracks_by_id, auto_play=True)

    def _on_error(self, err: str):
        QtWidgets.QMessageBox.warning(self, self._text("player_error"), err)

    def _prev(self):
        self.player.previous(self.tracks_by_id, auto_play=True)

    def _next(self):
        self.player.next(self.tracks_by_id, auto_play=True)

    def _seek_start(self):
        self._seek_dragging = True

    def _seek_end(self):
        self._seek_dragging = False
        val = self.slider.value()
        self.player.seek(val)

    def _loop_one_changed(self, _state: int):
        self.player.loop_one = self.cbLoopOne.isChecked()

    def _loop_playlist_changed(self, _state: int):
        self.player.loop_playlist = self.cbLoopPlaylist.isChecked()

    def _on_state_changed(self, state: object):
        playing = state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
        self._playing = playing
        self.visualizer.set_playing(playing)
        self.tbPlay.setText("Ⅱ" if playing else "▶")

    def _tick_playing_animation(self):
        state = self.player.state()
        playing = state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
        if playing != self._playing:
            self._on_state_changed(state)
        self.visualizer.tick()

    # Qt HighDPI
    # Некоторые версии PyQt6/Qt могут не иметь этих enum-значений
    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass



def main():
    # Qt HighDPI
    # Некоторые версии PyQt6/Qt могут не иметь этих enum-значений
    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        settings = AppSettings()
        language = settings.language
        title = TEXTS[language]["crash_title"]
        message = TEXTS[language]["crash_message"].format(error=traceback.format_exc())
        QtWidgets.QMessageBox.critical(None, title, message)
