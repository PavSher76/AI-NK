"""
Сервис пакетной загрузки технической документации
"""

import logging
import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import shutil

from .models import (
    ArchiveDocument, DocumentSection, ArchiveProject, 
    BatchUploadRequest, BatchUploadResponse, DocumentType, ProcessingStatus
)
from .database_manager import ArchiveDatabaseManager
from .document_processor import ArchiveDocumentProcessor
from .vector_indexer import ArchiveVectorIndexer
from .config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_FILE_TYPES, BATCH_SIZE

logger = logging.getLogger(__name__)

class BatchUploadService:
    """Сервис пакетной загрузки технической документации"""
    
    def __init__(self, db_manager: ArchiveDatabaseManager):
        self.db_manager = db_manager
        self.document_processor = ArchiveDocumentProcessor()
        self.vector_indexer = ArchiveVectorIndexer()
        
        # Создаем директорию для загрузок
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    async def upload_documents_batch(self, request: BatchUploadRequest) -> BatchUploadResponse:
        """Пакетная загрузка документов"""
        try:
            logger.info(f"🚀 [BATCH_UPLOAD] Starting batch upload for project {request.project_code}")
            start_time = datetime.now()
            
            # Валидируем запрос
            validation_result = self._validate_batch_request(request)
            if not validation_result['valid']:
                return BatchUploadResponse(
                    status="error",
                    message="Validation failed",
                    project_code=request.project_code,
                    total_documents=len(request.documents),
                    processed_documents=0,
                    failed_documents=len(request.documents),
                    errors=validation_result['errors']
                )
            
            # Создаем или обновляем проект
            await self._ensure_project_exists(request.project_code, request.metadata)
            
            # Обрабатываем документы пакетами
            processed_documents = 0
            failed_documents = 0
            document_ids = []
            errors = []
            
            for i in range(0, len(request.documents), BATCH_SIZE):
                batch = request.documents[i:i + BATCH_SIZE]
                batch_result = await self._process_document_batch(
                    batch, request.project_code, request.auto_extract_sections
                )
                
                processed_documents += batch_result['processed']
                failed_documents += batch_result['failed']
                document_ids.extend(batch_result['document_ids'])
                errors.extend(batch_result['errors'])
            
            # Создаем связи между документами, если требуется
            if request.create_relations and len(document_ids) > 1:
                await self._create_document_relations(document_ids, request.project_code)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response = BatchUploadResponse(
                status="success" if failed_documents == 0 else "partial_success",
                message=f"Batch upload completed. Processed: {processed_documents}, Failed: {failed_documents}",
                project_code=request.project_code,
                total_documents=len(request.documents),
                processed_documents=processed_documents,
                failed_documents=failed_documents,
                document_ids=document_ids,
                errors=errors,
                processing_time=processing_time
            )
            
            logger.info(f"✅ [BATCH_UPLOAD] Batch upload completed for project {request.project_code}")
            return response
            
        except Exception as e:
            logger.error(f"❌ [BATCH_UPLOAD] Error in batch upload: {e}")
            return BatchUploadResponse(
                status="error",
                message=f"Batch upload failed: {str(e)}",
                project_code=request.project_code,
                total_documents=len(request.documents),
                processed_documents=0,
                failed_documents=len(request.documents),
                errors=[str(e)]
            )
    
    def _validate_batch_request(self, request: BatchUploadRequest) -> Dict[str, Any]:
        """Валидация запроса пакетной загрузки"""
        errors = []
        
        if not request.project_code:
            errors.append("Project code is required")
        
        if not request.documents:
            errors.append("At least one document is required")
        
        for i, doc in enumerate(request.documents):
            if 'file_path' not in doc:
                errors.append(f"Document {i+1}: file_path is required")
                continue
            
            file_path = doc['file_path']
            if not os.path.exists(file_path):
                errors.append(f"Document {i+1}: file not found: {file_path}")
                continue
            
            # Проверяем размер файла
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                errors.append(f"Document {i+1}: file too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
            
            # Проверяем тип файла
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in ALLOWED_FILE_TYPES:
                errors.append(f"Document {i+1}: unsupported file type: {file_ext}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    async def _ensure_project_exists(self, project_code: str, metadata: Dict[str, Any]):
        """Создание или обновление проекта"""
        try:
            # Проверяем, существует ли проект
            existing_projects = self.db_manager.execute_read_query("""
                SELECT id FROM archive_projects WHERE project_code = %s
            """, (project_code,))
            
            if not existing_projects:
                # Создаем новый проект
                project = ArchiveProject(
                    project_code=project_code,
                    project_name=metadata.get('project_name', f'Проект {project_code}'),
                    project_description=metadata.get('project_description'),
                    project_manager=metadata.get('project_manager'),
                    department=metadata.get('department'),
                    start_date=metadata.get('start_date'),
                    end_date=metadata.get('end_date'),
                    status=metadata.get('status', 'active'),
                    metadata=metadata
                )
                
                self.db_manager.save_project(project)
                logger.info(f"✅ [ENSURE_PROJECT] Created new project: {project_code}")
            else:
                logger.info(f"ℹ️ [ENSURE_PROJECT] Project already exists: {project_code}")
                
        except Exception as e:
            logger.error(f"❌ [ENSURE_PROJECT] Error ensuring project exists: {e}")
            raise
    
    async def _process_document_batch(self, documents: List[Dict[str, Any]], 
                                    project_code: str, auto_extract_sections: bool) -> Dict[str, Any]:
        """Обработка пакета документов"""
        processed = 0
        failed = 0
        document_ids = []
        errors = []
        
        for doc_data in documents:
            try:
                file_path = doc_data['file_path']
                logger.info(f"🔄 [PROCESS_BATCH] Processing document: {file_path}")
                
                # Обрабатываем документ
                document, sections = self.document_processor.process_document(
                    file_path, project_code
                )
                
                # Обновляем данные из запроса
                if 'document_type' in doc_data:
                    document.document_type = DocumentType(doc_data['document_type'])
                if 'document_name' in doc_data:
                    document.document_name = doc_data['document_name']
                if 'document_number' in doc_data:
                    document.document_number = doc_data['document_number']
                if 'author' in doc_data:
                    document.author = doc_data['author']
                if 'department' in doc_data:
                    document.department = doc_data['department']
                if 'version' in doc_data:
                    document.version = doc_data['version']
                
                # Копируем файл в директорию загрузок
                saved_file_path = await self._save_uploaded_file(file_path, project_code)
                document.file_path = saved_file_path
                
                # Сохраняем документ в базу данных
                document_id = self.db_manager.save_document(document)
                document_ids.append(document_id)
                
                # Обновляем ID в разделах
                for section in sections:
                    section.archive_document_id = document_id
                
                # Сохраняем разделы, если требуется
                if auto_extract_sections and sections:
                    for section in sections:
                        self.db_manager.save_document_section(section)
                
                # Создаем векторные индексы для разделов
                if sections:
                    await self.vector_indexer.index_document_sections(document_id, sections)
                
                # Обновляем статус обработки
                self.db_manager.update_document_status(document_id, ProcessingStatus.COMPLETED)
                
                processed += 1
                logger.info(f"✅ [PROCESS_BATCH] Document processed successfully: {document_id}")
                
            except Exception as e:
                failed += 1
                error_msg = f"Error processing {doc_data.get('file_path', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ [PROCESS_BATCH] {error_msg}")
        
        return {
            'processed': processed,
            'failed': failed,
            'document_ids': document_ids,
            'errors': errors
        }
    
    async def _save_uploaded_file(self, source_path: str, project_code: str) -> str:
        """Сохранение загруженного файла в директорию проекта"""
        try:
            # Создаем директорию для проекта
            project_dir = os.path.join(UPLOAD_DIR, project_code)
            os.makedirs(project_dir, exist_ok=True)
            
            # Генерируем уникальное имя файла
            filename = os.path.basename(source_path)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{name}_{timestamp}{ext}"
            
            # Путь для сохранения
            dest_path = os.path.join(project_dir, unique_filename)
            
            # Копируем файл
            shutil.copy2(source_path, dest_path)
            
            logger.info(f"✅ [SAVE_FILE] File saved: {dest_path}")
            return dest_path
            
        except Exception as e:
            logger.error(f"❌ [SAVE_FILE] Error saving file: {e}")
            raise
    
    async def _create_document_relations(self, document_ids: List[int], project_code: str):
        """Создание связей между документами проекта"""
        try:
            if len(document_ids) < 2:
                return
            
            # Получаем документы проекта
            documents = self.db_manager.get_documents_by_project(project_code)
            
            # Создаем связи на основе типов документов
            relations_created = 0
            
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i+1:], i+1):
                    relation_type = self._determine_relation_type(doc1, doc2)
                    if relation_type:
                        # Создаем связь
                        relation = DocumentRelation(
                            source_document_id=doc1.id,
                            target_document_id=doc2.id,
                            relation_type=relation_type,
                            relation_description=f"Автоматически созданная связь между {doc1.document_type.value} и {doc2.document_type.value}"
                        )
                        
                        # Сохраняем связь (пока без реализации в database_manager)
                        relations_created += 1
            
            logger.info(f"✅ [CREATE_RELATIONS] Created {relations_created} relations for project {project_code}")
            
        except Exception as e:
            logger.error(f"❌ [CREATE_RELATIONS] Error creating relations: {e}")
    
    def _determine_relation_type(self, doc1: ArchiveDocument, doc2: ArchiveDocument) -> Optional[str]:
        """Определение типа связи между документами"""
        # Простая логика определения связей
        if doc1.document_type == DocumentType.PD and doc2.document_type == DocumentType.RD:
            return "DEPENDS_ON"  # РД зависит от ПД
        elif doc1.document_type == DocumentType.RD and doc2.document_type == DocumentType.PD:
            return "REFERENCES"  # РД ссылается на ПД
        elif doc1.document_type == DocumentType.TEO and doc2.document_type in [DocumentType.PD, DocumentType.RD]:
            return "RELATED_TO"  # ТЭО связано с ПД/РД
        else:
            return None
    
    async def get_upload_progress(self, project_code: str) -> Dict[str, Any]:
        """Получение прогресса загрузки для проекта"""
        try:
            # Получаем статистику проекта
            stats = self.db_manager.get_project_stats(project_code)
            if not stats:
                return {
                    'project_code': project_code,
                    'status': 'not_found',
                    'total_documents': 0,
                    'processed_documents': 0,
                    'failed_documents': 0,
                    'progress_percent': 0
                }
            
            # Подсчитываем документы по статусам
            total_docs = stats.total_documents
            processed_docs = stats.processing_status.get('completed', 0)
            failed_docs = stats.processing_status.get('failed', 0)
            pending_docs = stats.processing_status.get('pending', 0) + stats.processing_status.get('processing', 0)
            
            progress_percent = (processed_docs / total_docs * 100) if total_docs > 0 else 0
            
            return {
                'project_code': project_code,
                'status': 'active' if pending_docs > 0 else 'completed',
                'total_documents': total_docs,
                'processed_documents': processed_docs,
                'failed_documents': failed_docs,
                'pending_documents': pending_docs,
                'progress_percent': round(progress_percent, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ [GET_UPLOAD_PROGRESS] Error getting upload progress: {e}")
            return {
                'project_code': project_code,
                'status': 'error',
                'error': str(e)
            }
    
    async def cancel_upload(self, project_code: str) -> bool:
        """Отмена загрузки проекта"""
        try:
            # Обновляем статус всех документов проекта на "failed"
            self.db_manager.execute_write_query("""
                UPDATE archive_documents 
                SET processing_status = 'failed', processing_error = 'Upload cancelled by user'
                WHERE project_code = %s AND processing_status IN ('pending', 'processing')
            """, (project_code,))
            
            logger.info(f"✅ [CANCEL_UPLOAD] Upload cancelled for project {project_code}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [CANCEL_UPLOAD] Error cancelling upload: {e}")
            return False
