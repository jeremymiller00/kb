"""
Settings dialog for application configuration.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QFileDialog, QPushButton,
    QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from typing import Dict, Any
from pathlib import Path

class SettingsDialog(QDialog):
    """Settings dialog for configuring application."""
    
    def __init__(self, config: Dict[str, Any], parent=None):
        """Initialize settings dialog.
        
        Args:
            config: Current configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config.copy()
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tabs
        tabs = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QFormLayout()
        
        self.data_dir = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_data_dir)
        data_dir_layout = QHBoxLayout()
        data_dir_layout.addWidget(self.data_dir)
        data_dir_layout.addWidget(browse_btn)
        general_layout.addRow("Data Directory:", data_dir_layout)
        
        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(1, 1000)
        self.max_file_size.setSuffix(" MB")
        general_layout.addRow("Max File Size:", self.max_file_size)
        
        self.enable_cache = QCheckBox("Enable Caching")
        general_layout.addRow("", self.enable_cache)
        
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "General")
        
        # Database settings tab
        db_tab = QWidget()
        db_layout = QFormLayout()
        
        self.db_host = QLineEdit()
        db_layout.addRow("Host:", self.db_host)
        
        self.db_port = QSpinBox()
        self.db_port.setRange(1, 65535)
        db_layout.addRow("Port:", self.db_port)
        
        self.db_name = QLineEdit()
        db_layout.addRow("Database:", self.db_name)
        
        self.db_user = QLineEdit()
        db_layout.addRow("Username:", self.db_user)
        
        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.EchoMode.Password)
        db_layout.addRow("Password:", self.db_password)
        
        self.db_pool_size = QSpinBox()
        self.db_pool_size.setRange(1, 100)
        db_layout.addRow("Pool Size:", self.db_pool_size)
        
        db_tab.setLayout(db_layout)
        tabs.addTab(db_tab, "Database")
        
        # AI settings tab
        ai_tab = QWidget()
        ai_layout = QVBoxLayout()
        
        # OpenAI group
        openai_group = QGroupBox("OpenAI")
        openai_layout = QFormLayout()
        
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        openai_layout.addRow("API Key:", self.openai_key)
        
        self.openai_model = QComboBox()
        self.openai_model.addItems(["gpt-4", "gpt-3.5-turbo"])
        openai_layout.addRow("Model:", self.openai_model)
        
        openai_group.setLayout(openai_layout)
        ai_layout.addWidget(openai_group)
        
        # Local models group
        local_group = QGroupBox("Local Models")
        local_layout = QFormLayout()
        
        self.use_local = QCheckBox("Use Local Models")
        local_layout.addRow("", self.use_local)
        
        self.model_path = QLineEdit()
        browse_model_btn = QPushButton("Browse...")
        browse_model_btn.clicked.connect(self._browse_model_path)
        model_path_layout = QHBoxLayout()
        model_path_layout.addWidget(self.model_path)
        model_path_layout.addWidget(browse_model_btn)
        local_layout.addRow("Model Path:", model_path_layout)
        
        local_group.setLayout(local_layout)
        ai_layout.addWidget(local_group)
        
        ai_tab.setLayout(ai_layout)
        tabs.addTab(ai_tab, "AI")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_config(self) -> None:
        """Load current configuration into UI."""
        # General settings
        if storage_cfg := self.config.get('storage', {}):
            self.data_dir.setText(str(storage_cfg.get('base_path', '')))
            self.max_file_size.setValue(
                storage_cfg.get('max_file_size', 100) // (1024 * 1024)  # Convert to MB
            )
            self.enable_cache.setChecked(storage_cfg.get('enable_cache', True))
        
        # Database settings
        if db_cfg := self.config.get('database', {}):
            if conn_str := db_cfg.get('connection_string'):
                # Parse connection string
                try:
                    parts = conn_str.split(' ')
                    for part in parts:
                        if '=' not in part:
                            continue
                        key, value = part.split('=')
                        if key == 'host':
                            self.db_host.setText(value)
                        elif key == 'port':
                            self.db_port.setValue(int(value))
                        elif key == 'dbname':
                            self.db_name.setText(value)
                        elif key == 'user':
                            self.db_user.setText(value)
                        elif key == 'password':
                            self.db_password.setText(value)
                except:
                    pass
            
            self.db_pool_size.setValue(db_cfg.get('max_connections', 5))
        
        # AI settings
        if ai_cfg := self.config.get('ai', {}):
            self.openai_key.setText(ai_cfg.get('openai_api_key', ''))
            
            if model := ai_cfg.get('openai_model'):
                idx = self.openai_model.findText(model)
                if idx >= 0:
                    self.openai_model.setCurrentIndex(idx)
            
            self.use_local.setChecked(ai_cfg.get('use_local_models', False))
            if model_path := ai_cfg.get('local_model_path'):
                self.model_path.setText(str(model_path))
    
    def get_config(self) -> Dict[str, Any]:
        """Get updated configuration.
        
        Returns:
            Updated configuration dictionary
        """
        config = {}
        
        # General settings
        config['storage'] = {
            'base_path': self.data_dir.text(),
            'max_file_size': self.max_file_size.value() * 1024 * 1024,  # Convert to bytes
            'enable_cache': self.enable_cache.isChecked()
        }
        
        # Database settings
        config['database'] = {
            'connection_string': (
                f"host={self.db_host.text()} "
                f"port={self.db_port.value()} "
                f"dbname={self.db_name.text()} "
                f"user={self.db_user.text()} "
                f"password={self.db_password.text()}"
            ),
            'max_connections': self.db_pool_size.value()
        }
        
        # AI settings
        config['ai'] = {
            'openai_api_key': self.openai_key.text(),
            'openai_model': self.openai_model.currentText(),
            'use_local_models': self.use_local.isChecked(),
            'local_model_path': self.model_path.text()
        }
        
        return config
    
    def _browse_data_dir(self) -> None:
        """Browse for data directory."""
        current = self.data_dir.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Data Directory",
            current
        )
        if directory:
            self.data_dir.setText(directory)
    
    def _browse_model_path(self) -> None:
        """Browse for model path."""
        current = self.model_path.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Model Directory",
            current
        )
        if directory:
            self.model_path.setText(directory)