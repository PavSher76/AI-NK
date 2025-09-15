"""
Примеры использования API сервиса архива технической документации
"""

import requests
import json
import os
from typing import List, Dict, Any

class ArchiveServiceClient:
    """Клиент для работы с API сервиса архива"""
    
    def __init__(self, base_url: str = "http://localhost:8008"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_single_document(self, file_path: str, project_code: str, 
                             document_type: str = "OTHER", **kwargs) -> Dict[str, Any]:
        """Загрузка одного документа"""
        url = f"{self.base_url}/api/archive/upload/single"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'project_code': project_code,
                'document_type': document_type,
                **kwargs
            }
            
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
    
    def upload_batch_documents(self, project_code: str, documents: List[Dict[str, Any]], 
                             **options) -> Dict[str, Any]:
        """Пакетная загрузка документов"""
        url = f"{self.base_url}/api/archive/upload/batch"
        
        payload = {
            'project_code': project_code,
            'documents': documents,
            **options
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_project_documents(self, project_code: str) -> Dict[str, Any]:
        """Получение документов проекта"""
        url = f"{self.base_url}/api/archive/projects/{project_code}/documents"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_project_stats(self, project_code: str) -> Dict[str, Any]:
        """Получение статистики проекта"""
        url = f"{self.base_url}/api/archive/projects/{project_code}/stats"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def search_documents(self, query: str, project_code: str = None, 
                        document_type: str = None, limit: int = 10) -> Dict[str, Any]:
        """Поиск документов"""
        url = f"{self.base_url}/api/archive/search"
        
        payload = {
            'search_query': query,
            'limit': limit
        }
        
        if project_code:
            payload['project_code'] = project_code
        if document_type:
            payload['document_type'] = document_type
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_similar_sections(self, query: str, project_code: str = None, 
                               limit: int = 10, score_threshold: float = 0.7) -> Dict[str, Any]:
        """Поиск похожих разделов"""
        url = f"{self.base_url}/api/archive/search/similar"
        
        payload = {
            'query': query,
            'limit': limit,
            'score_threshold': score_threshold
        }
        
        if project_code:
            payload['project_code'] = project_code
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def merge_project_documents(self, project_code: str, output_format: str = "pdf") -> Dict[str, Any]:
        """Объединение документов проекта"""
        url = f"{self.base_url}/api/archive/projects/{project_code}/merge"
        
        payload = {
            'output_format': output_format,
            'include_sections': True
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_upload_progress(self, project_code: str) -> Dict[str, Any]:
        """Получение прогресса загрузки"""
        url = f"{self.base_url}/api/archive/projects/{project_code}/progress"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def cancel_upload(self, project_code: str) -> Dict[str, Any]:
        """Отмена загрузки"""
        url = f"{self.base_url}/api/archive/projects/{project_code}/cancel"
        
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        url = f"{self.base_url}/api/archive/health"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

def example_usage():
    """Примеры использования клиента"""
    
    # Создаем клиент
    client = ArchiveServiceClient()
    
    print("🔍 Проверка здоровья сервиса...")
    health = client.health_check()
    print(f"Статус: {health['status']}")
    
    # Пример 1: Загрузка одного документа
    print("\n📤 Загрузка одного документа...")
    try:
        result = client.upload_single_document(
            file_path="example_document.pdf",
            project_code="ПР-2024-001",
            document_type="PD",
            document_name="Проектная документация",
            author="Иванов И.И.",
            department="Проектный отдел"
        )
        print(f"Результат загрузки: {result['status']}")
        print(f"ID документа: {result['document_id']}")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
    
    # Пример 2: Пакетная загрузка
    print("\n📦 Пакетная загрузка документов...")
    try:
        documents = [
            {
                "file_path": "/path/to/pd_document.pdf",
                "document_type": "PD",
                "document_name": "Проектная документация",
                "author": "Иванов И.И."
            },
            {
                "file_path": "/path/to/rd_document.pdf", 
                "document_type": "RD",
                "document_name": "Рабочая документация",
                "author": "Петров П.П."
            },
            {
                "file_path": "/path/to/teo_document.pdf",
                "document_type": "TEO", 
                "document_name": "Технико-экономическое обоснование",
                "author": "Сидоров С.С."
            }
        ]
        
        result = client.upload_batch_documents(
            project_code="ПР-2024-001",
            documents=documents,
            auto_extract_sections=True,
            create_relations=True
        )
        print(f"Результат пакетной загрузки: {result['status']}")
        print(f"Обработано документов: {result['processed_documents']}")
        print(f"Ошибок: {result['failed_documents']}")
    except Exception as e:
        print(f"Ошибка пакетной загрузки: {e}")
    
    # Пример 3: Получение документов проекта
    print("\n📋 Получение документов проекта...")
    try:
        documents = client.get_project_documents("ПР-2024-001")
        print(f"Найдено документов: {documents['total_count']}")
        for doc in documents['documents']:
            print(f"- {doc['document_name']} ({doc['document_type']})")
    except Exception as e:
        print(f"Ошибка получения документов: {e}")
    
    # Пример 4: Статистика проекта
    print("\n📊 Статистика проекта...")
    try:
        stats = client.get_project_stats("ПР-2024-001")
        print(f"Проект: {stats['project_name']}")
        print(f"Всего документов: {stats['total_documents']}")
        print(f"Документов по типам: {stats['documents_by_type']}")
        print(f"Общий размер: {stats['total_size']} байт")
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
    
    # Пример 5: Поиск документов
    print("\n🔍 Поиск документов...")
    try:
        results = client.search_documents(
            query="требования безопасности",
            project_code="ПР-2024-001",
            limit=5
        )
        print(f"Найдено документов: {results['total_count']}")
        for doc in results['documents']:
            print(f"- {doc['document_name']} (релевантность: {doc.get('score', 'N/A')})")
    except Exception as e:
        print(f"Ошибка поиска: {e}")
    
    # Пример 6: Поиск похожих разделов
    print("\n🔍 Поиск похожих разделов...")
    try:
        results = client.search_similar_sections(
            query="требования к материалам",
            project_code="ПР-2024-001",
            limit=3
        )
        print(f"Найдено разделов: {results['total_found']}")
        for result in results['results']:
            print(f"- {result['section_title']} (схожесть: {result['score']:.2f})")
    except Exception as e:
        print(f"Ошибка поиска разделов: {e}")
    
    # Пример 7: Объединение документов
    print("\n📄 Объединение документов...")
    try:
        result = client.merge_project_documents(
            project_code="ПР-2024-001",
            output_format="pdf"
        )
        print(f"Результат объединения: {result['status']}")
        print(f"Путь к файлу: {result['output_path']}")
    except Exception as e:
        print(f"Ошибка объединения: {e}")

def create_test_documents():
    """Создание тестовых документов для демонстрации"""
    
    # Создаем тестовую директорию
    os.makedirs("test_documents", exist_ok=True)
    
    # Создаем простой PDF документ
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    
    def create_test_pdf(filename: str, title: str, content: str):
        c = canvas.Canvas(f"test_documents/{filename}", pagesize=A4)
        width, height = A4
        
        # Заголовок
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, title)
        
        # Содержимое
        c.setFont("Helvetica", 12)
        y = height - 150
        for line in content.split('\n'):
            c.drawString(100, y, line)
            y -= 20
        
        c.save()
    
    # Создаем тестовые документы
    create_test_pdf(
        "pd_document.pdf",
        "Проектная документация ПР-2024-001",
        """1. Общие положения
1.1. Настоящий документ определяет требования к проектированию
1.2. Документ разработан в соответствии с ГОСТ 21.101-97

2. Технические требования
2.1. Материалы должны соответствовать требованиям безопасности
2.2. Конструкции должны быть рассчитаны на нагрузки согласно СНиП

3. Требования безопасности
3.1. Все элементы должны иметь защиту от коррозии
3.2. Электробезопасность должна соответствовать ПУЭ"""
    )
    
    create_test_pdf(
        "rd_document.pdf", 
        "Рабочая документация ПР-2024-001",
        """1. Рабочие чертежи
1.1. Планы этажей
1.2. Разрезы и фасады
1.3. Детали узлов

2. Спецификации
2.1. Спецификация материалов
2.2. Спецификация оборудования
2.3. Ведомость объемов работ

3. Технические решения
3.1. Конструктивные решения
3.2. Инженерные системы
3.3. Отделочные работы"""
    )
    
    create_test_pdf(
        "teo_document.pdf",
        "ТЭО проекта ПР-2024-001", 
        """1. Экономическое обоснование
1.1. Анализ рынка
1.2. Финансовые показатели
1.3. Сроки окупаемости

2. Техническое обоснование
2.1. Выбор технологий
2.2. Оценка рисков
2.3. Ресурсное обеспечение

3. Социально-экономические аспекты
3.1. Влияние на окружающую среду
3.2. Социальные эффекты
3.3. Региональное развитие"""
    )
    
    print("✅ Тестовые документы созданы в директории test_documents/")

if __name__ == "__main__":
    print("🚀 Примеры использования API сервиса архива")
    print("=" * 50)
    
    # Создаем тестовые документы
    create_test_documents()
    
    # Запускаем примеры
    example_usage()
    
    print("\n✅ Примеры завершены")
