import os
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client
import httpx
import openpyxl
from openpyxl.styles import Font, PatternFill
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rule Engine Service", version="1.0.0")

# Конфигурация
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "norms-db")
POSTGRES_DB = os.getenv("POSTGRES_DB", "norms_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "norms_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "norms_password")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8080")

class RuleEngine:
    def __init__(self):
        self.db_conn = None
        self.qdrant_client = None
        self.connect_databases()
        self.load_rules()
    
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
    
    def load_rules(self):
        """Загрузка правил проверки"""
        self.rules = {
            # Правила форматирования
            "formatting": {
                "document_title": {
                    "pattern": r"^[А-ЯЁ][А-ЯЁ\s\-\(\)\d]+$",
                    "description": "Заголовок документа должен начинаться с заглавной буквы",
                    "severity": 3
                },
                "page_numbers": {
                    "pattern": r"^\d+$",
                    "description": "Номера страниц должны быть числовыми",
                    "severity": 2
                },
                "date_format": {
                    "pattern": r"^\d{2}\.\d{2}\.\d{4}$",
                    "description": "Даты должны быть в формате ДД.ММ.ГГГГ",
                    "severity": 4
                }
            },
            
            # Правила содержания
            "content": {
                "required_fields": {
                    "fields": ["title", "date", "author", "approver"],
                    "description": "Документ должен содержать все обязательные поля",
                    "severity": 5
                },
                "text_length": {
                    "min_length": 10,
                    "description": "Текст должен содержать минимум 10 символов",
                    "severity": 2
                }
            },
            
            # Правила соответствия нормам
            "compliance": {
                "gost_references": {
                    "pattern": r"ГОСТ\s+[Р]?\d+\.\d+-\d+",
                    "description": "Ссылки на ГОСТ должны быть в правильном формате",
                    "severity": 4
                },
                "sp_references": {
                    "pattern": r"СП\s+\d+\.\d+\.\d+",
                    "description": "Ссылки на СП должны быть в правильном формате",
                    "severity": 4
                }
            },
            
            # Технические правила
            "technical": {
                "units": {
                    "allowed_units": ["мм", "см", "м", "кг", "т", "л", "м³", "м²", "°C", "Вт", "А", "В"],
                    "description": "Используйте только стандартные единицы измерения",
                    "severity": 3
                },
                "dimensions": {
                    "pattern": r"\d+\s*(мм|см|м|кг|т|л|м³|м²|°C|Вт|А|В)",
                    "description": "Размерности должны содержать единицы измерения",
                    "severity": 3
                }
            }
        }
    
    def check_formatting_rules(self, text: str, element_type: str) -> List[Dict[str, Any]]:
        """Проверка правил форматирования"""
        findings = []
        
        for rule_name, rule in self.rules["formatting"].items():
            if rule_name == "document_title" and element_type == "text":
                # Проверка заголовка документа
                lines = text.split('\n')
                for i, line in enumerate(lines[:3]):  # Проверяем первые 3 строки
                    if line.strip() and not re.match(rule["pattern"], line.strip()):
                        findings.append({
                            "rule": rule_name,
                            "category": "formatting",
                            "severity": rule["severity"],
                            "title": "Неправильный формат заголовка",
                            "description": rule["description"],
                            "location": f"Строка {i+1}: {line.strip()}",
                            "recommendation": "Исправьте формат заголовка согласно требованиям"
                        })
            
            elif rule_name == "date_format":
                # Поиск дат в тексте
                dates = re.findall(r'\d{2}\.\d{2}\.\d{4}', text)
                for date in dates:
                    if not re.match(rule["pattern"], date):
                        findings.append({
                            "rule": rule_name,
                            "category": "formatting",
                            "severity": rule["severity"],
                            "title": "Неправильный формат даты",
                            "description": rule["description"],
                            "location": f"Дата: {date}",
                            "recommendation": "Используйте формат ДД.ММ.ГГГГ"
                        })
        
        return findings
    
    def check_content_rules(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Проверка правил содержания"""
        findings = []
        
        # Проверка обязательных полей
        required_fields = self.rules["content"]["required_fields"]["fields"]
        missing_fields = []
        
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                missing_fields.append(field)
        
        if missing_fields:
            findings.append({
                "rule": "required_fields",
                "category": "content",
                "severity": self.rules["content"]["required_fields"]["severity"],
                "title": "Отсутствуют обязательные поля",
                "description": self.rules["content"]["required_fields"]["description"],
                "location": f"Отсутствуют: {', '.join(missing_fields)}",
                "recommendation": "Добавьте все обязательные поля в документ"
            })
        
        # Проверка длины текста
        if len(text.strip()) < self.rules["content"]["text_length"]["min_length"]:
            findings.append({
                "rule": "text_length",
                "category": "content",
                "severity": self.rules["content"]["text_length"]["severity"],
                "title": "Недостаточная длина текста",
                "description": self.rules["content"]["text_length"]["description"],
                "location": f"Длина: {len(text.strip())} символов",
                "recommendation": "Дополните текст необходимой информацией"
            })
        
        return findings
    
    def check_compliance_rules(self, text: str) -> List[Dict[str, Any]]:
        """Проверка правил соответствия нормам"""
        findings = []
        
        # Проверка ссылок на ГОСТ
        gost_refs = re.findall(r'ГОСТ\s+[Р]?\d+\.\d+-\d+', text)
        for ref in gost_refs:
            if not re.match(self.rules["compliance"]["gost_references"]["pattern"], ref):
                findings.append({
                    "rule": "gost_references",
                    "category": "compliance",
                    "severity": self.rules["compliance"]["gost_references"]["severity"],
                    "title": "Неправильная ссылка на ГОСТ",
                    "description": self.rules["compliance"]["gost_references"]["description"],
                    "location": f"Ссылка: {ref}",
                    "recommendation": "Проверьте правильность ссылки на ГОСТ"
                })
        
        # Проверка ссылок на СП
        sp_refs = re.findall(r'СП\s+\d+\.\d+\.\d+', text)
        for ref in sp_refs:
            if not re.match(self.rules["compliance"]["sp_references"]["pattern"], ref):
                findings.append({
                    "rule": "sp_references",
                    "category": "compliance",
                    "severity": self.rules["compliance"]["sp_references"]["severity"],
                    "title": "Неправильная ссылка на СП",
                    "description": self.rules["compliance"]["sp_references"]["description"],
                    "location": f"Ссылка: {ref}",
                    "recommendation": "Проверьте правильность ссылки на СП"
                })
        
        return findings
    
    def check_technical_rules(self, text: str) -> List[Dict[str, Any]]:
        """Проверка технических правил"""
        findings = []
        
        # Проверка единиц измерения
        allowed_units = self.rules["technical"]["units"]["allowed_units"]
        unit_pattern = r'\b(\d+)\s*([а-яёА-ЯЁ]+)\b'
        units_found = re.findall(unit_pattern, text)
        
        for value, unit in units_found:
            if unit not in allowed_units:
                findings.append({
                    "rule": "units",
                    "category": "technical",
                    "severity": self.rules["technical"]["units"]["severity"],
                    "title": "Недопустимая единица измерения",
                    "description": self.rules["technical"]["units"]["description"],
                    "location": f"Единица: {unit}",
                    "recommendation": f"Используйте стандартные единицы: {', '.join(allowed_units)}"
                })
        
        return findings
    
    async def analyze_document(self, document_id: int, auth_token: str) -> Dict[str, Any]:
        """Полный анализ документа"""
        try:
            # Получение элементов документа
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, element_type, element_content, page_number, confidence_score
                    FROM extracted_elements
                    WHERE uploaded_document_id = %s
                    ORDER BY page_number, id
                """, (document_id,))
                elements = cursor.fetchall()
            
            if not elements:
                raise HTTPException(status_code=404, detail="Document elements not found")
            
            # Применение правил
            all_findings = []
            
            for element in elements:
                text = element["element_content"]
                element_type = element["element_type"]
                
                # Детерминированные проверки
                findings = []
                findings.extend(self.check_formatting_rules(text, element_type))
                findings.extend(self.check_content_rules(text, {}))
                findings.extend(self.check_compliance_rules(text))
                findings.extend(self.check_technical_rules(text))
                
                # Добавление информации о местоположении
                for finding in findings:
                    finding["element_id"] = element["id"]
                    finding["page_number"] = element["page_number"]
                    finding["element_type"] = element_type
                
                all_findings.extend(findings)
            
            # LLM анализ для дополнительных проверок
            llm_findings = await self.llm_analysis(elements, auth_token)
            all_findings.extend(llm_findings)
            
            # Сохранение результатов
            result_id = self.save_analysis_results(document_id, all_findings, auth_token)
            
            return {
                "analysis_id": result_id,
                "total_findings": len(all_findings),
                "critical_findings": len([f for f in all_findings if f["severity"] >= 4]),
                "warning_findings": len([f for f in all_findings if f["severity"] == 3]),
                "info_findings": len([f for f in all_findings if f["severity"] <= 2]),
                "findings": all_findings
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def llm_analysis(self, elements: List[Dict], auth_token: str) -> List[Dict[str, Any]]:
        """LLM анализ для дополнительных проверок"""
        findings = []
        
        try:
            # Объединяем текст всех элементов
            full_text = "\n".join([elem["element_content"] for elem in elements])
            
            # Формируем промпт для LLM
            prompt = f"""Проведите детальный анализ следующего документа на соответствие нормативным требованиям:

Документ:
{full_text}

Проверьте:
1. Соответствие требованиям ГОСТ, СП, ТР ТС
2. Правильность технических решений
3. Полноту информации
4. Логичность изложения
5. Соответствие стандартам оформления

Предоставьте конкретные замечания с указанием:
- Тип проблемы (violation/warning/recommendation/info)
- Уровень важности (1-5, где 5 - критически)
- Категория (formatting/content/compliance/technical)
- Описание проблемы
- Рекомендации по устранению
- Ссылки на нормативные документы

Формат ответа: JSON массив объектов с полями: type, severity, category, title, description, recommendation, norm_reference"""

            # Отправляем запрос к LLM
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{GATEWAY_URL}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={
                        "model": "llama3:8b",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Вы - эксперт по нормоконтролю документов. Анализируйте документы на соответствие нормативным требованиям."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    llm_response = data["choices"][0]["message"]["content"]
                    
                    # Парсим JSON ответ
                    try:
                        llm_findings = json.loads(llm_response)
                        for finding in llm_findings:
                            finding["rule"] = "llm_analysis"
                            finding["element_id"] = None
                            finding["page_number"] = None
                            finding["element_type"] = "llm"
                        findings.extend(llm_findings)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse LLM response as JSON")
                
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
        
        return findings
    
    def save_analysis_results(self, document_id: int, findings: List[Dict], auth_token: str) -> int:
        """Сохранение результатов анализа"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Создание записи результата
                cursor.execute("""
                    INSERT INTO norm_control_results 
                    (uploaded_document_id, analysis_type, model_used, total_findings, 
                     critical_findings, warning_findings, info_findings, analysis_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    document_id,
                    "full",
                    "rule_engine+llama3:8b",
                    len(findings),
                    len([f for f in findings if f["severity"] >= 4]),
                    len([f for f in findings if f["severity"] == 3]),
                    len([f for f in findings if f["severity"] <= 2]),
                    "completed"
                ))
                
                result_id = cursor.fetchone()["id"]
                
                # Сохранение findings
                for finding in findings:
                    cursor.execute("""
                        INSERT INTO findings 
                        (norm_control_result_id, finding_type, severity_level, category, 
                         title, description, recommendation, element_reference, rule_applied)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        result_id,
                        finding.get("type", "violation"),
                        finding.get("severity", 3),
                        finding.get("category", "general"),
                        finding.get("title", ""),
                        finding.get("description", ""),
                        finding.get("recommendation", ""),
                        json.dumps({
                            "element_id": finding.get("element_id"),
                            "page_number": finding.get("page_number"),
                            "element_type": finding.get("element_type")
                        }),
                        finding.get("rule", "unknown")
                    ))
                
                self.db_conn.commit()
                return result_id
                
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Save results error: {e}")
            raise

# Глобальный экземпляр rule engine
rule_engine = RuleEngine()

@app.post("/analyze/{document_id}")
async def analyze_document_endpoint(document_id: int, auth_token: str):
    """Анализ документа"""
    return await rule_engine.analyze_document(document_id, auth_token)

@app.get("/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    try:
        with rule_engine.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Статистика по результатам нормоконтроля
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_results,
                    COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as completed_analyses,
                    COUNT(CASE WHEN analysis_status = 'pending' THEN 1 END) as pending_analyses,
                    COUNT(CASE WHEN analysis_status = 'error' THEN 1 END) as error_analyses,
                    COUNT(CASE WHEN analysis_type = 'full' THEN 1 END) as full_analyses,
                    COUNT(CASE WHEN analysis_type = 'quick' THEN 1 END) as quick_analyses,
                    COUNT(DISTINCT model_used) as unique_models,
                    SUM(total_findings) as total_findings,
                    SUM(critical_findings) as critical_findings,
                    SUM(warning_findings) as warning_findings,
                    SUM(info_findings) as info_findings,
                    AVG(total_findings) as avg_findings_per_analysis,
                    AVG(critical_findings) as avg_critical_per_analysis,
                    AVG(warning_findings) as avg_warning_per_analysis,
                    AVG(info_findings) as avg_info_per_analysis
                FROM norm_control_results
            """)
            analysis_stats = cursor.fetchone()
            
            # Статистика по findings
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_findings,
                    COUNT(CASE WHEN severity_level >= 4 THEN 1 END) as critical_findings,
                    COUNT(CASE WHEN severity_level = 3 THEN 1 END) as warning_findings,
                    COUNT(CASE WHEN severity_level <= 2 THEN 1 END) as info_findings,
                    COUNT(DISTINCT category) as unique_categories,
                    COUNT(DISTINCT rule_applied) as unique_rules,
                    COUNT(DISTINCT finding_type) as unique_finding_types,
                    AVG(severity_level) as avg_severity_level,
                    AVG(confidence_score) as avg_confidence_score
                FROM findings
            """)
            findings_stats = cursor.fetchone()
            
            # Статистика по категориям findings
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    AVG(severity_level) as avg_severity,
                    COUNT(CASE WHEN severity_level >= 4 THEN 1 END) as critical_count
                FROM findings 
                GROUP BY category 
                ORDER BY count DESC
            """)
            category_stats = cursor.fetchall()
            
            # Статистика по правилам
            cursor.execute("""
                SELECT 
                    rule_applied,
                    COUNT(*) as count,
                    AVG(severity_level) as avg_severity,
                    COUNT(CASE WHEN severity_level >= 4 THEN 1 END) as critical_count
                FROM findings 
                WHERE rule_applied IS NOT NULL
                GROUP BY rule_applied 
                ORDER BY count DESC
            """)
            rule_stats = cursor.fetchall()
            
            # Статистика по времени (последние 24 часа)
            cursor.execute("""
                SELECT 
                    COUNT(*) as analyses_last_24h,
                    COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as completed_last_24h,
                    AVG(total_findings) as avg_findings_last_24h
                FROM norm_control_results 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            time_stats = cursor.fetchone()
            
            # Статистика по моделям
            cursor.execute("""
                SELECT 
                    model_used,
                    COUNT(*) as usage_count,
                    AVG(total_findings) as avg_findings,
                    AVG(critical_findings) as avg_critical
                FROM norm_control_results 
                WHERE model_used IS NOT NULL
                GROUP BY model_used 
                ORDER BY usage_count DESC
            """)
            model_stats = cursor.fetchall()
            
        # Формируем метрики в формате Prometheus
        metrics_lines = []
        
        # Метрики анализа
        metrics_lines.append(f"# HELP rule_engine_analysis_total Total number of analyses")
        metrics_lines.append(f"# TYPE rule_engine_analysis_total counter")
        metrics_lines.append(f"rule_engine_analysis_total {analysis_stats['total_results'] or 0}")
        
        metrics_lines.append(f"# HELP rule_engine_analysis_completed Completed analyses")
        metrics_lines.append(f"# TYPE rule_engine_analysis_completed counter")
        metrics_lines.append(f"rule_engine_analysis_completed {analysis_stats['completed_analyses'] or 0}")
        
        metrics_lines.append(f"# HELP rule_engine_analysis_pending Pending analyses")
        metrics_lines.append(f"# TYPE rule_engine_analysis_pending counter")
        metrics_lines.append(f"rule_engine_analysis_pending {analysis_stats['pending_analyses'] or 0}")
        
        metrics_lines.append(f"# HELP rule_engine_analysis_error Error analyses")
        metrics_lines.append(f"# TYPE rule_engine_analysis_error counter")
        metrics_lines.append(f"rule_engine_analysis_error {analysis_stats['error_analyses'] or 0}")
        
        # Метрики по типам анализа
        metrics_lines.append(f"# HELP rule_engine_analysis_by_type Analyses by type")
        metrics_lines.append(f"# TYPE rule_engine_analysis_by_type counter")
        metrics_lines.append(f'rule_engine_analysis_by_type{{type="full"}} {analysis_stats["full_analyses"] or 0}')
        metrics_lines.append(f'rule_engine_analysis_by_type{{type="quick"}} {analysis_stats["quick_analyses"] or 0}')
        
        # Метрики findings
        metrics_lines.append(f"# HELP rule_engine_findings_total Total findings")
        metrics_lines.append(f"# TYPE rule_engine_findings_total counter")
        metrics_lines.append(f"rule_engine_findings_total {findings_stats['total_findings'] or 0}")
        
        metrics_lines.append(f"# HELP rule_engine_findings_critical Critical findings")
        metrics_lines.append(f"# TYPE rule_engine_findings_critical counter")
        metrics_lines.append(f"rule_engine_findings_critical {findings_stats['critical_findings'] or 0}")
        
        metrics_lines.append(f"# HELP rule_engine_findings_warning Warning findings")
        metrics_lines.append(f"# TYPE rule_engine_findings_warning counter")
        metrics_lines.append(f"rule_engine_findings_warning {findings_stats['warning_findings'] or 0}")
        
        metrics_lines.append(f"# HELP rule_engine_findings_info Info findings")
        metrics_lines.append(f"# TYPE rule_engine_findings_info counter")
        metrics_lines.append(f"rule_engine_findings_info {findings_stats['info_findings'] or 0}")
        
        # Метрики по категориям
        for cat in category_stats:
            metrics_lines.append(f'rule_engine_findings_by_category{{category="{cat["category"]}"}} {cat["count"]}')
        
        # Метрики по правилам
        for rule in rule_stats:
            metrics_lines.append(f'rule_engine_findings_by_rule{{rule="{rule["rule_applied"]}"}} {rule["count"]}')
        
        # Метрики по моделям
        for model in model_stats:
            metrics_lines.append(f'rule_engine_model_usage{{model="{model["model_used"]}"}} {model["usage_count"]}')
        
        # Метрики производительности
        metrics_lines.append(f"# HELP rule_engine_analyses_last_24h Analyses in last 24 hours")
        metrics_lines.append(f"# TYPE rule_engine_analyses_last_24h counter")
        metrics_lines.append(f"rule_engine_analyses_last_24h {time_stats['analyses_last_24h'] or 0}")
        
        # Возвращаем метрики в формате Prometheus
        from fastapi.responses import Response
        return Response(
            content="\n".join(metrics_lines),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверка PostgreSQL
        with rule_engine.db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Проверка Qdrant
        rule_engine.qdrant_client.get_collections()
        
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
