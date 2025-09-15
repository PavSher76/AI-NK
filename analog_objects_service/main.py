"""
Сервис для работы с объектами аналогами
Предоставляет API для управления базой данных объектов аналогов
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import pandas as pd
import json
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import uuid
import shutil
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Analog Objects Service",
    description="Сервис для управления объектами аналогами",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/database")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads/analog_objects")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 104857600))  # 100 MB

# Создание директории для загрузок
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Подключение к базе данных
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Модели данных
class AnalogObject:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.name = data.get('name')
        self.type = data.get('type')
        self.region = data.get('region')
        self.city = data.get('city')
        self.year = data.get('year')
        self.status = data.get('status')
        self.area = data.get('area')
        self.floors = data.get('floors')
        self.apartments = data.get('apartments')
        self.developer = data.get('developer')
        self.developer_contact = data.get('developer_contact')
        self.developer_phone = data.get('developer_phone')
        self.developer_email = data.get('developer_email')
        self.description = data.get('description')
        self.coordinates = data.get('coordinates')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.created_by = data.get('created_by')
        self.is_active = data.get('is_active', True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'region': self.region,
            'city': self.city,
            'year': self.year,
            'status': self.status,
            'area': float(self.area) if self.area else None,
            'floors': self.floors,
            'apartments': self.apartments,
            'developer': self.developer,
            'developer_contact': self.developer_contact,
            'developer_phone': self.developer_phone,
            'developer_email': self.developer_email,
            'description': self.description,
            'coordinates': self.coordinates,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'is_active': self.is_active
        }

# API эндпоинты

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "healthy", "service": "analog-objects-service"}

@app.get("/api/analog-objects")
async def get_analog_objects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    type_filter: Optional[str] = Query(None),
    region_filter: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    area_from: Optional[float] = Query(None),
    area_to: Optional[float] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db = Depends(get_db)
):
    """Получение списка объектов аналогов с фильтрацией и пагинацией"""
    try:
        # Базовый запрос
        query = """
            SELECT * FROM analog_objects 
            WHERE is_active = TRUE
        """
        params = {}
        conditions = []

        # Применение фильтров
        if search:
            conditions.append("""
                (name ILIKE :search OR 
                 description ILIKE :search OR 
                 developer ILIKE :search)
            """)
            params['search'] = f"%{search}%"

        if type_filter:
            conditions.append("type = :type_filter")
            params['type_filter'] = type_filter

        if region_filter:
            conditions.append("region = :region_filter")
            params['region_filter'] = region_filter

        if year_from:
            conditions.append("year >= :year_from")
            params['year_from'] = year_from

        if year_to:
            conditions.append("year <= :year_to")
            params['year_to'] = year_to

        if area_from:
            conditions.append("area >= :area_from")
            params['area_from'] = area_from

        if area_to:
            conditions.append("area <= :area_to")
            params['area_to'] = area_to

        if conditions:
            query += " AND " + " AND ".join(conditions)

        # Подсчет общего количества (отдельный запрос без ORDER BY)
        count_query = f"""
            SELECT COUNT(*) FROM analog_objects 
            WHERE is_active = TRUE
        """
        if conditions:
            count_query += " AND " + " AND ".join(conditions)
        count_result = db.execute(text(count_query), params).fetchone()
        total_count = count_result[0] if count_result else 0

        # Сортировка
        valid_sort_fields = ['name', 'type', 'region', 'year', 'area', 'created_at', 'updated_at']
        if sort_by in valid_sort_fields:
            order = "ASC" if sort_order.lower() == "asc" else "DESC"
            query += f" ORDER BY {sort_by} {order}"

        # Пагинация
        offset = (page - 1) * limit
        query += " LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset

        # Выполнение запроса
        result = db.execute(text(query), params).fetchall()
        
        # Преобразование результатов
        objects = []
        for row in result:
            obj_data = dict(row._mapping)
            obj = AnalogObject(obj_data)
            objects.append(obj.to_dict())

        return {
            "objects": objects,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }

    except Exception as e:
        logger.error(f"Ошибка получения объектов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analog-objects/{object_id}")
async def get_analog_object(object_id: int, db = Depends(get_db)):
    """Получение детальной информации об объекте"""
    try:
        # Получение основного объекта
        query = "SELECT * FROM analog_objects WHERE id = :id AND is_active = TRUE"
        result = db.execute(text(query), {"id": object_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Объект не найден")

        obj_data = dict(result._mapping)
        obj = AnalogObject(obj_data)

        # Получение характеристик
        characteristics_query = """
            SELECT name, value, unit 
            FROM analog_object_characteristics 
            WHERE object_id = :id
        """
        characteristics_result = db.execute(text(characteristics_query), {"id": object_id}).fetchall()
        characteristics = [dict(row._mapping) for row in characteristics_result]

        # Получение файлов
        files_query = """
            SELECT id, filename, original_filename, file_type, file_size, 
                   mime_type, description, uploaded_at
            FROM analog_object_files 
            WHERE object_id = :id
        """
        files_result = db.execute(text(files_query), {"id": object_id}).fetchall()
        files = [dict(row._mapping) for row in files_result]

        # Получение связанных объектов
        relations_query = """
            SELECT aor.target_object_id, ao.name, ao.type, ao.region, 
                   aor.similarity_score, aor.relation_type
            FROM analog_object_relations aor
            JOIN analog_objects ao ON aor.target_object_id = ao.id
            WHERE aor.source_object_id = :id AND ao.is_active = TRUE
        """
        relations_result = db.execute(text(relations_query), {"id": object_id}).fetchall()
        relations = [dict(row._mapping) for row in relations_result]

        return {
            "object": obj.to_dict(),
            "characteristics": characteristics,
            "files": files,
            "relations": relations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения объекта {object_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analog-objects")
async def create_analog_object(
    name: str = Form(...),
    type: str = Form(...),
    region: str = Form(...),
    city: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    status: Optional[str] = Form(None),
    area: Optional[float] = Form(None),
    floors: Optional[int] = Form(None),
    apartments: Optional[int] = Form(None),
    developer: Optional[str] = Form(None),
    developer_contact: Optional[str] = Form(None),
    developer_phone: Optional[str] = Form(None),
    developer_email: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    coordinates: Optional[str] = Form(None),
    created_by: str = Form("system"),
    db = Depends(get_db)
):
    """Создание нового объекта аналога"""
    try:
        # Парсинг координат
        coordinates_point = None
        if coordinates:
            try:
                coords = json.loads(coordinates)
                if 'lat' in coords and 'lng' in coords:
                    coordinates_point = f"POINT({coords['lng']} {coords['lat']})"
            except:
                pass

        # Вставка объекта
        insert_query = """
            INSERT INTO analog_objects (
                name, type, region, city, year, status, area, floors, apartments,
                developer, developer_contact, developer_phone, developer_email,
                description, coordinates, created_by
            ) VALUES (
                :name, :type, :region, :city, :year, :status, :area, :floors, :apartments,
                :developer, :developer_contact, :developer_phone, :developer_email,
                :description, :coordinates, :created_by
            ) RETURNING id
        """
        
        result = db.execute(text(insert_query), {
            "name": name,
            "type": type,
            "region": region,
            "city": city,
            "year": year,
            "status": status,
            "area": area,
            "floors": floors,
            "apartments": apartments,
            "developer": developer,
            "developer_contact": developer_contact,
            "developer_phone": developer_phone,
            "developer_email": developer_email,
            "description": description,
            "coordinates": coordinates_point,
            "created_by": created_by
        })
        
        object_id = result.fetchone()[0]
        db.commit()

        return {"id": object_id, "message": "Объект успешно создан"}

    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка создания объекта: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/analog-objects/{object_id}")
async def update_analog_object(
    object_id: int,
    name: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    status: Optional[str] = Form(None),
    area: Optional[float] = Form(None),
    floors: Optional[int] = Form(None),
    apartments: Optional[int] = Form(None),
    developer: Optional[str] = Form(None),
    developer_contact: Optional[str] = Form(None),
    developer_phone: Optional[str] = Form(None),
    developer_email: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    coordinates: Optional[str] = Form(None),
    db = Depends(get_db)
):
    """Обновление объекта аналога"""
    try:
        # Проверка существования объекта
        check_query = "SELECT id FROM analog_objects WHERE id = :id AND is_active = TRUE"
        result = db.execute(text(check_query), {"id": object_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Объект не найден")

        # Подготовка данных для обновления
        update_fields = []
        params = {"id": object_id}

        if name is not None:
            update_fields.append("name = :name")
            params["name"] = name
        if type is not None:
            update_fields.append("type = :type")
            params["type"] = type
        if region is not None:
            update_fields.append("region = :region")
            params["region"] = region
        if city is not None:
            update_fields.append("city = :city")
            params["city"] = city
        if year is not None:
            update_fields.append("year = :year")
            params["year"] = year
        if status is not None:
            update_fields.append("status = :status")
            params["status"] = status
        if area is not None:
            update_fields.append("area = :area")
            params["area"] = area
        if floors is not None:
            update_fields.append("floors = :floors")
            params["floors"] = floors
        if apartments is not None:
            update_fields.append("apartments = :apartments")
            params["apartments"] = apartments
        if developer is not None:
            update_fields.append("developer = :developer")
            params["developer"] = developer
        if developer_contact is not None:
            update_fields.append("developer_contact = :developer_contact")
            params["developer_contact"] = developer_contact
        if developer_phone is not None:
            update_fields.append("developer_phone = :developer_phone")
            params["developer_phone"] = developer_phone
        if developer_email is not None:
            update_fields.append("developer_email = :developer_email")
            params["developer_email"] = developer_email
        if description is not None:
            update_fields.append("description = :description")
            params["description"] = description
        if coordinates is not None:
            coordinates_point = None
            try:
                coords = json.loads(coordinates)
                if 'lat' in coords and 'lng' in coords:
                    coordinates_point = f"POINT({coords['lng']} {coords['lat']})"
            except:
                pass
            update_fields.append("coordinates = :coordinates")
            params["coordinates"] = coordinates_point

        if not update_fields:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")

        # Обновление объекта
        update_query = f"""
            UPDATE analog_objects 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """
        
        db.execute(text(update_query), params)
        db.commit()

        return {"message": "Объект успешно обновлен"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка обновления объекта {object_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/analog-objects/{object_id}")
async def delete_analog_object(object_id: int, db = Depends(get_db)):
    """Удаление объекта аналога (мягкое удаление)"""
    try:
        # Проверка существования объекта
        check_query = "SELECT id FROM analog_objects WHERE id = :id AND is_active = TRUE"
        result = db.execute(text(check_query), {"id": object_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Объект не найден")

        # Мягкое удаление
        delete_query = "UPDATE analog_objects SET is_active = FALSE WHERE id = :id"
        db.execute(text(delete_query), {"id": object_id})
        db.commit()

        return {"message": "Объект успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления объекта {object_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analog-objects/upload")
async def upload_files(
    object_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db = Depends(get_db)
):
    """Загрузка файлов для объекта"""
    try:
        # Проверка существования объекта
        check_query = "SELECT id FROM analog_objects WHERE id = :id AND is_active = TRUE"
        result = db.execute(text(check_query), {"id": object_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Объект не найден")

        uploaded_files = []
        
        for file in files:
            # Проверка размера файла
            if file.size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"Файл {file.filename} слишком большой")

            # Определение типа файла
            file_type = "document"
            if file.content_type and file.content_type.startswith("image/"):
                file_type = "image"

            # Генерация уникального имени файла
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = Path(UPLOAD_DIR) / unique_filename

            # Сохранение файла
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Сохранение информации о файле в БД
            insert_query = """
                INSERT INTO analog_object_files (
                    object_id, filename, original_filename, file_path, 
                    file_type, file_size, mime_type, uploaded_by
                ) VALUES (
                    :object_id, :filename, :original_filename, :file_path,
                    :file_type, :file_size, :mime_type, :uploaded_by
                ) RETURNING id
            """
            
            result = db.execute(text(insert_query), {
                "object_id": object_id,
                "filename": unique_filename,
                "original_filename": file.filename,
                "file_path": str(file_path),
                "file_type": file_type,
                "file_size": file.size,
                "mime_type": file.content_type,
                "uploaded_by": "system"
            })
            
            file_id = result.fetchone()[0]
            uploaded_files.append({
                "id": file_id,
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file.size
            })

        db.commit()
        return {"message": "Файлы успешно загружены", "files": uploaded_files}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка загрузки файлов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analog-objects/analytics/summary")
async def get_analytics_summary(db = Depends(get_db)):
    """Получение сводной аналитики"""
    try:
        # Общее количество объектов
        total_query = "SELECT COUNT(*) FROM analog_objects WHERE is_active = TRUE"
        total_result = db.execute(text(total_query)).fetchone()
        total_objects = total_result[0] if total_result else 0

        # Объекты по типам
        types_query = """
            SELECT type, COUNT(*) as count 
            FROM analog_objects 
            WHERE is_active = TRUE 
            GROUP BY type
        """
        types_result = db.execute(text(types_query)).fetchall()
        by_type = [{"type": row[0], "count": row[1]} for row in types_result]

        # Объекты по регионам
        regions_query = """
            SELECT region, COUNT(*) as count 
            FROM analog_objects 
            WHERE is_active = TRUE 
            GROUP BY region 
            ORDER BY count DESC 
            LIMIT 10
        """
        regions_result = db.execute(text(regions_query)).fetchall()
        by_region = [{"region": row[0], "count": row[1]} for row in regions_result]

        # Средние значения
        stats_query = """
            SELECT 
                AVG(area) as avg_area,
                AVG(floors) as avg_floors,
                AVG(apartments) as avg_apartments,
                MIN(year) as min_year,
                MAX(year) as max_year
            FROM analog_objects 
            WHERE is_active = TRUE
        """
        stats_result = db.execute(text(stats_query)).fetchone()
        stats = {
            "avg_area": float(stats_result[0]) if stats_result[0] else 0,
            "avg_floors": float(stats_result[1]) if stats_result[1] else 0,
            "avg_apartments": float(stats_result[2]) if stats_result[2] else 0,
            "min_year": stats_result[3],
            "max_year": stats_result[4]
        }

        return {
            "total_objects": total_objects,
            "by_type": by_type,
            "by_region": by_region,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Ошибка получения аналитики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analog-objects/import")
async def import_objects(
    file: UploadFile = File(...),
    import_type: str = Form("csv"),
    db = Depends(get_db)
):
    """Импорт объектов из файла"""
    try:
        # Проверка типа файла
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла")

        # Сохранение файла
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = Path(UPLOAD_DIR) / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Запись информации об импорте
        import_query = """
            INSERT INTO analog_imports (
                filename, file_path, file_size, import_type, 
                records_total, status, imported_by, started_at
            ) VALUES (
                :filename, :file_path, :file_size, :import_type,
                :records_total, :status, :imported_by, :started_at
            ) RETURNING id
        """
        
        import_result = db.execute(text(import_query), {
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": file.size,
            "import_type": import_type,
            "records_total": 0,  # Будет обновлено после обработки
            "status": "processing",
            "imported_by": "system",
            "started_at": datetime.now()
        })
        
        import_id = import_result.fetchone()[0]
        db.commit()

        # Обработка файла (здесь должна быть логика парсинга CSV/Excel)
        # Пока возвращаем успешный результат
        return {
            "import_id": import_id,
            "message": "Импорт начат",
            "filename": file.filename
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка импорта: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
