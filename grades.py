import csv
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


f"Grade Editor\nElad Sasson\nGitHub: https://github.com/eladsasson1/grade-editor",


class GradesWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Grade Editor")
        self.resize(780, 570)

        self.student_ids = []
        self.original_grades = []
        self.corrected_grades = []
        self.selected_file = ""
        self.headers = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Grade Editor", objectName="title"))

        controls = QHBoxLayout()
        layout.addLayout(controls)

        open_button = QPushButton("Open grades file")
        open_button.clicked.connect(self.choose_file)
        controls.addWidget(open_button)

        controls.addWidget(QLabel("Bonus points:"))

        self.bonus_input = QLineEdit("0")
        self.bonus_input.setValidator(QIntValidator(0, 2147483647, self))
        self.bonus_input.setMaximumWidth(85)
        self.bonus_input.setToolTip("Enter bonus points and press Enter")
        self.bonus_input.returnPressed.connect(self.apply_bonus)
        controls.addWidget(self.bonus_input)

        self.update_button = QPushButton("Update File")
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_file)
        controls.addWidget(self.update_button)

        controls.addStretch()

        about_button = QPushButton("About")
        about_button.clicked.connect(self.show_about)
        controls.addWidget(about_button)

        self.file_label = QLabel("Select grades.csv to begin.")
        layout.addWidget(self.file_label)

        self.table = QTableWidget(50, 3)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Original Grades", "Corrected Grades"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select grades file", "", "CSV files (*.csv)"
        )
        if not path:
            return

        student_ids = []
        original_grades = []

        try:
            with open(path, encoding="utf-8-sig", newline="") as file:
                reader = csv.reader(file)
                headers = next(reader, None)

                if headers is None or len(headers) != 2:
                    raise ValueError("Expected a CSV file with two columns: ID,Grade.")

                for row in reader:
                    if not row:
                        continue

                    student_id, grade_text = row
                    grade = float(grade_text)

                    # הצגת ציון שלם כ-90 במקום 90.0
                    if grade.is_integer():
                        grade = int(grade)

                    student_ids.append(student_id)
                    original_grades.append(grade)

                if len(student_ids) > 50:
                    raise ValueError("The assignment table supports up to 50 students.")

        except (OSError, ValueError, csv.Error) as error:
            QMessageBox.warning(self, "Could not load grades", str(error))
            return

        self.selected_file = path
        self.headers = headers
        self.student_ids = student_ids
        self.original_grades = original_grades
        self.corrected_grades = original_grades.copy()

        self.bonus_input.setText("0")
        self.update_button.setEnabled(bool(student_ids))
        self.file_label.setText(f"{Path(path).name} — {len(student_ids)} students")
        self.refresh_table()

    def refresh_table(self):
        self.table.clearContents()

        for row, student_id in enumerate(self.student_ids):
            values = (
                student_id,
                self.original_grades[row],
                self.corrected_grades[row],
            )

            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def apply_bonus(self):
        if not self.original_grades:
            QMessageBox.information(self, "Bonus", "Please load a grades file first.")
            return

        if not self.bonus_input.hasAcceptableInput():
            return

        bonus = int(self.bonus_input.text())

        for index, original_grade in enumerate(self.original_grades):
            self.corrected_grades[index] = min(100, original_grade + bonus)

        self.refresh_table()
        self.file_label.setText(
            f"{Path(self.selected_file).name} — bonus applied: {bonus}"
        )

    def update_file(self):
        if not self.selected_file or not self.corrected_grades:
            return

        path = Path(self.selected_file)

        try:
            # שומרים על סוג קידוד ה-UTF-8 של הקובץ המקורי
            with path.open("rb") as source:
                has_bom = source.read(3) == b"\xef\xbb\xbf"

            encoding = "utf-8-sig" if has_bom else "utf-8"

            with path.open("w", encoding=encoding, newline="") as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)
                writer.writerows(zip(self.student_ids, self.corrected_grades))

        except (OSError, csv.Error) as error:
            QMessageBox.warning(self, "Could not save grades", str(error))
            return

        self.file_label.setText(f"Saved: {path.name}")
        self.open_updated_file()

    def open_updated_file(self):
        file_url = QUrl.fromLocalFile(self.selected_file)

        if not QDesktopServices.openUrl(file_url):
            QMessageBox.information(
                self,
                "File saved",
                f"Open the saved file here:\n{self.selected_file}",
            )

    def show_about(self):
        QMessageBox.about(
            self,
            "About Grade Editor",
            f"Grade Editor\nElad Sasson\nGitHub: {REPOSITORY}",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    style_path = Path(__file__).with_name("style.qss")
    app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    window = GradesWindow()
    window.show()
    sys.exit(app.exec())