import json
import logging
import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_fonts()
        self._setup_styles()
    
    def _setup_fonts(self):
        """Настройка шрифтов для поддержки кириллицы"""
        try:
            # Регистрируем шрифты DejaVu для поддержки кириллицы
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_name = os.path.basename(font_path).replace('.ttf', '')
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    logger.info(f"Registered font: {font_name} from {font_path}")
            
            # Устанавливаем DejaVu Sans как основной шрифт
            if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                self.default_font = "DejaVuSans"
                self.bold_font = "DejaVuSans-Bold"
                self.serif_font = "DejaVuSerif"
                self.serif_bold_font = "DejaVuSerif-Bold"
            else:
                # Fallback на стандартные шрифты
                self.default_font = "Helvetica"
                self.bold_font = "Helvetica-Bold"
                self.serif_font = "Times-Roman"
                self.serif_bold_font = "Times-Bold"
                logger.warning("DejaVu fonts not found, using fallback fonts")
                
        except Exception as e:
            logger.error(f"Error setting up fonts: {e}")
            # Fallback на стандартные шрифты
            self.default_font = "Helvetica"
            self.bold_font = "Helvetica-Bold"
            self.serif_font = "Times-Roman"
            self.serif_bold_font = "Times-Bold"
    
    def _setup_styles(self):
        """Настройка стилей для PDF"""
        # Основной заголовок
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontName=self.bold_font,
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Заголовок раздела
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontName=self.bold_font,
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        # Подзаголовок
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading3'],
            fontName=self.bold_font,
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkgreen
        ))
        
        # Обычный текст
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontName=self.default_font,
            fontSize=10,
            spaceAfter=6
        ))
        
        # Текст статуса
        self.styles.add(ParagraphStyle(
            name='StatusText',
            parent=self.styles['Normal'],
            fontName=self.default_font,
            fontSize=10,
            spaceAfter=6,
            textColor=colors.darkred
        ))
    
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
    
    def _create_header(self, document_info):
        """Создание заголовка отчета"""
        elements = []
        
        # Основной заголовок
        elements.append(Paragraph("ОТЧЕТ О ПРОВЕРКЕ НОРМОКОНТРОЛЯ", self.styles['MainTitle']))
        elements.append(Spacer(1, 20))
        
        # Информация о документе
        doc_table_data = [
            ['Параметр', 'Значение'],
            ['Название файла', document_info.get('original_filename', 'Не указано')],
            ['ID документа', str(document_info.get('id', 'Не указано'))],
            ['Статус обработки', document_info.get('processing_status', 'Не указано')],
            ['Дата создания отчета', datetime.now().strftime('%d.%m.%Y %H:%M:%S')]
        ]
        
        doc_table = Table(doc_table_data, colWidths=[2*inch, 4*inch])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), self.default_font)
        ]))
        
        elements.append(doc_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_project_info_section(self, project_info):
        """Создание раздела с информацией о проекте"""
        elements = []
        
        if not project_info:
            return elements
        
        project_data = self._parse_json_string(project_info)
        
        elements.append(Paragraph("ИНФОРМАЦИЯ О ПРОЕКТЕ", self.styles['SectionTitle']))
        
        project_table_data = [
            ['Параметр', 'Значение'],
            ['Название проекта', project_data.get('project_name', 'Не указано')],
            ['Стадия проектирования', project_data.get('project_stage', 'Не указано')],
            ['Тип проекта', project_data.get('project_type', 'Не указано')],
            ['Комплект документов', project_data.get('document_set', 'Не указано')],
            ['Уверенность анализа', f"{project_data.get('confidence', 0) * 100:.1f}%"]
        ]
        
        project_table = Table(project_table_data, colWidths=[2*inch, 4*inch])
        project_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), self.default_font)
        ]))
        
        elements.append(project_table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_compliance_summary_section(self, compliance_summary):
        """Создание раздела с сводкой по соответствию"""
        elements = []
        
        if not compliance_summary:
            return elements
        
        compliance_data = self._parse_json_string(compliance_summary)
        
        elements.append(Paragraph("СВОДКА ПО СООТВЕТСТВИЮ НОРМАМ", self.styles['SectionTitle']))
        
        # Общая статистика
        stats_table_data = [
            ['Параметр', 'Значение'],
            ['Всего страниц', str(compliance_data.get('total_pages', 0))],
            ['Соответствующих страниц', str(compliance_data.get('compliant_pages', 0))],
            ['Процент соответствия', f"{compliance_data.get('compliance_percentage', 0):.1f}%"],
            ['Всего находок', str(compliance_data.get('total_findings', 0))],
            ['Критических находок', str(compliance_data.get('critical_findings', 0))],
            ['Предупреждений', str(compliance_data.get('warning_findings', 0))],
            ['Информационных находок', str(compliance_data.get('info_findings', 0))]
        ]
        
        stats_table = Table(stats_table_data, colWidths=[2.5*inch, 3.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), self.default_font)
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 15))
        
        # Детальные находки
        findings = compliance_data.get('findings', [])
        if findings:
            elements.append(Paragraph("ДЕТАЛЬНЫЕ НАХОДКИ", self.styles['SubTitle']))
            
            findings_table_data = [['Тип', 'Заголовок', 'Описание', 'Рекомендация', 'Страница']]
            
            for finding in findings[:10]:  # Ограничиваем первыми 10 находками
                findings_table_data.append([
                    finding.get('type', ''),
                    finding.get('title', '')[:30] + '...' if len(finding.get('title', '')) > 30 else finding.get('title', ''),
                    finding.get('description', '')[:40] + '...' if len(finding.get('description', '')) > 40 else finding.get('description', ''),
                    finding.get('recommendation', '')[:40] + '...' if len(finding.get('recommendation', '')) > 40 else finding.get('recommendation', ''),
                    str(finding.get('page_number', ''))
                ])
            
            findings_table = Table(findings_table_data, colWidths=[0.8*inch, 1.5*inch, 1.5*inch, 1.5*inch, 0.7*inch])
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 1), (-1, -1), self.default_font)
            ]))
            
            elements.append(findings_table)
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_sections_analysis_section(self, sections_analysis):
        """Создание раздела с анализом секций"""
        elements = []
        
        if not sections_analysis:
            return elements
        
        sections_data = self._parse_json_string(sections_analysis)
        
        elements.append(Paragraph("АНАЛИЗ СЕКЦИЙ ДОКУМЕНТА", self.styles['SectionTitle']))
        
        sections = sections_data.get('sections', [])
        if sections:
            sections_table_data = [['Тип секции', 'Название', 'Страницы', 'Приоритет проверки']]
            
            for section in sections:
                sections_table_data.append([
                    section.get('section_type', ''),
                    section.get('section_name', ''),
                    f"{section.get('start_page', '')}-{section.get('end_page', '')}",
                    section.get('check_priority', '')
                ])
            
            sections_table = Table(sections_table_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1.5*inch])
            sections_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), self.default_font)
            ]))
            
            elements.append(sections_table)
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_overall_status_section(self, overall_status, execution_time):
        """Создание раздела с общим статусом"""
        elements = []
        
        elements.append(Paragraph("ОБЩИЙ СТАТУС ПРОВЕРКИ", self.styles['SectionTitle']))
        
        # Определяем цвет и текст статуса
        status_colors = {
            'pass': colors.green,
            'warning': colors.orange,
            'fail': colors.red
        }
        
        status_texts = {
            'pass': 'ПРОЙДЕН',
            'warning': 'ТРЕБУЕТ ВНИМАНИЯ',
            'fail': 'НЕ ПРОЙДЕН'
        }
        
        status_color = status_colors.get(overall_status, colors.grey)
        status_text = status_texts.get(overall_status, 'НЕИЗВЕСТНО')
        
        status_table_data = [
            ['Параметр', 'Значение'],
            ['Общий статус', status_text],
            ['Время выполнения', f"{execution_time:.3f} секунд"]
        ]
        
        status_table = Table(status_table_data, colWidths=[2*inch, 4*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (1, 1), (1, 1), status_color),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
            ('FONTNAME', (1, 1), (1, 1), self.bold_font),
            ('FONTNAME', (0, 1), (0, 1), self.default_font),
            ('FONTNAME', (1, 2), (1, 2), self.default_font)
        ]))
        
        elements.append(status_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def generate_hierarchical_report_pdf(self, report_data):
        """Генерация PDF отчета для иерархической проверки"""
        try:
            # Создаем буфер для PDF
            buffer = BytesIO()
            
            # Создаем документ
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            
            # Получаем данные отчета
            hierarchical_result = report_data.get('hierarchical_result', {})
            document_info = report_data.get('document_info', {})
            
            # Создаем заголовок
            elements.extend(self._create_header(document_info))
            
            # Информация о проекте
            if hierarchical_result.get('project_info'):
                elements.extend(self._create_project_info_section(hierarchical_result['project_info']))
            
            # Сводка по соответствию
            if hierarchical_result.get('norm_compliance_summary'):
                elements.extend(self._create_compliance_summary_section(hierarchical_result['norm_compliance_summary']))
            
            # Анализ секций
            if hierarchical_result.get('sections_analysis'):
                elements.extend(self._create_sections_analysis_section(hierarchical_result['sections_analysis']))
            
            # Общий статус
            overall_status = hierarchical_result.get('overall_status', 'unknown')
            execution_time = hierarchical_result.get('execution_time', 0)
            elements.extend(self._create_overall_status_section(overall_status, execution_time))
            
            # Строим PDF
            doc.build(elements)
            
            # Получаем содержимое буфера
            buffer.seek(0)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"PDF report generated successfully, size: {len(pdf_content)} bytes")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def generate_report_pdf(self, report_data):
        """Генерация PDF отчета (основной метод)"""
        # Проверяем тип отчета
        if report_data.get('hierarchical_result'):
            return self.generate_hierarchical_report_pdf(report_data)
        else:
            # Для обычных отчетов пока возвращаем заглушку
            logger.warning("Regular norm control reports not implemented yet")
            raise NotImplementedError("Regular norm control reports not implemented yet")
