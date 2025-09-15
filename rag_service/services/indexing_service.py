import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import threading
from queue import Queue, Empty

from .database_manager import DatabaseManager
from .qdrant_service import QdrantService
from .ollama_rag_service import OllamaEmbeddingService

# Настройка логирования
logger = logging.getLogger(__name__)

class IndexingStatus(Enum):
    """Статусы индексации"""
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class IndexingTask:
    """Задача индексации"""
    document_id: int
    filename: str
    content: bytes
    category: str
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # 0 = normal, 1 = high, -1 = low
    created_at: datetime = None
    last_attempt: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_attempt is None:
            self.last_attempt = datetime.now()

class ResilientIndexingService:
    """Сервис устойчивой индексации с поддержкой повторных попыток и восстановления"""
    
    def __init__(self, db_manager: DatabaseManager, qdrant_service: QdrantService, 
                 embedding_service: OllamaEmbeddingService, max_concurrent_tasks: int = 3):
        self.db_manager = db_manager
        self.qdrant_service = qdrant_service
        self.embedding_service = embedding_service
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Очередь задач
        self.task_queue = Queue()
        self.active_tasks: Dict[int, IndexingTask] = {}
        self.failed_tasks: List[IndexingTask] = []
        
        # Управление потоками
        self.worker_threads: List[threading.Thread] = []
        self.shutdown_event = threading.Event()
        self.is_running = False
        
        # Статистика
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'retries': 0,
            'start_time': None
        }
        
        logger.info(f"🚀 [INDEXING_SERVICE] ResilientIndexingService initialized with {max_concurrent_tasks} workers")
    
    def start(self):
        """Запуск сервиса индексации"""
        if self.is_running:
            logger.warning("⚠️ [INDEXING_SERVICE] Service is already running")
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        self.stats['start_time'] = datetime.now()
        
        # Запускаем worker потоки
        for i in range(self.max_concurrent_tasks):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"IndexingWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        # Запускаем мониторинг
        monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="IndexingMonitor",
            daemon=True
        )
        monitor_thread.start()
        
        logger.info(f"✅ [INDEXING_SERVICE] Service started with {len(self.worker_threads)} workers")
    
    def stop(self):
        """Остановка сервиса индексации"""
        if not self.is_running:
            logger.warning("⚠️ [INDEXING_SERVICE] Service is not running")
            return
        
        logger.info("🛑 [INDEXING_SERVICE] Stopping service...")
        self.is_running = False
        self.shutdown_event.set()
        
        # Ждем завершения активных задач
        timeout = 30  # секунд
        start_time = time.time()
        
        while self.active_tasks and (time.time() - start_time) < timeout:
            logger.info(f"⏳ [INDEXING_SERVICE] Waiting for {len(self.active_tasks)} active tasks to complete...")
            time.sleep(1)
        
        if self.active_tasks:
            logger.warning(f"⚠️ [INDEXING_SERVICE] {len(self.active_tasks)} tasks still active after timeout")
        
        logger.info("✅ [INDEXING_SERVICE] Service stopped")
    
    def add_indexing_task(self, document_id: int, filename: str, content: bytes, 
                         category: str, priority: int = 0, max_retries: int = 3):
        """Добавление задачи индексации в очередь"""
        task = IndexingTask(
            document_id=document_id,
            filename=filename,
            content=content,
            category=category,
            priority=priority,
            max_retries=max_retries
        )
        
        self.task_queue.put(task)
        logger.info(f"📝 [INDEXING_SERVICE] Added indexing task for document {document_id} (priority: {priority})")
    
    def _worker_loop(self):
        """Основной цикл worker потока"""
        worker_name = threading.current_thread().name
        logger.info(f"🔄 [INDEXING_SERVICE] {worker_name} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Получаем задачу из очереди с таймаутом
                try:
                    task = self.task_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Обрабатываем задачу
                self._process_indexing_task(task)
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ [INDEXING_SERVICE] {worker_name} error: {e}")
                time.sleep(1)
        
        logger.info(f"✅ [INDEXING_SERVICE] {worker_name} stopped")
    
    def _process_indexing_task(self, task: IndexingTask):
        """Обработка задачи индексации с повторными попытками"""
        document_id = task.document_id
        worker_name = threading.current_thread().name
        
        try:
            logger.info(f"🔄 [INDEXING_SERVICE] {worker_name} processing document {document_id} (attempt {task.retry_count + 1})")
            
            # Добавляем в активные задачи
            self.active_tasks[document_id] = task
            
            # Обновляем статус в БД
            self.db_manager.update_document_status(document_id, IndexingStatus.INDEXING.value)
            self.db_manager.update_indexing_progress(document_id, 10, "Starting indexing...")
            
            # Извлекаем текст из документа
            self.db_manager.update_indexing_progress(document_id, 20, "Extracting text...")
            text_content = self._extract_text_from_document(task.content, task.filename)
            
            if not text_content:
                raise Exception("Failed to extract text from document")
            
            # Создаем чанки
            self.db_manager.update_indexing_progress(document_id, 40, "Creating chunks...")
            chunks = self._create_chunks(text_content, document_id, task.filename)
            
            if not chunks:
                raise Exception("Failed to create chunks")
            
            # Создаем эмбеддинги и индексируем
            self.db_manager.update_indexing_progress(document_id, 60, "Creating embeddings...")
            success = self._index_chunks(chunks, document_id)
            
            if not success:
                raise Exception("Failed to index chunks")
            
            # Обновляем количество токенов
            self.db_manager.update_indexing_progress(document_id, 90, "Updating token count...")
            token_count = len(text_content.split())
            self.db_manager.execute_write_query("""
                UPDATE uploaded_documents 
                SET token_count = %s
                WHERE id = %s
            """, (token_count, document_id))
            
            # Завершаем успешно
            self.db_manager.update_document_status(document_id, IndexingStatus.COMPLETED.value)
            self.db_manager.update_indexing_progress(document_id, 100, "Indexing completed successfully")
            
            self.stats['successful'] += 1
            logger.info(f"✅ [INDEXING_SERVICE] {worker_name} completed document {document_id}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ [INDEXING_SERVICE] {worker_name} failed document {document_id}: {error_msg}")
            
            # Проверяем, нужно ли повторить попытку
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.last_attempt = datetime.now()
                
                # Добавляем обратно в очередь с задержкой
                retry_delay = min(2 ** task.retry_count, 60)  # Экспоненциальная задержка
                logger.info(f"🔄 [INDEXING_SERVICE] Retrying document {document_id} in {retry_delay} seconds (attempt {task.retry_count + 1})")
                
                # Помечаем для повторной попытки в БД
                self.db_manager.mark_document_for_retry(document_id, error_msg)
                
                # Добавляем в очередь с задержкой
                threading.Timer(retry_delay, lambda: self.task_queue.put(task)).start()
                
                self.stats['retries'] += 1
            else:
                # Максимальное количество попыток исчерпано
                self.db_manager.update_document_status(document_id, IndexingStatus.FAILED.value, error_msg)
                self.failed_tasks.append(task)
                self.stats['failed'] += 1
                
                logger.error(f"❌ [INDEXING_SERVICE] Document {document_id} failed after {task.max_retries} retries")
        
        finally:
            # Убираем из активных задач
            self.active_tasks.pop(document_id, None)
            self.stats['total_processed'] += 1
    
    def _extract_text_from_document(self, content: bytes, filename: str) -> str:
        """Извлечение текста из документа"""
        try:
            # Импортируем парсер документов
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            from utils import parse_document_from_bytes
            
            # Извлекаем текст
            text_content = parse_document_from_bytes(content, filename)
            return text_content
            
        except Exception as e:
            logger.error(f"❌ [INDEXING_SERVICE] Error extracting text from {filename}: {e}")
            raise
    
    def _create_chunks(self, text_content: str, document_id: int, filename: str) -> List[Dict[str, Any]]:
        """Создание чанков из текста"""
        try:
            # Импортируем чанкер
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            from utils import create_chunks
            
            # Создаем чанки
            chunks = create_chunks(text_content, document_id, filename)
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [INDEXING_SERVICE] Error creating chunks for document {document_id}: {e}")
            raise
    
    def _index_chunks(self, chunks: List[Dict[str, Any]], document_id: int) -> bool:
        """Индексация чанков в Qdrant"""
        try:
            points = []
            
            for chunk in chunks:
                # Создаем эмбеддинг
                content = chunk.get('content', '')
                if not content.strip():
                    continue
                
                embedding = self.embedding_service.create_embedding(content)
                
                # Создаем точку для Qdrant
                point = {
                    'id': chunk.get('id'),
                    'vector': embedding,
                    'payload': {
                        'document_id': document_id,
                        'title': chunk.get('document_title', ''),
                        'section_title': chunk.get('section_title', ''),
                        'content': content,
                        'chunk_type': chunk.get('chunk_type', 'paragraph'),
                        'page': chunk.get('page', 1),
                        'section': chunk.get('section', ''),
                        'metadata': chunk.get('metadata', {})
                    }
                }
                points.append(point)
            
            # Добавляем точки в Qdrant
            if points:
                self.qdrant_service.upsert_points(points)
                logger.info(f"✅ [INDEXING_SERVICE] Indexed {len(points)} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"⚠️ [INDEXING_SERVICE] No points to index for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [INDEXING_SERVICE] Error indexing chunks for document {document_id}: {e}")
            raise
    
    def _monitor_loop(self):
        """Мониторинг состояния сервиса"""
        logger.info("📊 [INDEXING_SERVICE] Monitor started")
        
        while not self.shutdown_event.is_set():
            try:
                # Проверяем состояние каждые 30 секунд
                time.sleep(30)
                
                # Логируем статистику
                self._log_statistics()
                
                # Проверяем зависшие задачи
                self._check_stuck_tasks()
                
                # Восстанавливаем задачи из БД при необходимости
                self._recover_pending_tasks()
                
            except Exception as e:
                logger.error(f"❌ [INDEXING_SERVICE] Monitor error: {e}")
        
        logger.info("✅ [INDEXING_SERVICE] Monitor stopped")
    
    def _log_statistics(self):
        """Логирование статистики"""
        uptime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        logger.info(f"📊 [INDEXING_SERVICE] Stats - "
                   f"Uptime: {uptime}, "
                   f"Total: {self.stats['total_processed']}, "
                   f"Success: {self.stats['successful']}, "
                   f"Failed: {self.stats['failed']}, "
                   f"Retries: {self.stats['retries']}, "
                   f"Queue: {self.task_queue.qsize()}, "
                   f"Active: {len(self.active_tasks)}")
    
    def _check_stuck_tasks(self):
        """Проверка зависших задач"""
        stuck_threshold = timedelta(minutes=10)  # 10 минут
        current_time = datetime.now()
        
        stuck_tasks = []
        for doc_id, task in self.active_tasks.items():
            if current_time - task.last_attempt > stuck_threshold:
                stuck_tasks.append(doc_id)
        
        if stuck_tasks:
            logger.warning(f"⚠️ [INDEXING_SERVICE] Found {len(stuck_tasks)} stuck tasks: {stuck_tasks}")
            
            # Помечаем как failed и убираем из активных
            for doc_id in stuck_tasks:
                task = self.active_tasks.pop(doc_id, None)
                if task:
                    self.db_manager.update_document_status(doc_id, IndexingStatus.FAILED.value, "Task stuck")
                    logger.warning(f"⚠️ [INDEXING_SERVICE] Marked stuck task {doc_id} as failed")
    
    def _recover_pending_tasks(self):
        """Восстановление задач из БД"""
        try:
            # Получаем документы, ожидающие индексации
            pending_docs = self.db_manager.get_pending_documents_for_indexing()
            
            for doc in pending_docs:
                doc_id = doc['id']
                
                # Проверяем, не обрабатывается ли уже
                if doc_id in self.active_tasks:
                    continue
                
                # Проверяем, нет ли в очереди
                if any(task.document_id == doc_id for task in list(self.task_queue.queue)):
                    continue
                
                # Добавляем в очередь (без контента, нужно будет загрузить)
                logger.info(f"🔄 [INDEXING_SERVICE] Recovering pending document {doc_id}")
                # Здесь нужно будет загрузить контент документа из файловой системы
                # Пока что просто помечаем как pending
                
        except Exception as e:
            logger.error(f"❌ [INDEXING_SERVICE] Error recovering pending tasks: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса"""
        uptime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        return {
            'is_running': self.is_running,
            'uptime_seconds': uptime.total_seconds(),
            'queue_size': self.task_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'failed_tasks': len(self.failed_tasks),
            'stats': self.stats.copy(),
            'worker_threads': len(self.worker_threads)
        }
