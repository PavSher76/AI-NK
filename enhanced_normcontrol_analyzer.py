"""
Улучшенный анализатор для проверки нормоконтролем
Интегрирует ультимативный анализатор документов с нормативными требованиями ОНК
"""

import logging
import os
import json
import time
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from ultimate_document_analyzer import UltimateDocumentAnalyzer, DocumentType, PageType, SeverityLevel

logger = logging.getLogger(__name__)


class EnhancedNormControlAnalyzer:
    """Улучшенный анализатор нормоконтроля с интеграцией нормативных требований ОНК"""
    
    def __init__(self):
        self.document_analyzer = UltimateDocumentAnalyzer()
        self.normative_requirements = self._load_normative_requirements()
        self.onk_checklist = self._load_onk_checklist()
        self.ntd_list = self._load_ntd_list()
    
    def _load_normative_requirements(self) -> Dict[str, Any]:
        """Загрузка нормативных требований"""
        return {
            'gost_21_501_2018': {
                'name': 'ГОСТ 21.501-2018 Правила выполнения архитектурно-строительных чертежей',
                'requirements': [
                    'Наличие штампа чертежа',
                    'Указание масштаба',
                    'Наличие размеров',
                    'Правильное оформление линий',
                    'Соответствие условных обозначений'
                ]
            },
            'gost_r_21_101_2020': {
                'name': 'ГОСТ Р 21.101-2020 Система проектной документации',
                'requirements': [
                    'Наличие информации о проекте',
                    'Правильное оформление титульного листа',
                    'Соответствие структуры документа',
                    'Наличие общих данных'
                ]
            },
            'sp_48_13330_2019': {
                'name': 'СП 48.13330.2019 Организация строительства',
                'requirements': [
                    'Соответствие стадий проектирования',
                    'Правильное оформление исполнительной документации',
                    'Наличие необходимых разделов'
                ]
            }
        }
    
    def _load_onk_checklist(self) -> Dict[str, Any]:
        """Загрузка чек-листа ОНК"""
        return {
            'title': 'Чек-лист перед НК ПТИ',
            'sections': {
                'document_structure': [
                    'Наличие титульного листа',
                    'Наличие общих данных',
                    'Правильная нумерация листов',
                    'Соответствие марки документа'
                ],
                'drawing_requirements': [
                    'Наличие штампа на каждом листе',
                    'Указание масштаба',
                    'Наличие размеров',
                    'Правильное оформление линий',
                    'Соответствие условных обозначений'
                ],
                'technical_requirements': [
                    'Соответствие материалов',
                    'Правильность расчетов',
                    'Наличие необходимых сечений',
                    'Соответствие нормативным требованиям'
                ],
                'quality_requirements': [
                    'Четкость изображений',
                    'Читаемость текста',
                    'Правильность оформления',
                    'Отсутствие ошибок'
                ]
            }
        }
    
    def _load_ntd_list(self) -> Dict[str, Any]:
        """Загрузка перечня НТД по маркам"""
        return {
            'title': 'Перечень НТД для руководства внутри ОНК по маркам',
            'marks': {
                'АР': {
                    'name': 'Архитектурные решения',
                    'ntd_list': [
                        'ГОСТ 21.501-2018',
                        'ГОСТ Р 21.101-2020',
                        'СП 48.13330.2019',
                        'СП 70.13330.2012'
                    ],
                    'requirements': [
                        'Планы этажей',
                        'Фасады',
                        'Разрезы',
                        'Детали',
                        'Спецификации'
                    ]
                },
                'КЖ': {
                    'name': 'Конструктивные решения',
                    'ntd_list': [
                        'ГОСТ 21.501-2018',
                        'ГОСТ Р 21.101-2020',
                        'СП 16.13330.2017',
                        'СП 20.13330.2016'
                    ],
                    'requirements': [
                        'Планы конструкций',
                        'Схемы армирования',
                        'Детали узлов',
                        'Спецификации материалов'
                    ]
                },
                'КМ': {
                    'name': 'Металлоконструкции',
                    'ntd_list': [
                        'ГОСТ 21.501-2018',
                        'ГОСТ Р 21.101-2020',
                        'СП 16.13330.2017',
                        'ГОСТ 23118-2012'
                    ],
                    'requirements': [
                        'Планы металлоконструкций',
                        'Схемы узлов',
                        'Детали соединений',
                        'Спецификации'
                    ]
                }
            }
        }
    
    def analyze_document_for_normcontrol(self, file_path: str) -> Dict[str, Any]:
        """Анализ документа для нормоконтроля"""
        start_time = time.time()
        
        try:
            # Анализ документа
            doc_analysis = self.document_analyzer.analyze_document(file_path)
            
            if not doc_analysis['success']:
                return {
                    'success': False,
                    'error': doc_analysis['error'],
                    'analysis_time': time.time() - start_time
                }
            
            # Определение марки документа
            mark = doc_analysis['filename_analysis'].get('mark', 'Unknown')
            
            # Получение требований для марки
            mark_requirements = self.ntd_list['marks'].get(mark, {})
            
            # Проверка соответствия требованиям ОНК
            onk_compliance = self._check_onk_compliance(doc_analysis, mark_requirements)
            
            # Генерация отчета о нормоконтроле
            normcontrol_report = self._generate_normcontrol_report(
                doc_analysis, 
                onk_compliance, 
                mark_requirements
            )
            
            result = {
                'success': True,
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'analysis_time': time.time() - start_time,
                'document_analysis': doc_analysis,
                'mark_requirements': mark_requirements,
                'onk_compliance': onk_compliance,
                'normcontrol_report': normcontrol_report
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа нормоконтроля {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'analysis_time': time.time() - start_time
            }
    
    def _check_onk_compliance(self, doc_analysis: Dict[str, Any], mark_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка соответствия требованиям ОНК"""
        compliance = {
            'overall_score': 0.0,
            'sections': {},
            'total_issues': 0,
            'critical_issues': 0,
            'warning_issues': 0,
            'info_issues': 0,
            'recommendations': []
        }
        
        # Проверка структуры документа
        structure_score = self._check_document_structure(doc_analysis)
        compliance['sections']['document_structure'] = structure_score
        
        # Проверка требований к чертежам
        drawing_score = self._check_drawing_requirements(doc_analysis)
        compliance['sections']['drawing_requirements'] = drawing_score
        
        # Проверка технических требований
        technical_score = self._check_technical_requirements(doc_analysis, mark_requirements)
        compliance['sections']['technical_requirements'] = technical_score
        
        # Проверка требований качества
        quality_score = self._check_quality_requirements(doc_analysis)
        compliance['sections']['quality_requirements'] = quality_score
        
        # Расчет общей оценки
        section_scores = [score['score'] for score in compliance['sections'].values()]
        compliance['overall_score'] = sum(section_scores) / len(section_scores) if section_scores else 0.0
        
        # Подсчет проблем
        for section in compliance['sections'].values():
            compliance['total_issues'] += section['issues_count']
            compliance['critical_issues'] += section['critical_issues']
            compliance['warning_issues'] += section['warning_issues']
            compliance['info_issues'] += section['info_issues']
        
        # Генерация рекомендаций
        compliance['recommendations'] = self._generate_compliance_recommendations(compliance)
        
        return compliance
    
    def _check_document_structure(self, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка структуры документа"""
        score = 0.0
        issues = []
        critical_issues = 0
        warning_issues = 0
        info_issues = 0
        
        # Проверка наличия титульного листа
        pages = doc_analysis.get('pages_analysis', [])
        has_title_page = any(page['page_type'] == PageType.TITLE_PAGE for page in pages)
        
        if has_title_page:
            score += 25
        else:
            issues.append({
                'type': 'missing_title_page',
                'severity': 'critical',
                'description': 'Отсутствует титульный лист',
                'recommendation': 'Добавить титульный лист согласно ГОСТ Р 21.101-2020'
            })
            critical_issues += 1
        
        # Проверка наличия общих данных
        has_general_data = any(page['page_type'] == PageType.GENERAL_DATA_PAGE for page in pages)
        
        if has_general_data:
            score += 25
        else:
            issues.append({
                'type': 'missing_general_data',
                'severity': 'critical',
                'description': 'Отсутствуют общие данные',
                'recommendation': 'Добавить лист общих данных'
            })
            critical_issues += 1
        
        # Проверка правильной нумерации
        page_numbers = [page['page_number'] for page in pages]
        if page_numbers == list(range(1, len(pages) + 1)):
            score += 25
        else:
            issues.append({
                'type': 'incorrect_numbering',
                'severity': 'warning',
                'description': 'Неправильная нумерация страниц',
                'recommendation': 'Исправить нумерацию страниц'
            })
            warning_issues += 1
        
        # Проверка соответствия марки
        filename_analysis = doc_analysis.get('filename_analysis', {})
        mark = filename_analysis.get('mark')
        if mark:
            score += 25
        else:
            issues.append({
                'type': 'missing_mark',
                'severity': 'warning',
                'description': 'Не определена марка документа',
                'recommendation': 'Указать марку документа в имени файла'
            })
            warning_issues += 1
        
        return {
            'score': score,
            'issues': issues,
            'issues_count': len(issues),
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'info_issues': info_issues
        }
    
    def _check_drawing_requirements(self, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка требований к чертежам"""
        score = 0.0
        issues = []
        critical_issues = 0
        warning_issues = 0
        info_issues = 0
        
        pages = doc_analysis.get('pages_analysis', [])
        drawing_pages = [page for page in pages if page['page_type'] == PageType.DRAWING_PAGE]
        
        if not drawing_pages:
            issues.append({
                'type': 'no_drawing_pages',
                'severity': 'critical',
                'description': 'Отсутствуют чертежные страницы',
                'recommendation': 'Добавить чертежи согласно требованиям'
            })
            critical_issues += 1
            return {
                'score': 0.0,
                'issues': issues,
                'issues_count': len(issues),
                'critical_issues': critical_issues,
                'warning_issues': warning_issues,
                'info_issues': info_issues
            }
        
        # Проверка штампов
        pages_with_stamps = sum(1 for page in drawing_pages if page['stamp_info'].has_stamp)
        stamp_percentage = (pages_with_stamps / len(drawing_pages)) * 100
        
        if stamp_percentage >= 90:
            score += 30
        elif stamp_percentage >= 50:
            score += 15
            issues.append({
                'type': 'incomplete_stamps',
                'severity': 'warning',
                'description': f'Штампы присутствуют только на {stamp_percentage:.1f}% страниц',
                'recommendation': 'Добавить штампы на все чертежные страницы'
            })
            warning_issues += 1
        else:
            issues.append({
                'type': 'missing_stamps',
                'severity': 'critical',
                'description': f'Штампы отсутствуют на большинстве страниц ({stamp_percentage:.1f}%)',
                'recommendation': 'Добавить штампы согласно ГОСТ 21.501-2018'
            })
            critical_issues += 1
        
        # Проверка масштабов
        pages_with_scale = sum(1 for page in drawing_pages if page['stamp_info'].scale)
        scale_percentage = (pages_with_scale / len(drawing_pages)) * 100
        
        if scale_percentage >= 90:
            score += 30
        elif scale_percentage >= 50:
            score += 15
            issues.append({
                'type': 'incomplete_scales',
                'severity': 'warning',
                'description': f'Масштабы указаны только на {scale_percentage:.1f}% страниц',
                'recommendation': 'Указать масштаб на всех чертежных страницах'
            })
            warning_issues += 1
        else:
            issues.append({
                'type': 'missing_scales',
                'severity': 'critical',
                'description': f'Масштабы отсутствуют на большинстве страниц ({scale_percentage:.1f}%)',
                'recommendation': 'Указать масштаб согласно ГОСТ 21.501-2018'
            })
            critical_issues += 1
        
        # Проверка размеров
        pages_with_dimensions = sum(1 for page in drawing_pages if page['drawing_elements'])
        dimension_percentage = (pages_with_dimensions / len(drawing_pages)) * 100
        
        if dimension_percentage >= 70:
            score += 25
        elif dimension_percentage >= 30:
            score += 10
            issues.append({
                'type': 'insufficient_dimensions',
                'severity': 'info',
                'description': f'Размеры присутствуют только на {dimension_percentage:.1f}% страниц',
                'recommendation': 'Добавить размеры на чертежи'
            })
            info_issues += 1
        else:
            issues.append({
                'type': 'missing_dimensions',
                'severity': 'warning',
                'description': f'Размеры отсутствуют на большинстве страниц ({dimension_percentage:.1f}%)',
                'recommendation': 'Добавить размеры согласно ГОСТ 21.501-2018'
            })
            warning_issues += 1
        
        # Проверка качества оформления
        avg_confidence = sum(page['confidence_score'] for page in drawing_pages) / len(drawing_pages)
        if avg_confidence >= 0.8:
            score += 15
        elif avg_confidence >= 0.6:
            score += 8
            issues.append({
                'type': 'low_quality',
                'severity': 'info',
                'description': f'Низкое качество оформления (уверенность: {avg_confidence:.1%})',
                'recommendation': 'Улучшить качество оформления чертежей'
            })
            info_issues += 1
        else:
            issues.append({
                'type': 'poor_quality',
                'severity': 'warning',
                'description': f'Плохое качество оформления (уверенность: {avg_confidence:.1%})',
                'recommendation': 'Переоформить чертежи согласно требованиям'
            })
            warning_issues += 1
        
        return {
            'score': score,
            'issues': issues,
            'issues_count': len(issues),
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'info_issues': info_issues
        }
    
    def _check_technical_requirements(self, doc_analysis: Dict[str, Any], mark_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка технических требований"""
        score = 0.0
        issues = []
        critical_issues = 0
        warning_issues = 0
        info_issues = 0
        
        # Проверка соответствия марке
        filename_analysis = doc_analysis.get('filename_analysis', {})
        mark = filename_analysis.get('mark')
        
        if mark and mark in self.ntd_list['marks']:
            score += 40
            required_ntd = self.ntd_list['marks'][mark]['ntd_list']
            issues.append({
                'type': 'ntd_reference',
                'severity': 'info',
                'description': f'Применяемые НТД: {", ".join(required_ntd)}',
                'recommendation': 'Проверить соответствие указанным НТД'
            })
            info_issues += 1
        else:
            issues.append({
                'type': 'unknown_mark',
                'severity': 'warning',
                'description': f'Неизвестная марка документа: {mark}',
                'recommendation': 'Уточнить марку документа'
            })
            warning_issues += 1
        
        # Проверка наличия технических элементов
        pages = doc_analysis.get('pages_analysis', [])
        total_elements = sum(len(page['drawing_elements']) for page in pages)
        
        if total_elements > 0:
            score += 30
        else:
            issues.append({
                'type': 'no_technical_elements',
                'severity': 'warning',
                'description': 'Отсутствуют технические элементы',
                'recommendation': 'Добавить размеры, материалы, маркировки'
            })
            warning_issues += 1
        
        # Проверка соответствия требованиям марки
        if mark_requirements:
            required_sections = mark_requirements.get('requirements', [])
            if required_sections:
                score += 30
                issues.append({
                    'type': 'mark_requirements',
                    'severity': 'info',
                    'description': f'Требуемые разделы для марки {mark}: {", ".join(required_sections)}',
                    'recommendation': 'Проверить наличие всех требуемых разделов'
                })
                info_issues += 1
        
        return {
            'score': score,
            'issues': issues,
            'issues_count': len(issues),
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'info_issues': info_issues
        }
    
    def _check_quality_requirements(self, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка требований качества"""
        score = 0.0
        issues = []
        critical_issues = 0
        warning_issues = 0
        info_issues = 0
        
        # Проверка общего качества
        overall_analysis = doc_analysis.get('overall_analysis', {})
        compliance_score = overall_analysis.get('compliance_score', 0)
        
        if compliance_score >= 90:
            score += 40
        elif compliance_score >= 70:
            score += 25
            issues.append({
                'type': 'moderate_quality',
                'severity': 'info',
                'description': f'Умеренное качество документа (соответствие: {compliance_score:.1f}%)',
                'recommendation': 'Улучшить качество оформления'
            })
            info_issues += 1
        else:
            issues.append({
                'type': 'low_quality',
                'severity': 'warning',
                'description': f'Низкое качество документа (соответствие: {compliance_score:.1f}%)',
                'recommendation': 'Переоформить документ согласно требованиям'
            })
            warning_issues += 1
        
        # Проверка средней уверенности
        avg_confidence = overall_analysis.get('average_confidence', 0)
        
        if avg_confidence >= 0.8:
            score += 30
        elif avg_confidence >= 0.6:
            score += 15
            issues.append({
                'type': 'moderate_confidence',
                'severity': 'info',
                'description': f'Умеренная уверенность анализа ({avg_confidence:.1%})',
                'recommendation': 'Проверить качество исходного документа'
            })
            info_issues += 1
        else:
            issues.append({
                'type': 'low_confidence',
                'severity': 'warning',
                'description': f'Низкая уверенность анализа ({avg_confidence:.1%})',
                'recommendation': 'Улучшить качество исходного документа'
            })
            warning_issues += 1
        
        # Проверка количества проблем
        total_issues = overall_analysis.get('total_issues', 0)
        
        if total_issues == 0:
            score += 30
        elif total_issues <= 5:
            score += 20
            issues.append({
                'type': 'few_issues',
                'severity': 'info',
                'description': f'Найдено {total_issues} проблем',
                'recommendation': 'Исправить найденные проблемы'
            })
            info_issues += 1
        else:
            issues.append({
                'type': 'many_issues',
                'severity': 'warning',
                'description': f'Найдено много проблем: {total_issues}',
                'recommendation': 'Систематически исправить все проблемы'
            })
            warning_issues += 1
        
        return {
            'score': score,
            'issues': issues,
            'issues_count': len(issues),
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'info_issues': info_issues
        }
    
    def _generate_compliance_recommendations(self, compliance: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций по соответствию"""
        recommendations = []
        
        if compliance['critical_issues'] > 0:
            recommendations.append('Устранить критические нарушения немедленно')
        
        if compliance['warning_issues'] > 0:
            recommendations.append('Исправить предупреждения в кратчайшие сроки')
        
        if compliance['overall_score'] < 70:
            recommendations.append('Провести полную переработку документа')
        elif compliance['overall_score'] < 85:
            recommendations.append('Улучшить качество оформления документа')
        
        if compliance['sections']['document_structure']['score'] < 80:
            recommendations.append('Проверить структуру документа')
        
        if compliance['sections']['drawing_requirements']['score'] < 80:
            recommendations.append('Проверить требования к чертежам')
        
        if compliance['sections']['technical_requirements']['score'] < 80:
            recommendations.append('Проверить технические требования')
        
        if compliance['sections']['quality_requirements']['score'] < 80:
            recommendations.append('Повысить качество документа')
        
        return recommendations
    
    def _generate_normcontrol_report(self, doc_analysis: Dict[str, Any], onk_compliance: Dict[str, Any], mark_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация отчета о нормоконтроле"""
        report = {
            'title': 'Отчет о проверке нормоконтролем',
            'document_info': {
                'file_name': doc_analysis['file_name'],
                'file_size_mb': doc_analysis['file_size'] / (1024 * 1024),
                'analysis_time': doc_analysis['analysis_time'],
                'file_hash': doc_analysis['file_hash'][:16]
            },
            'document_analysis': {
                'project_number': doc_analysis['filename_analysis'].get('project_number'),
                'document_type': doc_analysis['filename_analysis']['document_type'].value,
                'mark': doc_analysis['filename_analysis'].get('mark'),
                'revision': doc_analysis['filename_analysis'].get('revision'),
                'total_pages': doc_analysis['overall_analysis']['total_pages'],
                'compliance_score': doc_analysis['overall_analysis']['compliance_score']
            },
            'onk_compliance': {
                'overall_score': onk_compliance['overall_score'],
                'total_issues': onk_compliance['total_issues'],
                'critical_issues': onk_compliance['critical_issues'],
                'warning_issues': onk_compliance['warning_issues'],
                'info_issues': onk_compliance['info_issues']
            },
            'sections_analysis': onk_compliance['sections'],
            'mark_requirements': mark_requirements,
            'recommendations': onk_compliance['recommendations'],
            'status': self._determine_status(onk_compliance),
            'generated_at': time.time()
        }
        
        return report
    
    def _determine_status(self, compliance: Dict[str, Any]) -> str:
        """Определение статуса документа"""
        if compliance['critical_issues'] > 0:
            return 'rejected'
        elif compliance['overall_score'] >= 90:
            return 'approved'
        elif compliance['overall_score'] >= 70:
            return 'approved_with_comments'
        else:
            return 'needs_revision'


def analyze_document_for_normcontrol(file_path: str) -> Dict[str, Any]:
    """Анализ документа для нормоконтроля"""
    analyzer = EnhancedNormControlAnalyzer()
    return analyzer.analyze_document_for_normcontrol(file_path)


def print_normcontrol_analysis_results(result: Dict[str, Any]):
    """Красивый вывод результатов анализа нормоконтроля"""
    if not result['success']:
        print(f"❌ Ошибка анализа: {result.get('error', 'Unknown error')}")
        return
    
    print("=" * 80)
    print("🔍 АНАЛИЗ НОРМОКОНТРОЛЕМ С ИНТЕГРАЦИЕЙ ТРЕБОВАНИЙ ОНК")
    print("=" * 80)
    
    # Информация о документе
    doc_info = result['normcontrol_report']['document_info']
    print(f"📄 Файл: {doc_info['file_name']}")
    print(f"📊 Размер: {doc_info['file_size_mb']:.2f} МБ")
    print(f"⏱️ Время анализа: {doc_info['analysis_time']:.2f} сек")
    print(f"🔑 Хэш: {doc_info['file_hash']}...")
    
    # Анализ документа
    doc_analysis = result['normcontrol_report']['document_analysis']
    print(f"\n📋 АНАЛИЗ ДОКУМЕНТА:")
    print(f"  Проект: {doc_analysis['project_number'] or 'Не определен'}")
    print(f"  Тип: {doc_analysis['document_type']}")
    print(f"  Марка: {doc_analysis['mark'] or 'Не определена'}")
    print(f"  Ревизия: {doc_analysis['revision'] or 'Не определена'}")
    print(f"  Страниц: {doc_analysis['total_pages']}")
    print(f"  Соответствие: {doc_analysis['compliance_score']:.1f}%")
    
    # Соответствие требованиям ОНК
    onk_compliance = result['normcontrol_report']['onk_compliance']
    print(f"\n🏢 СООТВЕТСТВИЕ ТРЕБОВАНИЯМ ОНК:")
    print(f"  Общая оценка: {onk_compliance['overall_score']:.1f}%")
    print(f"  Всего проблем: {onk_compliance['total_issues']}")
    print(f"  Критических: {onk_compliance['critical_issues']}")
    print(f"  Предупреждений: {onk_compliance['warning_issues']}")
    print(f"  Информационных: {onk_compliance['info_issues']}")
    
    # Анализ разделов
    sections = result['normcontrol_report']['sections_analysis']
    print(f"\n📊 АНАЛИЗ РАЗДЕЛОВ:")
    for section_name, section_data in sections.items():
        print(f"  {section_name}: {section_data['score']:.1f}% ({section_data['issues_count']} проблем)")
    
    # Требования марки
    mark_requirements = result['normcontrol_report']['mark_requirements']
    if mark_requirements:
        print(f"\n📋 ТРЕБОВАНИЯ МАРКИ {mark_requirements.get('name', 'Unknown')}:")
        ntd_list = mark_requirements.get('ntd_list', [])
        for ntd in ntd_list:
            print(f"  - {ntd}")
        
        requirements = mark_requirements.get('requirements', [])
        if requirements:
            print(f"  Требуемые разделы:")
            for req in requirements:
                print(f"    - {req}")
    
    # Рекомендации
    recommendations = result['normcontrol_report']['recommendations']
    if recommendations:
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    # Статус
    status = result['normcontrol_report']['status']
    status_emoji = {
        'approved': '✅',
        'approved_with_comments': '⚠️',
        'needs_revision': '❌',
        'rejected': '🚫'
    }
    print(f"\n📋 СТАТУС: {status_emoji.get(status, '❓')} {status.upper()}")


if __name__ == "__main__":
    # Тестирование на конкретном документе
    file_path = "tests/TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf"
    
    print("🚀 Запуск анализа нормоконтролем с интеграцией требований ОНК...")
    
    # Запуск анализа
    result = analyze_document_for_normcontrol(file_path)
    
    # Вывод результатов
    print_normcontrol_analysis_results(result)
    
    # Сохранение результатов
    if result['success']:
        output_file = f"enhanced_normcontrol_analysis_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # Конвертируем Enum в строки для JSON
            def convert_enums(obj):
                if isinstance(obj, dict):
                    return {k: convert_enums(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enums(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    return convert_enums(obj.__dict__)
                else:
                    return obj
            
            json.dump(convert_enums(result), f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в {output_file}")
