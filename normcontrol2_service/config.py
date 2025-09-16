"""
Конфигурация модуля Нормоконтроль - 2
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ValidationConfig:
    """Конфигурация валидации"""
    critical_issues_threshold: int = 1
    high_issues_threshold: int = 5
    medium_issues_threshold: int = 10
    compliance_score_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.compliance_score_weights is None:
            self.compliance_score_weights = {
                "critical": 0.0,
                "high": 0.3,
                "medium": 0.6,
                "low": 0.8,
                "info": 1.0
            }


@dataclass
class DocumentProcessorConfig:
    """Конфигурация процессоров документов"""
    supported_formats: List[str] = None
    max_file_size_mb: int = 100
    timeout_seconds: int = 300
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["pdf", "dwg", "dxf", "docx", "xlsx"]


@dataclass
class ESKDConfig:
    """Конфигурация требований ЕСКД"""
    gost_21_501_2018_enabled: bool = True
    gost_r_21_101_2020_enabled: bool = True
    gost_21_1101_2013_enabled: bool = True
    gost_21_201_2011_enabled: bool = True


@dataclass
class SPDSConfig:
    """Конфигурация требований СПДС"""
    sp_48_13330_2019_enabled: bool = True
    sp_70_13330_2012_enabled: bool = True
    sp_16_13330_2017_enabled: bool = True
    sp_20_13330_2016_enabled: bool = True


@dataclass
class FontConfig:
    """Конфигурация шрифтов"""
    standard_fonts: List[str] = None
    min_font_size: float = 2.5
    max_font_size: float = 14.0
    standard_sizes: List[float] = None
    
    def __post_init__(self):
        if self.standard_fonts is None:
            self.standard_fonts = [
                "Arial", "Times New Roman", "Calibri", "Tahoma", "Verdana",
                "Helvetica", "Courier New", "Georgia", "Palatino", "Garamond"
            ]
        
        if self.standard_sizes is None:
            self.standard_sizes = [2.5, 3.5, 5.0, 7.0, 10.0, 14.0, 18.0, 24.0, 36.0, 48.0]


@dataclass
class ScaleConfig:
    """Конфигурация масштабов"""
    standard_scales: List[str] = None
    allow_custom_scales: bool = False
    max_scale_value: int = 10000
    
    def __post_init__(self):
        if self.standard_scales is None:
            self.standard_scales = [
                "1:1", "1:2", "1:5", "1:10", "1:20", "1:25", "1:50", "1:100", 
                "1:200", "1:500", "1:1000", "1:2000", "1:5000", "1:10000",
                "2:1", "5:1", "10:1", "20:1", "50:1", "100:1"
            ]


@dataclass
class UnitsConfig:
    """Конфигурация единиц измерений"""
    metric_system_required: bool = True
    standard_units: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.standard_units is None:
            self.standard_units = {
                "length": ["мм", "см", "м", "км"],
                "area": ["мм²", "см²", "м²", "га"],
                "volume": ["мм³", "см³", "м³", "л"],
                "angle": ["°", "град", "рад"],
                "temperature": ["°C", "°F", "K"]
            }


@dataclass
class NotationsConfig:
    """Конфигурация обозначений"""
    standard_symbols: List[str] = None
    standard_abbreviations: List[str] = None
    
    def __post_init__(self):
        if self.standard_symbols is None:
            self.standard_symbols = [
                "Ø", "R", "□", "∠", "∥", "⊥", "±", "°", "×", "÷", "≈", "≠", "≤", "≥"
            ]
        
        if self.standard_abbreviations is None:
            self.standard_abbreviations = [
                "мм", "см", "м", "км", "м²", "м³", "°", "'", "\"", "кг", "т", "г"
            ]


@dataclass
class NormControl2Config:
    """Основная конфигурация модуля Нормоконтроль - 2"""
    validation: ValidationConfig = None
    document_processor: DocumentProcessorConfig = None
    eskd: ESKDConfig = None
    spds: SPDSConfig = None
    fonts: FontConfig = None
    scales: ScaleConfig = None
    units: UnitsConfig = None
    notations: NotationsConfig = None
    
    def __post_init__(self):
        if self.validation is None:
            self.validation = ValidationConfig()
        if self.document_processor is None:
            self.document_processor = DocumentProcessorConfig()
        if self.eskd is None:
            self.eskd = ESKDConfig()
        if self.spds is None:
            self.spds = SPDSConfig()
        if self.fonts is None:
            self.fonts = FontConfig()
        if self.scales is None:
            self.scales = ScaleConfig()
        if self.units is None:
            self.units = UnitsConfig()
        if self.notations is None:
            self.notations = NotationsConfig()


def load_config_from_env() -> NormControl2Config:
    """Загрузка конфигурации из переменных окружения"""
    config = NormControl2Config()
    
    # Настройки валидации
    config.validation.critical_issues_threshold = int(os.getenv("NORM2_CRITICAL_THRESHOLD", "1"))
    config.validation.high_issues_threshold = int(os.getenv("NORM2_HIGH_THRESHOLD", "5"))
    config.validation.medium_issues_threshold = int(os.getenv("NORM2_MEDIUM_THRESHOLD", "10"))
    
    # Настройки процессора документов
    config.document_processor.max_file_size_mb = int(os.getenv("NORM2_MAX_FILE_SIZE_MB", "100"))
    config.document_processor.timeout_seconds = int(os.getenv("NORM2_TIMEOUT_SECONDS", "300"))
    
    # Настройки ЕСКД
    config.eskd.gost_21_501_2018_enabled = os.getenv("NORM2_ESKD_21_501_ENABLED", "true").lower() == "true"
    config.eskd.gost_r_21_101_2020_enabled = os.getenv("NORM2_ESKD_R_21_101_ENABLED", "true").lower() == "true"
    
    # Настройки СПДС
    config.spds.sp_48_13330_2019_enabled = os.getenv("NORM2_SPDS_48_13330_ENABLED", "true").lower() == "true"
    config.spds.sp_70_13330_2012_enabled = os.getenv("NORM2_SPDS_70_13330_ENABLED", "true").lower() == "true"
    
    # Настройки шрифтов
    config.fonts.min_font_size = float(os.getenv("NORM2_MIN_FONT_SIZE", "2.5"))
    config.fonts.max_font_size = float(os.getenv("NORM2_MAX_FONT_SIZE", "14.0"))
    
    # Настройки масштабов
    config.scales.allow_custom_scales = os.getenv("NORM2_ALLOW_CUSTOM_SCALES", "false").lower() == "true"
    config.scales.max_scale_value = int(os.getenv("NORM2_MAX_SCALE_VALUE", "10000"))
    
    # Настройки единиц измерений
    config.units.metric_system_required = os.getenv("NORM2_METRIC_SYSTEM_REQUIRED", "true").lower() == "true"
    
    return config


def load_config_from_file(config_path: str) -> NormControl2Config:
    """Загрузка конфигурации из файла"""
    import json
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Создание конфигурации из JSON
        config = NormControl2Config()
        
        if "validation" in config_data:
            validation_data = config_data["validation"]
            config.validation = ValidationConfig(
                critical_issues_threshold=validation_data.get("critical_issues_threshold", 1),
                high_issues_threshold=validation_data.get("high_issues_threshold", 5),
                medium_issues_threshold=validation_data.get("medium_issues_threshold", 10),
                compliance_score_weights=validation_data.get("compliance_score_weights", {
                    "critical": 0.0, "high": 0.3, "medium": 0.6, "low": 0.8, "info": 1.0
                })
            )
        
        # Аналогично для других секций конфигурации
        # ...
        
        return config
        
    except Exception as e:
        print(f"Ошибка загрузки конфигурации из файла {config_path}: {e}")
        return load_config_from_env()


# Глобальная конфигурация
config = load_config_from_env()
