import logging
import json
import fitz  # PyMuPDF
from typing import Dict, Any, List, Optional
from datetime import datetime

from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Сервис для обработки документов и извлечения элементов"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def process_document(self, document_id: int, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Обработка документа и извлечение элементов"""
        try:
            logger.info(f"🔄 [PROCESS] Starting document processing for document {document_id}")
            
            # Определяем тип файла
            file_type = filename.split('.')[-1].lower()
            
            if file_type == 'pdf':
                return self.process_pdf_document(document_id, file_content)
            elif file_type in ['dwg', 'ifc', 'docx']:
                # Для других типов файлов пока возвращаем заглушку
                logger.warning(f"⚠️ [PROCESS] File type {file_type} not fully supported yet")
                return self.process_unsupported_document(document_id, file_content, file_type)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"❌ [PROCESS] Document processing failed for document {document_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def process_pdf_document(self, document_id: int, file_content: bytes) -> Dict[str, Any]:
        """Обработка PDF документа"""
        try:
            logger.info(f"📄 [PDF_PROCESS] Processing PDF document {document_id}")
            
            # Открываем PDF документ
            doc = fitz.open(stream=file_content, filetype="pdf")
            total_pages = len(doc)
            
            logger.info(f"📄 [PDF_PROCESS] PDF has {total_pages} pages")
            
            # Извлекаем элементы с каждой страницы
            elements = []
            
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                
                # Извлекаем текст
                text_content = page.get_text()
                
                # Извлекаем изображения (если есть)
                image_list = page.get_images()
                
                # Создаем элемент для страницы
                element = {
                    "document_id": document_id,
                    "page_number": page_num + 1,
                    "content": text_content,
                    "content_type": "text",
                    "element_type": "page",
                    "metadata": {
                        "page_width": page.rect.width,
                        "page_height": page.rect.height,
                        "images_count": len(image_list),
                        "text_length": len(text_content)
                    }
                }
                
                elements.append(element)
                
                # Если есть изображения, создаем отдельные элементы для них
                for img_index, img in enumerate(image_list):
                    img_element = {
                        "document_id": document_id,
                        "page_number": page_num + 1,
                        "content": f"Image {img_index + 1} on page {page_num + 1}",
                        "content_type": "image",
                        "element_type": "image",
                        "metadata": {
                            "image_index": img_index,
                            "image_rect": img[0],  # bbox
                            "image_width": img[2],
                            "image_height": img[3]
                        }
                    }
                    elements.append(img_element)
                
                logger.debug(f"📄 [PDF_PROCESS] Processed page {page_num + 1}/{total_pages}")
            
            # Сохраняем элементы в базу данных
            saved_elements = self.save_elements(document_id, elements)
            
            # Обновляем статус документа
            self.update_document_status(document_id, "completed", {
                "total_pages": total_pages,
                "total_elements": len(elements),
                "text_elements": len([e for e in elements if e["content_type"] == "text"]),
                "image_elements": len([e for e in elements if e["content_type"] == "image"])
            })
            
            doc.close()
            
            logger.info(f"✅ [PDF_PROCESS] PDF document {document_id} processed successfully")
            return {
                "status": "success",
                "total_pages": total_pages,
                "total_elements": len(elements),
                "saved_elements": saved_elements
            }
            
        except Exception as e:
            logger.error(f"❌ [PDF_PROCESS] PDF processing failed for document {document_id}: {e}")
            self.update_document_status(document_id, "failed", {"error": str(e)})
            return {
                "status": "error",
                "error": str(e)
            }
    
    def process_unsupported_document(self, document_id: int, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Обработка неподдерживаемых типов документов"""
        try:
            logger.info(f"📄 [UNSUPPORTED_PROCESS] Processing {file_type} document {document_id}")
            
            # Создаем базовый элемент для неподдерживаемого типа
            element = {
                "document_id": document_id,
                "page_number": 1,
                "content": f"Document type {file_type} is not fully supported yet. File size: {len(file_content)} bytes",
                "content_type": "text",
                "element_type": "unsupported",
                "metadata": {
                    "file_type": file_type,
                    "file_size": len(file_content),
                    "processing_note": "Limited support for this file type"
                }
            }
            
            # Сохраняем элемент
            saved_elements = self.save_elements(document_id, [element])
            
            # Обновляем статус документа
            self.update_document_status(document_id, "completed", {
                "total_pages": 1,
                "total_elements": 1,
                "file_type": file_type,
                "processing_note": "Limited support"
            })
            
            logger.info(f"✅ [UNSUPPORTED_PROCESS] {file_type} document {document_id} processed with limited support")
            return {
                "status": "success",
                "total_pages": 1,
                "total_elements": 1,
                "saved_elements": saved_elements,
                "note": f"Limited support for {file_type} files"
            }
            
        except Exception as e:
            logger.error(f"❌ [UNSUPPORTED_PROCESS] Processing failed for document {document_id}: {e}")
            self.update_document_status(document_id, "failed", {"error": str(e)})
            return {
                "status": "error",
                "error": str(e)
            }
    
    def save_elements(self, document_id: int, elements: List[Dict[str, Any]]) -> int:
        """Сохранение элементов в базу данных"""
        try:
            def _save_elements(conn):
                with conn.cursor() as cursor:
                    saved_count = 0
                    
                    for element in elements:
                        cursor.execute("""
                            INSERT INTO checkable_elements 
                            (checkable_document_id, page_number, element_content, element_type, content_type, element_metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            element["document_id"],
                            element["page_number"],
                            element["content"],
                            element["element_type"],
                            element["content_type"],
                            json.dumps(element.get("metadata", {}))
                        ))
                        saved_count += 1
                    
                    conn.commit()
                    return saved_count
            
            saved_count = self.db_connection.execute_in_transaction(_save_elements)
            logger.info(f"💾 [SAVE_ELEMENTS] Saved {saved_count} elements for document {document_id}")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ [SAVE_ELEMENTS] Failed to save elements for document {document_id}: {e}")
            raise
    
    def update_document_status(self, document_id: int, status: str, metadata: Dict[str, Any] = None):
        """Обновление статуса документа"""
        try:
            def _update_status(conn):
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE checkable_documents 
                        SET processing_status = %s, 
                            processing_metadata = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        status,
                        json.dumps(metadata) if metadata else '{}',
                        document_id
                    ))
                    conn.commit()
            
            self.db_connection.execute_in_transaction(_update_status)
            logger.info(f"📝 [UPDATE_STATUS] Updated document {document_id} status to {status}")
            
        except Exception as e:
            logger.error(f"❌ [UPDATE_STATUS] Failed to update status for document {document_id}: {e}")
            raise
    
    async def reprocess_document(self, document_id: int) -> Dict[str, Any]:
        """Переобработка документа"""
        try:
            logger.info(f"🔄 [REPROCESS] Starting reprocessing for document {document_id}")
            
            # Получаем информацию о документе
            document_info = self.get_document_info(document_id)
            if not document_info:
                return {"status": "error", "error": "Document not found"}
            
            # Получаем содержимое файла (в реальной системе нужно получить из хранилища)
            # Пока возвращаем ошибку, так как у нас нет доступа к файлу
            return {
                "status": "error",
                "error": "File content not available for reprocessing"
            }
            
        except Exception as e:
            logger.error(f"❌ [REPROCESS] Reprocessing failed for document {document_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_document_info(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о документе"""
        try:
            with self.db_connection.get_db_connection().cursor() as cursor:
                cursor.execute("""
                    SELECT id, filename, original_filename, file_type, file_size, processing_status
                    FROM checkable_documents
                    WHERE id = %s
                """, (document_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "id": result[0],
                        "filename": result[1],
                        "original_filename": result[2],
                        "file_type": result[3],
                        "file_size": result[4],
                        "processing_status": result[5]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return None
