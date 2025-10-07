"""
Модуль для OCR обработки документов с распознаванием таблиц и чертежей
Использует pytesseract, opencv и pdf2image для улучшенного распознавания
"""

import logging
import os
import tempfile
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

# OCR зависимости
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Класс для OCR обработки документов"""
    
    def __init__(self, 
                 tesseract_path: Optional[str] = None,
                 languages: List[str] = None,
                 dpi: int = 300):
        """
        Инициализация OCR процессора
        
        Args:
            tesseract_path: Путь к tesseract (если не в PATH)
            languages: Языки для распознавания (по умолчанию: rus+eng)
            dpi: DPI для конвертации PDF в изображения
        """
        if not OCR_AVAILABLE:
            raise ImportError("OCR зависимости не установлены. Установите: pip install pytesseract pillow pdf2image opencv-python")
        
        self.languages = languages or ["rus", "eng"]
        self.dpi = dpi
        
        # Настройка tesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Конфигурация tesseract для лучшего распознавания
        self.tesseract_config = {
            'table': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя.,:;()[]{}"\\/-+=*%№',
            'text': '--oem 3 --psm 6',
            'drawing': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя.,:;()[]{}"\\/-+=*%№°ØR'
        }
    
    def process_pdf_with_ocr(self, pdf_path: str) -> Dict[str, Any]:
        """
        Обработка PDF с OCR для распознавания таблиц и чертежей
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            Словарь с результатами OCR обработки
        """
        try:
            logger.info(f"🔍 [OCR] Начинаем OCR обработку PDF: {pdf_path}")
            
            # Конвертируем PDF в изображения
            images = self._pdf_to_images(pdf_path)
            
            result = {
                'success': True,
                'pages': [],
                'tables': [],
                'drawings': [],
                'total_pages': len(images),
                'processing_time': 0
            }
            
            import time
            start_time = time.time()
            
            for page_num, image in enumerate(images, 1):
                logger.info(f"🔍 [OCR] Обрабатываем страницу {page_num}/{len(images)}")
                
                page_result = self._process_page_with_ocr(image, page_num)
                result['pages'].append(page_result)
                
                # Добавляем найденные таблицы и чертежи
                if page_result.get('tables'):
                    result['tables'].extend(page_result['tables'])
                if page_result.get('drawings'):
                    result['drawings'].extend(page_result['drawings'])
            
            result['processing_time'] = time.time() - start_time
            logger.info(f"✅ [OCR] OCR обработка завершена за {result['processing_time']:.2f} сек")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка OCR обработки: {e}")
            return {
                'success': False,
                'error': str(e),
                'pages': [],
                'tables': [],
                'drawings': []
            }
    
    def _pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Конвертация PDF в изображения"""
        try:
            # Конвертируем PDF в изображения с высоким DPI
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt='RGB',
                thread_count=2
            )
            
            logger.info(f"📄 [OCR] PDF конвертирован в {len(images)} изображений")
            return images
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка конвертации PDF: {e}")
            return []
    
    def _process_page_with_ocr(self, image: Image.Image, page_num: int) -> Dict[str, Any]:
        """Обработка одной страницы с OCR"""
        try:
            # Конвертируем PIL Image в OpenCV формат
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Предобработка изображения
            processed_image = self._preprocess_image(cv_image)
            
            # Распознавание текста
            text_result = self._extract_text_with_ocr(processed_image)
            
            # Поиск таблиц
            tables = self._detect_and_extract_tables(cv_image, processed_image, page_num)
            
            # Поиск чертежей
            drawings = self._detect_and_extract_drawings(cv_image, processed_image, page_num)
            
            return {
                'page_number': page_num,
                'text': text_result['text'],
                'confidence': text_result['confidence'],
                'tables': tables,
                'drawings': drawings,
                'processing_success': True
            }
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка обработки страницы {page_num}: {e}")
            return {
                'page_number': page_num,
                'text': '',
                'confidence': 0.0,
                'tables': [],
                'drawings': [],
                'processing_success': False,
                'error': str(e)
            }
    
    def _preprocess_image(self, cv_image: np.ndarray) -> np.ndarray:
        """Предобработка изображения для лучшего OCR"""
        try:
            # Конвертируем в оттенки серого
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Увеличиваем контраст
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Убираем шум
            denoised = cv2.medianBlur(enhanced, 3)
            
            # Бинаризация
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Морфологические операции для улучшения текста
            kernel = np.ones((1,1), np.uint8)
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка предобработки изображения: {e}")
            return cv_image
    
    def _extract_text_with_ocr(self, image: np.ndarray) -> Dict[str, Any]:
        """Извлечение текста с помощью OCR"""
        try:
            # Конвертируем обратно в PIL Image
            pil_image = Image.fromarray(image)
            
            # Распознавание текста
            text = pytesseract.image_to_string(
                pil_image,
                lang='+'.join(self.languages),
                config=self.tesseract_config['text']
            )
            
            # Получаем данные с уверенностью
            data = pytesseract.image_to_data(
                pil_image,
                lang='+'.join(self.languages),
                config=self.tesseract_config['text'],
                output_type=pytesseract.Output.DICT
            )
            
            # Вычисляем среднюю уверенность
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text.strip(),
                'confidence': avg_confidence / 100.0  # Нормализуем до 0-1
            }
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка извлечения текста: {e}")
            return {'text': '', 'confidence': 0.0}
    
    def _detect_and_extract_tables(self, original_image: np.ndarray, processed_image: np.ndarray, page_num: int) -> List[Dict[str, Any]]:
        """Обнаружение и извлечение таблиц"""
        try:
            tables = []
            
            # Поиск горизонтальных и вертикальных линий
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            # Обнаружение горизонтальных линий
            horizontal_lines = cv2.morphologyEx(processed_image, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Обнаружение вертикальных линий
            vertical_lines = cv2.morphologyEx(processed_image, cv2.MORPH_OPEN, vertical_kernel)
            
            # Объединяем линии
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Находим контуры таблиц
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours):
                # Фильтруем по размеру
                area = cv2.contourArea(contour)
                if area < 1000:  # Минимальная площадь таблицы
                    continue
                
                # Получаем ограничивающий прямоугольник
                x, y, w, h = cv2.boundingRect(contour)
                
                # Извлекаем область таблицы
                table_roi = original_image[y:y+h, x:x+w]
                
                # OCR для таблицы
                table_text = self._extract_table_text(table_roi)
                
                if table_text and len(table_text.strip()) > 10:  # Минимальная длина текста
                    tables.append({
                        'table_number': i + 1,
                        'page_number': page_num,
                        'bbox': [x, y, x+w, y+h],
                        'text': table_text,
                        'area': area,
                        'confidence': 0.8  # Высокая уверенность для обнаруженных таблиц
                    })
            
            logger.info(f"📊 [OCR] Найдено {len(tables)} таблиц на странице {page_num}")
            return tables
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка обнаружения таблиц: {e}")
            return []
    
    def _extract_table_text(self, table_image: np.ndarray) -> str:
        """Извлечение текста из области таблицы"""
        try:
            # Предобработка для таблицы
            processed = self._preprocess_image(table_image)
            
            # OCR с конфигурацией для таблиц
            pil_image = Image.fromarray(processed)
            text = pytesseract.image_to_string(
                pil_image,
                lang='+'.join(self.languages),
                config=self.tesseract_config['table']
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка извлечения текста таблицы: {e}")
            return ""
    
    def _detect_and_extract_drawings(self, original_image: np.ndarray, processed_image: np.ndarray, page_num: int) -> List[Dict[str, Any]]:
        """Обнаружение и извлечение чертежей"""
        try:
            drawings = []
            
            # Поиск контуров (чертежи обычно имеют четкие контуры)
            contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                
                # Фильтруем по размеру и форме (чертежи обычно большие и сложные)
                if area < 5000:  # Минимальная площадь чертежа
                    continue
                
                # Проверяем сложность контура (чертежи имеют много точек)
                if len(contour) < 50:
                    continue
                
                # Получаем ограничивающий прямоугольник
                x, y, w, h = cv2.boundingRect(contour)
                
                # Проверяем соотношение сторон (чертежи обычно не очень вытянутые)
                aspect_ratio = w / h
                if aspect_ratio < 0.3 or aspect_ratio > 3.0:
                    continue
                
                # Извлекаем область чертежа
                drawing_roi = original_image[y:y+h, x:x+w]
                
                # OCR для чертежа (поиск размеров, маркировок и т.д.)
                drawing_text = self._extract_drawing_text(drawing_roi)
                
                drawings.append({
                    'drawing_number': i + 1,
                    'page_number': page_num,
                    'bbox': [x, y, x+w, y+h],
                    'text': drawing_text,
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'contour_points': len(contour),
                    'confidence': 0.7  # Средняя уверенность для чертежей
                })
            
            logger.info(f"📐 [OCR] Найдено {len(drawings)} чертежей на странице {page_num}")
            return drawings
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка обнаружения чертежей: {e}")
            return []
    
    def _extract_drawing_text(self, drawing_image: np.ndarray) -> str:
        """Извлечение текста из области чертежа"""
        try:
            # Предобработка для чертежа
            processed = self._preprocess_image(drawing_image)
            
            # OCR с конфигурацией для чертежей
            pil_image = Image.fromarray(processed)
            text = pytesseract.image_to_string(
                pil_image,
                lang='+'.join(self.languages),
                config=self.tesseract_config['drawing']
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ [OCR] Ошибка извлечения текста чертежа: {e}")
            return ""


class AdvancedTableExtractor:
    """Продвинутый экстрактор таблиц с использованием компьютерного зрения"""
    
    def __init__(self):
        self.min_table_area = 1000
        self.min_cell_area = 100
    
    def extract_tables_from_image(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Извлечение таблиц из изображения с помощью компьютерного зрения"""
        try:
            # Конвертируем в оттенки серого
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Бинаризация
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Поиск горизонтальных линий
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Поиск вертикальных линий
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # Объединяем линии
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Находим контуры
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            tables = []
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > self.min_table_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Извлекаем ячейки таблицы
                    cells = self._extract_table_cells(image[y:y+h, x:x+w])
                    
                    tables.append({
                        'table_id': i + 1,
                        'bbox': [x, y, x+w, y+h],
                        'area': area,
                        'cells': cells,
                        'rows': len(cells),
                        'columns': len(cells[0]) if cells else 0
                    })
            
            return tables
            
        except Exception as e:
            logger.error(f"❌ [TABLE_EXTRACTOR] Ошибка извлечения таблиц: {e}")
            return []
    
    def _extract_table_cells(self, table_roi: np.ndarray) -> List[List[str]]:
        """Извлечение ячеек таблицы"""
        try:
            # Конвертируем в оттенки серого
            gray = cv2.cvtColor(table_roi, cv2.COLOR_BGR2GRAY)
            
            # Бинаризация
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Поиск горизонтальных и вертикальных линий
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
            
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # Находим пересечения линий
            intersections = cv2.bitwise_and(horizontal_lines, vertical_lines)
            
            # Находим контуры ячеек
            contours, _ = cv2.findContours(intersections, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            cells = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_cell_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    cell_roi = table_roi[y:y+h, x:x+w]
                    
                    # OCR для ячейки
                    cell_text = self._extract_cell_text(cell_roi)
                    cells.append(cell_text)
            
            # Организуем ячейки в строки и столбцы
            return self._organize_cells_into_table(cells, table_roi.shape)
            
        except Exception as e:
            logger.error(f"❌ [TABLE_EXTRACTOR] Ошибка извлечения ячеек: {e}")
            return []
    
    def _extract_cell_text(self, cell_image: np.ndarray) -> str:
        """Извлечение текста из ячейки таблицы"""
        try:
            if not OCR_AVAILABLE:
                return ""
            
            # Предобработка
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR
            pil_image = Image.fromarray(binary)
            text = pytesseract.image_to_string(
                pil_image,
                lang='rus+eng',
                config='--oem 3 --psm 8'
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ [TABLE_EXTRACTOR] Ошибка OCR ячейки: {e}")
            return ""
    
    def _organize_cells_into_table(self, cells: List[str], image_shape: Tuple[int, int, int]) -> List[List[str]]:
        """Организация ячеек в структуру таблицы"""
        # Упрощенная реализация - в реальности нужен более сложный алгоритм
        # для определения строк и столбцов на основе позиций ячеек
        if not cells:
            return []
        
        # Предполагаем простую таблицу с равномерным распределением
        estimated_rows = max(1, int(len(cells) ** 0.5))
        estimated_cols = max(1, len(cells) // estimated_rows)
        
        table = []
        for i in range(estimated_rows):
            row = []
            for j in range(estimated_cols):
                cell_index = i * estimated_cols + j
                if cell_index < len(cells):
                    row.append(cells[cell_index])
                else:
                    row.append("")
            table.append(row)
        
        return table
