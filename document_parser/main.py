import os
import hashlib
import json
import logging
import io
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client
from qdrant_client.models import Distance, VectorParams
import magic
import PyPDF2
from docx import Document
import re
import httpx
import asyncio
import tiktoken

# OCR imports
import pytesseract
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_bytes
import tempfile
import math

from datetime import datetime, timedelta


# структура данных о результате проверки документа и проверяемом документе
class DocumentInspectionResult:
    """Структура данных для результата проверки документа"""
    
    def __init__(self):
        # Основная информация о документе
        self.document_id = None # ID документа
        self.document_name = None # Наименование документа. Проверить на соответствие "A9.5.MTH.04"
        self.document_type = None # pdf, docx, dwg, txt
        self.document_engineering_stage = None # ПД, РД, ТЭО
        self.document_mark = None # Марка комплекта документации: КЖ, КМ, АС, ТХ, КС, КП, КР, КРС, КРС-1, КРС-2, КРС-3, КРС-4, КРС-5, КРС-6, КРС-7, КРС-8, КРС-9, КРС-10
        self.document_number = None # Номер комплекта документации
        self.document_date = None # Дата комплекта документации
        self.document_author = None # РАЗРАБОТАЛ комплект документации
        self.document_reviewer = None # ПРОВЕРИЛ комплект документации
        self.document_approver = None # ГИП комплекта документации
        self.document_status = None # Статус комплекта документации: IFR, IFD, IFC, IFS, IFT, IFT-1, IFT-2, IFT-3, IFT-4, IFT-5, IFT-6, IFT-7, IFT-8, IFT-9, IFT-10
        self.document_size = None # Размер файла в байтах
        
        # Информация о страницах
        self.document_pages = None # Количество страниц в документе
        self.document_pages_vector = None # Количество векторных страниц в документе
        self.document_pages_scanned = None # Количество сканированных страниц в документе
        self.document_pages_unknown = None # Количество неизвестных страниц в документе
        self.document_pages_total = None # Общее количество страниц в документе
        self.document_pages_total_a4_sheets_equivalent = None # Общее количество листов А4 эквивалентных в документе
        
        # Статистика по страницам
        self.document_pages_with_violations = None # Количество страниц с отклонениями
        self.document_pages_clean = None # Количество страниц без отклонений
        
        # Общие показатели отклонений
        self.document_total_violations = None # Общее количество выявленных отклонений
        self.document_critical_violations = None # Критические отклонения
        self.document_major_violations = None # Значительные отклонения
        self.document_minor_violations = None # Мелкие отклонения
        self.document_info_violations = None # Информационные замечания
        
        # Процентные показатели
        self.document_compliance_percentage = None # Процент соответствия (0-100)
        self.document_violations_per_page_avg = None # Среднее количество отклонений на страницу
        
        # Устаревшие поля (для обратной совместимости)
        self.document_total_errors_count = None # Общее количество ошибок в документе
        self.document_total_warnings_count = None # Общее количество предупреждений в документе
        self.document_total_info_count = None # Общее количество информационных сообщений в документе
        self.document_total_suggestions_count = None # Общее количество предложений в документе
        self.document_total_corrections_count = None # Общее количество исправлений в документе
        
        # Результаты проверки листов документа
        self.document_pages_results = [] # Результаты проверки листов документа

class DocumentPageInspectionResult:
    """Структура данных для результата проверки листа документа"""
    
    def __init__(self):
        # Основная информация о странице
        self.page_number = None # Номер страницы
        self.page_type = None # vector, scanned, unknown
        self.page_format = None # A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, B0, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10
        self.page_width_mm = None # Ширина страницы в мм
        self.page_height_mm = None # Высота страницы в мм
        self.page_orientation = None # portrait, landscape
        self.page_a4_sheets_equivalent = None # Эквивалент листов А4
        
        # Информация о тексте страницы
        self.page_text = None # Текст листа документа
        self.page_text_confidence = None # Уверенность в тексте листа документа
        self.page_text_method = None # Метод извлечения текста листа документа
        self.page_text_length = None # Длина текста в символах
        
        # Результаты OCR (для сканированных страниц)
        self.page_ocr_confidence = None # Уверенность OCR
        self.page_ocr_method = None # Метод OCR
        self.page_ocr_all_results = [] # Все результаты OCR
        
        # Показатели отклонений на странице
        self.page_violations_count = None # Общее количество отклонений на странице
        self.page_critical_violations = None # Критические отклонения на странице
        self.page_major_violations = None # Значительные отклонения на странице
        self.page_minor_violations = None # Мелкие отклонения на странице
        self.page_info_violations = None # Информационные замечания на странице
        self.page_compliance_percentage = None # Процент соответствия страницы
        
        # Детали отклонений на странице
        self.page_violations_details = [] # Детали отклонений на странице


class DocumentViolationDetail:
    """Структура данных для деталей отклонения"""
    
    def __init__(self):
        self.violation_type = None # critical, major, minor, info
        self.violation_category = None # general_requirements, text_part, graphical_part, specifications, assembly_drawings, detail_drawings, schemes
        self.violation_description = None # Описание отклонения
        self.violation_clause = None # Пункт нормы (например: ГОСТ Р 21.1101-2013 п.5.2)
        self.violation_severity = None # Серьезность (1-5)
        self.violation_recommendation = None # Рекомендация по исправлению
        self.violation_location = None # Местоположение на странице
        self.violation_confidence = None # Уверенность в отклонении (0-1)




# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Parser Service", version="1.0.0")

# Настройки для увеличения лимита размера файлов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Увеличиваем лимит размера файлов до 100MB
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class LargeFileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Увеличиваем лимит для загрузки файлов
        if request.url.path == "/upload" or request.url.path == "/upload/checkable":
            request.scope["max_content_size"] = 100 * 1024 * 1024  # 100MB
        return await call_next(request)

app.add_middleware(LargeFileMiddleware)

# CORS middleware уже добавлен выше

# Конфигурация
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "norms-db")
POSTGRES_DB = os.getenv("POSTGRES_DB", "norms_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "norms_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "norms_password")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8003")

