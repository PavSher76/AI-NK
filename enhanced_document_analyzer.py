"""
Улучшенный анализатор документов для чтения документации и чертежей
Специализирован для анализа проектной документации и извлечения метаданных
"""

import logging
import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import re

# Импорты для работы с PDF
try:
    import PyPDF2
    PDF2_AVAILABLE = True
except ImportError:
    PDF2_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text, extract_pages
    from pdfminer.layout import LAParams, LTTextContainer, LTTextBox, LTTextLine
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.pdfpage import PDFPage
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)


class DrawingMetadataExtractor:
    """Извлечение метаданных из чертежей и технических документов"""
    
    def __init__(self):
        self.stamp_patterns = [
            r'ЛИСТ\s+\d+',
            r'ИЗМ\.\s*\d+',
            r'ИНВ\.\s*№\s*\d+',
            r'ПОДП\.\s*И\s*ДАТА',
            r'СТ\.\s*ИНЖ\.',
            r'Н\.\s*КОНТР\.',
            r'УТВЕРЖД\.'
        ]
        
        self.drawing_elements = [
            'линии', 'окружности', 'прямоугольники', 'размеры', 'обозначения',
            'штриховка', 'выноски', 'координатные оси', 'масштаб'
        ]
    
    def extract_stamp_info(self, text: str) -> Dict[str, Any]:
        """Извлечение информации из штампа чертежа"""
        stamp_info = {
            'sheet_number': None,
            'revision': None,
            'inventory_number': None,
            'scale': None,
            'project_info': {},
            'approval_info': {}
        }
        
        # Поиск номера листа
        sheet_match = re.search(r'ЛИСТ\s+(\d+)', text, re.IGNORECASE)
        if sheet_match:
            stamp_info['sheet_number'] = int(sheet_match.group(1))
        
        # Поиск изменений
        revision_match = re.search(r'ИЗМ\.\s*(\d+)', text, re.IGNORECASE)
        if revision_match:
            stamp_info['revision'] = int(revision_match.group(1))
        
        # Поиск инвентарного номера
        inv_match = re.search(r'ИНВ\.\s*№\s*(\d+)', text, re.IGNORECASE)
        if inv_match:
            stamp_info['inventory_number'] = inv_match.group(1)
        
        # Поиск масштаба
        scale_match = re.search(r'М\s*(\d+:\d+)', text, re.IGNORECASE)
        if scale_match:
            stamp_info['scale'] = scale_match.group(1)
        
        return stamp_info
    
    def extract_drawing_elements(self, text: str) -> List[Dict[str, Any]]:
        """Извлечение элементов чертежа из текста"""
        elements = []
        
        # Поиск размеров
        dimensions = re.findall(r'(\d+(?:\.\d+)?)\s*мм', text)
        for dim in dimensions:
            elements.append({
                'type': 'dimension',
                'value': float(dim),
                'unit': 'мм',
                'confidence': 0.9
            })
        
        # Поиск обозначений материалов
        materials = re.findall(r'МАТЕРИАЛ[:\s]+([А-Яа-я\s\d]+)', text, re.IGNORECASE)
        for material in materials:
            elements.append({
                'type': 'material',
                'value': material.strip(),
                'confidence': 0.8
            })
        
        # Поиск маркировок
        markings = re.findall(r'МАРКА[:\s]+([А-Яа-я\d\-\.]+)', text, re.IGNORECASE)
        for marking in markings:
            elements.append({
                'type': 'marking',
                'value': marking.strip(),
                'confidence': 0.9
            })
        
        return elements


