import json
import logging
import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn

logger = logging.getLogger(__name__)

class DOCXReportGenerator:
    def __init__(self):
        self.document = None
        self._setup_styles()
    
    def _setup_styles(self):
        """Настройка стилей для DOCX документа"""
        # Стили будут применяться при создании документа
        pass
    
    def _parse_json_string(self, json_str):
        """Парсинг JSON строки, словаря или Python repr строки"""
        try:
            if isinstance(json_str, str):
                # Пробуем сначала как JSON
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Если не JSON, пробуем как Python repr (заменяем одинарные кавычки на двойные)
                    try:
                        # Заменяем одинарные кавычки на двойные для JSON совместимости
                        json_compatible = json_str.replace("'", '"')
                        return json.loads(json_compatible)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse string as JSON or Python repr: {json_str[:100]}...")
                        return {}
            elif isinstance(json_str, dict):
                return json_str
            else:
                logger.warning(f"Unexpected data type: {type(json_str)}")
                return {}
        except Exception as e:
            logger.warning(f"Failed to parse data: {e}")
            return {}
    
    def _add_heading(self, text, level=1):
        """Добавление заголовка"""
        heading = self.document.add_heading(text, level)
        if level == 1:
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # Устанавливаем цвет заголовка
            for run in heading.runs:
                run.font.color.rgb = RGBColor(0, 51, 102)  # Темно-синий
        return heading
    
    def _add_paragraph(self, text, style='Normal'):
        """Добавление параграфа"""
        paragraph = self.document.add_paragraph(text)
        if style == 'Normal':
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return paragraph
    
    def _create_table(self, data, headers=None):
        """Создание таблицы"""
        if headers:
            table_data = [headers] + data
        else:
            table_data = data
        
        table = self.document.add_table(rows=len(table_data), cols=len(table_data[0]))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = 'Table Grid'
        
        # Заполняем таблицу данными
        for i, row_data in enumerate(table_data):
            for j, cell_data in enumerate(row_data):
                cell = table.cell(i, j)
                cell.text = str(cell_data)
                
                # Стилизация заголовка таблицы
                if i == 0 and headers:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)  # Белый текст
                    # Устанавливаем фон заголовка
                    shading_elm = OxmlElement('w:shd')
                    shading_elm.set(qn('w:val'), 'clear')
                    shading_elm.set(qn('w:color'), 'auto')
                    shading_elm.set(qn('w:fill'), '4472C4')  # Синий фон
                    cell._tc.get_or_add_tcPr().append(shading_elm)
                else:
                    # Стилизация обычных ячеек
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(10)
        
        return table
    
    def _create_header(self, document_info):
        """Создание заголовка отчета"""
        # Основной заголовок
        self._add_heading("ОТЧЕТ О ПРОВЕРКЕ НОРМОКОНТРОЛЯ", 1)
        
        # Информация о документе
        self._add_heading("Информация о документе", 2)
        
        doc_data = [
            ['Название файла', document_info.get('original_filename', 'Не указано')],
            ['ID документа', str(document_info.get('id', 'Не указано'))],
            ['Статус обработки', document_info.get('processing_status', 'Не указано')],
            ['Дата создания отчета', datetime.now().strftime('%d.%m.%Y %H:%M:%S')]
        ]
        
        self._create_table(doc_data, ['Параметр', 'Значение'])
        
        # Добавляем отступ
        self.document.add_paragraph()
    
    def _create_project_info_section(self, project_info):
        """Создание раздела с информацией о проекте"""
        if not project_info:
            return
        
        self._add_heading("Информация о проекте", 2)
        
        project_data = self._parse_json_string(project_info)
        
        project_table_data = [
            ['Название проекта', project_data.get('project_name', 'Не указано')],
            ['Стадия проектирования', project_data.get('project_stage', 'Не указано')],
            ['Тип проекта', project_data.get('project_type', 'Не указано')],
            ['Марка комплекта', project_data.get('document_set', 'Не указано')],
            ['Уверенность анализа', f"{project_data.get('confidence', 0) * 100:.1f}%"]
        ]
        
        self._create_table(project_table_data, ['Параметр', 'Значение'])
        self.document.add_paragraph()
    
    def _create_compliance_summary_section(self, compliance_summary):
        """Создание раздела с сводкой по соответствию"""
        if not compliance_summary:
            return
        
        self._add_heading("Сводка по соответствию нормам", 2)
        
        compliance_data = self._parse_json_string(compliance_summary)
        
        # Добавляем информацию о том, на соответствие каким документам выполнялась проверка
        project_stage = compliance_data.get('project_stage', 'Неизвестная стадия')
        document_set = compliance_data.get('document_set', 'Неизвестный комплект')
        
        compliance_info = f"Документ проверен на соответствие: {project_stage}, {document_set}"
        self._add_paragraph(compliance_info)
        self.document.add_paragraph()
        
        # Общая статистика
        stats_data = [
            ['Страниц в документе', str(compliance_data.get('total_pages', 0))],
            ['Листов формата А4', str(compliance_data.get('total_pages', 0))],
            ['Соответствующих страниц', str(compliance_data.get('compliant_pages', 0))],
            ['Процент соответствия', f"{compliance_data.get('compliance_percentage', 0):.1f}%"],
            ['Всего находок', str(compliance_data.get('total_findings', 0))],
            ['Критических находок', str(compliance_data.get('critical_findings', 0))],
            ['Предупреждений', str(compliance_data.get('warning_findings', 0))],
            ['Информационных находок', str(compliance_data.get('info_findings', 0))]
        ]
        
        self._create_table(stats_data, ['Параметр', 'Значение'])
        self.document.add_paragraph()
        
        # Детальные находки
        findings = compliance_data.get('findings', [])
        if findings:
            self._add_heading("Детальные находки", 3)
            
            findings_data = []
            for finding in findings[:10]:  # Ограничиваем первыми 10 находками
                findings_data.append([
                    finding.get('type', ''),
                    finding.get('title', '')[:50] + '...' if len(finding.get('title', '')) > 50 else finding.get('title', ''),
                    finding.get('description', '')[:60] + '...' if len(finding.get('description', '')) > 60 else finding.get('description', ''),
                    finding.get('recommendation', '')[:60] + '...' if len(finding.get('recommendation', '')) > 60 else finding.get('recommendation', ''),
                    str(finding.get('page_number', ''))
                ])
            
            self._create_table(findings_data, ['Тип', 'Заголовок', 'Описание', 'Рекомендация', 'Страница'])
            self.document.add_paragraph()
    
    def _create_sections_analysis_section(self, sections_analysis):
        """Создание раздела с анализом секций"""
        if not sections_analysis:
            return
        
        self._add_heading("Анализ секций документа", 2)
        
        sections_data = self._parse_json_string(sections_analysis)
        
        sections = sections_data.get('sections', [])
        if sections:
            sections_table_data = []
            for section in sections:
                sections_table_data.append([
                    section.get('section_type', ''),
                    section.get('section_name', ''),
                    f"{section.get('start_page', '')}-{section.get('end_page', '')}",
                    section.get('check_priority', '')
                ])
            
            self._create_table(sections_table_data, ['Тип секции', 'Название', 'Страницы', 'Приоритет проверки'])
            self.document.add_paragraph()
    
    def _create_overall_status_section(self, overall_status, execution_time):
        """Создание раздела с общим статусом"""
        self._add_heading("Общий статус проверки", 2)
        
        # Определяем текст статуса
        status_texts = {
            'pass': 'ПРОЙДЕН',
            'warning': 'ТРЕБУЕТ ВНИМАНИЯ',
            'fail': 'НЕ ПРОЙДЕН'
        }
        
        status_text = status_texts.get(overall_status, 'НЕИЗВЕСТНО')
        
        status_data = [
            ['Общий статус', status_text],
            ['Время выполнения', f"{execution_time:.3f} секунд"]
        ]
        
        table = self._create_table(status_data, ['Параметр', 'Значение'])
        
        # Выделяем статус цветом
        if overall_status == 'pass':
            status_color = RGBColor(0, 128, 0)  # Зеленый
        elif overall_status == 'warning':
            status_color = RGBColor(255, 165, 0)  # Оранжевый
        elif overall_status == 'fail':
            status_color = RGBColor(255, 0, 0)  # Красный
        else:
            status_color = RGBColor(128, 128, 128)  # Серый
        
        # Применяем цвет к ячейке со статусом
        status_cell = table.cell(1, 1)
        for paragraph in status_cell.paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = status_color
                run.bold = True
        
        self.document.add_paragraph()
    
    def generate_hierarchical_report_docx(self, report_data):
        """Генерация DOCX отчета для иерархической проверки"""
        try:
            # Создаем новый документ
            self.document = Document()
            
            # Получаем данные отчета
            hierarchical_result = report_data.get('hierarchical_result', {})
            document_info = report_data.get('document_info', {})
            
            # Создаем заголовок
            self._create_header(document_info)
            
            # Информация о проекте
            if hierarchical_result.get('project_info'):
                self._create_project_info_section(hierarchical_result['project_info'])
            
            # Сводка по соответствию
            if hierarchical_result.get('norm_compliance_summary'):
                self._create_compliance_summary_section(hierarchical_result['norm_compliance_summary'])
            
            # Анализ секций
            if hierarchical_result.get('sections_analysis'):
                self._create_sections_analysis_section(hierarchical_result['sections_analysis'])
            
            # Общий статус
            overall_status = hierarchical_result.get('overall_status', 'unknown')
            execution_time = hierarchical_result.get('execution_time', 0)
            self._create_overall_status_section(overall_status, execution_time)
            
            # Сохраняем документ в буфер
            from io import BytesIO
            buffer = BytesIO()
            self.document.save(buffer)
            buffer.seek(0)
            docx_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"DOCX report generated successfully, size: {len(docx_content)} bytes")
            return docx_content
            
        except Exception as e:
            logger.error(f"Error generating DOCX report: {e}")
            raise
    
    def generate_report_docx(self, report_data):
        """Генерация DOCX отчета (основной метод)"""
        # Проверяем тип отчета
        if report_data.get('hierarchical_result'):
            return self.generate_hierarchical_report_docx(report_data)
        else:
            # Для обычных отчетов пока возвращаем заглушку
            logger.warning("Regular norm control reports not implemented yet")
            raise NotImplementedError("Regular norm control reports not implemented yet")
