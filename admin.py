import sys, os, sqlite3, shutil, subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy, QStackedWidget, QMessageBox,
    QLineEdit, QTextEdit, QFileDialog, QGridLayout, QScrollArea,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGraphicsDropShadowEffect, QCalendarWidget # (คงไว้)
)
from PyQt6.QtGui import (
    QFont, QPixmap, QColor, QIntValidator, QBrush, 
    QTextCharFormat # 👈 (คงไว้)
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QDate

# =========================
# 🔹 Database Helper (Products)
# (คงไว้ - เหมือนเดิม)
# =========================
def init_products_database(db_path="products.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_path TEXT,
            price TEXT,
            description TEXT,
            quantity INTEGER DEFAULT 0 
        )
    """)
    conn.commit()
    
    cur.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cur.fetchall()]
    
    if "price" not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN price TEXT")
    if "description" not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN description TEXT")
    if "quantity" not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN quantity INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

# =========================
# 🔹 Database Helper (Orders)
# (คงไว้ - เหมือนเดิม)
# =========================
def init_orders_database(db_path="orders.db"):
    """(คงไว้) สร้างตาราง orders และ order_items ถ้ายังไม่มี"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. ตารางเก็บคำสั่งซื้อหลัก
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending Payment',
            slip_image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. ตารางเก็บรายการสินค้าในคำสั่งซื้อนั้นๆ
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            size TEXT,
            quantity INTEGER NOT NULL,
            price_per_item REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    """)
    
    conn.commit()
    conn.close()

# ==================================
# 🔹 Add Product Page
# (คงไว้ - เหมือนเดิม)
# ==================================
class AddProductPage(QWidget):
    def __init__(self, image_folder, db_path="products.db"):
        super().__init__()
        self.image_folder = image_folder
        self.db_path = db_path
        self.selected_image_path = None 
        self.saved_image_filename = None 
        self.initUI()
        self.apply_styles() 
    def initUI(self):
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0,0,0,0)
        scroll = QScrollArea() 
        scroll.setWidgetResizable(True)
        scroll.setObjectName("MainScrollArea")
        main_widget = QWidget()
        scroll.setWidget(main_widget)
        layout = QVBoxLayout(main_widget) 
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        title = QLabel("📦 เพิ่มสินค้าใหม่ (Add New Product)")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setObjectName("MainTitle")
        layout.addWidget(title)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        self.left_card = QFrame() 
        self.left_card.setObjectName("Card")
        left_layout = QVBoxLayout(self.left_card)
        left_layout.setSpacing(20)
        form_grid = QGridLayout()
        form_grid.setSpacing(15)
        name_label = QLabel("ชื่อสินค้า (Name)")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("เช่น Manchester United 24/25 (เหย้า)")
        form_grid.addWidget(name_label, 0, 0)
        form_grid.addWidget(self.name_input, 1, 0)
        price_label = QLabel("ราคา (Price)")
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("เช่น ฿2,900")
        form_grid.addWidget(price_label, 0, 1)
        form_grid.addWidget(self.price_input, 1, 1)
        quantity_label = QLabel("จำนวนสต็อก (Stock Quantity)")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("เช่น 100")
        self.quantity_input.setValidator(QIntValidator(0, 9999))
        self.quantity_input.setFixedWidth(200) 
        form_grid.addWidget(quantity_label, 0, 2)
        form_grid.addWidget(self.quantity_input, 1, 2)
        left_layout.addLayout(form_grid)
        desc_label = QLabel("รายละเอียด (Description)")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("รายละเอียดสินค้า...\n- เทคโนโลยี...\n- โพลีเอสเตอร์รีไซเคิล 100%")
        self.desc_input.setMinimumHeight(300)
        left_layout.addWidget(desc_label)
        left_layout.addWidget(self.desc_input)
        left_layout.addStretch()
        self.right_card = QFrame() 
        self.right_card.setObjectName("Card")
        right_layout = QVBoxLayout(self.right_card)
        right_layout.setSpacing(15)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        img_title = QLabel("รูปภาพสินค้า")
        right_layout.addWidget(img_title)
        self.image_preview = QLabel("ยังไม่ได้เลือกรูปภาพ")
        self.image_preview.setMinimumSize(250, 250)
        self.image_preview.setMaximumWidth(350)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setObjectName("ImagePreview")
        self.image_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.image_preview, 1)
        self.upload_btn = QPushButton("📁 เลือกไฟล์รูปภาพ")
        self.upload_btn.clicked.connect(self.select_image)
        self.upload_btn.setObjectName("UploadButton")
        right_layout.addWidget(self.upload_btn)
        content_layout.addWidget(self.left_card, 2) 
        content_layout.addWidget(self.right_card, 1) 
        layout.addLayout(content_layout)
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = QPushButton("💾 บันทึกสินค้า")
        self.save_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setFixedWidth(200)
        self.save_btn.setObjectName("SaveButton")
        self.save_btn.clicked.connect(self.save_product)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)
        main_v_layout.addWidget(scroll)
    def apply_styles(self):
        # ❗ [แก้ไข] เปลี่ยน background-color หลักเป็น #ffffff
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QScrollArea#MainScrollArea { border: none; background-color: #ffffff; }
            QFrame#Card {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 25px;
            }
            QLabel#MainTitle { color: #2c3e50; }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding-bottom: 5px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #fdfdfd;
                border: 1px solid #d5d5d5;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: normal;
                color: #333;
            }
            QComboBox { padding-right: 20px; }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #005a9c;
            }
            QLabel#ImagePreview {
                border: 2px dashed #c0c0c0;
                background-color: #f9f9f9;
                border-radius: 8px;
                color: #888;
                font-weight: normal;
            }
            QPushButton {
                font-size: 14px;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
                font-weight: bold;
            }
            QPushButton#UploadButton {
                background-color: #004aad;
                color: white;
            }
            QPushButton#UploadButton:hover { background-color: #003580; }
            QPushButton#SaveButton {
                background-color: #008c4a;
                color: white;
            }
            QPushButton#SaveButton:hover { background-color: #006a38; }
            QPushButton#DeleteButton {
                background-color: #d9534f;
                color: white;
            }
            QPushButton#DeleteButton:hover { background-color: #c9302c; }
            QPushButton#RefreshButton {
                background-color: #f0ad4e;
                color: white;
                font-size: 12px;
                padding: 10px 16px;
            }
            QPushButton#RefreshButton:hover { background-color: #ec971f; }
        """)
    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "เลือกรูปภาพสินค้า", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            filename = os.path.basename(file_path)
            destination_path = os.path.join(self.image_folder, filename)
            if os.path.exists(destination_path):
                reply = QMessageBox.question(
                    self, "ไฟล์ซ้ำ",
                    f"ไฟล์ชื่อ '{filename}' มีอยู่แล้วในโฟลเดอร์ \n"
                    f"คุณต้องการเขียนทับไฟล์เดิมหรือไม่?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            self.selected_image_path = file_path
            self.saved_image_filename = filename
            pixmap = QPixmap(file_path)
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
            self.image_preview.setStyleSheet("border: none;") 
    def save_product(self):
        name = self.name_input.text().strip()
        price = self.price_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        image_name = self.saved_image_filename
        try:
            quantity = int(self.quantity_input.text().strip() or 0)
        except ValueError:
            quantity = 0
        if not name or not price:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "⚠️ กรุณากรอก 'ชื่อสินค้า' และ 'ราคา' เป็นอย่างน้อย")
            return
        if not image_name:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "⚠️ กรุณาเลือก 'รูปภาพ' สำหรับสินค้า")
            return
        try:
            destination_path = os.path.join(self.image_folder, image_name)
            shutil.copy(self.selected_image_path, destination_path)
        except Exception as e:
            QMessageBox.critical(self, "Error (Copy Image)", f"ไม่สามารถคัดลอกรูปภาพได้: {e}")
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO products (name, image_path, price, description, quantity) VALUES (?, ?, ?, ?, ?)",
                (name, image_name, price, description, quantity)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "สำเร็จ", f"✅ บันทึกสินค้า '{name}' เรียบร้อยแล้ว")
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
    def clear_form(self):
        self.name_input.clear()
        self.price_input.clear()
        self.desc_input.clear()
        self.quantity_input.clear()
        self.image_preview.clear()
        self.image_preview.setText("ยังไม่ได้เลือกรูปภาพ")
        self.image_preview.setObjectName("ImagePreview")
        self.apply_styles() 
        self.selected_image_path = None
        self.saved_image_filename = None
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.selected_image_path and os.path.exists(self.selected_image_path):
            pixmap = QPixmap(self.selected_image_path)
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))