class DocumentParser:
    def __init__(self):
        self.db_conn = None
        self.qdrant_client = None
        self.connect_databases()
    
    def connect_databases(self):
        """Подключение к базам данных"""
        try:
            # PostgreSQL
            self.db_conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            logger.info("Connected to PostgreSQL")
            
            # Qdrant
            self.qdrant_client = qdrant_client.QdrantClient(
                host=QDRANT_HOST,
                port=QDRANT_PORT
            )
            logger.info("Connected to Qdrant")
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Вычисление SHA-256 хеша файла"""
        return hashlib.sha256(file_content).hexdigest()

    def extract_text_from_image(self, image: Image.Image, page_number: int) -> Dict[str, Any]:
        """Извлечение текста из изображения с помощью OCR"""
        try:
            # Конвертируем PIL Image в OpenCV формат
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Предобработка изображения для улучшения OCR
            # Конвертируем в оттенки серого
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Применяем различные методы улучшения
            # 1. Адаптивная пороговая обработка
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # 2. Морфологические операции для удаления шума
            kernel = np.ones((1, 1), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # 3. Увеличение контрастности
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Настройки OCR для русского языка
            custom_config = r'--oem 3 --psm 6 -l rus+eng'
            
            # Пробуем разные варианты обработки
            results = []
            
            # 1. Оригинальное изображение
            try:
                text1 = pytesseract.image_to_string(image, config=custom_config)
                if text1.strip():
                    results.append(("original", text1.strip(), 0.7))
            except Exception as e:
                logger.warning(f"OCR failed on original image for page {page_number}: {e}")
            
            # 2. Обработанное изображение (адаптивная пороговая обработка)
            try:
                text2 = pytesseract.image_to_string(thresh, config=custom_config)
                if text2.strip():
                    results.append(("threshold", text2.strip(), 0.8))
            except Exception as e:
                logger.warning(f"OCR failed on threshold image for page {page_number}: {e}")
            
            # 3. Улучшенное изображение (CLAHE)
            try:
                text3 = pytesseract.image_to_string(enhanced, config=custom_config)
                if text3.strip():
                    results.append(("enhanced", text3.strip(), 0.9))
            except Exception as e:
                logger.warning(f"OCR failed on enhanced image for page {page_number}: {e}")
            
            # Выбираем лучший результат
            if results:
                # Сортируем по длине текста и уверенности
                results.sort(key=lambda x: (len(x[1]), x[2]), reverse=True)
                best_method, best_text, confidence = results[0]
                
                logger.info(f"OCR completed for page {page_number} using {best_method} method, confidence: {confidence}")
                
                return {
                    "text": best_text,
                    "confidence": confidence,
                    "method": best_method,
                    "all_results": results
                }
            else:
                logger.warning(f"No OCR results for page {page_number}")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "method": "none",
                    "all_results": []
                }
                
        except Exception as e:
            logger.error(f"OCR processing error for page {page_number}: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "method": "error",
                "all_results": []
            }

    def get_page_format_info(self, page) -> Dict[str, Any]:
        """Получение информации о формате страницы PDF"""
        try:
            # Получаем размеры страницы в точках (1/72 дюйма)
            media_box = page.mediabox
            width_pt = float(media_box.width)
            height_pt = float(media_box.height)
            
            # Конвертируем в миллиметры (1 дюйм = 25.4 мм, 1 точка = 1/72 дюйма)
            width_mm = width_pt * 25.4 / 72
            height_mm = height_pt * 25.4 / 72
            
            # Определяем стандартный формат
            format_name = self.determine_page_format(width_mm, height_mm)
            
            # Вычисляем количество листов А4
            a4_sheets = self.calculate_a4_sheets(width_mm, height_mm)
            
            return {
                "width_pt": width_pt,
                "height_pt": height_pt,
                "width_mm": round(width_mm, 2),
                "height_mm": round(height_mm, 2),
                "format_name": format_name,
                "a4_sheets": a4_sheets,
                "orientation": "portrait" if height_mm > width_mm else "landscape"
            }
            
        except Exception as e:
            logger.error(f"Error getting page format info: {e}")
            return {
                "width_pt": 0,
                "height_pt": 0,
                "width_mm": 0,
                "height_mm": 0,
                "format_name": "unknown",
                "a4_sheets": 0,
                "orientation": "unknown"
            }

    def determine_page_format(self, width_mm: float, height_mm: float) -> str:
        """Определение стандартного формата страницы"""
        # Стандартные форматы в мм (ширина x высота)
        formats = {
            "A0": (841, 1189),
            "A1": (594, 841),
            "A2": (420, 594),
            "A3": (297, 420),
            "A4": (210, 297),
            "A5": (148, 210),
            "A6": (105, 148),
            "A7": (74, 105),
            "A8": (52, 74),
            "A9": (37, 52),
            "A10": (26, 37),
            "B0": (1000, 1414),
            "B1": (707, 1000),
            "B2": (500, 707),
            "B3": (353, 500),
            "B4": (250, 353),
            "B5": (176, 250),
            "B6": (125, 176),
            "B7": (88, 125),
            "B8": (62, 88),
            "B9": (44, 62),
            "B10": (31, 44),
        }
        
        # Допустимое отклонение в мм
        tolerance = 5
        
        for format_name, (std_width, std_height) in formats.items():
            # Проверяем в обеих ориентациях
            if (abs(width_mm - std_width) <= tolerance and abs(height_mm - std_height) <= tolerance) or \
               (abs(width_mm - std_height) <= tolerance and abs(height_mm - std_width) <= tolerance):
                return format_name
        
        # Если не найден стандартный формат, возвращаем кастомный
        return f"custom_{int(width_mm)}x{int(height_mm)}"

    def calculate_a4_sheets(self, width_mm: float, height_mm: float) -> float:
        """Вычисление количества листов А4 (с округлением)"""
        try:
            # Площадь А4 в мм²
            a4_area = 210 * 297  # 62,370 мм²
            
            # Площадь текущей страницы в мм²
            page_area = width_mm * height_mm
            
            # Количество листов А4
            a4_sheets = page_area / a4_area
            
            # Округляем до 2 знаков после запятой
            return round(a4_sheets, 2)
            
        except Exception as e:
            logger.error(f"Error calculating A4 sheets: {e}")
            return 0.0

    def detect_page_type(self, page) -> str:
        """Определение типа страницы (векторная или сканированная)"""
        try:
            # Извлекаем текст
            text = page.extract_text()
            
            # Если текст извлекается легко и его достаточно, считаем страницу векторной
            if text and len(text.strip()) > 50:
                return "vector"
            
            # Проверяем наличие изображений на странице
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        return "scanned"
            
            # Если текст короткий или отсутствует, считаем сканированной
            if not text or len(text.strip()) < 10:
                return "scanned"
            
            return "vector"
            
        except Exception as e:
            logger.warning(f"Error detecting page type: {e}")
            return "unknown"

    def count_tokens(self, text: str) -> int:
        """Подсчет количества токенов в тексте"""
        try:
            # Используем cl100k_base кодировку (GPT-4, GPT-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Token counting error: {e}")
            # Fallback: приблизительный подсчет по словам
            return len(text.split())

    def calculate_document_tokens(self, elements: List[Dict[str, Any]]) -> int:
        """Подсчет общего количества токенов в документе"""
        total_tokens = 0
        for element in elements:
            content = element.get("element_content", "")
            if content:
                total_tokens += self.count_tokens(content)
        return total_tokens
    
    def detect_file_type(self, file_content: bytes) -> str:
        """Определение типа файла по содержимому"""
        print(f"🔍 [DEBUG] DocumentParser: detect_file_type called with content length: {len(file_content)}")
        print(f"🔍 [DEBUG] DocumentParser: Content preview: {file_content[:100]}...")
        
        mime_type = magic.from_buffer(file_content, mime=True)
        print(f"🔍 [DEBUG] DocumentParser: Magic detected MIME type: {mime_type}")
        
        if mime_type == "application/pdf":
            print(f"🔍 [DEBUG] DocumentParser: Detected as PDF")
            return "pdf"
        else:
            print(f"🔍 [DEBUG] DocumentParser: Unsupported MIME type: {mime_type}")
            raise ValueError(f"Only PDF files are supported. Detected MIME type: {mime_type}")

    def parse_file(self, file_content: bytes, file_type: str) -> List[Dict[str, Any]]:
        """Парсинг файла в зависимости от типа"""
        if file_type == "pdf":
            return self.parse_pdf(file_content)
        elif file_type == "docx":
            return self.parse_docx(file_content)
        elif file_type == "dwg":
            return self.parse_dwg(file_content)
        elif file_type == "txt":
            return self.parse_text(file_content)
        else:
            raise ValueError(f"Unsupported file type for parsing: {file_type}")

    def parse_text(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсинг текстового файла"""
        elements = []
        
        try:
            # Декодируем содержимое файла
            text_content = file_content.decode('utf-8')
            
            # Разбиваем на строки
            lines = text_content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line:  # Пропускаем пустые строки
                    elements.append({
                        "element_type": "text",
                        "element_content": line,
                        "page_number": 1,
                        "confidence_score": 1.0
                    })
            
            return elements
            
        except Exception as e:
            logger.error(f"Text parsing error: {e}")
            raise
    
    def parse_pdf(self, file_content: bytes) -> DocumentInspectionResult:
        """Парсинг PDF документа с поддержкой векторных и сканированных страниц"""
        result = DocumentInspectionResult()
        document_format_stats = {
            "total_pages": 0,
            "total_a4_sheets": 0.0,
            "formats": {},
            "orientations": {"portrait": 0, "landscape": 0},
            "page_types": {"vector": 0, "scanned": 0, "unknown": 0}
        }
        
        try:
            # Создаем file-like объект из bytes
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Получаем информацию о документе
            document_info = self.get_document_info(pdf_reader)
            result.document_name = document_info["name"]
            result.document_type = document_info["type"]
            result.document_engineering_stage = document_info["engineering_stage"]
            result.document_mark = document_info["mark"]
            result.document_number = document_info["number"]
            result.document_date = document_info["date"]
            result.document_author = document_info["author"]
            result.document_reviewer = document_info["reviewer"]
            result.document_approver = document_info["approver"]
            result.document_status = document_info["status"]
            result.document_size = document_info["size"]
            # покажем в лог информацию о документе
            logger.info(f"Document info: {document_info}")
            
            
            document_format_stats["total_pages"] = len(pdf_reader.pages)
            logger.info(f"Processing PDF with {len(pdf_reader.pages)} pages")
            
            # Конвертируем PDF в изображения для OCR
            try:
                images = convert_from_bytes(file_content, dpi=300)
                logger.info(f"Converted PDF to {len(images)} images")
            except Exception as e:
                logger.warning(f"Failed to convert PDF to images: {e}")
                images = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_number = page_num + 1
                logger.info(f"Processing page {page_number}")
                
                # Создаем объект результата страницы
                page_result = DocumentPageInspectionResult()
                page_result.page_number = page_number
                
                # Получаем информацию о формате страницы
                format_info = self.get_page_format_info(page)
                document_format_stats["total_a4_sheets"] += format_info["a4_sheets"]
                
                # Заполняем информацию о формате страницы
                page_result.page_format = format_info["format_name"]
                page_result.page_width_mm = format_info["width_mm"]
                page_result.page_height_mm = format_info["height_mm"]
                page_result.page_orientation = format_info["orientation"]
                page_result.page_a4_sheets_equivalent = format_info["a4_sheets"]
                
                # Обновляем статистику форматов
                format_name = format_info["format_name"]
                if format_name not in document_format_stats["formats"]:
                    document_format_stats["formats"][format_name] = 0
                document_format_stats["formats"][format_name] += 1
                
                # Обновляем статистику ориентаций
                orientation = format_info["orientation"]
                document_format_stats["orientations"][orientation] += 1
                
                # Логируем информацию о формате страницы
                logger.info(f"Page {page_number} format: {format_name} "
                          f"({format_info['width_mm']}x{format_info['height_mm']} mm, "
                          f"{orientation}, {format_info['a4_sheets']} A4 sheets)")
                
                # Определяем тип страницы
                page_type = self.detect_page_type(page)
                page_result.page_type = page_type
                document_format_stats["page_types"][page_type] += 1
                logger.info(f"Page {page_number} type: {page_type}")
                
                if page_type == "vector":
                    # Обработка векторной страницы
                    text = page.extract_text()
                    if text.strip():
                        page_result.page_text = text
                        page_result.page_text_confidence = 0.9
                        page_result.page_text_method = "direct_extraction"
                        page_result.page_text_length = len(text)
                        logger.info(f"Page {page_number}: Extracted {len(text)} characters (vector)")
                    else:
                        logger.warning(f"Page {page_number}: No text extracted from vector page")
                        page_result.page_text = ""
                        page_result.page_text_confidence = 0.0
                        page_result.page_text_method = "failed"
                        page_result.page_text_length = 0
                
                elif page_type == "scanned" and page_num < len(images):
                    # Обработка сканированной страницы с OCR
                    logger.info(f"Page {page_number}: Processing as scanned page with OCR")
                    
                    try:
                        # Извлекаем текст с помощью OCR
                        ocr_result = self.extract_text_from_image(images[page_num], page_number)
                        
                        if ocr_result["text"]:
                            page_result.page_text = ocr_result["text"]
                            page_result.page_text_confidence = ocr_result["confidence"]
                            page_result.page_text_method = f"ocr_{ocr_result['method']}"
                            page_result.page_text_length = len(ocr_result["text"])
                            page_result.page_ocr_confidence = ocr_result["confidence"]
                            page_result.page_ocr_method = ocr_result["method"]
                            page_result.page_ocr_all_results = ocr_result.get("all_results", [])
                            logger.info(f"Page {page_number}: OCR extracted {len(ocr_result['text'])} characters "
                                      f"(confidence: {ocr_result['confidence']})")
                        else:
                            logger.warning(f"Page {page_number}: OCR failed to extract text")
                            page_result.page_text = f"[OCR не смог извлечь текст со страницы {page_number}]"
                            page_result.page_text_confidence = 0.1
                            page_result.page_text_method = "ocr_failed"
                            page_result.page_text_length = 0
                    
                    except Exception as e:
                        logger.error(f"OCR processing failed for page {page_number}: {e}")
                        page_result.page_text = f"[Ошибка OCR обработки страницы {page_number}: {str(e)}]"
                        page_result.page_text_confidence = 0.0
                        page_result.page_text_method = "ocr_error"
                        page_result.page_text_length = 0
                
                else:
                    # Неизвестный тип страницы или нет изображения
                    logger.warning(f"Page {page_number}: Unknown type or no image available")
                    text = page.extract_text()
                    if text.strip():
                        page_result.page_text = text
                        page_result.page_text_confidence = 0.5
                        page_result.page_text_method = "fallback_extraction"
                        page_result.page_text_length = len(text)
                    else:
                        page_result.page_text = f"[Не удалось обработать страницу {page_number}]"
                        page_result.page_text_confidence = 0.0
                        page_result.page_text_method = "failed"
                        page_result.page_text_length = 0
                
                # Добавляем результат страницы в общий результат
                result.document_pages_results.append(page_result)
                
                # TODO: Добавить извлечение таблиц, изображений, штампов
                # с помощью OpenCV и дополнительного анализа
            
            # Заполняем общую статистику документа
            result.document_pages = document_format_stats['total_pages']
            result.document_pages_total = document_format_stats['total_pages']
            result.document_pages_total_a4_sheets_equivalent = document_format_stats['total_a4_sheets']
            result.document_pages_vector = document_format_stats['page_types'].get('vector', 0)
            result.document_pages_scanned = document_format_stats['page_types'].get('scanned', 0)
            result.document_pages_unknown = document_format_stats['page_types'].get('unknown', 0)
            
            # Логируем итоговую статистику документа
            logger.info("=== PDF DOCUMENT FORMAT STATISTICS ===")
            logger.info(f"Total pages: {document_format_stats['total_pages']}")
            logger.info(f"Total A4 sheets equivalent: {document_format_stats['total_a4_sheets']:.2f}")
            logger.info(f"Page formats: {document_format_stats['formats']}")
            logger.info(f"Orientations: {document_format_stats['orientations']}")
            logger.info(f"Page types: {document_format_stats['page_types']}")
            logger.info("=====================================")
                
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            raise
        
        logger.info(f"PDF parsing completed. Total pages: {len(result.document_pages_results)}")
        return result
    
    def parse_docx(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсинг DOCX документа"""
        elements = []
        
        try:
            # Сохраняем временный файл
            temp_path = "/app/temp/temp.docx"
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            doc = Document(temp_path)
            
            for para in doc.paragraphs:
                if para.text.strip():
                    elements.append({
                        "element_type": "text",
                        "element_content": para.text,
                        "page_number": 1,  # DOCX не имеет страниц
                        "confidence_score": 0.95
                    })
            
            # Извлечение таблиц
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                
                if table_data:
                    elements.append({
                        "element_type": "table",
                        "element_content": json.dumps(table_data),
                        "page_number": 1,
                        "confidence_score": 0.9
                    })
            
            # Удаляем временный файл
            os.remove(temp_path)
            
        except Exception as e:
            logger.error(f"DOCX parsing error: {e}")
            raise
        
        return elements
    
    def parse_dwg(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсинг DWG документа"""
        elements = []
        
        try:
            # Простое извлечение текста из DWG файла
            # В реальной реализации здесь будет ezdxf
            elements.append({
                "element_type": "text",
                "element_content": "DWG файл загружен (парсинг не реализован)",
                "page_number": 1,
                "confidence_score": 0.5
            })
            
        except Exception as e:
            logger.error(f"DWG parsing error: {e}")
            raise
        
        return elements
    
    def parse_ifc(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсинг IFC документа с продвинутым текстовым анализом"""
        elements = []
        
        try:
            # Декодируем содержимое файла
            text_content = file_content.decode('utf-8', errors='ignore')
            
            # Счетчики для статистики
            entity_counts = {}
            project_info = None
            buildings = []
            storeys = []
            walls = []
            windows = []
            doors = []
            materials = []
            property_sets = []
            
            # Регулярные выражения для поиска IFC элементов
            entity_pattern = r'#(\d+)\s*=\s*([A-Z_]+)\s*\('
            name_pattern = r'Name\s*=\s*[\'"]([^\'"]*)[\'"]'
            description_pattern = r'Description\s*=\s*[\'"]([^\'"]*)[\'"]'
            object_type_pattern = r'ObjectType\s*=\s*[\'"]([^\'"]*)[\'"]'
            elevation_pattern = r'Elevation\s*=\s*([-\d.]+)'
            
            # Обрабатываем весь текст как единое целое для поиска IFC сущностей
            entity_matches = re.finditer(entity_pattern, text_content)
            
            for entity_match in entity_matches:
                entity_id = entity_match.group(1)
                entity_type = entity_match.group(2)
                
                # Находим конец записи (закрывающую скобку)
                start_pos = entity_match.end()
                bracket_count = 0
                end_pos = start_pos
                
                for i, char in enumerate(text_content[start_pos:], start_pos):
                    if char == '(':
                        bracket_count += 1
                    elif char == ')':
                        bracket_count -= 1
                        if bracket_count < 0:
                            end_pos = i + 1
                            break
                
                entity_params = text_content[start_pos:end_pos]
                
                # Подсчитываем типы сущностей
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                
                # Извлекаем информацию в зависимости от типа сущности
                if entity_type == 'IFCPROJECT':
                    name_match = re.search(name_pattern, entity_params)
                    desc_match = re.search(description_pattern, entity_params)
                    project_name = name_match.group(1) if name_match else 'Без названия'
                    project_desc = desc_match.group(1) if desc_match else 'Без описания'
                    project_info = f"Проект: {project_name} - {project_desc}"
                    
                elif entity_type == 'IFCBUILDING':
                    name_match = re.search(name_pattern, entity_params)
                    building_name = name_match.group(1) if name_match else 'Без названия'
                    buildings.append(f"Здание: {building_name}")
                    
                elif entity_type == 'IFCBUILDINGSTOREY':
                    name_match = re.search(name_pattern, entity_params)
                    elevation_match = re.search(elevation_pattern, entity_params)
                    storey_name = name_match.group(1) if name_match else 'Без названия'
                    elevation = elevation_match.group(1) if elevation_match else 'Не указана'
                    storeys.append(f"Этаж: {storey_name} - Высота: {elevation}")
                    
                elif entity_type == 'IFCWALL':
                    name_match = re.search(name_pattern, entity_params)
                    type_match = re.search(object_type_pattern, entity_params)
                    wall_name = name_match.group(1) if name_match else 'Без названия'
                    wall_type = type_match.group(1) if type_match else 'Не указан'
                    walls.append(f"Стена: {wall_name} - Тип: {wall_type}")
                    
                elif entity_type == 'IFCWINDOW':
                    name_match = re.search(name_pattern, entity_params)
                    type_match = re.search(object_type_pattern, entity_params)
                    window_name = name_match.group(1) if name_match else 'Без названия'
                    window_type = type_match.group(1) if type_match else 'Не указан'
                    windows.append(f"Окно: {window_name} - Тип: {window_type}")
                    
                elif entity_type == 'IFCDOOR':
                    name_match = re.search(name_pattern, entity_params)
                    type_match = re.search(object_type_pattern, entity_params)
                    door_name = name_match.group(1) if name_match else 'Без названия'
                    door_type = type_match.group(1) if type_match else 'Не указан'
                    doors.append(f"Дверь: {door_name} - Тип: {door_type}")
                    
                elif entity_type == 'IFCMATERIAL':
                    name_match = re.search(name_pattern, entity_params)
                    desc_match = re.search(description_pattern, entity_params)
                    material_name = name_match.group(1) if name_match else 'Без названия'
                    material_desc = desc_match.group(1) if desc_match else 'Без описания'
                    materials.append(f"Материал: {material_name} - {material_desc}")
                        
                elif entity_type == 'IFCPROPERTYSET':
                    name_match = re.search(name_pattern, entity_params)
                    desc_match = re.search(description_pattern, entity_params)
                    pset_name = name_match.group(1) if name_match else 'Без названия'
                    pset_desc = desc_match.group(1) if desc_match else 'Без описания'
                    property_sets.append(f"Набор свойств: {pset_name} - {pset_desc}")
            
            # Добавляем извлеченную информацию в элементы
            if project_info:
                elements.append({
                    "element_type": "project_info",
                    "element_content": project_info,
                    "page_number": 1,
                    "confidence_score": 0.95
                })
            
            for building in buildings[:10]:  # Ограничиваем количество
                elements.append({
                    "element_type": "building",
                    "element_content": building,
                    "page_number": 1,
                    "confidence_score": 0.9
                })
            
            for storey in storeys[:10]:
                elements.append({
                    "element_type": "storey",
                    "element_content": storey,
                    "page_number": 1,
                    "confidence_score": 0.9
                })
            
            for wall in walls[:20]:
                elements.append({
                    "element_type": "wall",
                    "element_content": wall,
                    "page_number": 1,
                    "confidence_score": 0.85
                })
            
            for window in windows[:20]:
                elements.append({
                    "element_type": "window",
                    "element_content": window,
                    "page_number": 1,
                    "confidence_score": 0.85
                })
            
            for door in doors[:20]:
                elements.append({
                    "element_type": "door",
                    "element_content": door,
                    "page_number": 1,
                    "confidence_score": 0.85
                })
            
            for material in materials[:10]:
                elements.append({
                    "element_type": "material",
                    "element_content": material,
                    "page_number": 1,
                    "confidence_score": 0.8
                })
            
            for pset in property_sets[:10]:
                elements.append({
                    "element_type": "property_set",
                    "element_content": pset,
                    "page_number": 1,
                    "confidence_score": 0.8
                })
            
            # Статистика модели
            total_entities = sum(entity_counts.values())
            top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            stats_text = f"Всего сущностей: {total_entities}. Топ типов: " + ", ".join([f"{entity}({count})" for entity, count in top_entities])
            
            elements.append({
                "element_type": "statistics",
                "element_content": stats_text,
                "page_number": 1,
                "confidence_score": 0.95
            })
            
            # Если не нашли структурированных элементов, сохраняем базовую информацию
            if len(elements.document_pages_results) <= 1:  # Только статистика
                elements.append({
                    "element_type": "text",
                    "element_content": f"IFC файл содержит {total_entities} сущностей различных типов",
                    "page_number": 1,
                    "confidence_score": 0.7
                })
            
        except Exception as e:
            logger.error(f"IFC parsing error: {e}")
            # Fallback к простому текстовому парсингу
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
                elements.append({
                    "element_type": "text",
                    "element_content": f"IFC файл (продвинутый парсинг не удался): {text_content[:500]}",
                    "page_number": 1,
                    "confidence_score": 0.3
                })
            except:
                elements.append({
                    "element_type": "error",
                    "element_content": f"Ошибка парсинга IFC файла: {str(e)}",
                    "page_number": 1,
                    "confidence_score": 0.1
                })
        
        return elements
    
    def save_to_database(self, filename: str, original_filename: str, file_type: str, 
                        file_size: int, document_hash: str, inspection_result: DocumentInspectionResult, 
                        category: str = "other", document_type: str = "normative") -> int:
        """Сохранение документа и элементов в базу данных"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if document_type == "checkable":
                    # Сохраняем как проверяемый документ
                    review_deadline = datetime.now() + timedelta(days=2)
                    
                    cursor.execute("""
                        INSERT INTO checkable_documents 
                        (filename, original_filename, file_type, file_size, document_hash, 
                         processing_status, category, review_deadline)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (filename, original_filename, file_type, file_size, document_hash, 
                          "completed", category, review_deadline))
                    document_id = cursor.fetchone()["id"]
                else:
                    # Сохраняем как нормативный документ
                    # Подсчитываем количество токенов
                    token_count = self.calculate_document_tokens(inspection_result)
                    
                    cursor.execute("""
                        INSERT INTO uploaded_documents 
                        (filename, original_filename, file_type, file_size, document_hash, 
                         processing_status, category, token_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (filename, original_filename, file_type, file_size, document_hash, 
                          "completed", category, token_count))
                    document_id = cursor.fetchone()["id"]
                
                # Сохранение элементов
                for page_result in inspection_result.document_pages_results:
                    # Подготавливаем дополнительные данные
                    metadata = {
                        "page_type": page_result.page_type,
                        "processing_method": page_result.page_text_method,
                        "format_info": {
                            "format_name": page_result.page_format,
                            "width_mm": page_result.page_width_mm,
                            "height_mm": page_result.page_height_mm,
                            "orientation": page_result.page_orientation,
                            "a4_sheets": page_result.page_a4_sheets_equivalent
                        }
                    }
                    
                    if page_result.page_ocr_confidence is not None:
                        metadata["ocr_confidence"] = page_result.page_ocr_confidence
                    if page_result.page_ocr_method is not None:
                        metadata["ocr_method"] = page_result.page_ocr_method
                    
                    if document_type == "checkable":
                        cursor.execute("""
                            INSERT INTO checkable_elements 
                            (checkable_document_id, element_type, element_content, page_number, confidence_score, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            document_id,
                            "text",
                            page_result.page_text,
                            page_result.page_number,
                            page_result.page_text_confidence,
                            json.dumps(metadata)
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO extracted_elements 
                            (uploaded_document_id, element_type, element_content, page_number, confidence_score, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            document_id,
                            "text",
                            page_result.page_text,
                            page_result.page_number,
                            page_result.page_text_confidence,
                            json.dumps(metadata)
                        ))
                
                self.db_conn.commit()
                
                # Автоматическая проверка нормоконтроля для проверяемых документов
                if document_type == "checkable":
                    try:
                        # Объединяем содержимое для проверки
                        document_content = "\n\n".join([page_result.page_text for page_result in inspection_result.document_pages_results])
                        
                        # Запускаем проверку в фоновом режиме
                        asyncio.create_task(self.perform_norm_control_check(document_id, document_content))
                        logger.info(f"Started automatic norm control check for document {document_id}")
                    except Exception as e:
                        logger.error(f"Failed to start norm control check for document {document_id}: {e}")
                
                return document_id
                
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Database save error: {e}")
            raise
    
    def create_initial_document_record(self, filename: str, file_type: str, file_size: int, document_hash: str, file_path: str, category: str = "other") -> int:
        """Создание начальной записи документа в базе данных"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO uploaded_documents 
                    (filename, original_filename, file_type, file_size, document_hash, processing_status, file_path, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (filename, filename, file_type, file_size, document_hash, "uploaded", file_path, category))
                
                document_id = cursor.fetchone()["id"]
                self.db_conn.commit()
                logger.info(f"Created initial document record with ID: {document_id}")
                return document_id
                
        except Exception as e:
            logger.error(f"Error creating initial document record: {e}")
            raise
    
    def update_document_status(self, document_id: int, status: str):
        """Обновление статуса документа"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE uploaded_documents 
                    SET processing_status = %s
                    WHERE id = %s
                """, (status, document_id))
                self.db_conn.commit()
                logger.info(f"Updated document {document_id} status to: {status}")
                
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            raise
    
    def save_elements_to_database(self, document_id: int, inspection_result: DocumentInspectionResult):
        """Сохранение элементов документа в базу данных"""
        try:
            with self.db_conn.cursor() as cursor:
                # Сохранение элементов
                for page_result in inspection_result.document_pages_results:
                    # Подготавливаем дополнительные данные
                    metadata = {
                        "page_type": page_result.page_type,
                        "processing_method": page_result.page_text_method,
                        "format_info": {
                            "format_name": page_result.page_format,
                            "width_mm": page_result.page_width_mm,
                            "height_mm": page_result.page_height_mm,
                            "orientation": page_result.page_orientation,
                            "a4_sheets": page_result.page_a4_sheets_equivalent
                        }
                    }
                    
                    if page_result.page_ocr_confidence is not None:
                        metadata["ocr_confidence"] = page_result.page_ocr_confidence
                    if page_result.page_ocr_method is not None:
                        metadata["ocr_method"] = page_result.page_ocr_method
                    
                    cursor.execute("""
                        INSERT INTO extracted_elements 
                        (uploaded_document_id, element_type, element_content, page_number, confidence_score, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        document_id,
                        "text",
                        page_result.page_text,
                        page_result.page_number,
                        page_result.page_text_confidence,
                        json.dumps(metadata)
                    ))
                
                self.db_conn.commit()
                logger.info(f"Saved {len(inspection_result.document_pages_results)} elements for document {document_id}")
                
        except Exception as e:
            logger.error(f"Error saving elements to database: {e}")
            raise
    
    def update_document_completion(self, document_id: int, elements_count: int, token_count: int):
        """Обновление записи документа после завершения обработки"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE uploaded_documents 
                    SET processing_status = %s, token_count = %s
                    WHERE id = %s
                """, ("completed", token_count, document_id))
                self.db_conn.commit()
                logger.info(f"Updated document {document_id} completion: {elements_count} elements, {token_count} tokens")
                
        except Exception as e:
            logger.error(f"Error updating document completion: {e}")
            raise
    
    async def index_to_rag_service_async(self, document_id: int, document_title: str, inspection_result: DocumentInspectionResult):
        """Асинхронная индексация в RAG-сервис"""
        try:
            logger.info(f"Starting async RAG indexing for document {document_id}")
            
            # Подготавливаем данные для индексации
            elements = []
            for page_result in inspection_result.document_pages_results:
                elements.append({
                    "element_type": "text",
                    "element_content": page_result.page_text,
                    "page_number": page_result.page_number,
                    "confidence_score": page_result.page_text_confidence
                })
            
            # Объединяем текст всех страниц
            combined_text = ""
            for page_result in inspection_result.document_pages_results:
                if page_result.page_text:
                    combined_text += page_result.page_text + "\n\n"
                        # Отправляем данные в RAG-сервис
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{RAG_SERVICE_URL}/index",
                    data={
                        "document_id": document_id,
                        "document_title": document_title,
                        "content": combined_text,
                        "chapter": "",
                        "section": "",
                        "page_number": 1
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully indexed document {document_id} to RAG service")
                else:
                    logger.error(f"Failed to index document {document_id} to RAG service: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error in async RAG indexing for document {document_id}: {e}")
    
    def calculate_document_tokens(self, inspection_result: DocumentInspectionResult) -> int:
        """Подсчет токенов в документе"""
        try:
            total_tokens = 0
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            
            for page_result in inspection_result.document_pages_results:
                if page_result.page_text:
                    tokens = encoding.encode(page_result.page_text)
                    total_tokens += len(tokens)
            
            logger.info(f"Calculated {total_tokens} tokens for document")
            return total_tokens
            
        except Exception as e:
            logger.error(f"Error calculating document tokens: {e}")
            return 0
            logger.error(f"Database save error: {e}")
            raise

    def save_checkable_document(self, filename: str, original_filename: str, file_type: str, 
                               file_size: int, document_hash: str, inspection_result: DocumentInspectionResult, 
                               category: str = "other") -> int:
        """Сохранение проверяемого документа"""
        return self.save_to_database(filename, original_filename, file_type, file_size, 
                                   document_hash, inspection_result, category, "checkable")

    def cleanup_expired_documents(self) -> int:
        """Очистка просроченных проверяемых документов"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT cleanup_expired_checkable_documents()")
                result = cursor.fetchone()
                self.db_conn.commit()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0

    def get_checkable_documents(self) -> List[Dict[str, Any]]:
        """Получение списка проверяемых документов"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, original_filename, file_type, file_size, upload_date, 
                           processing_status, category, review_deadline, review_status,
                           assigned_reviewer, review_notes
                    FROM checkable_documents
                    ORDER BY upload_date DESC
                """)
                documents = cursor.fetchall()
                return [dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Get checkable documents error: {e}")
            return []

    def get_document_info(self, pdf_reader) -> Dict[str, Any]:
        """Извлечение информации о документе из PDF метаданных"""
        try:
            info = pdf_reader.metadata
            if info:
                # Извлекаем информацию из метаданных PDF
                title = info.get('/Title', 'Неизвестный документ')
                author = info.get('/Author', 'Неизвестный автор')
                subject = info.get('/Subject', '')
                creator = info.get('/Creator', '')
                producer = info.get('/Producer', '')
                creation_date = info.get('/CreationDate', '')
                mod_date = info.get('/ModDate', '')
                
                # Попытка извлечь номер документа из названия
                document_number = ""
                if title:
                    # Ищем паттерны типа "A9.5.MTH.04" или "КЖ-01" и т.д.
                    import re
                    number_match = re.search(r'[A-ZА-Я]{1,3}[-\d\.]+[A-ZА-Я]*\d*', title)
                    if number_match:
                        document_number = number_match.group(0)
                
                # Определяем тип документа по названию
                document_type = "pdf"
                engineering_stage = "ПД"  # По умолчанию
                document_mark = ""
                document_status = "IFR"  # По умолчанию
                
                # Попытка определить марку по названию
                if title:
                    title_upper = title.upper()
                    if any(mark in title_upper for mark in ['КЖ', 'KZH']):
                        document_mark = "КЖ"
                    elif any(mark in title_upper for mark in ['КМ', 'KM']):
                        document_mark = "КМ"
                    elif any(mark in title_upper for mark in ['АС', 'AS']):
                        document_mark = "АС"
                    elif any(mark in title_upper for mark in ['ТХ', 'TX']):
                        document_mark = "ТХ"
                    elif any(mark in title_upper for mark in ['КС', 'KS']):
                        document_mark = "КС"
                    elif any(mark in title_upper for mark in ['КП', 'KP']):
                        document_mark = "КП"
                    elif any(mark in title_upper for mark in ['КР', 'KR']):
                        document_mark = "КР"
                
                return {
                    "name": title,
                    "type": document_type,
                    "engineering_stage": engineering_stage,
                    "mark": document_mark,
                    "number": document_number,
                    "date": creation_date or mod_date,
                    "author": author,
                    "reviewer": "",  # Не извлекается из PDF
                    "approver": "",  # Не извлекается из PDF
                    "status": document_status,
                    "size": 0  # Будет заполнено позже
                }
            else:
                # Если метаданные отсутствуют, возвращаем значения по умолчанию
                return {
                    "name": "Документ без названия",
                    "type": "pdf",
                    "engineering_stage": "ПД",
                    "mark": "",
                    "number": "",
                    "date": "",
                    "author": "Неизвестный автор",
                    "reviewer": "",
                    "approver": "",
                    "status": "IFR",
                    "size": 0
                }
        except Exception as e:
            logger.error(f"Error extracting document info: {e}")
            return {
                "name": "Документ с ошибкой метаданных",
                "type": "pdf",
                "engineering_stage": "ПД",
                "mark": "",
                "number": "",
                "date": "",
                "author": "Неизвестный автор",
                "reviewer": "",
                "approver": "",
                "status": "IFR",
                "size": 0
            }

    def get_document_format_statistics(self, document_id: int) -> Dict[str, Any]:
        """Получение статистики форматов документа"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT metadata->>'format_info' as format_info
                    FROM checkable_elements
                    WHERE checkable_document_id = %s
                    ORDER BY page_number
                """, (document_id,))
                elements = cursor.fetchall()
                
                if not elements:
                    return {"error": "Document not found or no elements"}
                
                stats = {
                    "total_pages": len(elements.document_pages_results),
                    "total_a4_sheets": 0.0,
                    "formats": {},
                    "orientations": {"portrait": 0, "landscape": 0},
                    "page_types": {"vector": 0, "scanned": 0, "unknown": 0},
                    "pages": []
                }
                
                for element in elements:
                    try:
                        format_info = json.loads(element["format_info"]) if element["format_info"] else {}
                        
                        # Добавляем информацию о странице
                        page_info = {
                            "page_number": format_info.get("page_number", 0),
                            "format": format_info.get("format_name", "unknown"),
                            "width_mm": format_info.get("width_mm", 0),
                            "height_mm": format_info.get("height_mm", 0),
                            "orientation": format_info.get("orientation", "unknown"),
                            "a4_sheets": format_info.get("a4_sheets", 0)
                        }
                        stats["pages"].append(page_info)
                        
                        # Обновляем общую статистику
                        a4_sheets = format_info.get("a4_sheets", 0)
                        if a4_sheets is not None:
                            stats["total_a4_sheets"] += a4_sheets
                        
                        format_name = format_info.get("format_name", "unknown")
                        if format_name not in stats["formats"]:
                            stats["formats"][format_name] = 0
                        stats["formats"][format_name] += 1
                        
                        orientation = format_info.get("orientation", "unknown")
                        if orientation in stats["orientations"]:
                            stats["orientations"][orientation] += 1
                        
                    except Exception as e:
                        logger.warning(f"Error parsing format info: {e}")
                        # Добавляем пустую информацию о странице
                        stats["pages"].append({
                            "page_number": 0,
                            "format": "unknown",
                            "width_mm": 0,
                            "height_mm": 0,
                            "orientation": "unknown",
                            "a4_sheets": 0
                        })
                        continue
                
                # Округляем общее количество листов А4
                stats["total_a4_sheets"] = round(stats["total_a4_sheets"], 2)
                
                return stats
                
        except Exception as e:
            logger.error(f"Get document format statistics error: {e}")
            return {"error": str(e)}

    def determine_document_category(self, filename: str, content: str) -> str:
        """Определение категории документа по имени файла и содержимому"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Проверка по ключевым словам в названии и содержимом
        if any(keyword in filename_lower for keyword in ['gost', 'гост']):
            return 'gost'
        elif any(keyword in filename_lower for keyword in ['sp', 'сн']):
            return 'sp'
        elif any(keyword in filename_lower for keyword in ['snip', 'снип']):
            return 'snip'
        elif any(keyword in filename_lower for keyword in ['tr', 'тр']):
            return 'tr'
        elif any(keyword in content_lower for keyword in ['корпоративный', 'корп', 'corporate']):
            return 'corporate'
        else:
            return 'other'

    def update_review_status(self, document_id: int, status: str, reviewer: str = None, notes: str = None) -> bool:
        """Обновление статуса проверки документа"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE checkable_documents 
                    SET review_status = %s, assigned_reviewer = %s, review_notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (status, reviewer, notes, document_id))
                self.db_conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update review status error: {e}")
            return False

    async def delete_normative_document(self, document_id: int) -> bool:
        """Удаление нормативного документа и связанных данных"""
        try:
            with self.db_conn.cursor() as cursor:
                # Получаем информацию о документе для логирования
                cursor.execute("""
                    SELECT original_filename, document_hash 
                    FROM uploaded_documents 
                    WHERE id = %s AND document_type = 'normative'
                """, (document_id,))
                doc_info = cursor.fetchone()
                
                if not doc_info:
                    logger.warning(f"Document {document_id} not found or not a normative document")
                    return False
                
                # Удаляем элементы документа
                cursor.execute("DELETE FROM extracted_elements WHERE uploaded_document_id = %s", (document_id,))
                elements_deleted = cursor.rowcount
                
                # Удаляем результаты нормоконтроля
                cursor.execute("DELETE FROM norm_control_results WHERE uploaded_document_id = %s", (document_id,))
                results_deleted = cursor.rowcount
                
                # Удаляем сам документ
                cursor.execute("DELETE FROM uploaded_documents WHERE id = %s", (document_id,))
                document_deleted = cursor.rowcount
                
                self.db_conn.commit()
                
                logger.info(f"Deleted normative document {document_id} ({doc_info[0]}): "
                          f"{elements_deleted} elements, {results_deleted} results, {document_deleted} document")
                
                # Удаляем индексы из RAG сервиса
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.delete(f"{RAG_SERVICE_URL}/index-documentes/document/{document_id}")
                        if response.status_code == 200:
                            logger.info(f"Successfully deleted indexes for document {document_id}")
                        else:
                            logger.warning(f"Failed to delete indexes for document {document_id}: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error deleting indexes for document {document_id}: {e}")
                
                return document_deleted > 0
                
        except Exception as e:
            logger.error(f"Delete normative document error: {e}")
            self.db_conn.rollback()
            return False

    def delete_checkable_document(self, document_id: int) -> bool:
        """Удаление проверяемого документа и связанных данных"""
        try:
            with self.db_conn.cursor() as cursor:
                # Получаем информацию о документе для логирования
                cursor.execute("""
                    SELECT original_filename, document_hash 
                    FROM checkable_documents 
                    WHERE id = %s
                """, (document_id,))
                doc_info = cursor.fetchone()
                
                if not doc_info:
                    logger.warning(f"Checkable document {document_id} not found")
                    return False
                
                # Удаляем элементы документа
                cursor.execute("DELETE FROM checkable_elements WHERE checkable_document_id = %s", (document_id,))
                elements_deleted = cursor.rowcount
                
                # Удаляем отчеты о проверке
                cursor.execute("DELETE FROM review_reports WHERE checkable_document_id = %s", (document_id,))
                reports_deleted = cursor.rowcount
                
                # Удаляем результаты нормоконтроля
                cursor.execute("DELETE FROM norm_control_results WHERE checkable_document_id = %s", (document_id,))
                results_deleted = cursor.rowcount
                
                # Удаляем сам документ
                cursor.execute("DELETE FROM checkable_documents WHERE id = %s", (document_id,))
                document_deleted = cursor.rowcount
                
                self.db_conn.commit()
                
                logger.info(f"Deleted checkable document {document_id} ({doc_info[0]}): "
                          f"{elements_deleted} elements, {reports_deleted} reports, "
                          f"{results_deleted} results, {document_deleted} document")
                
                return document_deleted > 0
                
        except Exception as e:
            logger.error(f"Delete checkable document error: {e}")
            self.db_conn.rollback()
            return False
    
    async def index_to_rag_service(self, document_id: int, document_title: str, elements: List[Dict[str, Any]]):
        """Индексация документа в RAG-сервис"""
        try:
            # Объединяем все элементы в один текст
            content = "\n\n".join([elem["element_content"] for elem in elements])
            
            # Определяем главу и раздел из элементов
            chapter = ""
            section = ""
            for elem in elements:
                if elem["element_type"] in ["project_info", "building", "storey"]:
                    chapter = elem["element_content"][:100]
                    break
            
            # Отправляем в RAG-сервис
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{RAG_SERVICE_URL}/index",
                    data={
                        "document_id": document_id,
                        "document_title": document_title,
                        "content": content,
                        "chapter": chapter,
                        "section": section,
                        "page_number": 1
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully indexed document {document_id} in RAG service: {result}")
                else:
                    logger.error(f"Failed to index document {document_id} in RAG service: {response.text}")
                    
        except Exception as e:
            logger.error(f"RAG indexing error for document {document_id}: {e}")
            # Не прерываем основной процесс, если RAG индексация не удалась

    def get_system_settings(self) -> List[Dict[str, Any]]:
        """Получение всех настроек системы"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT setting_key, setting_value, setting_description, setting_type, is_public, updated_at
                    FROM system_settings
                    WHERE is_public = true
                    ORDER BY setting_key
                """)
                settings = cursor.fetchall()
                return [dict(setting) for setting in settings]
        except Exception as e:
            logger.error(f"Get system settings error: {e}")
            return []

    def get_system_setting(self, setting_key: str) -> Optional[str]:
        """Получение конкретной настройки системы"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT setting_value
                    FROM system_settings
                    WHERE setting_key = %s AND is_public = true
                """, (setting_key,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Get system setting error: {e}")
            return None

    def update_system_setting(self, setting_key: str, setting_value: str) -> bool:
        """Обновление настройки системы"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE system_settings
                    SET setting_value = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = %s AND is_public = true
                """, (setting_value, setting_key))
                self.db_conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update system setting error: {e}")
            return False

    def create_system_setting(self, setting_key: str, setting_value: str, 
                            setting_description: str, setting_type: str = "text") -> bool:
        """Создание новой настройки системы"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, setting_description, setting_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (setting_key) DO UPDATE SET
                    setting_value = EXCLUDED.setting_value,
                    setting_description = EXCLUDED.setting_description,
                    setting_type = EXCLUDED.setting_type,
                    updated_at = CURRENT_TIMESTAMP
                """, (setting_key, setting_value, setting_description, setting_type))
                self.db_conn.commit()
                return True
        except Exception as e:
            logger.error(f"Create system setting error: {e}")
            return False

    def delete_system_setting(self, setting_key: str) -> bool:
        """Удаление настройки системы"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM system_settings
                    WHERE setting_key = %s AND is_public = true
                """, (setting_key,))
                self.db_conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete system setting error: {e}")
            return False

    def get_normcontrol_prompt_template(self) -> str:
        """Получение полного шаблона промпта для нормоконтроля из системы настроек"""
        try:
            # Получаем основной промпт для нормоконтроля
            normcontrol_prompt = self.get_system_setting("normcontrol_prompt")
            if not normcontrol_prompt:
                normcontrol_prompt = "Ты - эксперт по нормоконтролю в строительстве и проектировании. Проведи проверку документа на соответствие нормативным требованиям."
            
            # Получаем пользовательский шаблон промпта (если есть)
            prompt_template = self.get_system_setting("normcontrol_prompt_template")
            if prompt_template:
                # Используем пользовательский шаблон
                prompt_template = prompt_template.replace("{normcontrol_prompt}", normcontrol_prompt)
                return prompt_template
            
            # Если пользовательский шаблон не задан, используем упрощенный формат
            # Заменяем плейсхолдеры в основном промпте на плейсхолдеры для страниц
            processed_prompt = normcontrol_prompt.replace("{document_content}", "{page_content}")
            processed_prompt = processed_prompt.replace("{normative_docs}", "нормативным требованиям")
            
            # Создаем простой шаблон без сложного JSON для избежания конфликтов форматирования
            simple_template = f"""
{processed_prompt}

СОДЕРЖИМОЕ СТРАНИЦЫ {{page_number}}:
{{page_content}}

ВАЖНО: Анализируйте только содержимое страницы {{page_number}}. Указывайте номер страницы в findings.

Сформируйте детальный отчет в формате JSON с полями:
- page_number: номер страницы
- overall_status: pass/fail/uncertain
- confidence: 0.0-1.0
- total_findings: количество найденных нарушений
- critical_findings: количество критических нарушений
- warning_findings: количество предупреждений
- info_findings: количество информационных замечаний
- findings: массив найденных нарушений
- summary: общий вывод
- compliance_percentage: процент соответствия (0-100)
- recommendations: рекомендации по улучшению
"""
            
            return simple_template
            
        except Exception as e:
            logger.error(f"Get normcontrol prompt template error: {e}")
            # Возвращаем базовый промпт в случае ошибки
            return "Ты - эксперт по нормоконтролю в строительстве и проектировании. Проведи проверку документа на соответствие нормативным требованиям."

    def split_document_into_pages(self, document_id: int) -> List[Dict[str, Any]]:
        """Разбиение документа на страницы в соответствии с реальной структурой PDF"""
        try:
            pages = []
            
            # Получаем элементы документа из базы данных, сгруппированные по страницам
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT page_number, element_content, element_type, confidence_score
                    FROM checkable_elements
                    WHERE checkable_document_id = %s
                    ORDER BY page_number, id
                """, (document_id,))
                elements = cursor.fetchall()
            
            if not elements:
                logger.warning(f"No elements found for document {document_id}")
                return []
            
            # Группируем элементы по страницам
            current_page = None
            current_page_content = []
            current_page_elements = []
            
            for element in elements:
                page_number = element["page_number"]
                
                if current_page is None:
                    current_page = page_number
                    current_page_content = []
                    current_page_elements = []
                
                if page_number != current_page:
                    # Сохраняем предыдущую страницу
                    pages.append({
                        "page_number": current_page,
                        "content": "\n\n".join(current_page_content),
                        "char_count": len("\n\n".join(current_page_content)),
                        "element_count": len(current_page_elements),
                        "elements": current_page_elements
                    })
                    
                    # Начинаем новую страницу
                    current_page = page_number
                    current_page_content = []
                    current_page_elements = []
                
                # Добавляем элемент к текущей странице
                current_page_content.append(element["element_content"])
                current_page_elements.append({
                    "type": element["element_type"],
                    "content": element["element_content"],
                    "confidence": element["confidence_score"]
                })
            
            # Добавляем последнюю страницу
            if current_page is not None:
                pages.append({
                    "page_number": current_page,
                    "content": "\n\n".join(current_page_content),
                    "char_count": len("\n\n".join(current_page_content)),
                    "element_count": len(current_page_elements),
                    "elements": current_page_elements
                })
            
            logger.info(f"Split document {document_id} into {len(pages)} pages based on PDF structure")
            for page in pages:
                logger.info(f"Page {page['page_number']}: {page['char_count']} chars, {page['element_count']} elements")
            
            return pages
            
        except Exception as e:
            logger.error(f"Error splitting document into pages: {e}")
            # В случае ошибки возвращаем пустой список
            return []

    async def perform_norm_control_check_for_page(self, document_id: int, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение проверки нормоконтроля для одной страницы документа"""
        try:
            page_number = page_data["page_number"]
            page_content = page_data["content"]
            
            logger.info(f"Starting norm control check for document {document_id}, page {page_number}")
            logger.info(f"Page content length: {len(page_content)} characters")
            
            # ===== ПОЛУЧЕНИЕ ПРОМПТА ДЛЯ LLM ИЗ СИСТЕМЫ НАСТРОЕК =====
            # Получаем полный шаблон промпта для нормоконтроля из системы настроек
            prompt_template = self.get_normcontrol_prompt_template()
            
            # Формируем запрос к LLM для конкретной страницы с использованием шаблона
            prompt = prompt_template.format(
                page_number=page_number,
                page_content=page_content
            )
            
            # ===== ОТПРАВКА ЗАПРОСА К LLM ДЛЯ ПРОВЕРКИ СТРАНИЦЫ =====
            # Отправляем запрос к LLM через gateway для выполнения нормоконтроля
            logger.info(f"Sending request to LLM for page {page_number}...")
            logger.info(f"Prompt length: {len(prompt)} characters")
            
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                response = await client.post(
                    "http://gateway:8443/v1/chat/completions",
                    headers={
                        "Authorization": "Bearer test-token",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama3.1:8b",
                        "messages": [
                            {"role": "system", "content": "Ты — эксперт по нормоконтролю проектной документации."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1
                    }
                )
                
                # ===== ПОЛУЧЕНИЕ РЕЗУЛЬТАТА ПРОВЕРКИ ОТ LLM =====
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Парсим JSON ответ от LLM
                    try:
                        import json
                        import re
                        
                        # Ищем JSON в ответе (между фигурными скобками)
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            check_result = json.loads(json_str)
                        else:
                            # Если JSON не найден, пробуем парсить весь ответ
                            check_result = json.loads(content)
                        
                        return {
                            "status": "success",
                            "result": check_result,
                            "raw_response": content
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error: {e}")
                        logger.error(f"Raw response: {content}")
                        return {
                            "status": "error",
                            "error": "Invalid JSON response from LLM",
                            "raw_response": content
                        }
                else:
                    logger.error(f"LLM request failed: {response.status_code} - {response.text}")
                    return {
                        "status": "error",
                        "error": f"LLM request failed: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Norm control check error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def perform_norm_control_check(self, document_id: int, document_content: str) -> Dict[str, Any]:
        """Выполнение проверки нормоконтроля для документа по страницам с применением LLM"""
        try:
            logger.info(f"Starting norm control check for document {document_id}")
            logger.info(f"Document content length: {len(document_content)} characters")
            
            # ===== ОСНОВНАЯ ФУНКЦИЯ ПРОВЕРКИ НОРМОКОНТРОЛЯ С LLM =====
            
            # Разбиваем документ на страницы в соответствии с реальной структурой PDF
            pages = self.split_document_into_pages(document_id)
            logger.info(f"Document split into {len(pages)} pages based on PDF structure")
            
            # Проверяем каждую страницу отдельно
            page_results = []
            total_findings = 0
            total_critical_findings = 0
            total_warning_findings = 0
            total_info_findings = 0
            all_findings = []
            
            for page_data in pages:
                logger.info(f"Processing page {page_data['page_number']} of {len(pages)}")
                
                # Проверяем страницу
                # ===== ВЫЗОВ ПРОВЕРКИ СТРАНИЦЫ С ПРИМЕНЕНИЕМ LLM =====
                # Выполняем проверку для каждой страницы с использованием LLM
                page_result = await self.perform_norm_control_check_for_page(document_id, page_data)
                
                if page_result["status"] == "success":
                    result_data = page_result["result"]
                    page_results.append(result_data)
                    
                    # Собираем статистику
                    total_findings += result_data.get("total_findings", 0)
                    total_critical_findings += result_data.get("critical_findings", 0)
                    total_warning_findings += result_data.get("warning_findings", 0)
                    total_info_findings += result_data.get("info_findings", 0)
                    
                    # Собираем все findings
                    page_findings = result_data.get("findings", [])
                    for finding in page_findings:
                        finding["page_number"] = page_data["page_number"]
                    all_findings.extend(page_findings)
                    
                    logger.info(f"Page {page_data['page_number']} processed successfully")
                else:
                    logger.error(f"Failed to process page {page_data['page_number']}: {page_result.get('error', 'Unknown error')}")
                    # Добавляем пустой результат для страницы
                    page_results.append({
                        "page_number": page_data["page_number"],
                        "overall_status": "error",
                        "confidence": 0.0,
                        "total_findings": 0,
                        "critical_findings": 0,
                        "warning_findings": 0,
                        "info_findings": 0,
                        "findings": [],
                        "summary": f"Ошибка обработки страницы: {page_result.get('error', 'Unknown error')}",
                        "compliance_percentage": 0
                    })
            
            # Формируем общий результат
            overall_status = "pass"
            if total_critical_findings > 0:
                overall_status = "fail"
            elif total_warning_findings > 0:
                overall_status = "uncertain"
            
            # Вычисляем общий процент соответствия
            total_pages = len(pages)
            successful_pages = len([r for r in page_results if r.get("overall_status") == "pass"])
            compliance_percentage = (successful_pages / total_pages * 100) if total_pages > 0 else 0
            
            # Формируем общий отчет
            combined_result = {
                "overall_status": overall_status,
                "confidence": 0.8,  # Высокая уверенность при постраничной проверке
                "total_findings": total_findings,
                "critical_findings": total_critical_findings,
                "warning_findings": total_warning_findings,
                "info_findings": total_info_findings,
                "total_pages": total_pages,
                "successful_pages": successful_pages,
                "page_results": page_results,
                "findings": all_findings,
                "summary": f"Проверка завершена. Обработано {total_pages} страниц. Найдено {total_findings} нарушений.",
                "compliance_percentage": compliance_percentage,
                "recommendations": f"Общие рекомендации: {total_critical_findings} критических нарушений, {total_warning_findings} предупреждений, {total_info_findings} замечаний."
            }
            
            # Сохраняем результат в базу данных
            # ===== СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ПРОВЕРКИ LLM =====
            # Сохраняем общий результат проверки в базу данных
            await self.save_norm_control_result(document_id, combined_result)
            
            return {
                "status": "success",
                "result": combined_result,
                "pages_processed": len(pages)
            }
                    
        except Exception as e:
            logger.error(f"Norm control check error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def save_norm_control_result(self, document_id: int, check_result: Dict[str, Any]):
        """Сохранение результата проверки нормоконтроля от LLM в базу данных"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO norm_control_results 
                    (checkable_document_id, analysis_date, analysis_type, model_used, overall_status, confidence,
                     total_findings, critical_findings, warning_findings, info_findings,
                     findings_details, summary, compliance_score, recommendations)
                    VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    document_id,
                    "norm_control",
                    "llama3.1:8b",
                    check_result.get("overall_status", "uncertain"),
                    check_result.get("confidence", 0.0),
                    check_result.get("total_findings", 0),
                    check_result.get("critical_findings", 0),
                    check_result.get("warning_findings", 0),
                    check_result.get("info_findings", 0),
                    json.dumps(check_result.get("findings", [])),
                    check_result.get("summary", ""),
                    check_result.get("compliance_percentage", 0),
                    check_result.get("recommendations", "")
                ))
                
                result_id = cursor.fetchone()[0]
                self.db_conn.commit()
                
                # ===== СОЗДАНИЕ ОТЧЕТА О ПРОВЕРКЕ LLM =====
                # Создаем отчет о проверке на основе результатов LLM
                await self.create_review_report(document_id, result_id, check_result)
                
                logger.info(f"Saved norm control result {result_id} for document {document_id}")
                return result_id
                
        except Exception as e:
            logger.error(f"Save norm control result error: {e}")
            self.db_conn.rollback()
            raise

    async def create_review_report(self, document_id: int, result_id: int, check_result: Dict[str, Any]):
        """Создание отчета о проверке на основе результатов LLM"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO review_reports 
                    (checkable_document_id, norm_control_result_id, report_date, review_type,
                     overall_status, reviewer_notes, report_content)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    document_id,
                    result_id,
                    "automatic",
                    check_result.get("overall_status", "uncertain"),
                    f"Автоматическая проверка: {check_result.get('summary', '')}",
                    json.dumps(check_result)
                ))
                
                report_id = cursor.fetchone()[0]
                self.db_conn.commit()
                
                logger.info(f"Created review report {report_id} for document {document_id}")
                return report_id
                
        except Exception as e:
            logger.error(f"Create review report error: {e}")
            self.db_conn.rollback()
            raise

# Модели Pydantic
class StatusUpdateRequest(BaseModel):
    status: str
    reviewer: str = None
    notes: str = None

# Глобальный экземпляр парсера
parser = DocumentParser()

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("other")
):
    """Загрузка и парсинг документа"""
    print(f"🔍 [DEBUG] DocumentParser: Upload started for file: {file.filename}")
    print(f"🔍 [DEBUG] DocumentParser: File size: {file.size} bytes")
    print(f"🔍 [DEBUG] DocumentParser: Content type: {file.content_type}")
    
    try:
        # Чтение файла
        print(f"🔍 [DEBUG] DocumentParser: Reading file content...")
        file_content = await file.read()
        file_size = len(file_content)
        print(f"🔍 [DEBUG] DocumentParser: File content read, size: {file_size} bytes")
        
        # Определение типа файла
        print(f"🔍 [DEBUG] DocumentParser: Detecting file type...")
        file_type = parser.detect_file_type(file_content)
        print(f"🔍 [DEBUG] DocumentParser: Detected file type: {file_type}")
        
        # Вычисление хеша
        print(f"🔍 [DEBUG] DocumentParser: Calculating file hash...")
        document_hash = parser.calculate_file_hash(file_content)
        print(f"🔍 [DEBUG] DocumentParser: File hash: {document_hash}")
        
        # Проверка на дубликат
        print(f"🔍 [DEBUG] DocumentParser: Checking for duplicates...")
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id FROM uploaded_documents WHERE document_hash = %s", (document_hash,))
            existing_doc = cursor.fetchone()
            if existing_doc:
                print(f"🔍 [DEBUG] DocumentParser: Document already exists with ID: {existing_doc['id']}")
                raise HTTPException(status_code=400, detail="Document already exists")
        print(f"🔍 [DEBUG] DocumentParser: No duplicates found")
        
        # Сохраняем файл на диск
        print(f"🔍 [DEBUG] DocumentParser: Saving file to disk...")
        file_path = f"/app/uploads/{document_hash}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)
        print(f"🔍 [DEBUG] DocumentParser: File saved to: {file_path}")
        
        # Создаем запись в базе данных с статусом "processing"
        print(f"🔍 [DEBUG] DocumentParser: Creating initial database record...")
        document_id = parser.create_initial_document_record(
            file.filename,
            file_type,
            file_size,
            document_hash,
            file_path,
            category
        )
        print(f"🔍 [DEBUG] DocumentParser: Created document record with ID: {document_id}")
        
        # Асинхронная обработка документа
        print(f"🔍 [DEBUG] DocumentParser: Starting async document processing...")
        print(f"🔍 [DEBUG] DocumentParser: Adding background task for document {document_id}")
        background_tasks.add_task(
            process_document_async,
            document_id=document_id,
            file_path=file_path,
            file_type=file_type,
            filename=file.filename
        )
        print(f"🔍 [DEBUG] DocumentParser: Background task added successfully")
        
        result = {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "status": "processing",
            "message": "Document uploaded successfully. Processing started in background."
        }
        print(f"🔍 [DEBUG] DocumentParser: Upload initiated successfully: {result}")
        return result
        
    except HTTPException as e:
        print(f"🔍 [DEBUG] DocumentParser: HTTPException in upload: {e.status_code} - {e.detail}")
        raise e
    except Exception as e:
        print(f"🔍 [DEBUG] DocumentParser: Unexpected error in upload: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"🔍 [DEBUG] DocumentParser: Traceback: {traceback.format_exc()}")
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_async(document_id: int, file_path: str, file_type: str, filename: str):
    """Асинхронная обработка документа"""
    print(f"🔍 [DEBUG] DocumentParser: Starting async processing for document {document_id}")
    print(f"🔍 [DEBUG] DocumentParser: File type: {file_type}, filename: {filename}")
    print(f"🔍 [DEBUG] DocumentParser: File path: {file_path}")
    
    try:
        # Обновляем статус на "processing"
        print(f"🔍 [DEBUG] DocumentParser: Updating status to 'processing' for document {document_id}")
        parser.update_document_status(document_id, "processing")
        print(f"🔍 [DEBUG] DocumentParser: Status updated successfully")
        
        # Читаем файл с диска
        print(f"🔍 [DEBUG] DocumentParser: Reading file from disk: {file_path}")
        with open(file_path, "rb") as f:
            file_content = f.read()
        print(f"🔍 [DEBUG] DocumentParser: File content size: {len(file_content)} bytes")
        
        # Парсинг документа
        print(f"🔍 [DEBUG] DocumentParser: Parsing document {document_id}...")
        if file_type == "pdf":
            elements = parser.parse_pdf(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        print(f"🔍 [DEBUG] DocumentParser: Parsing completed for document {document_id}, elements count: {len(elements.document_pages_results)}")
        
        # Сохранение элементов в базу данных
        print(f"🔍 [DEBUG] DocumentParser: Saving elements to database for document {document_id}...")
        parser.save_elements_to_database(document_id, elements)
        
        # Подсчет токенов
        print(f"🔍 [DEBUG] DocumentParser: Calculating tokens for document {document_id}...")
        total_tokens = parser.calculate_document_tokens(elements)
        
        # Обновляем запись в базе данных
        print(f"🔍 [DEBUG] DocumentParser: Updating document record for {document_id}...")
        parser.update_document_completion(document_id, len(elements.document_pages_results), total_tokens)
        
        # Асинхронная индексация в RAG-сервис
        print(f"🔍 [DEBUG] DocumentParser: Starting RAG indexing for document {document_id}...")
        asyncio.create_task(
            parser.index_to_rag_service_async(
                document_id=document_id,
                document_title=filename,
                inspection_result=elements
            )
        )
        
        print(f"🔍 [DEBUG] DocumentParser: Async processing completed for document {document_id}")
        
    except Exception as e:
        print(f"🔍 [DEBUG] DocumentParser: Error in async processing for document {document_id}: {str(e)}")
        import traceback
        print(f"🔍 [DEBUG] DocumentParser: Async processing traceback: {traceback.format_exc()}")
        
        # Обновляем статус на "error"
        try:
            parser.update_document_status(document_id, "error")
        except Exception as update_error:
            print(f"🔍 [DEBUG] DocumentParser: Failed to update error status: {update_error}")
        
        logger.error(f"Async processing error for document {document_id}: {e}")

@app.get("/documents")
async def list_documents():
    """Список загруженных документов"""
    try:
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, original_filename, file_type, file_size, upload_date, processing_status, token_count, category
                FROM uploaded_documents
                ORDER BY upload_date DESC
            """)
            documents = cursor.fetchall()
            
        return {"documents": [dict(doc) for doc in documents]}
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/elements")
async def get_document_elements(document_id: int):
    """Получение элементов документа"""
    try:
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, element_type, element_content, page_number, confidence_score, created_at
                FROM extracted_elements
                WHERE uploaded_document_id = %s
                ORDER BY page_number, id
            """, (document_id,))
            elements = cursor.fetchall()
            
        return {"elements": [dict(elem) for elem in elements]}
        
    except Exception as e:
        logger.error(f"Get elements error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/{document_id}/process")
async def process_document_manual(document_id: int, background_tasks: BackgroundTasks):
    """Ручной запуск обработки документа"""
    try:
        print(f"🔍 [DEBUG] DocumentParser: Manual processing requested for document {document_id}")
        
        # Получаем информацию о документе
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, original_filename, file_type, file_size, document_hash, processing_status
                FROM uploaded_documents
                WHERE id = %s
            """, (document_id,))
            document = cursor.fetchone()
            
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        if document["processing_status"] == "completed":
            return {"message": "Document already processed", "status": "completed"}
            
        print(f"🔍 [DEBUG] DocumentParser: Document info: {document}")
        
        # Получаем путь к файлу из базы данных
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT file_path FROM uploaded_documents WHERE id = %s
            """, (document_id,))
            result = cursor.fetchone()
            file_path = result.get("file_path") if result else None
            
        if not file_path:
            raise HTTPException(status_code=404, detail="File not found on disk")
            
        # Запускаем асинхронную обработку
        background_tasks.add_task(
            process_document_async,
            document_id=document_id,
            file_path=file_path,
            file_type=document["file_type"],
            filename=document["original_filename"]
        )
        
        return {"message": "Processing started", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Manual processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_normative_document(document_id: int):
    """Удаление нормативного документа"""
    try:
        success = await parser.delete_normative_document(document_id)
        
        if success:
            return {"status": "success", "message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete normative document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/checkable-documents/{document_id}")
async def delete_checkable_document(document_id: int):
    """Удаление проверяемого документа"""
    try:
        success = parser.delete_checkable_document(document_id)
        
        if success:
            return {"status": "success", "message": f"Checkable document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete checkable document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/chat")
async def upload_chat_file(
    file: UploadFile = File(...)
):
    """Загрузка файла для обработки в чате"""
    try:
        # Чтение файла
        file_content = await file.read()
        file_size = len(file_content)
        
        # Проверка размера файла (максимум 10MB для чата)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Определение типа файла
        file_type = parser.detect_file_type(file_content)
        
        # Парсинг файла
        elements = parser.parse_file(file_content, file_type)
        
        # Извлечение текстового содержимого
        text_content = "\n\n".join([elem.get("element_content", "") for elem in elements if elem.get("element_content")])
        
        # Ограничиваем размер текста для чата (учитывая лимит Ollama ~4000 токенов)
        # Приблизительно 1 токен = 4 символа, но лучше использовать более консервативный подход
        # 4000 токенов ≈ 12000 символов (3 символа на токен)
        max_chars = 10000  # Консервативный лимит для Ollama
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars] + "\n\n[Содержимое обрезано из-за ограничений размера. Максимум 10000 символов для чата]"
        
        return {
            "success": True,
            "filename": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "content": text_content,
            "elements_count": len(elements.document_pages_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat file upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/checkable")
async def upload_checkable_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Загрузка проверяемого документа"""
    try:
        # Чтение файла
        file_content = await file.read()
        file_size = len(file_content)
        
        # Определение типа файла
        file_type = parser.detect_file_type(file_content)
        
        # Вычисление хеша
        document_hash = parser.calculate_file_hash(file_content)
        
        # Проверка на дубликат
        with parser.db_conn.cursor() as cursor:
            cursor.execute("SELECT id FROM checkable_documents WHERE document_hash = %s", (document_hash,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Document already exists")
        
        # Парсинг документа
        if file_type == "pdf":
            # TODO: log start of parsing process
            inspection_result = parser.parse_pdf(file_content)
            # TODO: log result of partong PDF

        elif file_type == "docx":
            # Временно используем старый метод для docx
            elements = parser.parse_docx(file_content)
            inspection_result = DocumentInspectionResult()
            inspection_result.document_pages_results = []
            for element in elements:
                page_result = DocumentPageInspectionResult()
                page_result.page_number = element.get("page_number", 1)
                page_result.page_text = element.get("element_content", "")
                page_result.page_text_confidence = element.get("confidence_score", 1.0)
                page_result.page_text_method = "docx_parsing"
                page_result.page_text_length = len(element.get("element_content", ""))
                page_result.page_type = "vector"
                inspection_result.document_pages_results.append(page_result)
        elif file_type == "dwg":
            # Временно используем старый метод для dwg
            elements = parser.parse_dwg(file_content)
            inspection_result = DocumentInspectionResult()
            inspection_result.document_pages_results = []
            for element in elements:
                page_result = DocumentPageInspectionResult()
                page_result.page_number = element.get("page_number", 1)
                page_result.page_text = element.get("element_content", "")
                page_result.page_text_confidence = element.get("confidence_score", 1.0)
                page_result.page_text_method = "dwg_parsing"
                page_result.page_text_length = len(element.get("element_content", ""))
                page_result.page_type = "vector"
                inspection_result.document_pages_results.append(page_result)
        elif file_type == "ifc":
            # Временно используем старый метод для ifc
            elements = parser.parse_ifc(file_content)
            inspection_result = DocumentInspectionResult()
            inspection_result.document_pages_results = []
            for element in elements:
                page_result = DocumentPageInspectionResult()
                page_result.page_number = element.get("page_number", 1)
                page_result.page_text = element.get("element_content", "")
                page_result.page_text_confidence = element.get("confidence_score", 1.0)
                page_result.page_text_method = "ifc_parsing"
                page_result.page_text_length = len(element.get("element_content", ""))
                page_result.page_type = "vector"
                inspection_result.document_pages_results.append(page_result)
        elif file_type == "txt":
            # Временно используем старый метод для txt
            elements = parser.parse_text(file_content)
            inspection_result = DocumentInspectionResult()
            inspection_result.document_pages_results = []
            for element in elements:
                page_result = DocumentPageInspectionResult()
                page_result.page_number = element.get("page_number", 1)
                page_result.page_text = element.get("element_content", "")
                page_result.page_text_confidence = element.get("confidence_score", 1.0)
                page_result.page_text_method = "txt_parsing"
                page_result.page_text_length = len(element.get("element_content", ""))
                page_result.page_type = "vector"
                inspection_result.document_pages_results.append(page_result)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
        
        # Определение категории документа
        content_text = "\n".join([page_result.page_text for page_result in inspection_result.document_pages_results])
        category = parser.determine_document_category(file.filename, content_text)
        
        # Сохранение как проверяемый документ
        document_id = parser.save_checkable_document(
            file.filename,
            file.filename,
            file_type,
            file_size,
            document_hash,
            inspection_result,
            category
        )
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "pages_count": len(inspection_result.document_pages_results),
            "category": category,
            "status": "completed",
            "review_deadline": (datetime.now() + timedelta(days=2)).isoformat(),
            "document_stats": {
                "total_pages": inspection_result.document_pages,
                "vector_pages": inspection_result.document_pages_vector,
                "scanned_pages": inspection_result.document_pages_scanned,
                "unknown_pages": inspection_result.document_pages_unknown,
                "a4_sheets_equivalent": inspection_result.document_pages_total_a4_sheets_equivalent
            }
        }
        
    except Exception as e:
        logger.error(f"Upload checkable document error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checkable-documents")
async def list_checkable_documents():
    """Список проверяемых документов"""
    try:
        documents = parser.get_checkable_documents()
        return {"documents": documents}
        
    except Exception as e:
        logger.error(f"List checkable documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checkable-documents/{document_id}/elements")
async def get_checkable_document_elements(document_id: int):
    """Получение элементов проверяемого документа"""
    try:
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, element_type, element_content, page_number, confidence_score, created_at
                FROM checkable_elements
                WHERE checkable_document_id = %s
                ORDER BY page_number, id
            """, (document_id,))
            elements = cursor.fetchall()
            
        return {"elements": [dict(elem) for elem in elements]}
        
    except Exception as e:
        logger.error(f"Get checkable elements error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/checkable-documents/{document_id}/status")
async def update_checkable_document_status(
    document_id: int,
    request: StatusUpdateRequest
):
    """Обновление статуса проверяемого документа"""
    try:
        success = parser.update_review_status(document_id, request.status, request.reviewer, request.notes)
        if success:
            return {"status": "success", "message": f"Document {document_id} status updated"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except Exception as e:
        logger.error(f"Update status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup-expired")
async def cleanup_expired_documents():
    """Очистка просроченных документов"""
    try:
        deleted_count = parser.cleanup_expired_documents()
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} expired documents"
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex-documents")
async def reindex_documents():
    """Принудительная реиндексация всех документов"""
    try:
        # Получаем все документы
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, original_filename, token_count
                FROM uploaded_documents
                WHERE processing_status = 'completed'
                ORDER BY upload_date DESC
            """)
            documents = cursor.fetchall()
        
        total_documents = len(documents)
        total_tokens = sum(doc['token_count'] or 0 for doc in documents)
        
        # Получаем элементы для каждого документа и пересчитываем токены
        updated_count = 0
        new_total_tokens = 0
        
        for doc in documents:
            try:
                # Получаем элементы документа в отдельном блоке
                with parser.db_conn.cursor(cursor_factory=RealDictCursor) as element_cursor:
                    element_cursor.execute("""
                        SELECT element_content
                        FROM extracted_elements
                        WHERE uploaded_document_id = %s
                    """, (doc['id'],))
                    elements = element_cursor.fetchall()
                
                # Подсчитываем токены
                total_doc_tokens = 0
                for element in elements:
                    if element['element_content']:
                        total_doc_tokens += parser.count_tokens(element['element_content'])
                
                # Обновляем количество токенов
                with parser.db_conn.cursor() as update_cursor:
                    update_cursor.execute("""
                        UPDATE uploaded_documents
                        SET token_count = %s
                        WHERE id = %s
                    """, (total_doc_tokens, doc['id']))
                
                # Индексируем документ в RAG сервис
                try:
                    # Получаем элементы для индексации
                    with parser.db_conn.cursor(cursor_factory=RealDictCursor) as rag_cursor:
                        rag_cursor.execute("""
                            SELECT element_type, element_content, page_number
                            FROM extracted_elements
                            WHERE uploaded_document_id = %s
                            ORDER BY page_number, id
                        """, (doc['id'],))
                        rag_elements = rag_cursor.fetchall()
                    
                    # Индексируем в RAG сервис
                    await parser.index_to_rag_service(
                        document_id=doc['id'],
                        document_title=doc['original_filename'],
                        elements=[dict(elem) for elem in rag_elements]
                    )
                    logger.info(f"Successfully indexed document {doc['id']} in RAG service")
                except Exception as rag_error:
                    logger.error(f"Failed to index document {doc['id']} in RAG service: {rag_error}")
                
                new_total_tokens += total_doc_tokens
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Error updating tokens for document {doc['id']}: {e}")
                parser.db_conn.rollback()
                continue
        
        parser.db_conn.commit()
        
        return {
            "status": "success",
            "total_documents": total_documents,
            "updated_documents": updated_count,
            "old_total_tokens": total_tokens,
            "new_total_tokens": new_total_tokens,
            "message": f"Reindexed {updated_count} documents with {new_total_tokens} total tokens"
        }
        
    except Exception as e:
        logger.error(f"Reindex error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/tokens")
async def get_document_tokens(document_id: int):
    """Получение информации о токенах документа"""
    try:
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, original_filename, token_count, file_size, upload_date
                FROM uploaded_documents
                WHERE id = %s
            """, (document_id,))
            document = cursor.fetchone()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Получаем детальную информацию о токенах по элементам
            cursor.execute("""
                SELECT element_type, element_content, page_number
                FROM extracted_elements
                WHERE uploaded_document_id = %s
                ORDER BY page_number, id
            """, (document_id,))
            elements = cursor.fetchall()
            
            # Подсчитываем токены по типам элементов
            token_stats = {
                "total_tokens": document['token_count'] or 0,
                "elements_count": len(elements.document_pages_results),
                "by_type": {},
                "by_page": {}
            }
            
            for element in elements:
                element_type = element['element_type']
                page_number = element['page_number'] or 1
                content = element['element_content'] or ""
                
                if content:
                    tokens = parser.count_tokens(content)
                    
                    # По типам
                    if element_type not in token_stats["by_type"]:
                        token_stats["by_type"][element_type] = {"count": 0, "tokens": 0}
                    token_stats["by_type"][element_type]["count"] += 1
                    token_stats["by_type"][element_type]["tokens"] += tokens
                    
                    # По страницам
                    if page_number not in token_stats["by_page"]:
                        token_stats["by_page"][page_number] = {"count": 0, "tokens": 0}
                    token_stats["by_page"][page_number]["count"] += 1
                    token_stats["by_page"][page_number]["tokens"] += tokens
            
            return {
                "document": dict(document),
                "token_statistics": token_stats
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document tokens error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Модели Pydantic для настроек
class SettingUpdateRequest(BaseModel):
    setting_value: str

class SettingCreateRequest(BaseModel):
    setting_key: str
    setting_value: str
    setting_description: str
    setting_type: str = "text"

@app.get("/settings/prompt-templates")
async def get_prompt_templates():
    """Получение доступных шаблонов промптов"""
    try:
        logger.info("Getting prompt templates...")
        
        # Получаем основной промпт
        normcontrol_prompt = parser.get_system_setting("normcontrol_prompt")
        logger.info(f"Normcontrol prompt: {normcontrol_prompt[:100] if normcontrol_prompt else 'None'}...")
        
        # Получаем шаблон промпта (если есть)
        prompt_template = parser.get_system_setting("normcontrol_prompt_template")
        logger.info(f"Prompt template: {prompt_template[:100] if prompt_template else 'None'}...")
        
        templates = {
            "normcontrol_prompt": normcontrol_prompt,
            "normcontrol_prompt_template": prompt_template,
            "has_custom_template": prompt_template is not None
        }
        
        logger.info("Successfully retrieved prompt templates")
        return {"status": "success", "templates": templates}
    except Exception as e:
        logger.error(f"Get prompt templates error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings/prompt-templates")
async def update_prompt_template(request: Dict[str, Any]):
    """Обновление шаблона промпта"""
    try:
        template_key = request.get("template_key")
        template_value = request.get("template_value")
        template_description = request.get("template_description", "")
        
        if not template_key or not template_value:
            raise HTTPException(status_code=400, detail="Missing template_key or template_value")
        
        success = parser.create_system_setting(
            template_key, 
            template_value, 
            template_description, 
            "prompt_template"
        )
        
        if success:
            return {"status": "success", "message": f"Template {template_key} updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update template")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update prompt template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_settings():
    """Получение всех настроек системы"""
    try:
        settings = parser.get_system_settings()
        return {"settings": settings}
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings/{setting_key}")
async def get_setting(setting_key: str):
    """Получение конкретной настройки"""
    try:
        setting_value = parser.get_system_setting(setting_key)
        if setting_value is None:
            raise HTTPException(status_code=404, detail="Setting not found")
        return {"setting_key": setting_key, "setting_value": setting_value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get setting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/settings/{setting_key}")
async def update_setting(setting_key: str, request: SettingUpdateRequest):
    """Обновление настройки"""
    try:
        success = parser.update_system_setting(setting_key, request.setting_value)
        if success:
            return {"status": "success", "message": f"Setting {setting_key} updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Setting not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update setting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings")
async def create_setting(request: SettingCreateRequest):
    """Создание новой настройки"""
    try:
        success = parser.create_system_setting(
            request.setting_key,
            request.setting_value,
            request.setting_description,
            request.setting_type
        )
        if success:
            return {"status": "success", "message": f"Setting {request.setting_key} created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create setting")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create setting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/settings/{setting_key}")
async def delete_setting(setting_key: str):
    """Удаление настройки"""
    try:
        success = parser.delete_system_setting(setting_key)
        if success:
            return {"status": "success", "message": f"Setting {setting_key} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Setting not found or cannot be deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete setting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checkable-documents/{document_id}/report")
async def get_checkable_document_report(document_id: int):
    """Получение отчета о проверке документа"""
    try:
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Получаем информацию о документе
            cursor.execute("""
                SELECT id, original_filename, file_type, upload_date, review_deadline, review_status
                FROM checkable_documents
                WHERE id = %s
            """, (document_id,))
            document = cursor.fetchone()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Получаем результаты нормоконтроля
            cursor.execute("""
                SELECT id, analysis_date, overall_status, confidence,
                       total_findings, critical_findings, warning_findings, info_findings,
                       findings_details, summary, compliance_score, recommendations
                FROM norm_control_results
                WHERE checkable_document_id = %s
                ORDER BY analysis_date DESC
                LIMIT 1
            """, (document_id,))
            norm_result = cursor.fetchone()
            
            # Получаем отчеты о проверке
            cursor.execute("""
                SELECT id, report_date, overall_status, reviewer_notes, report_content
                FROM review_reports
                WHERE checkable_document_id = %s
                ORDER BY report_date DESC
            """, (document_id,))
            reports = cursor.fetchall()
            
            return {
                "document": dict(document),
                "norm_control_result": dict(norm_result) if norm_result else None,
                "review_reports": [dict(report) for report in reports]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checkable-documents/{document_id}/check")
async def trigger_norm_control_check(document_id: int):
    """Принудительный запуск проверки нормоконтроля"""
    try:
        # Получаем содержимое документа
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT element_content
                FROM checkable_elements
                WHERE checkable_document_id = %s
                ORDER BY element_order, page_number
            """, (document_id,))
            elements = cursor.fetchall()
        
        if not elements:
            raise HTTPException(status_code=404, detail="Document content not found")
        
        # Объединяем содержимое
        document_content = "\n\n".join([elem["element_content"] for elem in elements])
        
        # ===== ЗАПУСК ПРОВЕРКИ НОРМОКОНТРОЛЯ С ПРИМЕНЕНИЕМ LLM =====
        # Выполняем проверку документа с использованием LLM
        result = await parser.perform_norm_control_check(document_id, document_content)
        
        return {
            "status": "success",
            "message": "Norm control check completed",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trigger norm control check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checkable-documents/{document_id}/format-statistics")
async def get_document_format_statistics(document_id: int):
    """Получение статистики форматов документа"""
    try:
        stats = parser.get_document_format_statistics(document_id)
        return {"status": "success", "statistics": stats}
    except Exception as e:
        logger.error(f"Get document format statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    try:
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Статистика по загруженным документам
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed_documents,
                    COUNT(CASE WHEN processing_status = 'pending' THEN 1 END) as pending_documents,
                    COUNT(CASE WHEN processing_status = 'error' THEN 1 END) as error_documents,
                    COUNT(CASE WHEN file_type = 'pdf' THEN 1 END) as pdf_documents,
                    COUNT(CASE WHEN file_type = 'docx' THEN 1 END) as docx_documents,
                    COUNT(CASE WHEN file_type = 'dwg' THEN 1 END) as dwg_documents,
                    COUNT(CASE WHEN file_type = 'txt' THEN 1 END) as txt_documents,
                    SUM(file_size) as total_size_bytes,
                    AVG(file_size) as avg_file_size_bytes,
                    SUM(token_count) as total_tokens
                FROM uploaded_documents
            """)
            doc_stats = cursor.fetchone()
            
            # Статистика по проверяемым документам
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_checkable_documents,
                    COUNT(CASE WHEN review_status = 'pending' THEN 1 END) as pending_reviews,
                    COUNT(CASE WHEN review_status = 'completed' THEN 1 END) as completed_reviews,
                    COUNT(CASE WHEN review_status = 'in_progress' THEN 1 END) as in_progress_reviews,
                    COUNT(CASE WHEN review_status = 'overdue' THEN 1 END) as overdue_reviews
                FROM checkable_documents
            """)
            checkable_stats = cursor.fetchone()
            
            # Статистика по извлеченным элементам
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_elements,
                    COUNT(CASE WHEN element_type = 'text' THEN 1 END) as text_elements,
                    COUNT(CASE WHEN element_type = 'table' THEN 1 END) as table_elements,
                    COUNT(CASE WHEN element_type = 'figure' THEN 1 END) as figure_elements,
                    COUNT(CASE WHEN element_type = 'stamp' THEN 1 END) as stamp_elements
                FROM extracted_elements
            """)
            elements_stats = cursor.fetchone()
            
            # Статистика по результатам нормоконтроля
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_norm_control_results,
                    COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as completed_checks,
                    COUNT(CASE WHEN analysis_status = 'pending' THEN 1 END) as pending_checks,
                    COUNT(CASE WHEN analysis_status = 'error' THEN 1 END) as error_checks,
                    SUM(total_findings) as total_findings,
                    SUM(critical_findings) as critical_findings,
                    SUM(warning_findings) as warning_findings,
                    SUM(info_findings) as info_findings
                FROM norm_control_results
            """)
            norm_control_stats = cursor.fetchone()
            
            # Статистика по отчетам
            cursor.execute("""
                SELECT COUNT(*) as total_review_reports
                FROM review_reports
            """)
            reports_stats = cursor.fetchone()
            
            # Статистика по времени обработки (последние 24 часа)
            cursor.execute("""
                SELECT 
                    COUNT(*) as documents_last_24h
                FROM uploaded_documents 
                WHERE upload_date >= NOW() - INTERVAL '24 hours'
            """)
            time_stats = cursor.fetchone()
            
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "documents": {
                    "total": doc_stats["total_documents"] or 0,
                    "completed": doc_stats["completed_documents"] or 0,
                    "pending": doc_stats["pending_documents"] or 0,
                    "error": doc_stats["error_documents"] or 0,
                    "by_type": {
                        "pdf": doc_stats["pdf_documents"] or 0,
                        "docx": doc_stats["docx_documents"] or 0,
                        "dwg": doc_stats["dwg_documents"] or 0,
                        "txt": doc_stats["txt_documents"] or 0
                    },
                    "total_size_bytes": doc_stats["total_size_bytes"] or 0,
                    "avg_file_size_bytes": float(doc_stats["avg_file_size_bytes"] or 0),
                    "total_tokens": doc_stats["total_tokens"] or 0
                },
                "checkable_documents": {
                    "total": checkable_stats["total_checkable_documents"] or 0,
                    "pending_reviews": checkable_stats["pending_reviews"] or 0,
                    "completed_reviews": checkable_stats["completed_reviews"] or 0,
                    "in_progress_reviews": checkable_stats["in_progress_reviews"] or 0,
                    "overdue_reviews": checkable_stats["overdue_reviews"] or 0
                },
                "elements": {
                    "total": elements_stats["total_elements"] or 0,
                    "text": elements_stats["text_elements"] or 0,
                    "table": elements_stats["table_elements"] or 0,
                    "figure": elements_stats["figure_elements"] or 0,
                    "stamp": elements_stats["stamp_elements"] or 0
                },
                "norm_control": {
                    "total_results": norm_control_stats["total_norm_control_results"] or 0,
                    "completed_checks": norm_control_stats["completed_checks"] or 0,
                    "pending_checks": norm_control_stats["pending_checks"] or 0,
                    "error_checks": norm_control_stats["error_checks"] or 0,
                    "total_findings": norm_control_stats["total_findings"] or 0,
                    "critical_findings": norm_control_stats["critical_findings"] or 0,
                    "warning_findings": norm_control_stats["warning_findings"] or 0,
                    "info_findings": norm_control_stats["info_findings"] or 0
                },
                "reports": {
                    "total": reports_stats["total_review_reports"] or 0
                },
                "performance": {
                    "documents_last_24h": time_stats["documents_last_24h"] or 0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверка PostgreSQL
        with parser.db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Проверка Qdrant
        parser.qdrant_client.get_collections()
        
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Тестовый endpoint для проверки
@app.get("/test-prompt-templates")
async def test_prompt_templates():
    """Тестовый endpoint для проверки промпт-шаблонов"""
    return {"status": "success", "message": "Test endpoint works"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
