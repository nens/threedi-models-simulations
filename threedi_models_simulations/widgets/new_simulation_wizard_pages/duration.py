from datetime import datetime

from dateutil.relativedelta import relativedelta
from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import QDate, QDateTime, QSettings, QTime, QTimeZone
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from threedi_models_simulations.widgets.new_simulation_wizard_pages.wizard_page import (
    WizardPage,
)


class DurationPage(WizardPage):
    UTC_DISPLAY_NAME = "UTC"
    NO_TIMEZONE_DISPLAY_NAME = "No time zone selected"

    def __init__(self, parent, new_sim):
        super().__init__(parent, show_steps=True)
        self.setTitle("Duration")
        self.setSubTitle(
            r'You can find more information about setting durations in the <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a>.'
        )
        self.new_sim = new_sim

        main_widget = self.get_page_widget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        duration_widget = QWidget(main_widget)
        duration_widget_layout = QGridLayout()
        duration_widget.setLayout(duration_widget_layout)
        duration_widget_layout.setContentsMargins(0, 0, 0, 0)

        duration_widget_layout.addWidget(QLabel("From", duration_widget), 0, 0, 1, 2)
        duration_widget_layout.addWidget(QLabel("To", duration_widget), 0, 2, 1, 2)

        self.from_de = QDateEdit(duration_widget)
        self.from_de.setCalendarPopup(True)
        self.from_de.setDisplayFormat("MMMM d, yyyy")
        self.from_te = QTimeEdit(duration_widget)
        self.from_te.setDisplayFormat("HH:mm")
        duration_widget_layout.addWidget(self.from_de, 1, 0)
        duration_widget_layout.addWidget(self.from_te, 1, 1)

        self.to_de = QDateEdit(duration_widget)
        self.to_de.setCalendarPopup(True)
        self.to_de.setDisplayFormat("MMMM d, yyyy")
        self.to_te = QTimeEdit(duration_widget)
        self.to_te.setDisplayFormat("HH:mm")
        duration_widget_layout.addWidget(self.to_de, 1, 2)
        duration_widget_layout.addWidget(self.to_te, 1, 3)

        self.from_de.dateTimeChanged.connect(self.update_time_difference)
        self.from_te.dateTimeChanged.connect(self.update_time_difference)
        self.to_de.dateTimeChanged.connect(self.update_time_difference)
        self.to_te.dateTimeChanged.connect(self.update_time_difference)

        layout.addWidget(duration_widget)

        layout.addWidget(QLabel("Total simulation time", main_widget))
        self.total_simulation_time = QLabel("", main_widget)
        layout.addWidget(self.total_simulation_time)

        time_zone_gb = QGroupBox("Time zone", main_widget)
        time_zone_layout = QVBoxLayout()
        time_zone_gb.setLayout(time_zone_layout)
        time_zone_text = QLabel(
            r'The time zone parameter is optional. See the <a href="https://docs.3di.live/i_running_a_simulation.html#starting-a-simulation/">documentation</a> for details on when specifying a time zone is relevant.',
            main_widget,
        )
        time_zone_text.setWordWrap(True)
        time_zone_layout.addWidget(time_zone_text)
        self.time_zone_cb = QComboBox(main_widget)
        self.time_zone_cb.currentTextChanged.connect(self.on_timezone_change)
        time_zone_layout.addWidget(self.time_zone_cb)
        self.label_utc_info = QLabel("", main_widget)
        self.label_utc_info.setWordWrap(True)
        time_zone_layout.addWidget(self.label_utc_info)

        layout.addWidget(time_zone_gb)

        self.setup_timezones()

        layout.addStretch()

    def initializePage(self):
        # Fill the page with the current model, this is in UTC
        start_datetime = self.new_sim.simulation.start_datetime.strftime(
            "%Y-%m-%dT%H:%M"
        )
        end_datetime = self.new_sim.simulation.end_datetime.strftime("%Y-%m-%dT%H:%M")
        start_date, start_time = start_datetime.split("T")
        end_date, end_time = end_datetime.split("T")
        self.from_de.setDate(QDate.fromString(start_date))
        self.from_te.setTime(QTime.fromString(start_time))
        self.to_de.setDate(QDate.fromString(end_date))
        self.to_te.setTime(QTime.fromString(end_time))
        self.time_zone_cb.setCurrentText(self.NO_TIMEZONE_DISPLAY_NAME)

        self.update_time_difference()

        return

    def validatePage(self):
        # when the user clicks Next or Finish to perform some last-minute validation. If it returns true, the next page is shown (or the wizard finishes); otherwise, the current page stays up.
        # to_datetime() converts to UTC
        start, end = self.to_datetime()
        self.new_sim.simulation.start_datetime = start
        self.new_sim.simulation.end_datetime = end
        QgsMessageLog.logMessage(
            str(self.new_sim.simulation.start_datetime), level=Qgis.Critical
        )
        QgsMessageLog.logMessage(
            str(self.new_sim.simulation.end_datetime), level=Qgis.Critical
        )
        return True

    def isComplete(self):
        # We also need to emit the QWizardPage::completeChanged() signal every time isComplete() may potentially return a different value,
        # so that the wizard knows that it must refresh the Next button.
        if self.calculate_simulation_duration() == 0.0:
            return False
        return True

    def setup_timezones(self):
        """Populate timezones."""
        self.time_zone_cb.addItem(self.NO_TIMEZONE_DISPLAY_NAME)

        default_timezone = QSettings().value("threedi/timezone", self.UTC_DISPLAY_NAME)
        for timezone_id in QTimeZone.availableTimeZoneIds():
            timezone_text = timezone_id.data().decode()
            timezone = QTimeZone(timezone_id)
            self.time_zone_cb.addItem(timezone_text, timezone)
        self.time_zone_cb.setCurrentText(default_timezone)
        self.on_timezone_change(default_timezone)

    def to_datetime(self):
        """Method for QDateTime ==> datetime conversion."""
        date_from = self.from_de.date()
        time_from = self.from_te.time()
        date_to = self.to_de.date()
        time_to = self.to_te.time()
        if self.time_zone_cb.currentText() not in (
            self.UTC_DISPLAY_NAME,
            self.NO_TIMEZONE_DISPLAY_NAME,
        ):
            current_timezone = self.time_zone_cb.currentData()
            datetime_from = QDateTime(date_from, time_from, current_timezone)
            datetime_to = QDateTime(date_to, time_to, current_timezone)
            datetime_from_utc = datetime_from.toUTC()
            datetime_to_utc = datetime_to.toUTC()
            date_from, time_from = datetime_from_utc.date(), datetime_from_utc.time()
            date_to, time_to = datetime_to_utc.date(), datetime_to_utc.time()
        date_from_str = date_from.toString("yyyy-MM-dd")
        time_from_str = time_from.toString("H:m")
        date_to_str = date_to.toString("yyyy-MM-dd")
        time_to_str = time_to.toString("H:m")
        start = datetime.strptime(f"{date_from_str} {time_from_str}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{date_to_str} {time_to_str}", "%Y-%m-%d %H:%M")
        return start, end

    def calculate_simulation_duration(self):
        """Method for simulation duration calculations."""
        try:
            start, end = self.to_datetime()
            if start > end:
                start = end
            delta = end - start
            delta_in_seconds = delta.total_seconds()
            if delta_in_seconds < 0:
                delta_in_seconds = 0.0
            return delta_in_seconds
        except ValueError:
            return 0.0

    def update_time_difference(self):
        """Updating label with simulation duration showed in the human-readable format."""
        timezone_template = r'<html><head/><body><p><span style=" color:#ff5500;">Simulation start date and time will be converted to Coordinated Universal Time (UTC)<br/></span><span style=" color:#000000;">Simulation start in UTC: {}<br/>Simulation end in UTC: {}</span></p></body></html>'

        try:
            start, end = self.to_datetime()
            if start > end:
                start = end
            rel_delta = relativedelta(end, start)
            duration = (
                rel_delta.years,
                rel_delta.months,
                rel_delta.days,
                rel_delta.hours,
                rel_delta.minutes,
            )
            self.total_simulation_time.setText(
                "{} years, {} months, {} days, {} hours, {} minutes".format(*duration)
            )
            self.label_utc_info.setText(timezone_template.format(start, end))
        except ValueError:
            self.total_simulation_time.setText("Invalid datetime format!")

        self.completeChanged.emit()

    def on_timezone_change(self, timezone_id_str):
        """Method for handling timezone change."""
        self.update_time_difference()
        if timezone_id_str in (self.UTC_DISPLAY_NAME, self.NO_TIMEZONE_DISPLAY_NAME):
            self.label_utc_info.hide()
        else:
            self.label_utc_info.show()

        QSettings().setValue("threedi/timezone", timezone_id_str)