# ==================================
# 🔹 Edit Product Page
# (คงไว้ - เหมือนเดิม)
# ==================================
class EditProductPage(QWidget):
    def __init__(self, image_folder, db_path="products.db"):
        super().__init__()
        self.image_folder = image_folder
        self.db_path = db_path
        self.current_product_id = None
        self.selected_image_path = None 
        self.saved_image_filename = None
        self.new_image_selected = False 
        self.initUI()
        self.apply_styles()
        self.set_form_enabled(False) 
    def initUI(self):
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0,0,0,0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("MainScrollArea")
        main_widget = QWidget()
        scroll.setWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(15)
        selector_label = QLabel("เลือกสินค้าที่จะแก้ไข:")
        selector_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.product_selector = QComboBox()
        self.product_selector.setFont(QFont("Arial", 14))
        self.product_selector.setMinimumWidth(400)
        self.product_selector.currentIndexChanged.connect(self.load_selected_product)
        self.refresh_btn = QPushButton("🔄 Refresh List")
        self.refresh_btn.setObjectName("RefreshButton")
        self.refresh_btn.clicked.connect(self.populate_product_selector)
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.product_selector, 1)
        selector_layout.addWidget(self.refresh_btn)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #e0e0e0; height: 1px; border: none;")
        layout.addWidget(line)
        title = QLabel(" แก้ไขสินค้า (Edit Product)")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setObjectName("MainTitle")
        layout.addWidget(title)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        self.left_card = QFrame()
        self.left_card.setObjectName("Card")
        left_layout = QVBoxLayout(self.left_card)
        left_layout.setSpacing(20)
        form_grid = QGridLayout()
        form_grid.setSpacing(15)
        name_label = QLabel("ชื่อสินค้า (Name)")
        self.name_input = QLineEdit()
        form_grid.addWidget(name_label, 0, 0)
        form_grid.addWidget(self.name_input, 1, 0)
        price_label = QLabel("ราคา (Price)")
        self.price_input = QLineEdit()
        form_grid.addWidget(price_label, 0, 1)
        form_grid.addWidget(self.price_input, 1, 1)
        quantity_label = QLabel("จำนวนสต็อก (Stock Quantity)")
        self.quantity_input = QLineEdit()
        self.quantity_input.setValidator(QIntValidator(0, 9999))
        self.quantity_input.setFixedWidth(200)
        form_grid.addWidget(quantity_label, 0, 2)
        form_grid.addWidget(self.quantity_input, 1, 2)
        left_layout.addLayout(form_grid)
        desc_label = QLabel("รายละเอียด (Description)")
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(300)
        left_layout.addWidget(desc_label)
        left_layout.addWidget(self.desc_input)
        left_layout.addStretch()
        self.right_card = QFrame()
        self.right_card.setObjectName("Card")
        right_layout = QVBoxLayout(self.right_card)
        right_layout.setSpacing(15)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        img_title = QLabel("รูปภาพสินค้า")
        right_layout.addWidget(img_title)
        self.image_preview = QLabel("กรุณาเลือกสินค้าก่อน")
        self.image_preview.setMinimumSize(250, 250)
        self.image_preview.setMaximumWidth(350)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setObjectName("ImagePreview")
        self.image_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.image_preview, 1)
        self.upload_btn = QPushButton("📁 เปลี่ยนไฟล์รูปภาพ")
        self.upload_btn.clicked.connect(self.select_image)
        self.upload_btn.setObjectName("UploadButton")
        right_layout.addWidget(self.upload_btn)
        content_layout.addWidget(self.left_card, 2)
        content_layout.addWidget(self.right_card, 1)
        layout.addLayout(content_layout)
        save_layout = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ ลบสินค้า")
        self.delete_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.delete_btn.setMinimumHeight(45)
        self.delete_btn.setFixedWidth(200)
        self.delete_btn.setObjectName("DeleteButton")
        self.delete_btn.clicked.connect(self.delete_product)
        save_layout.addWidget(self.delete_btn)
        save_layout.addStretch()
        self.save_btn = QPushButton("💾 อัปเดตสินค้า") 
        self.save_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setFixedWidth(200)
        self.save_btn.setObjectName("SaveButton")
        self.save_btn.clicked.connect(self.update_product) 
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)
        main_v_layout.addWidget(scroll)
    def apply_styles(self):
        # ❗ [แก้ไข] เปลี่ยน background-color หลักเป็น #ffffff
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QScrollArea#MainScrollArea { border: none; background-color: #ffffff; }
            QFrame#Card {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 25px;
            }
            QLabel#MainTitle { color: #2c3e50; }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding-bottom: 5px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #fdfdfd;
                border: 1px solid #d5d5d5;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: normal;
                color: #333;
            }
            QComboBox { padding-right: 20px; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d5d5d5;
                selection-background-color: #004aad;
                selection-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #005a9c;
            }
            QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
            QFrame#Card:disabled {
                 background-color: #f8f9fa;
            }
            QLabel#ImagePreview {
                border: 2px dashed #c0c0c0;
                background-color: #f9f9f9;
                border-radius: 8px;
                color: #888;
                font-weight: normal;
            }
            QPushButton {
                font-size: 14px;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
                font-weight: bold;
            }
            QPushButton#UploadButton {
                background-color: #004aad;
                color: white;
            }
            QPushButton#UploadButton:hover { background-color: #003580; }
            QPushButton#SaveButton {
                background-color: #008c4a;
                color: white;
            }
            QPushButton#SaveButton:hover { background-color: #006a38; }
            QPushButton#DeleteButton {
                background-color: #d9534f;
                color: white;
            }
            QPushButton#DeleteButton:hover { background-color: #c9302c; }
            QPushButton#RefreshButton {
                background-color: #f0ad4e;
                color: white;
                font-size: 12px;
                padding: 10px 16px;
            }
            QPushButton#RefreshButton:hover { background-color: #ec971f; }
            QPushButton:disabled {
                background-color: #c0c0c0;
                color: #888;
            }
        """)
    def set_form_enabled(self, enabled):
        self.left_card.setEnabled(enabled)
        self.right_card.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        if not enabled:
            self.clear_form()
            self.image_preview.setText("กรุณาเลือกสินค้าก่อน")
    def populate_product_selector(self):
        try:
            self.product_selector.blockSignals(True) 
            self.product_selector.clear()
            self.product_selector.addItem("--- กรุณาเลือกสินค้า ---", userData=None)
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM products ORDER BY name ASC")
            products = cur.fetchall()
            conn.close()
            for prod_id, name in products:
                self.product_selector.addItem(name, userData=prod_id)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ไม่สามารถโหลดรายการสินค้าได้: {e}")
        finally:
            self.product_selector.blockSignals(False) 
            self.set_form_enabled(False) 
    def load_selected_product(self):
        self.current_product_id = self.product_selector.currentData()
        if self.current_product_id is None:
            self.set_form_enabled(False)
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT name, image_path, price, description, quantity FROM products WHERE id=?", 
                (self.current_product_id,)
            )
            data = cur.fetchone()
            conn.close()
            if data:
                name, image_name, price, description, quantity = data
                self.name_input.setText(name)
                self.price_input.setText(price)
                self.desc_input.setPlainText(description)
                self.quantity_input.setText(str(quantity))
                self.saved_image_filename = image_name
                self.selected_image_path = os.path.join(self.image_folder, image_name) if image_name else None
                self.new_image_selected = False 
                if self.selected_image_path and os.path.exists(self.selected_image_path):
                    pixmap = QPixmap(self.selected_image_path)
                    self.image_preview.setPixmap(pixmap.scaled(
                        self.image_preview.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    ))
                    self.image_preview.setStyleSheet("border: none;")
                else:
                    self.image_preview.setText(f"ไม่พบไฟล์รูปภาพ\n({image_name})")
                    self.image_preview.setObjectName("ImagePreview")
                    self.apply_styles() 
                self.set_form_enabled(True) 
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ไม่สามารถโหลดข้อมูลสินค้าได้: {e}")
            self.set_form_enabled(False)
    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "เลือกรูปภาพสินค้า", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            filename = os.path.basename(file_path)
            destination_path = os.path.join(self.image_folder, filename)
            if os.path.exists(destination_path):
                reply = QMessageBox.question(
                    self, "ไฟล์ซ้ำ",
                    f"ไฟล์ชื่อ '{filename}' มีอยู่แล้วในโฟลเดอร์ \n"
                    f"คุณต้องการเขียนทับไฟล์เดิมหรือไม่?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            self.selected_image_path = file_path 
            self.saved_image_filename = filename 
            self.new_image_selected = True 
            pixmap = QPixmap(file_path)
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
            self.image_preview.setStyleSheet("border: none;") 
    def update_product(self):
        if self.current_product_id is None:
            return
        name = self.name_input.text().strip()
        price = self.price_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        image_name = self.saved_image_filename
        try:
            quantity = int(self.quantity_input.text().strip() or 0)
        except ValueError:
            quantity = 0
        if not name or not price:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "⚠️ กรุณากรอก 'ชื่อสินค้า' และ 'ราคา' เป็นอย่างน้อย")
            return
        if not image_name:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "⚠️ ต้องมี 'รูปภาพ' สำหรับสินค้า")
            return
        if self.new_image_selected:
            try:
                destination_path = os.path.join(self.image_folder, image_name)
                shutil.copy(self.selected_image_path, destination_path)
                self.new_image_selected = False 
            except Exception as e:
                QMessageBox.critical(self, "Error (Copy Image)", f"ไม่สามารถคัดลอกรูปภาพใหม่ได้: {e}")
                return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "UPDATE products SET name=?, image_path=?, price=?, description=?, quantity=? WHERE id=?",
                (name, image_name, price, description, quantity, self.current_product_id)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "สำเร็จ", f"✅ อัปเดตสินค้า '{name}' เรียบร้อยแล้ว")
            current_id = self.current_product_id
            self.populate_product_selector()
            index = self.product_selector.findData(current_id)
            if index > 0:
                self.product_selector.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"เกิดข้อผิดพลาดในการอัปเดตข้อมูล: {e}")
    def delete_product(self):
        if self.current_product_id is None:
            return
        name = self.name_input.text()
        reply = QMessageBox.question(
            self, "ยืนยันการลบ",
            f"คุณต้องการลบสินค้า '{name}' ใช่หรือไม่?\n"
            f"(การกระทำนี้ไม่สามารถย้อนกลับได้)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("DELETE FROM products WHERE id=?", (self.current_product_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "ลบสำเร็จ", f"ลบสินค้า '{name}' เรียบร้อยแล้ว")
                self.populate_product_selector() 
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"เกิดข้อผิดพลาดในการลบข้อมูล: {e}")
    def clear_form(self):
        self.name_input.clear()
        self.price_input.clear()
        self.desc_input.clear()
        self.quantity_input.clear()
        self.image_preview.clear()
        self.image_preview.setText("กรุณาเลือกสินค้าก่อน")
        self.image_preview.setObjectName("ImagePreview")
        self.apply_styles()
        self.selected_image_path = None
        self.saved_image_filename = None
        self.current_product_id = None
        self.new_image_selected = False
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.selected_image_path and os.path.exists(self.selected_image_path):
            pixmap = QPixmap(self.selected_image_path)
            self.image_preview.setPixmap(pixmap.scaled(
                self.image_preview.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
    def load_product_by_id(self, product_id_to_load):
        ''' (Public Method) ถูกเรียกโดย MainApp '''
        print(f"Attempting to load ID: {product_id_to_load}")
        self.populate_product_selector()
        index = self.product_selector.findData(product_id_to_load)
        if index > 0:
            self.product_selector.setCurrentIndex(index)
            self.set_form_enabled(True)
        else:
            QMessageBox.warning(self, "Error", f"ไม่พบสินค้า ID: {product_id_to_load} ในรายการ")
            self.set_form_enabled(False)


# =========================
# 🔹 OrderCard (Widget)
# (คงไว้ - เหมือนเดิม)
# =========================
class OrderCard(QFrame):
    """
    (คงไว้) Widget สำหรับแสดงข้อมูล 'ออเดอร์' หนึ่งใบในรูปแบบการ์ด
    """
    # Signal ที่ส่ง Order ID ออกไป
    card_clicked = pyqtSignal(int) 

    def __init__(self, order_data, items_list, parent=None):
        super().__init__(parent)
        
        # order_data = (id, username, total_amount, status, slip_image_path, created_at)
        # ❗ (ลำดับที่ถูกต้องจาก DB คือ 4=slip_path, 5=created_at)
        
        self.order_data = order_data
        self.items_list = items_list
        self.order_id = order_data[0] # (id)
        
        self.setObjectName("OrderCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor) # (ทำให้รู้ว่าคลิกได้)
        self.initUI()
        self.apply_card_styles()
        
        # (เพิ่ม Shadow)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)

    def initUI(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # --- 1. Info Section (ID, User, Date, Slip) --- ❗ [แก้ไข] ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        id_label = QLabel(f"Order ID: #{self.order_id}")
        id_label.setObjectName("OrderCardID")
        info_layout.addWidget(id_label)
        
        user_label = QLabel(f"<b>ลูกค้า:</b> {self.order_data[1]}") # (username)
        user_label.setObjectName("OrderCardInfo")
        info_layout.addWidget(user_label)

        # ❗ [แก้ไข] วันที่ ต้องดึงจาก [5]
        date_str = self.order_data[5].split(" ")[0] # (created_at)
        date_label = QLabel(f"<b>วันที่:</b> {date_str}")
        date_label.setObjectName("OrderCardInfo")
        info_layout.addWidget(date_label)
        
        # ❗ [เพิ่ม] เพิ่มแถวสลิป (ตามที่เห็นใน Screenshot)
        slip_path = self.order_data[4] # (slip_image_path)
        slip_label = QLabel(f"<b>สลิป:</b> {slip_path}")
        slip_label.setObjectName("OrderCardSlip") # (ใช้สไตล์ใหม่)
        info_layout.addWidget(slip_label)
        
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

        # --- 2. Price & Status Section ---
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        total_label = QLabel(f"฿{self.order_data[2]:,.2f}") # (total_amount)
        total_label.setObjectName("OrderCardTotal")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(total_label)

        # Status Badge
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_status_badge(self.order_data[3]) # (status)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addLayout(status_layout)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(120) # (เพิ่มความสูงเล็กน้อย)

    def update_status_badge(self, status_text):
        self.status_label.setText(status_text)
        self.status_label.setProperty("status", status_text.replace(" ", "_"))
        self.style().polish(self.status_label) # (บังคับ QSS ให้อัปเดต)

    def set_selected(self, is_selected):
        """(ใหม่) ตั้งค่าสถานะ "ถูกเลือก" สำหรับ QSS"""
        self.setProperty("selected", "true" if is_selected else "false")
        self.style().polish(self)

    def mousePressEvent(self, event):
        """(ใหม่) เมื่อการ์ดถูกคลิก ให้ส่ง Signal ออกไป"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.card_clicked.emit(self.order_id)
        super().mousePressEvent(event)

    def apply_card_styles(self):
        # ❗ [แก้ไข] เพิ่ม QSS สำหรับ #OrderCardSlip
        self.setStyleSheet("""
            QFrame#OrderCard {
                background-color: #ffffff;
                border-radius: 10px;
                border: 2px solid #e0e0e0;
            }
            QFrame#OrderCard[selected="true"] {
                border: 2px solid #004aad; 
            }
            QFrame#OrderCard:hover {
                border: 2px solid #a0a0a0;
            }

            QLabel#OrderCardID {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                background-color: transparent;
            }
            QLabel#OrderCardInfo {
                font-size: 13px;
                color: #333;
                background-color: transparent;
            }
            QLabel#OrderCardSlip {
                font-size: 12px; /* (ทำให้เล็กกว่า) */
                color: #777;  /* (ทำให้สีจางกว่า) */
                background-color: transparent;
            }
            QLabel#OrderCardTotal {
                font-size: 16px;
                font-weight: bold;
                color: #e74c3c;
                background-color: transparent;
            }

            /* --- Status Badges (สำหรับ Order) --- */
            QLabel[status="Completed"] {
                color: #006a38;
                background-color: #e6f7ec;
                font-size: 12px; font-weight: bold;
                padding: 5px 10px; border-radius: 10px;
                min-width: 130px;
            }
            QLabel[status="Pending_Confirmation"] {
                color: #b98900;
                background-color: #fef9e7;
                font-size: 12px; font-weight: bold;
                padding: 5px 10px; border-radius: 10px;
                min-width: 130px;
            }
            QLabel[status="Cancelled"] {
                color: #c9302c;
                background-color: #fdecea;
                font-size: 12px; font-weight: bold;
                padding: 5px 10px; border-radius: 10px;
                min-width: 130px;
            }
            QLabel[status="Pending_Payment"] {
                color: #555;
                background-color: #f0f0f0;
                font-size: 12px; font-weight: bold;
                padding: 5px 10px; border-radius: 10px;
                min-width: 130px;
            }
        """)
        
