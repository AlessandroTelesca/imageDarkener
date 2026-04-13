# pyright: reportMissingImports=false

from pathlib import Path
import sys

import cv2
from PyQt6 import QtCore, QtGui, QtWidgets


script_dir = Path(__file__).resolve().parent
images_dir = script_dir / "images"

# Backward-compatible fallback for older project layouts.
if not images_dir.exists():
	images_dir = Path(__file__).resolve().parents[2] / "data" / "images"
output_file = "img_bright_recolored.jpg"

image_candidates = []
for pattern in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tif", "*.tiff"):
	image_candidates.extend(sorted(images_dir.glob(pattern)))

if not image_candidates:
	raise FileNotFoundError(f"No image files found in: {images_dir}")

input_file = image_candidates[0]
img = cv2.imread(str(input_file), cv2.IMREAD_COLOR)

if img is None:
	raise FileNotFoundError(f"Could not load image: {input_file}")


class ImageDarkenerWindow(QtWidgets.QWidget):
	def __init__(self, image_bgr, input_path: Path, output_path: Path):
		super().__init__()
		self.input_path = input_path
		self.output_path = output_path
		self.original_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
		self.processed_rgb = self.original_rgb.copy()
		self._syncing_sliders = False

		self.setWindowTitle(f"Image Darkener - {self.input_path.name}")
		self.resize(1100, 760)
		self._build_ui()
		self._update_preview()

	def _build_ui(self) -> None:
		main_layout = QtWidgets.QHBoxLayout(self)

		left_panel = QtWidgets.QWidget()
		left_panel.setFixedWidth(320)
		left_layout = QtWidgets.QVBoxLayout(left_panel)
		left_layout.setSpacing(10)

		self.image_label = QtWidgets.QLabel()
		self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
		self.image_label.setSizePolicy(
			QtWidgets.QSizePolicy.Policy.Expanding,
			QtWidgets.QSizePolicy.Policy.Expanding,
		)
		self.image_label.setMinimumSize(320, 240)
		main_layout.addWidget(left_panel)
		main_layout.addWidget(self.image_label, stretch=1)

		self.sliders = {}
		self.value_labels = {}

		reference_header = QtWidgets.QLabel("Original Reference")
		reference_header.setStyleSheet("font-weight: 600;")
		left_layout.addWidget(reference_header)

		self.reference_image_label = QtWidgets.QLabel()
		self.reference_image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
		self.reference_image_label.setMinimumHeight(90)
		self.reference_image_label.setMaximumHeight(120)
		self.reference_image_label.setSizePolicy(
			QtWidgets.QSizePolicy.Policy.Expanding,
			QtWidgets.QSizePolicy.Policy.Fixed,
		)
		reference_pixmap = self._rgb_to_pixmap(self.original_rgb)
		self.reference_image_label.setPixmap(
			reference_pixmap.scaled(
				300,
				110,
				QtCore.Qt.AspectRatioMode.KeepAspectRatio,
				QtCore.Qt.TransformationMode.SmoothTransformation,
			)
		)
		left_layout.addWidget(self.reference_image_label)

		left_layout.addStretch(1)

		output_header_row = QtWidgets.QHBoxLayout()
		output_header = QtWidgets.QLabel("Output")
		output_header.setStyleSheet("font-weight: 600;")
		self.output_lock_button = QtWidgets.QPushButton("Lock RGB")
		self.output_lock_button.setCheckable(True)
		self.output_lock_button.setChecked(False)
		output_header_row.addWidget(output_header)
		output_header_row.addStretch(1)
		output_header_row.addWidget(self.output_lock_button)
		left_layout.addLayout(output_header_row)

		output_controls = QtWidgets.QGridLayout()
		output_controls.setVerticalSpacing(8)
		output_controls.setHorizontalSpacing(8)

		minimum_header_row = QtWidgets.QHBoxLayout()
		minimum_header = QtWidgets.QLabel("Minimum")
		minimum_header.setStyleSheet("font-weight: 600;")
		self.minimum_lock_button = QtWidgets.QPushButton("Lock RGB")
		self.minimum_lock_button.setCheckable(True)
		self.minimum_lock_button.setChecked(False)
		minimum_header_row.addWidget(minimum_header)
		minimum_header_row.addStretch(1)
		minimum_header_row.addWidget(self.minimum_lock_button)

		minimum_controls = QtWidgets.QGridLayout()
		minimum_controls.setVerticalSpacing(8)
		minimum_controls.setHorizontalSpacing(8)

		for row, (key, title, default) in enumerate(
			[
				("out_r", "R", 40),
				("out_g", "G", 40),
				("out_b", "B", 40),
			]
		):
			label = QtWidgets.QLabel(title)
			slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
			slider.setRange(0, 255)
			slider.setValue(default)
			value_label = QtWidgets.QLabel(str(default))
			value_label.setFixedWidth(36)
			slider.valueChanged.connect(lambda value, k=key: self._on_slider_changed(k, value))

			self.sliders[key] = slider
			self.value_labels[key] = value_label

			output_controls.addWidget(label, row, 0)
			output_controls.addWidget(slider, row, 1)
			output_controls.addWidget(value_label, row, 2)

		left_layout.addLayout(output_controls)

		divider = QtWidgets.QFrame()
		divider.setFrameShape(QtWidgets.QFrame.Shape.HLine)
		divider.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
		left_layout.addWidget(divider)

		left_layout.addLayout(minimum_header_row)

		for row, (key, title, default) in enumerate(
			[
				("min_r", "R", 125),
				("min_g", "G", 125),
				("min_b", "B", 125),
			]
		):
			label = QtWidgets.QLabel(title)
			slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
			slider.setRange(0, 255)
			slider.setValue(default)
			value_label = QtWidgets.QLabel(str(default))
			value_label.setFixedWidth(36)
			slider.valueChanged.connect(lambda value, k=key: self._on_slider_changed(k, value))

			self.sliders[key] = slider
			self.value_labels[key] = value_label

			minimum_controls.addWidget(label, row, 0)
			minimum_controls.addWidget(slider, row, 1)
			minimum_controls.addWidget(value_label, row, 2)

		left_layout.addLayout(minimum_controls)

		button_row = QtWidgets.QHBoxLayout()
		save_button = QtWidgets.QPushButton("Save")
		close_button = QtWidgets.QPushButton("Close")
		save_button.clicked.connect(self._save_image)
		close_button.clicked.connect(self.close)
		button_row.addWidget(save_button)
		button_row.addWidget(close_button)
		left_layout.addLayout(button_row)

	def _on_slider_changed(self, key: str, value: int) -> None:
		self.value_labels[key].setText(str(value))
		if self._syncing_sliders:
			return
		if not self._syncing_sliders:
			if key.startswith("out_") and self.output_lock_button.isChecked():
				self._sync_triplet("out", key, value)
			if key.startswith("min_") and self.minimum_lock_button.isChecked():
				self._sync_triplet("min", key, value)
		self._update_preview()

	def _sync_triplet(self, group_prefix: str, source_key: str, value: int) -> None:
		self._syncing_sliders = True
		try:
			for channel in ("r", "g", "b"):
				key = f"{group_prefix}_{channel}"
				if key != source_key:
					self.sliders[key].setValue(value)
		finally:
			self._syncing_sliders = False

	def _process_image(self):
		out_r = self.sliders["out_r"].value()
		out_g = self.sliders["out_g"].value()
		out_b = self.sliders["out_b"].value()
		min_r = self.sliders["min_r"].value()
		min_g = self.sliders["min_g"].value()
		min_b = self.sliders["min_b"].value()

		result = self.original_rgb.copy()
		mask = (
			(result[:, :, 0] >= min_r)
			& (result[:, :, 1] >= min_g)
			& (result[:, :, 2] >= min_b)
		)
		result[mask] = [out_r, out_g, out_b]
		return result

	def _rgb_to_pixmap(self, rgb_image):
		height, width, channels = rgb_image.shape
		bytes_per_line = channels * width
		qimage = QtGui.QImage(
			rgb_image.data,
			width,
			height,
			bytes_per_line,
			QtGui.QImage.Format.Format_RGB888,
		)
		return QtGui.QPixmap.fromImage(qimage)

	def _update_preview(self) -> None:
		self.processed_rgb = self._process_image()
		pixmap = self._rgb_to_pixmap(self.processed_rgb)
		fitted = pixmap.scaled(
			self.image_label.size(),
			QtCore.Qt.AspectRatioMode.KeepAspectRatio,
			QtCore.Qt.TransformationMode.SmoothTransformation,
		)
		self.image_label.setPixmap(fitted)

	def resizeEvent(self, event) -> None:
		super().resizeEvent(event)
		if self.image_label.width() > 0 and self.image_label.height() > 0:
			self._update_preview()

	def _save_image(self) -> None:
		bgr = cv2.cvtColor(self.processed_rgb, cv2.COLOR_RGB2BGR)
		cv2.imwrite(str(self.output_path), bgr)
		QtWidgets.QMessageBox.information(self, "Saved", f"Saved image to:\n{self.output_path.resolve()}")


def main() -> int:
	app = QtWidgets.QApplication(sys.argv)
	window = ImageDarkenerWindow(img, input_file, Path(output_file))
	window.show()
	return app.exec()


if __name__ == "__main__":
	raise SystemExit(main())
