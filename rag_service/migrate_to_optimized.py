"""
Скрипт миграции существующих данных в оптимизированную структуру RAG базы
"""

import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://norms_user:norms_password@norms-db:5432/norms_db")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

class OptimizedMigrationService:
    """Сервис миграции в оптимизированную структуру"""
    
    def __init__(self):
        self.db_conn = None
        self.qdrant_client = None
        self.connect_services()
    
    def connect_services(self):
        """Подключение к сервисам"""
        try:
            # PostgreSQL
            self.db_conn = psycopg2.connect(POSTGRES_URL)
            logger.info("✅ Connected to PostgreSQL")
            
            # Qdrant
            self.qdrant_client = qdrant_client.QdrantClient(url=QDRANT_URL)
            logger.info("✅ Connected to Qdrant")
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            raise
    
    def migrate_existing_documents(self):
        """Миграция существующих документов в оптимизированную структуру"""
        logger.info("🚀 Starting migration to optimized structure...")
        
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Получаем все существующие нормативные документы
                cursor.execute("""
                    SELECT 
                        nd.id,
                        nd.document_type,
                        nd.document_number,
                        nd.document_name,
                        nd.version,
                        nd.publication_date,
                        nd.effective_date,
                        nd.status
                    FROM normative_documents nd
                    ORDER BY nd.id
                """)
                
                documents = cursor.fetchall()
                logger.info(f"📄 Found {len(documents)} documents to migrate")
                
                for doc in documents:
                    logger.info(f"📄 Migrating document: {doc['document_number']} - {doc['document_name']}")
                    
                    # Получаем все пункты документа
                    cursor.execute("""
                        SELECT 
                            dc.id,
                            dc.clause_id,
                            dc.clause_number,
                            dc.section_title,
                            dc.clause_title,
                            dc.clause_text,
                            dc.clause_type,
                            dc.importance_level,
                            dc.page_number
                        FROM document_clauses dc
                        WHERE dc.document_id = %s
                        ORDER BY dc.clause_number
                    """, (doc['id'],))
                    
                    clauses = cursor.fetchall()
                    logger.info(f"📝 Found {len(clauses)} clauses for document {doc['document_number']}")
                    
                    # Мигрируем каждый пункт
                    for clause in clauses:
                        self.migrate_clause_to_optimized(doc, clause)
                
                logger.info("✅ Migration completed successfully")
                
        except Exception as e:
            logger.error(f"❌ Migration error: {e}")
            self.db_conn.rollback()
            raise
    
    def migrate_clause_to_optimized(self, document: Dict[str, Any], clause: Dict[str, Any]):
        """Миграция отдельного пункта в оптимизированную структуру"""
        try:
            # Создаем унифицированную структуру
            unified_structure = self.create_unified_structure(document, clause)
            
            # Определяем теги контента
            content_tags = self.detect_content_tags(clause['clause_text'])
            
            # Создаем семантические чанки
            semantic_chunks = self.create_semantic_chunks(clause['clause_text'], clause['clause_id'])
            
            # Сохраняем в оптимизированную структуру
            self.save_optimized_structure(unified_structure, semantic_chunks, content_tags)
            
            logger.debug(f"✅ Migrated clause: {clause['clause_id']}")
            
        except Exception as e:
            logger.error(f"❌ Error migrating clause {clause['clause_id']}: {e}")
            raise
    
    def create_unified_structure(self, document: Dict[str, Any], clause: Dict[str, Any]) -> Dict[str, Any]:
        """Создание унифицированной структуры"""
        return {
            'clause_id': clause['clause_id'],
            'section_title': clause['section_title'] or '',
            'full_text': clause['clause_text'],
            'document_type': document['document_type'],
            'document_number': document['document_number'],
            'clause_number': clause['clause_number'],
            'importance_level': clause['importance_level'] or 1,
            'metadata': {
                'original_document_id': document['id'],
                'original_clause_id': clause['id'],
                'page_number': clause['page_number'],
                'clause_type': clause['clause_type'],
                'migrated_at': datetime.now().isoformat()
            }
        }
    
    def detect_content_tags(self, text: str) -> List[str]:
        """Определение тегов контента"""
        tags = []
        text_lower = text.lower()
        
        # Анализ по ключевым словам
        if any(word in text_lower for word in ['подпись', 'подписан', 'утвержден', 'согласован']):
            tags.append('подписи')
        
        if any(word in text_lower for word in ['оформление', 'формат', 'шрифт', 'размер']):
            tags.append('оформление')
        
        if any(word in text_lower for word in ['структура', 'состав', 'раздел', 'глава']):
            tags.append('структура')
        
        if any(word in text_lower for word in ['таблица', 'табл.', 'таб.']):
            tags.append('таблицы')
        
        if any(word in text_lower for word in ['рисунок', 'рис.', 'чертеж', 'схема']):
            tags.append('графика')
        
        if any(word in text_lower for word in ['расчет', 'вычисление', 'формула']):
            tags.append('расчеты')
        
        if any(word in text_lower for word in ['должен', 'обязательно', 'необходимо', 'требуется']):
            tags.append('требования')
        
        if any(word in text_lower for word in ['рекомендуется', 'следует', 'желательно']):
            tags.append('рекомендации')
        
        if any(word in text_lower for word in ['например', 'пример', 'образец']):
            tags.append('примеры')
        
        if any(word in text_lower for word in ['примечание', 'прим.', 'замечание']):
            tags.append('примечания')
        
        # По умолчанию добавляем тег "текст"
        if not tags:
            tags.append('текст')
        
        return tags
    
    def create_semantic_chunks(self, text: str, clause_id: str) -> List[Dict[str, Any]]:
        """Создание семантических чанков"""
        chunks = []
        
        # Разбиваем на абзацы
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            # Определяем тип контента
            chunk_type = self.detect_chunk_type(paragraph)
            
            # Создаем чанк
            chunk = {
                'chunk_id': f"{clause_id}_chunk_{i}",
                'clause_id': clause_id,
                'content': paragraph,
                'chunk_type': chunk_type,
                'semantic_context': f"clause_id: {clause_id}, paragraph: {i+1}/{len(paragraphs)}",
                'metadata': {
                    'paragraph_index': i,
                    'total_paragraphs': len(paragraphs),
                    'token_count': len(paragraph.split()),
                    'created_at': datetime.now().isoformat()
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def detect_chunk_type(self, text: str) -> str:
        """Определение типа чанка"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['должен', 'обязательно', 'необходимо', 'требуется']):
            return "requirement"
        
        if any(word in text_lower for word in ['рекомендуется', 'следует', 'желательно']):
            return "recommendation"
        
        if any(word in text_lower for word in ['например', 'пример', 'образец']):
            return "example"
        
        if any(word in text_lower for word in ['примечание', 'прим.', 'замечание']):
            return "note"
        
        return "text"
    
    def save_optimized_structure(self, unified_structure: Dict[str, Any], 
                               semantic_chunks: List[Dict[str, Any]], 
                               content_tags: List[str]):
        """Сохранение оптимизированной структуры"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Сохраняем основную структуру
                cursor.execute("""
                    INSERT INTO document_clauses 
                    (clause_id, clause_number, section_title, clause_text, clause_type, importance_level, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (clause_id) DO UPDATE SET
                    clause_text = EXCLUDED.clause_text,
                    importance_level = EXCLUDED.importance_level,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
                """, (
                    unified_structure['clause_id'],
                    unified_structure['clause_number'],
                    unified_structure['section_title'],
                    unified_structure['full_text'],
                    'requirement',  # По умолчанию
                    unified_structure['importance_level'],
                    json.dumps(unified_structure['metadata'])
                ))
                
                # Сохраняем атрибуты (теги)
                for tag in content_tags:
                    cursor.execute("""
                        INSERT INTO clause_attributes 
                        (clause_id, attribute_name, attribute_value, attribute_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        unified_structure['clause_id'],
                        'tag',
                        tag,
                        'text'
                    ))
                
                # Сохраняем информацию о чанках
                for chunk in semantic_chunks:
                    cursor.execute("""
                        INSERT INTO normative_chunks 
                        (chunk_id, clause_id, content, chunk_type, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        chunk_type = EXCLUDED.chunk_type,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """, (
                        chunk['chunk_id'],
                        chunk['clause_id'],
                        chunk['content'],
                        chunk['chunk_type'],
                        json.dumps(chunk['metadata'])
                    ))
                
                self.db_conn.commit()
                logger.debug(f"✅ Saved optimized structure for clause: {unified_structure['clause_id']}")
                
        except Exception as e:
            logger.error(f"❌ Error saving optimized structure: {e}")
            self.db_conn.rollback()
            raise
    
    def create_optimized_tables(self):
        """Создание дополнительных таблиц для оптимизированной структуры"""
        logger.info("🔧 Creating optimized tables...")
        
        try:
            with self.db_conn.cursor() as cursor:
                # Таблица для чанков
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS normative_chunks (
                        id SERIAL PRIMARY KEY,
                        chunk_id VARCHAR(255) UNIQUE NOT NULL,
                        clause_id VARCHAR(100) NOT NULL,
                        content TEXT NOT NULL,
                        chunk_type VARCHAR(50),
                        semantic_context TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Индексы для быстрого поиска
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_normative_chunks_clause_id 
                    ON normative_chunks(clause_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_normative_chunks_chunk_type 
                    ON normative_chunks(chunk_type)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_normative_chunks_metadata 
                    ON normative_chunks USING GIN(metadata)
                """)
                
                # Таблица для метаданных документов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_metadata (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES normative_documents(id),
                        document_mark VARCHAR(50),
                        document_stage VARCHAR(50),
                        content_tags TEXT[],
                        processing_status VARCHAR(50) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.db_conn.commit()
                logger.info("✅ Optimized tables created successfully")
                
        except Exception as e:
            logger.error(f"❌ Error creating optimized tables: {e}")
            self.db_conn.rollback()
            raise
    
    def get_migration_statistics(self) -> Dict[str, Any]:
        """Получение статистики миграции"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Статистика документов
                cursor.execute("SELECT COUNT(*) as total_documents FROM normative_documents")
                total_documents = cursor.fetchone()['total_documents']
                
                # Статистика пунктов
                cursor.execute("SELECT COUNT(*) as total_clauses FROM document_clauses")
                total_clauses = cursor.fetchone()['total_clauses']
                
                # Статистика чанков
                cursor.execute("SELECT COUNT(*) as total_chunks FROM normative_chunks")
                total_chunks = cursor.fetchone()['total_chunks']
                
                # Статистика атрибутов
                cursor.execute("SELECT COUNT(*) as total_attributes FROM clause_attributes")
                total_attributes = cursor.fetchone()['total_attributes']
                
                # Статистика по типам документов
                cursor.execute("""
                    SELECT document_type, COUNT(*) as count 
                    FROM normative_documents 
                    GROUP BY document_type
                """)
                document_types = cursor.fetchall()
                
                return {
                    'total_documents': total_documents,
                    'total_clauses': total_clauses,
                    'total_chunks': total_chunks,
                    'total_attributes': total_attributes,
                    'document_types': {row['document_type']: row['count'] for row in document_types},
                    'migration_status': 'completed',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting migration statistics: {e}")
            return {'error': str(e)}

def main():
    """Основная функция миграции"""
    logger.info("🚀 Starting RAG Base optimization migration...")
    
    try:
        migration_service = OptimizedMigrationService()
        
        # Создаем оптимизированные таблицы
        migration_service.create_optimized_tables()
        
        # Мигрируем существующие документы
        migration_service.migrate_existing_documents()
        
        # Получаем статистику
        stats = migration_service.get_migration_statistics()
        logger.info(f"📊 Migration statistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()