# ==================================
# 🔹 Admin Order Page
# (คงไว้ - เหมือนเดิม)
# ==================================
class AdminOrderPage(QWidget):
    """(ดีไซน์ใหม่) หน้าสำหรับ Admin เพื่อจัดการออเดอร์ (Master-Detail View)"""
    
    def __init__(self):
        super().__init__()
        self.db_path = "orders.db"
        self.current_selected_order_id = None
        self.all_orders_data = {} # (เก็บข้อมูลดิบของออเดอร์)
        self.all_items_data = {}  # (เก็บรายการสินค้าของแต่ละออเดอร์)
        self.card_widgets = {}    # (เก็บ widget ของการ์ด)
        
        self.initUI()
        self.apply_page_styles()
        self.load_all_data() # (โหลดข้อมูลครั้งแรก)

    def initUI(self):
        self.setWindowTitle("จัดการออเดอร์ (Admin)")
        
        # --- Layout หลัก (ซ้าย-ขวา) ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 30)
        main_layout.setSpacing(25)
        
        # ---------- 1. ฝั่งซ้าย (รายการออเดอร์) ----------
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # (Header ฝั่งซ้าย)
        left_header_layout = QHBoxLayout()
        title = QLabel("รายการออเดอร์")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setObjectName("MainTitle")
        left_header_layout.addWidget(title)
        left_header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 โหลดใหม่")
        refresh_btn.setObjectName("RefreshButton")
        refresh_btn.setMinimumHeight(45)
        refresh_btn.clicked.connect(self.load_all_data)
        left_header_layout.addWidget(refresh_btn)
        
        left_layout.addLayout(left_header_layout)
        
        # (Scroll Area สำหรับการ์ด)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("OrderScrollArea")
        
        self.cards_container_widget = QWidget()
        self.cards_container_widget.setObjectName("CardsContainer")
        
        self.cards_layout = QVBoxLayout(self.cards_container_widget)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.cards_container_widget)
        left_layout.addWidget(self.scroll_area, 1) # (ยืด 1 ส่วน)
        
        main_layout.addLayout(left_layout, 2) # (ฝั่งซ้ายขยาย 2 ส่วน)
        
        # ---------- 2. แผงด้านขวา (แผงรายละเอียด) ----------
        self.right_panel = QFrame()
        self.right_panel.setObjectName("DetailPanel")
        self.right_panel.setFixedWidth(450) # (ล็อคความกว้าง)
        
        right_panel_layout = QVBoxLayout(self.right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0) # (ไม่มี Margin)
        right_panel_layout.setSpacing(0) # (ไม่มี Spacing)
        
        # (สร้าง QScrollArea สำหรับเนื้อหาด้านขวา)
        self.detail_scroll_area = QScrollArea()
        self.detail_scroll_area.setWidgetResizable(True)
        self.detail_scroll_area.setObjectName("DetailScrollArea")

        # (ปิด Scrollbar แนวตั้ง)
        self.detail_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.detail_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.detail_scroll_widget = QWidget() # Widget ที่จะอยู่ข้างใน
        self.detail_scroll_widget.setObjectName("DetailScrollWidget")
        
        self.detail_content_layout = QVBoxLayout(self.detail_scroll_widget) # Layout ของ Widget
        self.detail_content_layout.setContentsMargins(25, 25, 25, 25)
        self.detail_content_layout.setSpacing(15)
        self.detail_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # (Header: ID + Status Badge)
        detail_header_layout = QHBoxLayout()
        self.detail_order_id_label = QLabel("ยังไม่ได้เลือกออเดอร์")
        self.detail_order_id_label.setObjectName("DetailID")
        self.detail_status_badge = QLabel("N/A")
        self.detail_status_badge.setObjectName("DetailStatusBadge")
        detail_header_layout.addWidget(self.detail_order_id_label)
        detail_header_layout.addStretch()
        detail_header_layout.addWidget(self.detail_status_badge)
        self.detail_content_layout.addLayout(detail_header_layout)

        # (Metadata: User + Date)
        self.detail_user_label = QLabel()
        self.detail_user_label.setObjectName("DetailMeta")
        self.detail_date_label = QLabel()
        self.detail_date_label.setObjectName("DetailMeta")
        self.detail_content_layout.addWidget(self.detail_user_label)
        self.detail_content_layout.addWidget(self.detail_date_label)

        # (เส้นคั่น)
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setObjectName("SeparatorLine")
        self.detail_content_layout.addWidget(line1)
        
        # (ที่แสดงสลิป)
        slip_title = QLabel("สลิปโอนเงิน:")
        slip_title.setObjectName("DetailSubTitle")
        self.detail_content_layout.addWidget(slip_title)
        
        self.slip_preview = QLabel("กรุณาเลือกออเดอร์")
        self.slip_preview.setMinimumHeight(400) # (ขยายให้ใหญ่ขึ้น)
        self.slip_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slip_preview.setObjectName("SlipPreview")
        self.slip_preview.setScaledContents(False)
        self.detail_content_layout.addWidget(self.slip_preview)

        # (เส้นคั่น)
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setObjectName("SeparatorLine")
        self.detail_content_layout.addWidget(line2)

        # (ที่แสดงรายการสินค้า)
        items_title = QLabel("รายการสินค้า:")
        items_title.setObjectName("DetailSubTitle")
        self.detail_content_layout.addWidget(items_title)
        
        # (กรอบสำหรับใส่รายการสินค้าแบบไดนามิก)
        self.detail_items_frame = QFrame()
        self.detail_items_frame.setObjectName("ItemsFrame")
        self.detail_items_layout = QVBoxLayout(self.detail_items_frame)
        self.detail_items_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_items_layout.setSpacing(10)
        
        self.detail_content_layout.addWidget(self.detail_items_frame)
        
        self.detail_content_layout.addStretch() # (ดันทุกอย่างขึ้นบน)
        
        # (ตั้งค่า Scroll Area)
        self.detail_scroll_area.setWidget(self.detail_scroll_widget)
        
        # (เพิ่ม Scroll Area และปุ่ม ลงใน right_panel_layout)
        right_panel_layout.addWidget(self.detail_scroll_area, 1) # (ยืด 1 ส่วน)
        
        # (กรอบสำหรับปุ่ม Action)
        action_frame = QFrame()
        action_frame.setObjectName("ActionFrame")
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(20, 15, 20, 15)
        action_layout.setSpacing(15)
        
        self.approve_btn = QPushButton("✅ อนุมัติ (Completed)")
        self.approve_btn.setObjectName("ApproveButton")
        self.approve_btn.setMinimumHeight(45)
        self.approve_btn.clicked.connect(self.approve_order)
        
        self.reject_btn = QPushButton("❌ ปฏิเสธ (Cancelled)")
        self.reject_btn.setObjectName("RejectButton")
        self.reject_btn.setMinimumHeight(45)
        self.reject_btn.clicked.connect(self.reject_order)
        
        action_layout.addWidget(self.approve_btn, 1)
        action_layout.addWidget(self.reject_btn, 1)
        
        right_panel_layout.addWidget(action_frame) # (ไม่ยืด)
        
        main_layout.addWidget(self.right_panel) # (ฝั่งขวา 1 ส่วน)
        
        self.update_detail_panel(None) # (ซ่อนปุ่มตอนเริ่มต้น)

    def apply_page_styles(self):
        # ❗ [แก้ไข] เปลี่ยน background-color หลักเป็น #ffffff
        self.setStyleSheet("""
            QWidget { 
                background-color: #ffffff; 
                color: #333; /* (ตั้งค่าสีตัวอักษรหลัก) */
            }
            QLabel {
                background-color: transparent; /* (สำคัญมาก) */
            }
            QLabel#MainTitle { 
                color: #2c3e50; 
                background-color: transparent; 
            }
            
            /* --- Scroll Area (ซ้าย) --- */
            QScrollArea#OrderScrollArea { 
                border: 1px solid #e0e0e0; 
                background-color: #ffffff; 
            }
            QWidget#CardsContainer { background-color: #ffffff; }

            /* --- แผงรายละเอียดด้านขวา --- */
            QFrame#DetailPanel {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
            QScrollArea#DetailScrollArea {
                border: none;
            }
            QWidget#DetailScrollWidget {
                background-color: white;
            }
            
            QLabel#DetailID { 
                font-size: 20px; 
                font-weight: bold; 
                color: #004aad; 
            }
            QLabel#DetailStatusBadge {
                font-size: 12px; font-weight: bold;
                padding: 5px 10px; border-radius: 10px;
                min-width: 130px;
                alignment: 'AlignCenter';
            }
            QLabel#DetailMeta { 
                font-size: 14px; 
                color: #555; 
            }
            QLabel#DetailSubTitle {
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
            
            QFrame#SeparatorLine {
                background-color: #f0f0f0;
                height: 1px;
                border: none;
            }
            
            QLabel#SlipPreview {
                background-color: #f9f9f9;
                border: 2px dashed #c0c0c0;
                border-radius: 8px;
                color: #888;
                font-size: 14px;
            }
            
            /* (กรอบรายการสินค้า) */
            QFrame#ItemsFrame {
                background-color: #f9f9f9;
                border-radius: 8px;
            }
            /* (สไตล์สำหรับ Label สินค้าที่เพิ่มแบบไดนามิก) */
            QLabel.ItemNameLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
            QLabel.ItemDetailLabel {
                font-size: 13px;
                color: #555;
                padding-left: 15px; /* (ย่อหน้าเล็กน้อย) */
            }

            /* --- กรอบปุ่ม Action ด้านล่างขวา --- */
            QFrame#ActionFrame {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
            }

            /* --- ปุ่ม --- */
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton#RefreshButton {
                background-color: #004aad; 
                color: white;
            }
            QPushButton#RefreshButton:hover { background-color: #003580; }
            
            QPushButton#ApproveButton { background-color: #008c4a; color: white; }
            QPushButton#ApproveButton:hover { background-color: #006a38; }
            QPushButton#RejectButton { background-color: #d9534f; color: white; }
            QPushButton#RejectButton:hover { background-color: #c9302c; }
            
            QPushButton:disabled { 
                background-color: #c0c0c0; 
                color: #888;
                border: none;
            }
            
            /* --- QSS สำหรับ Status Badge (ย้ายมาจาก OrderCard) --- */
            QLabel[status="Completed"] {
                color: #006a38;
                background-color: #e6f7ec;
            }
            QLabel[status="Pending_Confirmation"] {
                color: #b98900;
                background-color: #fef9e7;
            }
            QLabel[status="Cancelled"] {
                color: #c9302c;
                background-color: #fdecea;
            }
            QLabel[status="Pending_Payment"] {
                color: #555;
                background-color: #f0f0f0;
            }
        """)

    def load_all_data(self):
        """(เหมือนเดิม) โหลดข้อมูล Orders และ Items ทั้งหมดเก็บไว้ใน Dictionary"""
        print("Loading all order data...")
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

             # --- 1. (เพิ่ม) ATTACH users.db เพื่อดึง email ---
             # (สมมติว่า users.db อยู่ใน path เดียวกันกับ orders.db)
            users_db_path = self.db_path.replace("orders.db", "users.db")
            if "addedit.py" in users_db_path: # (ป้องกันกรณี path ผิดพลาด)
                users_db_path = "users.db"

            try:
                cur.execute(f"ATTACH DATABASE '{users_db_path}' AS users_db")
            except sqlite3.OperationalError:
                print(f"Warning: Could not attach {users_db_path}. Email field might be blank.")

            # --- 2. (แก้ไข) เปลี่ยน SELECT * เป็น JOIN และใช้ datetime() ---
            cur.execute("""
                SELECT 
                    o.id, 
                    o.username, 
                    o.total_amount, 
                    o.status, 
                    o.slip_image_path, 
                    datetime(o.created_at, 'localtime') as local_created_at, 
                    o.shipping_address, 
                    u.email
                FROM orders o
                LEFT JOIN users_db.users u ON o.username = u.username
                ORDER BY o.id ASC
            """)

            orders = cur.fetchall()
            # (ลำดับใน tuple คือ: id, username, total_amount, status, slip_image_path, created_at)
            self.all_orders_data = {order['id']: tuple(order) for order in orders}
            
            cur.execute("SELECT * FROM order_items")
            items = cur.fetchall()
            conn.close()
            
            self.all_items_data.clear()
            for item in items:
                order_id = item['order_id']
                if order_id not in self.all_items_data:
                    self.all_items_data[order_id] = []
                self.all_items_data[order_id].append(tuple(item))
                
            print(f"Loaded {len(self.all_orders_data)} orders and item groups for {len(self.all_items_data)} orders.")
            
            self.populate_cards()
            self.update_detail_panel(None) # (เคลียร์แผงด้านขวา)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ไม่สามารถโหลดข้อมูลออเดอร์ได้: {e}")

    def populate_cards(self):
        """ (เหมือนเดิม) สร้างการ์ดจากข้อมูลที่โหลดมา"""
        
        for i in reversed(range(self.cards_layout.count())): 
            widget = self.cards_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.card_widgets.clear()
        
        if not self.all_orders_data:
            no_orders_label = QLabel("ยังไม่มีออเดอร์ในระบบ")
            no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_orders_label.setStyleSheet("font-size: 16px; color: #888; padding: 40px;")
            self.cards_layout.addWidget(no_orders_label, 0, Qt.AlignmentFlag.AlignCenter)
            return

        for order_id, order_data in self.all_orders_data.items():
            items_list = self.all_items_data.get(order_id, [])
            
            card = OrderCard(order_data, items_list)
            card.card_clicked.connect(self.on_card_selected)
            
            self.cards_layout.addWidget(card)
            self.card_widgets[order_id] = card
            
        self.cards_layout.addStretch()
        self.current_selected_id = None

    def on_card_selected(self, order_id):
        """(เหมือนเดิม) Slot เมื่อการ์ดถูกคลิก"""
        
        if self.current_selected_id is not None:
            old_card = self.card_widgets.get(self.current_selected_id)
            if old_card:
                old_card.set_selected(False)
        
        new_card = self.card_widgets.get(order_id)
        if new_card:
            new_card.set_selected(True)
            self.current_selected_id = order_id
            
            order_data = self.all_orders_data.get(order_id)
            items_list = self.all_items_data.get(order_id, [])
            self.update_detail_panel(order_data, items_list)

    def update_detail_panel(self, order_data, items_list=None):
        """ (❗ [แก้ไข] ฟังก์ชันนี้ถูกเขียนใหม่ทั้งหมด) """
        
        # (ล้างรายการสินค้าเก่าใน layout)
        for i in reversed(range(self.detail_items_layout.count())): 
            widget = self.detail_items_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if order_data is None:
            self.detail_order_id_label.setText("ยังไม่ได้เลือกออเดอร์")
            self.detail_status_badge.setText("N/A")
            self.detail_status_badge.setProperty("status", "")
            self.detail_user_label.setText("")
            self.detail_date_label.setText("")
            self.slip_preview.clear()
            self.slip_preview.setText("กรุณาเลือกออเดอร์")
            self.approve_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.current_selected_id = None
            return
            
        # (ถ้ามีข้อมูล)
        # ❗ [แก้ไข] นี่คือลำดับที่ถูกต้องของ tuple
        # (id, username, total_amount, status, slip_image_path, created_at)
        order_id, username, total, status, slip_path, created_at, shipping_address, email = order_data
        
        self.detail_order_id_label.setText(f"Order ID: #{order_id}")
        self.detail_status_badge.setText(status)
        self.detail_status_badge.setProperty("status", status.replace(" ", "_"))
        self.style().polish(self.detail_status_badge) # (บังคับอัปเดต QSS)
        
        self.detail_user_label.setText(f"<b>โดย:</b> {username}")
        self.detail_date_label.setText(f"<b>วันที่:</b> {created_at}")
        
        # (แสดงสลิป)
        if slip_path and os.path.exists(slip_path):
            pixmap = QPixmap(slip_path)
            # (ปรับขนาดให้พอดีกับกรอบ โดยคงสัดส่วน)
            scaled_pixmap = pixmap.scaled(self.slip_preview.width(), self.slip_preview.height(), 
                                            Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
            self.slip_preview.setPixmap(scaled_pixmap)
        else:
            self.slip_preview.clear()
            self.slip_preview.setText(f"ไม่พบไฟล์สลิป\n{slip_path}")
            
        # (แสดงรายการสินค้า)
        if items_list:
            for item in items_list:
                # (item = id, order_id, name, size, qty, price)
                item_name_label = QLabel(f"{item[2]} (Size: {item[3]})")
                item_name_label.setObjectName("ItemNameLabel")
                item_name_label.setWordWrap(True)
                
                item_detail_label = QLabel(f"{item[4]} ชิ้น x ฿{item[5]:,.2f} = ฿{item[4] * item[5]:,.2f}")
                item_detail_label.setObjectName("ItemDetailLabel")
                
                self.detail_items_layout.addWidget(item_name_label)
                self.detail_items_layout.addWidget(item_detail_label)
        else:
            no_items_label = QLabel("ไม่พบรายการสินค้า")
            no_items_label.setObjectName("ItemDetailLabel")
            self.detail_items_layout.addWidget(no_items_label)
        
        # (ควบคุมปุ่ม)
        if status == "Pending Confirmation":
            self.approve_btn.setEnabled(True)
            self.reject_btn.setEnabled(True)
        else:
            # (ถ้าเป็น Completed หรือ Cancelled แล้ว ก็ปิดปุ่ม)
            self.approve_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)

    def approve_order(self):
        """ปุ่มอนุมัติ"""
        if self.current_selected_id is None: return
        self._update_order_status(self.current_selected_id, "Completed")

    def reject_order(self):
        """ปุ่มปฏิเสธ"""
        if self.current_selected_id is None: return
        self._update_order_status(self.current_selected_id, "Cancelled")
        
    def _update_order_status(self, order_id, new_status):
        """(ฟังก์ชันหลัก) อัปเดตสถานะใน DB"""
        
        reply = QMessageBox.question(self, "ยืนยันการอัปเดต",
            f"คุณต้องการเปลี่ยนสถานะของ Order ID: #{order_id}\n"
            f"ไปเป็น '{new_status}' ใช่หรือไม่?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "สำเร็จ", f"อัปเดตสถานะ Order ID: #{order_id} เป็น '{new_status}' เรียบร้อยแล้ว")
            
            # (รีเฟรชข้อมูลทั้งหมด)
            self.load_all_data() 
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ไม่สามารถอัปเดตสถานะได้: {e}")


# =========================
# 🔹 Manage Stock Page
# (คงไว้ - เหมือนเดิม)
# =========================
class TableActionButtons(QWidget):
    """
    (Widget ใหม่) สำหรับใส่ปุ่ม Edit/Delete ลงในตาราง
    """
    # (คงไว้ - เหมือนเดิม)
    edit_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5) 
        layout.setSpacing(0)
        
        layout.addStretch() 

        # Edit Button
        self.edit_btn = QPushButton(" แก้ไข")
        self.edit_btn.setObjectName("TableEditButton")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.clicked.connect(self.edit_clicked.emit)
        layout.addWidget(self.edit_btn)

        # Delete Button
        self.delete_btn = QPushButton(" ลบ")
        self.delete_btn.setObjectName("TableDeleteButton")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self.delete_clicked.emit)
        layout.addWidget(self.delete_btn)

        layout.addStretch() 

        self.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 6px 12px;
                border: none;
                border-radius: 6px; 
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton#TableEditButton {
                background-color: #004aad;
                color: white;
                margin-right: 2px; 
            }
            QPushButton#TableEditButton:hover {
                background-color: #003580;
            }
            QPushButton#TableDeleteButton {
                background-color: #d9534f;
                color: white;
                margin-left: 2px; 
            }
            QPushButton#TableDeleteButton:hover {
                background-color: #c9302c;
            }
        """)

class ManageStockPage(QWidget):
    """
    (❗ อัปเดต) หน้านี้จะแสดงสต็อกสินค้า
    พร้อม 3 อันดับสินค้าขายดี และเรียงตารางตามยอดขาย
    """
    edit_product_requested = pyqtSignal(int) 
    add_product_requested = pyqtSignal()     

    # ❗ [เพิ่ม] รับ orders_db_path เพิ่ม
    def __init__(self, image_folder, db_path="products.db", orders_db_path="orders.db"):
        super().__init__()
        self.setObjectName("ManageStockPage")
        self.image_folder = image_folder
        self.db_path = db_path
        self.orders_db_path = orders_db_path # 👈 [เพิ่ม] เก็บ path
        self.products_data = []  
        self.initUI()
        self.apply_page_styles()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 30)
        main_layout.setSpacing(20)

        # --- 1. Header Section ---
        header_layout = QHBoxLayout()
        title = QLabel("จัดการสต็อกสินค้า (Manage Stock)")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setObjectName("MainTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # --- 2. ❗ [เพิ่ม] Best Sellers Section ---
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        
        # (สร้าง Card 3 ใบ และ Label ภายใน)
        self.bs1_name = QLabel("N/A")
        self.bs1_sold = QLabel("0 units")
        kpi_layout.addWidget(self._create_bestseller_card("🏆 อันดับ 1", self.bs1_name, self.bs1_sold))
        
        self.bs2_name = QLabel("N/A")
        self.bs2_sold = QLabel("0 units")
        kpi_layout.addWidget(self._create_bestseller_card("🥈 อันดับ 2", self.bs2_name, self.bs2_sold))
        
        self.bs3_name = QLabel("N/A")
        self.bs3_sold = QLabel("0 units")
        kpi_layout.addWidget(self._create_bestseller_card("🥉 อันดับ 3", self.bs3_name, self.bs3_sold))
        
        main_layout.addLayout(kpi_layout)

        # --- 3. ❗ [แก้ไข] Table Widget ---
        self.table_widget = QTableWidget()
        self.table_widget.setObjectName("ProductTable")
        
        # ❗ [แก้ไข] เพิ่มคอลัมน์ "ขายแล้ว" (เป็น 7 คอลัมน์)
        self.table_widget.setColumnCount(7) 
        self.table_widget.setHorizontalHeaderLabels([
            "ID", "รูปภาพ", "ชื่อสินค้า", "ราคา", "สต็อก", "ขายแล้ว", "การกระทำ"
        ])
        
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table_widget.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table_widget.setAlternatingRowColors(True)
        
        # ❗ [แก้ไข] ปรับขนาดคอลัมน์
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed) # Image
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Price
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Stock
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # 👈 [เพิ่ม] Sold
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed) # 👈 [แก้ไข] Actions (ย้ายไป 6)
        
        self.table_widget.setColumnWidth(1, 120) 
        self.table_widget.setColumnWidth(6, 200) # 👈 [แก้ไข] Actions (ย้ายไป 6)
        
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.verticalHeader().setDefaultSectionSize(110)

        main_layout.addWidget(self.table_widget, 1)

    def _create_bestseller_card(self, rank_text, name_label, sold_label):
        """(Helper) สร้าง QFrame สำหรับการ์ด Best Seller"""
        card = QFrame()
        card.setObjectName("KpiCard")
        layout = QVBoxLayout(card)
        
        rank_label = QLabel(rank_text)
        rank_label.setObjectName("BSRank")
        layout.addWidget(rank_label)
        
        name_label.setObjectName("BSName")
        name_label.setWordWrap(True) # (เผื่อชื่อยาว)
        layout.addWidget(name_label)
        
        sold_label.setObjectName("BSSold")
        layout.addWidget(sold_label)
        
        layout.addStretch()
        return card

    def apply_page_styles(self):
        self.setStyleSheet("""
            QWidget#ManageStockPage { 
                background-color: #ffffff; 
            } 
            
            QLabel#MainTitle { 
                color: #2c3e50; 
                background-color: transparent;
            }
            
            /* --- ❗ [เพิ่ม] สไตล์สำหรับ Best Seller Cards (คล้าย KpiCard) --- */
            QFrame#KpiCard {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                min-height: 120px;
            }
            QLabel#BSRank {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding-bottom: 8px;
            }
            QLabel#BSName {
                font-size: 18px;
                font-weight: bold;
                color: #005a9c; /* (สีน้ำเงินเข้ม) */
            }
            QLabel#BSSold {
                font-size: 14px;
                color: #555;
                font-weight: bold;
                padding-top: 5px;
            }
            /* --- สิ้นสุดส่วนที่เพิ่ม --- */

            /* --- Table Widget --- */
            QTableWidget#ProductTable {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                gridline-color: #f0f0f0;
                font-size: 14px;
            }
            
            QTableWidget#ProductTable::item {
                padding: 10px;
                color: #333;
                vertical-align: middle; 
            }
            
            QTableWidget#ProductTable::item:selected {
                background-color: white; 
                color: #333;
            }
            
            QTableWidget#ProductTable::item:hover {
                background-color: white;
                color: #333; 
            }
            
            QTableWidget#ProductTable::item:selected:hover {
                background-color: white; 
                color: #333;
            }
            
            QTableWidget#ProductTable::item:focus {
                background-color: white; 
                color: #333;     
                outline: none; /* ลบกรอบประสีฟ้า/เขียว ตอน focus */
            }
            
            QTableWidget::alternating-row-color {
                background-color: #f9f9f9;
            }

            /* (Table Header) */
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            /* --- Custom Scrollbar --- */
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0; 
                width: 12px;
                margin: 13px 0 13px 0; 
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 6px;
                min-height: 25px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)    

    def refresh_products(self):
        """ (❗ [แก้ไข] โหลด/รีโหลดสินค้า (จาก products.db)
            และดึงยอดขาย (จาก orders.db) มารวมกัน """
        
        print("Refreshing Manage Stock Table with Sales Data...")
        
        sales_lookup = {}
        top_3_sellers = []
        
        # --- 1. ดึงข้อมูลยอดขายจาก orders.db ---
        try:
            conn_orders = sqlite3.connect(self.orders_db_path)
            conn_orders.row_factory = sqlite3.Row
            cur_orders = conn_orders.cursor()
            
            # (Query หายอดขายรวมของสินค้าแต่ละชื่อ ที่ Status = Completed)
            cur_orders.execute("""
                SELECT 
                    oi.product_name, 
                    SUM(oi.quantity) as TotalSold
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status = 'Completed'
                GROUP BY oi.product_name
                ORDER BY TotalSold DESC
            """)
            
            all_sales = cur_orders.fetchall()
            
            # (เก็บ 3 อันดับแรก)
            top_3_sellers = all_sales[:3]
            
            # (สร้าง Dictionary เพื่อค้นหาได้ง่าย)
            sales_lookup = {row['product_name']: row['TotalSold'] for row in all_sales}
            
            conn_orders.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error (Orders)", f"ไม่สามารถโหลดข้อมูลยอดขายได้: {e}")
        
        # --- 2. อัปเดตการ์ด 3 อันดับแรก ---
        self.update_bestseller_cards(top_3_sellers)
        
        # --- 3. ดึงข้อมูลสินค้าจาก products.db และรวมข้อมูล ---
        combined_data = []
        try:
            conn_products = sqlite3.connect(self.db_path)
            conn_products.row_factory = sqlite3.Row 
            cur_products = conn_products.cursor()
            
            cur_products.execute("SELECT id, name, image_path, price, quantity FROM products")
            all_products = cur_products.fetchall()
            conn_products.close()
            
            # (รวมข้อมูล)
            for product in all_products:
                sold_count = sales_lookup.get(product['name'], 0)
                combined_data.append({
                    'id': product['id'],
                    'name': product['name'],
                    'image_path': product['image_path'],
                    'price': product['price'],
                    'quantity': product['quantity'],
                    'total_sold': sold_count  # 👈 [เพิ่ม] เพิ่มยอดขาย
                })

            # --- 4. ❗ [สำคัญ] เรียงลำดับข้อมูลตามยอดขาย (มากไปน้อย) ---
            self.products_data = sorted(combined_data, key=lambda x: x['total_sold'], reverse=True)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error (Products)", f"ไม่สามารถโหลดสินค้าได้: {e}")
            return
        
        # --- 5. แสดงผลในตาราง ---
        self.populate_table()

    def update_bestseller_cards(self, top_3_sellers):
        """ (Helper) อัปเดตข้อความในการ์ด 3 อันดับแรก """
        
        # (ล้างข้อมูลเก่า)
        self.bs1_name.setText("N/A")
        self.bs1_sold.setText("0 units")
        self.bs2_name.setText("N/A")
        self.bs2_sold.setText("0 units")
        self.bs3_name.setText("N/A")
        self.bs3_sold.setText("0 units")
        
        # (ใส่ข้อมูลใหม่)
        if len(top_3_sellers) > 0:
            self.bs1_name.setText(top_3_sellers[0]['product_name'])
            self.bs1_sold.setText(f"{top_3_sellers[0]['TotalSold']} units")
        
        if len(top_3_sellers) > 1:
            self.bs2_name.setText(top_3_sellers[1]['product_name'])
            self.bs2_sold.setText(f"{top_3_sellers[1]['TotalSold']} units")
            
        if len(top_3_sellers) > 2:
            self.bs3_name.setText(top_3_sellers[2]['product_name'])
            self.bs3_sold.setText(f"{top_3_sellers[2]['TotalSold']} units")

    def populate_table(self):
        """ (❗ [แก้ไข]) ล้างตารางเก่า และสร้างแถวใหม่จากข้อมูลที่ *รวมยอดขายแล้ว* """
        
        self.table_widget.setRowCount(0) 
        
        if not self.products_data:
            return

        self.table_widget.setRowCount(len(self.products_data))
        
        for row_index, product_row in enumerate(self.products_data):
            
            # (ดึงข้อมูลจาก dict ที่รวมไว้แล้ว)
            product_id = product_row['id']
            image_path = product_row['image_path']
            name = product_row['name']
            price = product_row['price']
            quantity = product_row['quantity']
            total_sold = product_row['total_sold'] # 👈 [เพิ่ม]

            # --- 0. ID ---
            id_item = QTableWidgetItem(str(product_id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row_index, 0, id_item)

            # --- 1. Image ---
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setFixedSize(100, 100)
            img_label.setStyleSheet("background-color: #f9f9f9; border: 1px solid #f0f0f0; border-radius: 6px;")
            
            full_path = os.path.join(self.image_folder, image_path) if image_path else ""
            if image_path and os.path.exists(full_path):
                pixmap = QPixmap(full_path)
                img_label.setPixmap(pixmap.scaled(
                    100, 100, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                img_label.setText("No Img")
                
            self.table_widget.setCellWidget(row_index, 1, img_label)

            # --- 2. Name ---
            name_item = QTableWidgetItem(name)
            self.table_widget.setItem(row_index, 2, name_item)

            # --- 3. Price ---
            price_item = QTableWidgetItem(price)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_widget.setItem(row_index, 3, price_item)

            # --- 4. Stock ---
            stock_item = QTableWidgetItem(str(quantity))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if quantity <= 0:
                stock_item.setForeground(QBrush(QColor("#c9302c"))) # แดง
                stock_item.setText(f"{quantity} (Out of Stock)")
            elif quantity < 10:
                stock_item.setForeground(QBrush(QColor("#b98900"))) # ส้ม
                stock_item.setText(f"{quantity} (Low Stock)")
            else:
                stock_item.setForeground(QBrush(QColor("#006a38"))) # เขียว
            
            self.table_widget.setItem(row_index, 4, stock_item)

            # --- 5. ❗ [เพิ่ม] Sold ---
            sold_item = QTableWidgetItem(str(total_sold))
            sold_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if total_sold > 0:
                # (ถ้าขายได้ ให้เป็นสีน้ำเงินเข้ม)
                sold_item.setForeground(QBrush(QColor("#004aad")))
                sold_item.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            self.table_widget.setItem(row_index, 5, sold_item)

            # --- 6. ❗ [แก้ไข] Actions (ย้ายไปคอลัมน์ 6) ---
            action_buttons = TableActionButtons()
            action_buttons.edit_clicked.connect(lambda pid=product_id: self.handle_edit_request(pid))
            action_buttons.delete_clicked.connect(lambda pid=product_id: self.handle_delete_product(pid))
            
            self.table_widget.setCellWidget(row_index, 6, action_buttons)
            
        self.table_widget.resizeRowsToContents()
        self.table_widget.verticalHeader().setDefaultSectionSize(110)

    def handle_edit_request(self, product_id):
        """(Slot) ถูกเรียกเมื่อปุ่ม 'แก้ไข' ในตารางถูกคลิก"""
        print(f"Table requested edit for ID: {product_id}")
        self.edit_product_requested.emit(product_id)

    def handle_delete_product(self, product_id):
        """(Slot) ถูกเรียกเมื่อปุ่ม 'ลบ' ในตารางถูกคลิก"""
        
        product_name = "สินค้านี้"
        for data in self.products_data:
            if data['id'] == product_id:
                product_name = data['name']
                break
                
        reply = QMessageBox.question(self, 'ยืนยันการลบ', 
                                     f"คุณต้องการลบ '{product_name}' (ID: {product_id}) ใช่หรือไม่?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            print(f"Deleting product with ID: {product_id}")
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
                conn.close()
                
                self.refresh_products()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"ไม่สามารถลบสินค้าได้: {e}")

# ==================================
# 🆕 🔹 Sales Dashboard Page (❗ อัปเดตใหม่)
# ==================================
class SalesDashboardPage(QWidget):
    """
    (❗ อัปเดตใหม่) หน้าสำหรับแสดงประวัติยอดขาย พร้อมปฏิทินสำหรับเลือกวัน
    """
    def __init__(self, db_path="orders.db"):
        super().__init__()
        self.db_path = db_path
        self.setObjectName("SalesDashboardPage")
        self.initUI()
        self.apply_styles()
        # (เชื่อมต่อ Signal ของปฏิทิน)
        self.calendar.selectionChanged.connect(self.on_date_selected)

    def initUI(self):
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Scroll Area หลัก ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("MainScrollArea")
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # 👈 (เพิ่ม: ซ่อน Scrollbar)
        main_v_layout.addWidget(scroll_area)
        
        main_widget = QWidget() # (Widget ภายใน ScrollArea)
        # ❗ [แก้ไข] เพิ่ม ObjectName เพื่อให้ QSS ทำงาน
        main_widget.setObjectName("DashboardMainWidget") 
        scroll_area.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget) # (Layout ของ main_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 25, 30, 30)
        layout.setSpacing(25)

        # --- 1. Header ---
        header_layout = QHBoxLayout()
        title = QLabel(" สรุปยอดขาย (Sales Dashboard)")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setObjectName("MainTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 รีเฟรชข้อมูล")
        self.refresh_btn.setObjectName("RefreshButton") # (ใช้สไตล์ #RefreshButton)
        self.refresh_btn.setMinimumHeight(45)
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)

        # --- 2. Layout สำหรับการ์ด (Grid) ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(25)
        layout.addLayout(grid_layout)

        # --- Card 1: สถิติรวมทั้งหมด (All-Time) ---
        all_time_card = QFrame()
        all_time_card.setObjectName("KpiCard")
        all_time_layout = QVBoxLayout(all_time_card)
        
        all_time_title = QLabel("สถิติรวมทั้งหมด (All-Time)")
        all_time_title.setObjectName("CardTitle")
        all_time_layout.addWidget(all_time_title)
        
        self.all_time_revenue_label = QLabel("฿0.00")
        self.all_time_revenue_label.setObjectName("KpiValue")
        all_time_layout.addWidget(self.all_time_revenue_label)
        
        self.all_time_units_label = QLabel("ขายไปแล้ว 0 ตัว")
        self.all_time_units_label.setObjectName("KpiSubText")
        all_time_layout.addWidget(self.all_time_units_label)
        
        all_time_layout.addStretch()
        grid_layout.addWidget(all_time_card, 0, 0) # 👈 (Row 0, Col 0)

        # --- Card 2: สถิติวันนี้ (Today) ---
        today_card = QFrame()
        today_card.setObjectName("KpiCard")
        today_layout = QVBoxLayout(today_card)
        
        today_title = QLabel("ยอดขายวันนี้ (Today)")
        today_title.setObjectName("CardTitle")
        today_layout.addWidget(today_title)
        
        self.today_revenue_label = QLabel("฿0.00")
        self.today_revenue_label.setObjectName("KpiValue")
        today_layout.addWidget(self.today_revenue_label)
        
        self.today_units_label = QLabel("ขายไปแล้ว 0 ตัว")
        self.today_units_label.setObjectName("KpiSubText")
        today_layout.addWidget(self.today_units_label)
        
        today_layout.addStretch()
        grid_layout.addWidget(today_card, 0, 1) # 👈 (Row 0, Col 1)

        # --- ❗ (ใหม่) Card 3: ปฏิทิน ---
        calendar_card = QFrame()
        calendar_card.setObjectName("KpiCard") # (ใช้ KpiCard เพื่อให้มีพื้นหลังสีขาวขอบมน)
        calendar_layout = QVBoxLayout(calendar_card)
        calendar_layout.setSpacing(10)
        
        calendar_title = QLabel("เลือกวันที่")
        calendar_title.setObjectName("CardTitle")
        calendar_layout.addWidget(calendar_title)
        
        self.calendar = QCalendarWidget()
        self.calendar.setObjectName("SalesCalendar")
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        
        # (โค้ดไฮไลท์สีครีมถูกลบไปแล้ว)
        
        calendar_layout.addWidget(self.calendar)
        
        grid_layout.addWidget(calendar_card, 0, 2, 2, 1) # 👈 (Row 0, Col 2, ยืด 2 แถว)

        # --- ❗ (ใหม่) Card 4: สถิติสำหรับวันที่เลือก ---
        selected_day_card = QFrame()
        selected_day_card.setObjectName("KpiCard")
        selected_day_layout = QVBoxLayout(selected_day_card)
        
        self.selected_day_title = QLabel("สถิติสำหรับวันที่เลือก")
        self.selected_day_title.setObjectName("CardTitle")
        selected_day_layout.addWidget(self.selected_day_title)
        
        self.selected_revenue_label = QLabel("฿0.00")
        self.selected_revenue_label.setObjectName("KpiValue")
        selected_day_layout.addWidget(self.selected_revenue_label)
        
        self.selected_units_label = QLabel("ขายไปแล้ว 0 ตัว")
        self.selected_units_label.setObjectName("KpiSubText")
        selected_day_layout.addWidget(self.selected_units_label)
        
        selected_day_layout.addStretch()
        grid_layout.addWidget(selected_day_card, 1, 0) # 👈 (Row 1, Col 0)

        # --- ❗ (แก้ไข) Card 5: รายการที่ขายในวันที่เลือก ---
        selected_items_card = QFrame()
        selected_items_card.setObjectName("TableCard")
        selected_items_layout = QVBoxLayout(selected_items_card)
        selected_items_layout.setContentsMargins(0, 0, 0, 0)
        
        self.selected_items_title = QLabel("รายการที่ขายได้ในวันที่เลือก")
        self.selected_items_title.setObjectName("CardTitle")
        self.selected_items_title.setStyleSheet("padding: 20px; padding-bottom: 10px;")
        selected_items_layout.addWidget(self.selected_items_title)
        
        self.selected_items_table = QTableWidget()
        self.selected_items_table.setColumnCount(3)
        self.selected_items_table.setHorizontalHeaderLabels(["ชื่อสินค้า", "ขนาด", "จำนวน"])
        self.selected_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.selected_items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.selected_items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.selected_items_table.setAlternatingRowColors(True)
        self.selected_items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        selected_items_layout.addWidget(self.selected_items_table)
        grid_layout.addWidget(selected_items_card, 1, 1) # 👈 (Row 1, Col 1)

        # (ตั้งค่าให้ Grid ยืดหยุ่น)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 2) # (ให้ตารางรายการสินค้ากว้างขึ้น)
        grid_layout.setColumnStretch(2, 1) 
        
        layout.addStretch() # 👈 (เพิ่ม: ดันการ์ดทั้งหมดขึ้นบน)

    def apply_styles(self):
        # 🎨 (คงไว้) QSS ที่แก้ไขสำหรับปฏิทินธีมสว่าง
        self.setStyleSheet("""
            /* ❗ [แก้ไข] เปลี่ยนตัวหลักเป็น #ffffff */
            QWidget {
                background-color: #ffffff;
            }
            /* ❗ [แก้ไข] กำหนดเป้าหมาย Widget ภายใน ScrollArea */
            QWidget#DashboardMainWidget {
                background-color: #ffffff;
            }
            QScrollArea#MainScrollArea { 
                border: none; 
                background-color: #ffffff; 
            }
            QLabel#MainTitle { 
                color: #2c3e50; 
            }
            
            /* --- สไตล์การ์ด KPI --- */
            QFrame#KpiCard {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 25px;
                min-height: 150px;
            }
            QLabel#CardTitle {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding-bottom: 10px;
            }
            QLabel#KpiValue {
                font-size: 36px;
                font-weight: bold;
                color: #005a9c; /* (สีน้ำเงินเข้ม) */
                padding-bottom: 5px;
            }
            QLabel#KpiSubText {
                font-size: 14px;
                color: #555;
            }
            
            /* --- 🎨 (คงไว้) สไตล์ปฏิทิน (ธีมสว่าง) --- */
            QCalendarWidget {
                background-color: #ffffff; 
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar { 
                background-color: #f5f5f5; 
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QCalendarWidget QToolButton {
                color: #004aad; 
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                padding: 10px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e0e0e0; 
                border-radius: 6px;
            }
            QCalendarWidget QSpinBox, QCalendarWidget QAbstractSpinBox {
                color: #004aad; 
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff; 
                color: #333;
                border: 1px solid #d0d0d0;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #004aad; 
                color: white;
            }
            QCalendarWidget QTableView {
                background-color: #ffffff; 
                border: 1px solid #e0e0e0;
                border-top: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                gridline-color: #f0f0f0; 
            }
            QCalendarWidget QTableView QHeaderView::section {
                background-color: #f9f9f9;
                border: none;
                padding: 8px;
                font-weight: bold;
                color: #555;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #333; 
                font-size: 13px;
                font-weight: normal;
                selection-background-color: #004aad; 
                selection-color: white; 
                outline: none; 
            }
            QCalendarWidget QAbstractItemView:disabled {
                 color: #c0c0c0; 
            }
            
            /* --- สไตล์การ์ดตาราง --- */
            QFrame#TableCard {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                min-height: 400px;
            }
            
            /* ❗ [แก้ไข] เพิ่ม background-color: #ffffff; ให้ตาราง */
            QTableWidget {
                border: none; 
                background-color: #ffffff;
                gridline-color: #f0f0f0;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 10px 15px;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #f0f0f0;
                color: #333;
            }
            QTableWidget::alternating-row-color {
                background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            /* --- ปุ่ม Refresh --- */
            QPushButton#RefreshButton {
                background-color: #004aad;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#RefreshButton:hover {
                background-color: #003580;
            }
            
            /* --- Custom Scrollbar --- */
            QScrollBar:vertical {
                border: none; background: #f0f0f0; 
                width: 12px; margin: 13px 0 13px 0; border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0; border-radius: 6px; min-height: 25px;
            }
            QScrollBar::handle:vertical:hover { background: #a0a0a0; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

    #
    # (ฟังก์ชันที่เหลือของ SalesDashboardPage เหมือนเดิม)
    #
    def refresh_data(self):
        """
        (Public Method) โหลดข้อมูลสถิติ (All-Time, Today, Period) และ
        เรียกใช้ on_date_selected() เพื่อโหลดข้อมูลตามวันที่เลือก
        """
        print("Refreshing Sales Dashboard...")
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # --- 1. คำนวณสถิติรวม (All-Time) ---
            cur.execute("""
                SELECT SUM(o.total_amount), SUM(oi.quantity)
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'Completed'
            """)
            all_time_stats = cur.fetchone()
            all_time_revenue = all_time_stats[0] or 0
            all_time_units = all_time_stats[1] or 0
            
            self.all_time_revenue_label.setText(f"฿{all_time_revenue:,.2f}")
            self.all_time_units_label.setText(f"ขายไปแล้ว {all_time_units} ตัว")

            # --- 2. คำนวณสถิติวันนี้ (Today) ---
            today_date_str = QDate.currentDate().toString("yyyy-MM-dd")
            cur.execute("""
                SELECT SUM(o.total_amount), SUM(oi.quantity)
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'Completed' AND DATE(o.created_at, 'localtime') = ?
            """, (today_date_str,))
            today_stats = cur.fetchone()
            today_revenue = today_stats[0] or 0
            today_units = today_stats[1] or 0
            
            self.today_revenue_label.setText(f"฿{today_revenue:,.2f}")
            self.today_units_label.setText(f"ขายไปแล้ว {today_units} ตัว")

            conn.close()
            
            # --- 4. (สำคัญ) โหลดข้อมูลสำหรับวันที่เลือกในปฏิทิน ---
            self.on_date_selected()
            
            print("Sales Dashboard refresh complete.")
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ไม่สามารถโหลดข้อมูลสถิติได้: {e}")

    def on_date_selected(self):
        """
        (❗ ใหม่) Slot นี้ทำงานเมื่อผู้ใช้คลิกวันที่ในปฏิทิน
        """
        selected_date = self.calendar.selectedDate()
        selected_date_str_db = selected_date.toString("yyyy-MM-dd") # (สำหรับ Query)
        selected_date_str_ui = selected_date.toString("dd/MM/yyyy") # (สำหรับแสดงผล)
        
        print(f"Calendar date selected: {selected_date_str_db}")

        # (อัปเดต Title)
        self.selected_day_title.setText(f"สถิติสำหรับวันที่ {selected_date_str_ui}")
        self.selected_items_title.setText(f"รายการที่ขายได้ในวันที่ {selected_date_str_ui}")

        # (เรียกฟังก์ชันโหลดข้อมูลสำหรับวันนั้นๆ)
        self.load_data_for_date(selected_date_str_db)

    def load_data_for_date(self, date_str):
        """
        (❗ ใหม่) โหลด KPI และ Items สำหรับวันที่ที่ระบุ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # --- 1. คำนวณสถิติสำหรับวันที่เลือก (KPI) ---
            cur.execute("""
                SELECT SUM(o.total_amount), SUM(oi.quantity)
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'Completed' AND DATE(o.created_at, 'localtime') = ?
            """, (date_str,))
            
            selected_stats = cur.fetchone()
            selected_revenue = selected_stats[0] or 0
            selected_units = selected_stats[1] or 0
            
            self.selected_revenue_label.setText(f"฿{selected_revenue:,.2f}")
            self.selected_units_label.setText(f"ขายไปแล้ว {selected_units} ตัว")

            # --- 2. ดึงรายการที่ขายในวันที่เลือก (Table) ---
            cur.execute("""
                SELECT oi.product_name, oi.size, SUM(oi.quantity) as TotalQuantity
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status = 'Completed' AND DATE(o.created_at, 'localtime') = ?
                GROUP BY oi.product_name, oi.size
                ORDER BY TotalQuantity DESC
            """, (date_str,))
            
            selected_items = cur.fetchall()
            # (อัปเดตตาราง selected_items_table)
            self.populate_table(self.selected_items_table, selected_items)
            
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"ไม่สามารถโหลดข้อมูลสำหรับวันที่ {date_str} ได้: {e}")

    def populate_table(self, table_widget, data):
        """
        (Helper) เคลียร์และเติมข้อมูลลงใน QTableWidget
        """
        table_widget.setRowCount(0)
        if not data:
            return
            
        table_widget.setRowCount(len(data))
        for row_index, row_data in enumerate(data):
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                if col_index > 0: # (จัดชิดขวาสำหรับตัวเลข/ยอดเงิน)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table_widget.setItem(row_index, col_index, item)
        
        table_widget.resizeRowsToContents()

        
# =========================
# 🔹 Sidebar (คงไว้ - เหมือนเดิม)
# =========================
class Sidebar(QFrame):
    menu_clicked = pyqtSignal(str)
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = image_folder
        self.initUI()
    def initUI(self):
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            QFrame {
                background-color: #1a0033;
                border: none;
                color: white;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 10, 25, 10)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        logo_label = QLabel()
        logo_path = os.path.join(self.image_folder, "logo.png")
        if os.path.exists(logo_path):
            logo_pix = QPixmap(logo_path)
            logo_label.setPixmap(
                logo_pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
            )
        else:
            logo_label.setText("Logo")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        shop_label = QLabel("Admin Panel") 
        shop_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        shop_label.setStyleSheet("color: white;")
        layout.addWidget(shop_label)
        layout.addStretch()
        
        # ❗ (อัปเดต) เพิ่ม "Sales Dashboard"
        menu_items = [
            "Sales Dashboard", 
            "Manage Stock", 
            "Manage Orders", 
            "Add Product", 
            "Edit Product", 
            "Logout"
        ]
        
        self.buttons = {}
        for item in menu_items:
            btn = QPushButton(item)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFont(QFont("Segoe UI", 11))
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 8px 14px;
                    border-radius: 6px;
                    color: white;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #5b5b58;
                }
                QPushButton:checked {
                    background-color: #004aad;
                    color: white;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, b=btn, name=item: self.handle_menu_click(b, name))
            self.buttons[item] = btn
            layout.addWidget(btn)
            
    def handle_menu_click(self, btn, name):
        for b in self.buttons.values():
            if b is not btn:
                b.setChecked(False)
        btn.setChecked(True)
        self.menu_clicked.emit(name)


