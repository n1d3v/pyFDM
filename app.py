import sys
import os
import time
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QDialog, QLabel, QLineEdit, QListWidgetItem, QFileDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class AddUrlDialog(QDialog):
    url_added = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add URL")
        self.layout = QVBoxLayout()

        self.url_input = QLineEdit()
        self.layout.addWidget(self.url_input)

        self.dir_input = QLineEdit()
        self.layout.addWidget(self.dir_input)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_directory)
        self.layout.addWidget(self.browse_button)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_url)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)

    def add_url(self):
        url = self.url_input.text()
        directory = self.dir_input.text()
        
        if directory.lower() == "current":
            directory = os.path.dirname(os.path.abspath(__file__))

        if url:
            self.url_added.emit(url, directory)
            self.close()

class DownloadThread(QThread):
    progress_updated = pyqtSignal(int, float)

    def __init__(self, url, directory, parent=None):
        super().__init__(parent)
        self.url = url
        self.directory = directory

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            filename = self.url.split("/")[-1]
            filepath = os.path.join(self.directory, filename)

            start_time = time.time()
            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        downloaded += len(chunk)
                        elapsed_time = time.time() - start_time
                        download_speed = downloaded / (1024 * 1024 * elapsed_time) if elapsed_time > 0 else 0
                        self.progress_updated.emit(downloaded * 100 // total_size, download_speed)

        except Exception as e:
            print(f"Error downloading {self.url}: {e}")

class SimpleDownloadManager(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("pyFDM")
        self.layout = QVBoxLayout()

        self.add_button = QPushButton("Add URL")
        self.add_button.clicked.connect(self.show_add_url_dialog)
        self.layout.addWidget(self.add_button)

        self.download_list = QListWidget()
        self.layout.addWidget(self.download_list)

        self.setLayout(self.layout)

    def show_add_url_dialog(self):
        dialog = AddUrlDialog(self)
        dialog.url_added.connect(self.add_download)
        dialog.exec_()

    def add_download(self, url, directory):
        download_thread = DownloadThread(url, directory)
        download_thread.progress_updated.connect(self.update_progress)
        download_thread.start()

        filename = url.split("/")[-1]
        item_label = QLabel(f"File: {filename}, Type: {filename.split('.')[-1]}, Progress: 0%, Speed: 0 MB/s")
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_label.sizeHint())
        self.download_list.addItem(list_item)
        self.download_list.setItemWidget(list_item, item_label)

    def update_progress(self, percentage, speed):
        item = self.download_list.item(self.download_list.count() - 1)
        widget = self.download_list.itemWidget(item)
        filename = widget.text().split(',')[0].split(': ')[1]
        widget.setText(f"File: {filename}, Type: {filename.split('.')[-1]}, Progress: {percentage}%, Speed: {speed:.2f} MB/s")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleDownloadManager()
    window.show()
    sys.exit(app.exec_())