class ProjectDocumentAnalyzer:
    """Анализатор проектной документации"""
    
    def __init__(self):
        self.drawing_extractor = DrawingMetadataExtractor()
        self.supported_formats = ['.pdf', '.docx', '.txt']
    
    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """Полный анализ документа"""
        start_time = time.time()
        
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Определяем формат файла
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.pdf':
                result = self._analyze_pdf(file_path)
            else:
                raise ValueError(f"Неподдерживаемый формат: {file_extension}")
            
            # Добавляем общую информацию
            result.update({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'analysis_time': time.time() - start_time,
                'success': True
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа документа {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': str(file_path),
                'analysis_time': time.time() - start_time
            }
    
    def _analyze_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Анализ PDF документа"""
        try:
            # Пробуем разные методы извлечения
            if PDFPLUMBER_AVAILABLE:
                return self._analyze_with_pdfplumber(file_path)
            elif PDFMINER_AVAILABLE:
                return self._analyze_with_pdfminer(file_path)
            elif PDF2_AVAILABLE:
                return self._analyze_with_pypdf2(file_path)
            else:
                raise Exception("Нет доступных библиотек для работы с PDF")
                
        except Exception as e:
            logger.error(f"Ошибка анализа PDF {file_path}: {e}")
            raise
    
    def _analyze_with_pdfplumber(self, file_path: Path) -> Dict[str, Any]:
        """Анализ с помощью pdfplumber (лучший для таблиц и структуры)"""
        pages_data = []
        full_text = ""
        all_tables = []
        all_images = []
        
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"Анализируем страницу {page_num}/{total_pages}")
                
                # Извлечение текста
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"
                
                # Извлечение таблиц
                page_tables = page.extract_tables()
                for table_num, table in enumerate(page_tables, 1):
                    if table and len(table) > 1:
                        all_tables.append({
                            'page_number': page_num,
                            'table_number': table_num,
                            'data': table,
                            'rows': len(table),
                            'columns': len(table[0]) if table else 0
                        })
                
                # Извлечение изображений
                page_images = page.images
                for img_num, img in enumerate(page_images, 1):
                    all_images.append({
                        'page_number': page_num,
                        'image_number': img_num,
                        'bbox': img['bbox'],
                        'width': img['width'],
                        'height': img['height']
                    })
                
                # Анализ страницы
                page_analysis = self._analyze_page_content(page_text, page_num)
                
                pages_data.append({
                    'page_number': page_num,
                    'text': page_text,
                    'char_count': len(page_text),
                    'word_count': len(page_text.split()),
                    'analysis': page_analysis,
                    'tables_count': len(page_tables),
                    'images_count': len(page_images)
                })
        
        # Общий анализ документа
        document_analysis = self._analyze_document_structure(full_text, pages_data)
        
        return {
            'method': 'pdfplumber',
            'total_pages': total_pages,
            'pages': pages_data,
            'full_text': full_text,
            'tables': all_tables,
            'images': all_images,
            'document_analysis': document_analysis,
            'metadata': {
                'total_chars': len(full_text),
                'total_words': len(full_text.split()),
                'total_tables': len(all_tables),
                'total_images': len(all_images)
            }
        }
    
    def _analyze_with_pdfminer(self, file_path: Path) -> Dict[str, Any]:
        """Анализ с помощью pdfminer (лучший для точного извлечения текста)"""
        pages_data = []
        full_text = ""
        
        # Настройки для лучшего извлечения
        laparams = LAParams(
            word_margin=0.1,
            char_margin=2.0,
            line_margin=0.5,
            boxes_flow=0.5,
            all_texts=True
        )
        
        for page_num, page_layout in enumerate(extract_pages(str(file_path), laparams=laparams), 1):
            page_text = ""
            
            # Извлечение текста из элементов страницы
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_text += element.get_text()
            
            full_text += page_text + "\n"
            
            # Анализ страницы
            page_analysis = self._analyze_page_content(page_text, page_num)
            
            pages_data.append({
                'page_number': page_num,
                'text': page_text,
                'char_count': len(page_text),
                'word_count': len(page_text.split()),
                'analysis': page_analysis
            })
        
        # Общий анализ документа
        document_analysis = self._analyze_document_structure(full_text, pages_data)
        
        return {
            'method': 'pdfminer',
            'total_pages': len(pages_data),
            'pages': pages_data,
            'full_text': full_text,
            'document_analysis': document_analysis,
            'metadata': {
                'total_chars': len(full_text),
                'total_words': len(full_text.split())
            }
        }
    
    def _analyze_with_pypdf2(self, file_path: Path) -> Dict[str, Any]:
        """Анализ с помощью PyPDF2 (базовый)"""
        pages_data = []
        full_text = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                full_text += page_text + "\n"
                
                # Анализ страницы
                page_analysis = self._analyze_page_content(page_text, page_num + 1)
                
                pages_data.append({
                    'page_number': page_num + 1,
                    'text': page_text,
                    'char_count': len(page_text),
                    'word_count': len(page_text.split()),
                    'analysis': page_analysis
                })
        
        # Общий анализ документа
        document_analysis = self._analyze_document_structure(full_text, pages_data)
        
        return {
            'method': 'pypdf2',
            'total_pages': total_pages,
            'pages': pages_data,
            'full_text': full_text,
            'document_analysis': document_analysis,
            'metadata': {
                'total_chars': len(full_text),
                'total_words': len(full_text.split())
            }
        }
    
    def _analyze_page_content(self, text: str, page_num: int) -> Dict[str, Any]:
        """Анализ содержимого страницы"""
        analysis = {
            'page_type': 'unknown',
            'stamp_info': {},
            'drawing_elements': [],
            'technical_info': {},
            'compliance_issues': []
        }
        
        # Определение типа страницы
        if self._is_title_page(text):
            analysis['page_type'] = 'title_page'
        elif self._is_drawing_page(text):
            analysis['page_type'] = 'drawing_page'
        elif self._is_specification_page(text):
            analysis['page_type'] = 'specification_page'
        elif self._is_general_data_page(text):
            analysis['page_type'] = 'general_data_page'
        
        # Извлечение информации из штампа
        analysis['stamp_info'] = self.drawing_extractor.extract_stamp_info(text)
        
        # Извлечение элементов чертежа
        analysis['drawing_elements'] = self.drawing_extractor.extract_drawing_elements(text)
        
        # Извлечение технической информации
        analysis['technical_info'] = self._extract_technical_info(text)
        
        # Проверка на соответствие нормам
        analysis['compliance_issues'] = self._check_compliance_issues(text, page_num)
        
        return analysis
    
    def _is_title_page(self, text: str) -> bool:
        """Проверка, является ли страница титульной"""
        title_indicators = [
            'ТИТУЛЬНЫЙ ЛИСТ',
            'ПОЯСНИТЕЛЬНАЯ ЗАПИСКА',
            'ОБЩИЕ ДАННЫЕ',
            'СОДЕРЖАНИЕ'
        ]
        return any(indicator in text.upper() for indicator in title_indicators)
    
    def _is_drawing_page(self, text: str) -> bool:
        """Проверка, является ли страница чертежом"""
        drawing_indicators = [
            'МАСШТАБ',
            'ЛИСТ',
            'ИЗМ.',
            'ИНВ.',
            'ПОДП.',
            'СТ. ИНЖ.',
            'Н. КОНТР.',
            'УТВЕРЖД.'
        ]
        return any(indicator in text.upper() for indicator in drawing_indicators)
    
    def _is_specification_page(self, text: str) -> bool:
        """Проверка, является ли страница спецификацией"""
        spec_indicators = [
            'СПЕЦИФИКАЦИЯ',
            'ВЕДОМОСТЬ',
            'ПОЗИЦИЯ',
            'ОБОЗНАЧЕНИЕ',
            'НАИМЕНОВАНИЕ',
            'КОЛ.',
            'МАССА'
        ]
        return any(indicator in text.upper() for indicator in spec_indicators)
    
    def _is_general_data_page(self, text: str) -> bool:
        """Проверка, является ли страница общими данными"""
        general_indicators = [
            'ОБЩИЕ ДАННЫЕ',
            'ПРОЕКТ',
            'ОБЪЕКТ',
            'СТАДИЯ',
            'КОМПЛЕКТ'
        ]
        return any(indicator in text.upper() for indicator in general_indicators)
    
    def _extract_technical_info(self, text: str) -> Dict[str, Any]:
        """Извлечение технической информации"""
        tech_info = {
            'project_number': None,
            'object_name': None,
            'stage': None,
            'document_set': None,
            'materials': [],
            'dimensions': []
        }
        
        # Поиск номера проекта
        project_match = re.search(r'ПРОЕКТ[:\s]+([А-Яа-я\d\-\.]+)', text, re.IGNORECASE)
        if project_match:
            tech_info['project_number'] = project_match.group(1).strip()
        
        # Поиск названия объекта
        object_match = re.search(r'ОБЪЕКТ[:\s]+([А-Яа-я\s\d\-\.]+)', text, re.IGNORECASE)
        if object_match:
            tech_info['object_name'] = object_match.group(1).strip()
        
        # Поиск стадии
        stage_match = re.search(r'СТАДИЯ[:\s]+([А-Яа-я\s\d\-\.]+)', text, re.IGNORECASE)
        if stage_match:
            tech_info['stage'] = stage_match.group(1).strip()
        
        # Поиск комплекта документов
        set_match = re.search(r'КОМПЛЕКТ[:\s]+([А-Яа-я\s\d\-\.]+)', text, re.IGNORECASE)
        if set_match:
            tech_info['document_set'] = set_match.group(1).strip()
        
        return tech_info
    
    def _check_compliance_issues(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """Проверка на соответствие нормам"""
        issues = []
        
        # Проверка наличия штампа на чертеже
        if self._is_drawing_page(text) and not self._has_stamp(text):
            issues.append({
                'type': 'missing_stamp',
                'severity': 'critical',
                'description': 'Отсутствует штамп чертежа',
                'page': page_num
            })
        
        # Проверка масштаба
        if self._is_drawing_page(text) and not re.search(r'М\s*\d+:\d+', text, re.IGNORECASE):
            issues.append({
                'type': 'missing_scale',
                'severity': 'warning',
                'description': 'Не указан масштаб чертежа',
                'page': page_num
            })
        
        return issues
    
    def _has_stamp(self, text: str) -> bool:
        """Проверка наличия штампа"""
        stamp_indicators = ['ЛИСТ', 'ИЗМ.', 'ИНВ.', 'ПОДП.', 'СТ. ИНЖ.']
        return any(indicator in text.upper() for indicator in stamp_indicators)
    
    def _analyze_document_structure(self, full_text: str, pages_data: List[Dict]) -> Dict[str, Any]:
        """Анализ структуры документа"""
        structure = {
            'document_type': 'unknown',
            'total_pages': len(pages_data),
            'page_types': {},
            'compliance_score': 0.0,
            'recommendations': []
        }
        
        # Подсчет типов страниц
        for page in pages_data:
            page_type = page['analysis']['page_type']
            structure['page_types'][page_type] = structure['page_types'].get(page_type, 0) + 1
        
        # Определение типа документа
        if structure['page_types'].get('drawing_page', 0) > 0:
            structure['document_type'] = 'drawing_document'
        elif structure['page_types'].get('specification_page', 0) > 0:
            structure['document_type'] = 'specification_document'
        elif structure['page_types'].get('general_data_page', 0) > 0:
            structure['document_type'] = 'general_data_document'
        
        # Расчет оценки соответствия
        total_issues = sum(len(page['analysis']['compliance_issues']) for page in pages_data)
        structure['compliance_score'] = max(0, 100 - total_issues * 10)
        
        return structure


def analyze_project_document(file_path: str) -> Dict[str, Any]:
    """Функция для анализа проектного документа"""
    analyzer = ProjectDocumentAnalyzer()
    return analyzer.analyze_document(file_path)


if __name__ == "__main__":
    # Тестирование на конкретном документе
    file_path = "tests/TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf"
    
    print(f"🔍 Анализируем документ: {file_path}")
    print("=" * 80)
    
    result = analyze_project_document(file_path)
    
    if result['success']:
        print(f"✅ Анализ завершен успешно")
        print(f"📄 Метод: {result.get('method', 'unknown')}")
        print(f"📊 Страниц: {result.get('total_pages', 0)}")
        print(f"⏱️ Время анализа: {result.get('analysis_time', 0):.2f} сек")
        
        # Анализ структуры
        doc_analysis = result.get('document_analysis', {})
        print(f"\n📋 Тип документа: {doc_analysis.get('document_type', 'unknown')}")
        print(f"📈 Оценка соответствия: {doc_analysis.get('compliance_score', 0)}%")
        
        # Типы страниц
        page_types = doc_analysis.get('page_types', {})
        print(f"\n📄 Типы страниц:")
        for page_type, count in page_types.items():
            print(f"  - {page_type}: {count}")
        
        # Анализ первых страниц
        pages = result.get('pages', [])
        print(f"\n🔍 Анализ первых 3 страниц:")
        for i, page in enumerate(pages[:3]):
            print(f"\nСтраница {page['page_number']}:")
            print(f"  Тип: {page['analysis']['page_type']}")
            print(f"  Символов: {page['char_count']}")
            print(f"  Слов: {page['word_count']}")
            
            # Информация из штампа
            stamp_info = page['analysis']['stamp_info']
            if stamp_info.get('sheet_number'):
                print(f"  Номер листа: {stamp_info['sheet_number']}")
            if stamp_info.get('revision'):
                print(f"  Изменение: {stamp_info['revision']}")
            if stamp_info.get('scale'):
                print(f"  Масштаб: {stamp_info['scale']}")
            
            # Проблемы соответствия
            issues = page['analysis']['compliance_issues']
            if issues:
                print(f"  ⚠️ Проблемы: {len(issues)}")
                for issue in issues:
                    print(f"    - {issue['description']} ({issue['severity']})")
        
        # Сохранение результатов
        output_file = f"analysis_result_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в {output_file}")
        
    else:
        print(f"❌ Ошибка анализа: {result.get('error', 'Unknown error')}")
