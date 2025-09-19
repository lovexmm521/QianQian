# timer_engine.py
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from enum import Enum, auto


class TimerState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class PomodoroPhase(Enum):
    WORK = auto()
    BREAK = auto()
    LONG_BREAK = auto()


class TimerEngine(QObject):
    time_updated = pyqtSignal(str)
    phase_finished = pyqtSignal(PomodoroPhase)
    cycle_finished = pyqtSignal()
    state_changed = pyqtSignal(TimerState)
    # **新增**: 当计时器启动时发出此信号
    timer_started = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._work_duration_sec = 25 * 60
        self._break_duration_sec = 5 * 60
        self._long_break_duration_sec = 15 * 60
        self._pomodoros_per_cycle = 4

        self._pomodoros_completed = 0
        self._remaining_sec = self._work_duration_sec
        self._state = TimerState.STOPPED
        self._phase = PomodoroPhase.WORK

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        if self._remaining_sec > 0:
            self._remaining_sec -= 1
            self.time_updated.emit(self.get_formatted_time())
        else:
            self._timer.stop()
            current_phase = self._phase

            if current_phase == PomodoroPhase.WORK:
                self._pomodoros_completed += 1

            if current_phase == PomodoroPhase.LONG_BREAK:
                self.cycle_finished.emit()
                self.reset_timer()
            else:
                self._switch_phase()
                self.set_state(TimerState.STOPPED)
                self.phase_finished.emit(current_phase)

    def _switch_phase(self):
        if self._phase == PomodoroPhase.WORK:
            if self._pomodoros_completed >= self._pomodoros_per_cycle:
                self._phase = PomodoroPhase.LONG_BREAK
                self._remaining_sec = self._long_break_duration_sec
            else:
                self._phase = PomodoroPhase.BREAK
                self._remaining_sec = self._break_duration_sec
        else:
            self._phase = PomodoroPhase.WORK
            self._remaining_sec = self._work_duration_sec

        self.time_updated.emit(self.get_formatted_time())

    def start_timer(self):
        """开始或从暂停恢复计时。"""
        if self._state != TimerState.RUNNING:
            self._timer.start()
            self.set_state(TimerState.RUNNING)
            # **新增**: 发出计时器已启动的信号
            self.timer_started.emit()

    def pause_timer(self):
        if self._state == TimerState.RUNNING:
            self._timer.stop()
            self.set_state(TimerState.PAUSED)

    def reset_timer(self):
        self._timer.stop()
        self._pomodoros_completed = 0
        self._phase = PomodoroPhase.WORK
        self._remaining_sec = self._work_duration_sec
        self.set_state(TimerState.STOPPED)
        self.time_updated.emit(self.get_formatted_time())

    def set_durations(self, work_mins, break_mins, long_break_mins, pomos_per_cycle, is_debug=False):
        self._pomodoros_per_cycle = pomos_per_cycle

        if is_debug:
            self._work_duration_sec = 1
            self._break_duration_sec = 1
            self._long_break_duration_sec = 1
        else:
            self._work_duration_sec = work_mins * 60
            self._break_duration_sec = break_mins * 60
            self._long_break_duration_sec = long_break_mins * 60

        if self._state == TimerState.STOPPED:
            self.reset_timer()

    def get_formatted_time(self):
        minutes = self._remaining_sec // 60
        seconds = self._remaining_sec % 60
        return f"{minutes:02d}:{seconds:02d}"

    def set_state(self, new_state):
        if self._state != new_state:
            self._state = new_state
            self.state_changed.emit(new_state)

    @property
    def state(self):
        return self._state

    @property
    def phase(self):
        return self._phase