# =========================
# 🔹 MainApp (คงไว้ - เหมือนเดิม)
# =========================
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arai Football Shop (Admin Panel)")
        self.image_folder = "C:/project/picture/" # (❗ ใช้ Path ของคุณ)
        self.db_path = "products.db"
        self.orders_db_path = "orders.db" # (❗ เพิ่ม Path ของ DB Orders)
        self.setStyleSheet("QMainWindow { background-color: #f4f7f6; }")
        
        # (สร้างโฟลเดอร์รูปภาพ ถ้ายังไม่มี)
        os.makedirs(self.image_folder, exist_ok=True)
        
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0) 

        self.sidebar = Sidebar(self.image_folder)
        self.sidebar.menu_clicked.connect(self.handle_menu)
        main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1) # (ยืด Stack)

        self.pages = {}
        
        # (❗ อัปเดต: สร้างหน้าต่างๆ)
        self.pages["Sales Dashboard"] = SalesDashboardPage(self.orders_db_path) # ❗ (เพิ่ม)
        self.pages["Manage Stock"] = ManageStockPage(self.image_folder, self.db_path) 
        self.pages["Add Product"]  = AddProductPage(self.image_folder, self.db_path) 
        self.pages["Edit Product"] = EditProductPage(self.image_folder, self.db_path)
        self.pages["Manage Orders"] = AdminOrderPage() 

        for page in self.pages.values():
            self.stack.addWidget(page)

        self.setCentralWidget(central)

        # (เชื่อมต่อ Signal จากหน้า Manage Stock)
        self.pages["Manage Stock"].edit_product_requested.connect(self.handle_edit_request)
        self.pages["Manage Stock"].add_product_requested.connect(self.handle_add_request)

        # ❗ (อัปเดต) ตั้งค่าหน้าเริ่มต้นเป็น Sales Dashboard
        self.stack.setCurrentWidget(self.pages["Sales Dashboard"])
        if "Sales Dashboard" in self.sidebar.buttons:
            self.sidebar.buttons["Sales Dashboard"].setChecked(True)
                                
        # (โหลดข้อมูลครั้งแรกสำหรับหน้าเริ่มต้น)
        self.pages["Sales Dashboard"].refresh_data()


    def handle_menu(self, name):
        if name == "Logout":
            reply = QMessageBox.question(
                self, "ยืนยันการ Logout", 
                "คุณต้องการออกจาก Admin Panel และกลับไปหน้าหลัก (test.py) หรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                main_app_path = "C:/project/new/test.py" # (❗ ใช้ Path ของคุณ)
                if not os.path.exists(main_app_path):
                    QMessageBox.critical(self, "File Not Found", 
                                         f"ไม่พบไฟล์ '{main_app_path}'.\n"
                                         f"กรุณาตรวจสอบว่าไฟล์ admin panel นี้ อยู่ในโฟลเดอร์เดียวกับ test.py")
                    self.sidebar.buttons["Logout"].setChecked(False)
                    return
                try:
                    subprocess.Popen([sys.executable, main_app_path])
                    QApplication.instance().quit()
                except Exception as e:
                    QMessageBox.critical(self, "Launch Error", f"ไม่สามารถเปิด {main_app_path} ได้: {e}")
            else: 
                self.sidebar.buttons["Logout"].setChecked(False)
                current_page = self.stack.currentWidget()
                for page_name, page_widget in self.pages.items():
                    if page_widget == current_page:
                        if page_name in self.sidebar.buttons: # (ตรวจสอบก่อน)
                            self.sidebar.buttons[page_name].setChecked(True)
                        break
            return
        
        if name in self.pages:
            print(f"Switching to page: {name}")
            self.stack.setCurrentWidget(self.pages[name])
            
            # (❗ อัปเดต: รีเฟรชข้อมูลทุกครั้งที่คลิกแท็บ)
            
            if name == "Sales Dashboard":
                if hasattr(self.pages[name], "refresh_data"):
                    self.pages[name].refresh_data()
            
            if name == "Manage Stock":
                if hasattr(self.pages[name], "refresh_products"):
                    self.pages[name].refresh_products()
            
            if name == "Manage Orders":
                if hasattr(self.pages[name], "load_all_data"):
                    self.pages[name].load_all_data()
            
            if name == "Edit Product":
                if hasattr(self.pages[name], "populate_product_selector"):
                    self.pages[name].populate_product_selector()
            
            if name == "Add Product":
                if hasattr(self.pages[name], "clear_form"):
                    self.pages[name].clear_form()
        else:
            print(f"No page defined for: {name}")

    # (Slot สำหรับรับ Signal "แก้ไข")
    def handle_edit_request(self, product_id):
        """
        (Slot) ทำงานเมื่อผู้ใช้คลิกการ์ดในหน้า Manage Stock (ดีไซน์ใหม่)
        """
        print(f"Edit requested for Product ID: {product_id}")
        
        edit_page = self.pages.get("Edit Product")
        if not edit_page or not hasattr(edit_page, "load_product_by_id"):
            QMessageBox.warning(self, "Error", "ไม่พบหน้า Edit Product")
            return

        # 1. สลับไปหน้า Edit Product (ทั้งใน Stack และ Sidebar)
        self.stack.setCurrentWidget(edit_page)
        for b in self.sidebar.buttons.values():
            b.setChecked(False)
        self.sidebar.buttons["Edit Product"].setChecked(True)
        
        # 2. สั่งให้หน้า Edit Product โหลด ID นี้
        edit_page.load_product_by_id(product_id)

    # (Slot สำหรับรับ Signal "เพิ่มสินค้า")
    def handle_add_request(self):
        """
        (Slot) ทำงานเมื่อผู้ใช้คลิกปุ่ม "เพิ่มสินค้าใหม่" จากหน้า Manage Stock
        """
        print("Add product requested from Manage Page")
        
        add_page = self.pages.get("Add Product")
        if add_page:
            # 1. สลับไปหน้า Add Product
            self.stack.setCurrentWidget(add_page)
            for b in self.sidebar.buttons.values():
                b.setChecked(False)
            self.sidebar.buttons["Add Product"].setChecked(True)
            
            # 2. เคลียร์ฟอร์ม
            if hasattr(add_page, "clear_form"):
                add_page.clear_form()

        
# 🔹 Run App (คงไว้ - เหมือนเดิม)
# =========================
if __name__ == "__main__":
    init_products_database() 
    init_orders_database() # ❗ (คงไว้) เรียกใช้ฟังก์ชันสร้าง DB Orders ด้วย
    
    app = QApplication(sys.argv)
    
    # (สร้างโฟลเดอร์รูปภาพ ถ้ายังไม่มี - ตรวจสอบอีกครั้งเผื่อรันตรง)
    os.makedirs("C:/project/picture/", exist_ok=True) 
    
    window = MainApp()
    
    # ❗ (คงไว้) ใช้ .showMaximized() เพื่อเปิดเต็มจอ
    window.showMaximized() # 👈 (ใช้คำสั่งนี้เพื่อเปิดเต็มจอ)
    
    sys.exit(app.exec())
