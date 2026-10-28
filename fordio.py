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
    stateChanged = QtCore.pyqtSignal(int)

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
    """LED-эквалайзер: каждая полоска состоит из светящихся сегментов
    (как на классическом hi-fi индикаторе уровня).

    Каждая полоска двигается независимо и случайно, но только во время
    воспроизведения. На паузе/стопе все полоски плавно "гаснут" сверху вниз.
    Это имитация (без реального FFT-анализа звука).
    """

    def __init__(self, bars: int = 24, segments: int = 10, parent=None):
        super().__init__(parent)
        self.bars_count = max(4, bars)
        self.segments = max(3, segments)

        self.levels = [0.0 for _ in range(self.bars_count)]
        self.targets = [0.0 for _ in range(self.bars_count)]

        self._playing = False
        self._hue = 0.0

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setMinimumHeight(90)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )

    def set_playing(self, playing: bool):
        self._playing = bool(playing)
        if not self._playing:
            # При остановке все полоски стремятся в "0" (гаснут)
            self.targets = [0.0 for _ in range(self.bars_count)]

    def tick(self, hue_deg: float):
        self._hue = hue_deg % 360.0

        if self._playing:
            for i in range(self.bars_count):
                # с некоторой вероятностью (или когда почти достигли цели)
                # выбираем новую случайную "цель" — каждая полоска живёт
                # своей жизнью и движется независимо
                if random.random() < 0.18 or abs(self.levels[i] - self.targets[i]) < 0.02:
                    self.targets[i] = random.uniform(0.12, 1.0)
                self.levels[i] += (self.targets[i] - self.levels[i]) * 0.35
        else:
            # плавное затухание до нуля (полоски "гаснут")
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

        off_color = QtGui.QColor(255, 255, 255, 18)
        p.setPen(QtCore.Qt.PenStyle.NoPen)

        for i, level in enumerate(self.levels):
            level = max(0.0, min(1.0, level))
            lit = int(round(level * segs))

            hue = (self._hue + i * (360.0 / n)) % 360.0
            on_color = QtGui.QColor.fromHsvF(hue / 360.0, 0.85, 1.0)

            x = i * (bar_w + gap)

            for s in range(segs):
                # сегмент 0 — самый нижний
                y = h - (s + 1) * seg_h - s * seg_gap
                rect = QtCore.QRectF(x, y, bar_w, seg_h)

                if s < lit:
                    p.setBrush(on_color)
                else:
                    p.setBrush(off_color)

                p.drawRoundedRect(rect, 2.0, 2.0)

        p.end()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self._timeDot = None

        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 650)

        self.library = Library()
        self.tracks_by_id = {t.id: t for t in self.library.tracks}

        self.player = Player()
        self.player.ended.connect(self._on_ended)
        self.player.trackChanged.connect(self._on_track_changed)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.errorOccured.connect(self._on_error)
        self.player.stateChanged.connect(self._on_state_changed)

        # Playlist ids for UI
        self.playlist_ids: list[str] = []

        self._build_ui()
        self._refresh_library_list()
        self._sync_player_from_playlist()
        self._apply_brand_icon()

        # ---- playing animations ----
        self._animTimer = QtCore.QTimer(self)
        self._animTimer.setInterval(30)
        self._animTimer.timeout.connect(self._tick_playing_animation)
        self._animPhase = 0.0
        self._playing = False

        # Таймер анимации работает постоянно: он отвечает и за переливающееся
        # неоновое свечение во время игры, и за плавное "затухание" эквалайзера
        # и подсветки, когда музыка на паузе/остановлена.
        self._animTimer.start()

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
        self.setCentralWidget(cw)

        # ---------- Styles ----------
        # Simple but good looking glass UI
        self.setStyleSheet(
            """
            QWidget{font-family:Segoe UI, Arial;}
            QMainWindow{background:transparent;}
            .bg{
              background: radial-gradient(circle at 15% 10%, rgba(255,79,216,.30), transparent 45%),
                          radial-gradient(circle at 80% 30%, rgba(59,224,255,.25), transparent 50%),
                          radial-gradient(circle at 55% 95%, rgba(139,92,246,.18), transparent 55%),
                          linear-gradient(180deg, #070717, #050513);
            }
            QGroupBox{border:1px solid rgba(255,255,255,.14); border-radius:16px; margin-top:8px;}
            QGroupBox::title{color:rgba(255,255,255,.85); padding:0 10px;}

            QListWidget{
              background: rgba(255,255,255,.05);
              border:1px solid rgba(255,255,255,.10);
              border-radius:14px;
              color: rgba(255,255,255,.92);
            }
            QListWidget::item{
              padding:8px 10px;
              border-bottom:1px solid rgba(255,255,255,.06);
            }
            QListWidget::item:selected{
              background: rgba(59,224,255,.18);
              border-left:3px solid rgba(59,224,255,.85);
            }

            QPushButton{
              background: rgba(255,255,255,.06);
              border:1px solid rgba(255,255,255,.14);
              color: rgba(255,255,255,.92);
              border-radius:14px;
              padding:10px 12px;
              font-weight:700;
            }
            QPushButton:hover{background: rgba(255,255,255,.10);}
            QPushButton:pressed{transform: translateY(1px);}

            QSlider{background:transparent;}
            QSlider::groove:horizontal{height:6px; background: rgba(255,255,255,.10); border-radius:4px;}
            QSlider::handle:horizontal{width:16px; height:16px; margin:-5px 0; background: #FF4FD8; border:2px solid #3BE0FF; border-radius:8px;}

            QCheckBox{color: rgba(255,255,255,.85);}
            QCheckBox::indicator{width:18px; height:18px;}
            QLineEdit{
              background: rgba(255,255,255,.06);
              border:1px solid rgba(255,255,255,.14);
              border-radius:12px;
              padding:9px 10px;
              color: rgba(255,255,255,.92);
            }
            QLabel{color: rgba(255,255,255,.92);} 

            /* Blue FORDIO title */
            QLabel#appTitle{color:#3BE0FF;}


            .title{
              font-size:20px;
              font-weight:900;
              letter-spacing:.3px;
              background: linear-gradient(90deg, #3BE0FF, #FF4FD8, #8B5CF6);
              -webkit-background-clip:text;
              background-clip:text;
              color:transparent;
            }

            QToolButton{
              background: rgba(255,255,255,.06);
              border:1px solid rgba(255,255,255,.14);
              border-radius:14px;
              color: rgba(255,255,255,.92);
              padding:10px;
              font-weight:800;
            }
            QToolButton:hover{background: rgba(255,255,255,.10);} 

            .now{
              background: rgba(0,0,0,.18);
              border:1px solid rgba(255,255,255,.10);
              border-radius:16px;
              padding:12px;
            }

            .small{color: rgba(255,255,255,.65);} 

            
            /* --- Playing animations --- */
            QWidget#nowGlow{
              background: rgba(0,0,0,.22);
              border:1px solid rgba(255,255,255,.10);
              border-radius:16px;
            }
            QWidget#nowGlow[playing="true"]{
              background: rgba(0,0,0,.12);
              border:1px solid rgba(59,224,255,.35);
            }
            QWidget#nowNeon{
              background: transparent;
              border-radius:16px;
            }
            """
        )

        root = QtWidgets.QWidget()
        root.setObjectName("root")
        root.setProperty("class", "bg")
        root.setStyleSheet("QWidget#root{background:transparent;}")

        layout = QtWidgets.QVBoxLayout(cw)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Top bar
        top = QtWidgets.QHBoxLayout()
        layout.addLayout(top)




        # Logo/brand: крупнее и “премиальнее”
        titleWrap = QtWidgets.QHBoxLayout()

        logo = QtWidgets.QLabel("FORDIO")
        logo.setObjectName("appTitle")
        logo.setProperty("class", "title")
        logo.setStyleSheet(
            "font-size:26px; padding:10px 14px;"
            "background:rgba(255,255,255,.06);"
            "border:1px solid rgba(59,224,255,.22);"
            "border-radius:16px;"
            "letter-spacing:1px;"
            ""
        )
        titleWrap.addWidget(logo)
        titleWrap.addStretch(1)
        top.addLayout(titleWrap)




        # PRO Plan pill (самый правый верхний угол)
        pro = QtWidgets.QLabel("PRO PLAN")
        pro.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        pro.setFixedHeight(34)
        pro.setStyleSheet(
            "color: rgba(255,255,255,.92);"
            "background: rgba(255,255,255,.05);"
            "border: 1px solid rgba(255,255,255,.16);"
            "border-radius: 14px;"
            "padding: 0 14px;"
            "font-weight: 900;"
            "letter-spacing: .8px;"
        )

        # Чтобы было именно справа: порядок в layout важен.
        # Вставляем ПОСЛЕ logo/названия и не добавляем растяжку после него.
        top.addStretch(1)
        top.addWidget(pro)


        # Main layout

        grid = QtWidgets.QHBoxLayout()
        layout.addLayout(grid, 1)

        # Left: Library
        libBox = QtWidgets.QGroupBox("Библиотека (что сохранено)")
        libLayout = QtWidgets.QVBoxLayout(libBox)

        btnAdd = QtWidgets.QPushButton("Загрузить музыку")
        btnAdd.clicked.connect(self._add_music)
        libLayout.addWidget(btnAdd)

        self.listLibrary = QtWidgets.QListWidget()
        self.listLibrary.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listLibrary.itemDoubleClicked.connect(self._play_selected_as_playlist)
        libLayout.addWidget(self.listLibrary, 1)

        libBtns = QtWidgets.QHBoxLayout()
        libLayout.addLayout(libBtns)

        btnFav = QtWidgets.QPushButton("★ Избранное")
        btnFav.setToolTip("Добавить/убрать выбранные треки из избранного")
        btnFav.clicked.connect(self._toggle_favorite_selected)
        libBtns.addWidget(btnFav)

        btnRemove = QtWidgets.QPushButton("Удалить выбранное")
        btnRemove.clicked.connect(self._remove_selected)
        libBtns.addWidget(btnRemove)

        grid.addWidget(libBox, 1)

        # Right: Player & Playlist
        right = QtWidgets.QVBoxLayout()
        grid.addLayout(right, 1)

        now = QtWidgets.QGroupBox("Сейчас играет")
        nowLayout = QtWidgets.QVBoxLayout(now)

        # animated overlay widgets
        self.nowGlow = QtWidgets.QWidget(now)
        self.nowGlow.setObjectName("nowGlow")
        self.nowGlow.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.nowGlow.setProperty("playing", "false")
        self.nowGlow.setStyleSheet("background: rgba(0,0,0,.22);")
        self.nowGlow.lower()

        self.nowNeon = QtWidgets.QWidget(now)
        self.nowNeon.setObjectName("nowNeon")
        self.nowNeon.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.nowNeon.lower()

        # Update overlays on resize/layout changes
        nowLayout.addWidget(QtWidgets.QWidget())
        nowLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.lblNowTitle = QtWidgets.QLabel("—")
        self.lblNowTitle.setStyleSheet("font-size:16px; font-weight:900;")
        nowLayout.addWidget(self.lblNowTitle)

        self.lblNowArtist = QtWidgets.QLabel("")
        self.lblNowArtist.setProperty("class", "small")
        nowLayout.addWidget(self.lblNowArtist)

        # Визуализатор-эквалайзер: LED-бары "пляшут" во время игры
        self.visualizer = VisualizerBars(bars=24, segments=10)
        nowLayout.addWidget(self.visualizer)

        # Controls row
        ctrlRow = QtWidgets.QHBoxLayout()
        nowLayout.addLayout(ctrlRow)

        tbPrev = QtWidgets.QToolButton()
        tbPrev.setText("⏮")
        tbPrev.clicked.connect(self._prev)
        ctrlRow.addWidget(tbPrev)

        tbPlay = QtWidgets.QToolButton()
        tbPlay.setText("▶")
        tbPlay.clicked.connect(self._toggle_play)
        self.tbPlay = tbPlay
        ctrlRow.addWidget(tbPlay)

        tbNext = QtWidgets.QToolButton()
        tbNext.setText("⏭")
        tbNext.clicked.connect(self._next)
        ctrlRow.addWidget(tbNext)

        # Repeat controls
        repeatRow = QtWidgets.QHBoxLayout()
        nowLayout.addLayout(repeatRow)

        self.cbLoopOne = QtWidgets.QCheckBox("Зациклить трек")
        self.cbLoopOne.stateChanged.connect(self._loop_one_changed)
        repeatRow.addWidget(self.cbLoopOne)

        self.cbLoopPlaylist = QtWidgets.QCheckBox("Зациклить плейлист")
        self.cbLoopPlaylist.stateChanged.connect(self._loop_playlist_changed)
        repeatRow.addWidget(self.cbLoopPlaylist)

        # Timeline
        timeline = QtWidgets.QVBoxLayout()
        nowLayout.addLayout(timeline)

        timeRow = QtWidgets.QHBoxLayout()
        timeline.addLayout(timeRow)

        self.lblPos = QtWidgets.QLabel("0:00")
        self.lblPos.setProperty("class", "small")
        timeRow.addWidget(self.lblPos)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setSingleStep(1000)
        self.slider.sliderPressed.connect(self._seek_start)
        self.slider.sliderReleased.connect(self._seek_end)
        # add visible progress marker
        self.slider.setStyleSheet(
            """
            QSlider::groove:horizontal{height:6px; background: rgba(255,255,255,.10); border-radius:3px;}
            QSlider::handle:horizontal{width:14px; height:14px; margin:-4px 0; background: #3BE0FF; border-radius:7px;}
            QSlider::sub-page:horizontal{background: rgba(59,224,255,.55); border-radius:3px;}
            """
        )
        timeline.addWidget(self.slider, 1)

        # (не трогаем бегущую точку/маркер)
        # это обычный индикатор громкости/прогресса на другом контроле.
        # Здесь оставляем только один draggable marker (у тебя он реализован через QSlider handle).


        self.lblDur = QtWidgets.QLabel("0:00")
        self.lblDur.setProperty("class", "small")
        timeRow.addWidget(self.lblDur)


        # Volume
        volRow = QtWidgets.QHBoxLayout()
        timeline.addLayout(volRow)

        volLbl = QtWidgets.QLabel("Громкость")
        volRow.addWidget(volLbl)

        self.volSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volSlider.setMinimum(0)
        self.volSlider.setMaximum(100)
        self.volSlider.setValue(self.player.volume())
        self.volSlider.valueChanged.connect(self.player.set_volume)


        volRow.addWidget(self.volSlider, 1)

        # Настраиваем громкость: ползунок управляет аудио напрямую.

        
        # Try to apply initial volume after UI is created (some Qt backends apply late).
        try:
            self.player.set_volume(self.volSlider.value())
        except Exception:
            pass

        # визуальная точка — это сам handle QSlider, отдельные QLabel-«точки» больше не используем



        # Playlist box

        plBox = QtWidgets.QGroupBox("Плейлист")
        plLayout = QtWidgets.QVBoxLayout(plBox)

        self.listPlaylist = QtWidgets.QListWidget()
        self.listPlaylist.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.listPlaylist.itemDoubleClicked.connect(self._play_playlist_item)
        plLayout.addWidget(self.listPlaylist, 1)

        plBtns = QtWidgets.QHBoxLayout()
        plLayout.addLayout(plBtns)

        btnAddToPl = QtWidgets.QPushButton("Добавить в плейлист")
        btnAddToPl.clicked.connect(self._add_selected_to_playlist)
        plBtns.addWidget(btnAddToPl)

        btnClear = QtWidgets.QPushButton("Очистить")
        btnClear.clicked.connect(self._clear_playlist)
        plBtns.addWidget(btnClear)

        btnShuffle = QtWidgets.QPushButton("Перемешать")
        btnShuffle.clicked.connect(self._shuffle_playlist)
        plBtns.addWidget(btnShuffle)

        right.addWidget(now, 1)
        right.addWidget(plBox, 2)

        # Set background gradient behind everything
        deco = QtWidgets.QWidget()
        deco.setObjectName("bgWidget")
        deco.setStyleSheet(
            "QWidget#bgWidget{"
            "background: radial-gradient(circle at 15% 10%, rgba(255,79,216,.30), transparent 45%),"
            "radial-gradient(circle at 80% 30%, rgba(59,224,255,.25), transparent 50%),"
            "radial-gradient(circle at 55% 95%, rgba(139,92,246,.18), transparent 55%),"
            "linear-gradient(180deg, #070717, #050513);"
            "}"
        )
        decoLayout = QtWidgets.QVBoxLayout(deco)
        decoLayout.setContentsMargins(0, 0, 0, 0)
        decoLayout.addLayout(layout)

        # Replace root by background widget
        cw.setLayout(QtWidgets.QVBoxLayout())
        cw.layout().setContentsMargins(0, 0, 0, 0)
        cw.layout().addWidget(deco)

        # store references to avoid GC
        self._btnAdd = btnAdd
        self._btnRemove = btnRemove
        self._btnFav = btnFav
        self._seek_dragging = False
        self._seek_value = 0

    # ---------- UI actions ----------
    def _add_music(self):
        dlg = QtWidgets.QFileDialog(self, "Выберите музыку", "", "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma *.mp4)")
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
                    QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось добавить: {os.path.basename(f)}\n\n{e}")
            self._refresh_library_list()

    def _remove_selected(self):
        items = self.listLibrary.selectedItems()
        if not items:
            return
        ids = []
        for it in items:
            ids.append(it.data(QtCore.Qt.ItemDataRole.UserRole))
        res = QtWidgets.QMessageBox.question(self, "Удаление", f"Удалить выбранных треков: {len(ids)}?", QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if res != QtWidgets.QMessageBox.StandardButton.Yes:
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

    def _refresh_library_list(self):
        self.listLibrary.clear()
        # Избранные треки — наверху, дальше по дате добавления (новые сверху)
        tracks = sorted(
            self.library.tracks,
            key=lambda t: (0 if t.favorite else 1, -t.added_at),
        )
        for t in tracks:
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
        self.lblNowArtist.setText("")
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
            self.lblNowArtist.setText("")
            return
        self.lblNowTitle.setText(t.title)
        self.lblNowArtist.setText(t.artist or "")
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
        # slider range in milliseconds
        self.slider.setMaximum(ms)
        # keep dot/marker updated
        if hasattr(self, "_timeDot") and self.slider.maximum() > 0:
            self._update_time_dot(self.slider.value())

    def _update_time_dot(self, ms: int) -> None:
        """Move the blue dot to reflect current slider position (time)."""
        if not getattr(self, "_timeDot", None):
            return

    def _update_vol_dot_from_slider_value(self, vol: int) -> None:
        """Move volume dot to match current volSlider value."""
        if not getattr(self, "_volDot", None):
            return
        if not getattr(self, "volSlider", None):
            return
        if self.volSlider.maximum() <= 0:
            self._volDot.hide()
            return

        # Convert value -> position in slider coordinates.
        # Use QStyle machinery to get correct groove/handle geometry.
        opt = QtWidgets.QStyleOptionSlider()
        self.volSlider.initStyleOption(opt)
        groove_rect = opt.rect

        # Avoid division by zero.
        maxv = float(self.volSlider.maximum() - self.volSlider.minimum())
        if maxv <= 0:
            self._volDot.hide()
            return

        v = float(vol - self.volSlider.minimum())
        ratio = max(0.0, min(1.0, v / maxv))

        # For a horizontal slider, handle center moves along groove rect.
        x = groove_rect.left() + int(ratio * groove_rect.width())
        center_y = groove_rect.top() + groove_rect.height() // 2

        # _volDot lives in the same parent as the slider (volRow inside nowLayout).
        parent = self._volDot.parentWidget()
        if parent is None:
            return

        # Convert slider-local -> parent-local.
        p = self.volSlider.mapTo(parent, QtCore.QPoint(x, center_y))
        self._volDot.move(int(p.x() - self._volDot.width() // 2), int(p.y() - self._volDot.height() // 2))
        self._volDot.show()

    def _vol_x_to_value(self, x_in_slider: int) -> int:
        """Map an x coordinate (in slider widget coordinates) to slider value."""
        if self.volSlider.maximum() <= self.volSlider.minimum():
            return self.volSlider.minimum()

        opt = QtWidgets.QStyleOptionSlider()
        self.volSlider.initStyleOption(opt)
        groove_rect = opt.rect

        x_clamped = max(groove_rect.left(), min(groove_rect.right(), x_in_slider))
        ratio = (x_clamped - groove_rect.left()) / float(groove_rect.width()) if groove_rect.width() > 0 else 0.0

        val = self.volSlider.minimum() + ratio * (self.volSlider.maximum() - self.volSlider.minimum())
        return int(val + 0.5)

    def _vol_dot_mouse_press_event(self, ev):
        if not self.volSlider.maximum():
            return
        self._volDot_dragging = True
        self._volDot_last_x = ev.position().x() if hasattr(ev, 'position') else ev.x()
        ev.accept()

    def _vol_dot_mouse_move_event(self, ev):
        if not getattr(self, "_volDot_dragging", False):
            return
        # Convert global/mouse position -> slider local x.
        pos = ev.globalPosition().toPoint() if hasattr(ev, 'globalPosition') else ev.globalPos()
        slider_pos = self.volSlider.mapFromGlobal(pos)
        new_val = self._vol_x_to_value(slider_pos.x())
        self.volSlider.setValue(new_val)  # triggers audio change and dot sync
        ev.accept()

    def _vol_dot_mouse_release_event(self, ev):
        self._volDot_dragging = False
        ev.accept()



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
        QtWidgets.QMessageBox.warning(self, "Ошибка плеера", err)

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

    def _on_state_changed(self, state: int):
        playing = state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
        self._playing = playing

        # Сообщаем эквалайзеру, играет ли музыка — он сам решит,
        # "скакать" по таргетам или плавно опуститься к базовой линии.
        if hasattr(self, "visualizer") and self.visualizer is not None:
            self.visualizer.set_playing(playing)

        if playing:
            self._animPhase = 0.0
            if hasattr(self, "nowGlow") and self.nowGlow is not None:
                self.nowGlow.setProperty("playing", "true")
                self.nowGlow.style().unpolish(self.nowGlow)
                self.nowGlow.style().polish(self.nowGlow)
        else:
            if hasattr(self, "nowGlow") and self.nowGlow is not None:
                self.nowGlow.setProperty("playing", "false")
                self.nowGlow.style().unpolish(self.nowGlow)
                self.nowGlow.style().polish(self.nowGlow)
            if hasattr(self, "nowNeon") and self.nowNeon is not None:
                self.nowNeon.setStyleSheet(
                    "border:1px solid rgba(255,255,255,.0); border-radius:16px; background: transparent;"
                )

    def _tick_playing_animation(self):
        # Эта функция теперь работает постоянно (таймер не останавливается),
        # чтобы эквалайзер мог плавно "затухать", а не выключаться резко.
        self._animPhase += 0.06

        # Бегущий цвет (hue) для радужного неонового переливания.
        hue = (self._animPhase * 22.0) % 360.0

        if hasattr(self, "visualizer") and self.visualizer is not None:
            self.visualizer.tick(hue)

        if not self._playing:
            # глоу постепенно гасится через QSS-свойство [playing="false"],
            # а нео-обводку просто держим прозрачной
            if hasattr(self, "nowGlow") and self.nowGlow is not None:
                self.nowGlow.setGeometry(self.nowGlow.parentWidget().rect())
            return

        a = (QtCore.qSin(self._animPhase) + 1.0) / 2.0  # 0..1

        # Переливающееся неоновое свечение: цвет рамки бежит по кругу HSV.
        if hasattr(self, "nowGlow") and self.nowGlow is not None:
            alpha = 0.10 + 0.16 * a
            glow_color = QtGui.QColor.fromHsvF(hue / 360.0, 0.65, 1.0)
            r, g, b, _ = glow_color.getRgb()
            border_alpha = 0.20 + 0.35 * a
            self.nowGlow.setStyleSheet(
                f"background: rgba(0,0,0,{alpha:.3f});"
                f"border:2px solid rgba({r},{g},{b},{border_alpha:.3f});"
                "border-radius:16px;"
            )
            # keep overlay covering groupbox
            self.nowGlow.setGeometry(self.nowGlow.parentWidget().rect())

        if hasattr(self, "nowNeon") and self.nowNeon is not None:
            # вторая, смещённая по фазе неоновая полоса — для эффекта переливания
            hue2 = (hue + 90.0) % 360.0
            neon_color = QtGui.QColor.fromHsvF(hue2 / 360.0, 0.95, 1.0)
            r2, g2, b2, _ = neon_color.getRgb()
            alpha2 = 0.25 + 0.30 * (0.5 + 0.5 * QtCore.qCos(self._animPhase * 1.3))
            # keep geometry
            self.nowNeon.setGeometry(self.nowNeon.parentWidget().rect())
            self.nowNeon.setStyleSheet(
                f"border:2px solid rgba({r2},{g2},{b2},{alpha2:.3f}); border-radius:16px; background: transparent;"
            )

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
        QtWidgets.QMessageBox.critical(None, "Fordio crashed", "Ошибка: не удалось запустить программу.\n\n" + traceback.format_exc())
