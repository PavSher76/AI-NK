"""
Модуль с бизнес-логикой расчетов
"""
import logging
import time
import math
from typing import Dict, Any, List
from datetime import datetime

from models import (
    CalculationCreate, CalculationResponse, CalculationExecute,
    StructuralCalculationParams, FoundationCalculationParams,
    ThermalCalculationParams, VentilationCalculationParams,
    DegasificationCalculationParams, ElectricalLoadCalculationParams,
    WaterSupplyCalculationParams, FireSafetyCalculationParams,
    AcousticCalculationParams, LightingCalculationParams,
    GeologicalCalculationParams,
    CalculationTypeInfo, CalculationCategoryInfo
)
from database import db_manager

logger = logging.getLogger(__name__)


class CalculationEngine:
    """Движок для выполнения расчетов"""
    
    def __init__(self):
        self.calculation_types = {
            "structural": {
                "name": "Строительные конструкции",
                "description": "Расчеты строительных конструкций",
                "categories": ["beam", "column", "slab", "foundation"]
            },
            "foundation": {
                "name": "Основания и фундаменты", 
                "description": "Расчеты оснований и фундаментов",
                "categories": ["bearing_capacity", "settlement", "stability"]
            },
            "thermal": {
                "name": "Теплотехнические расчеты",
                "description": "Теплотехнические расчеты зданий",
                "categories": ["heat_loss", "thermal_insulation", "condensation"]
            },
            "ventilation": {
                "name": "Вентиляция и кондиционирование",
                "description": "Расчеты систем вентиляции согласно СП 60.13330.2016, СП 7.13130.2013, СП 54.13330.2016",
                "categories": [
                    "air_exchange",           # Расчеты воздухообмена
                    "smoke_ventilation",      # Противодымная вентиляция
                    "residential_ventilation", # Вентиляция жилых зданий
                    "energy_efficiency",      # Энергоэффективность
                    "acoustic_calculations",  # Акустические расчеты
                    "heat_recovery",          # Рекуперация тепла
                    "air_conditioning"        # Кондиционирование
                ]
            },
            "degasification": {
                "name": "Расчет дегазации угольных шахт",
                "description": "Расчеты систем дегазации угольных шахт",
                "categories": ["methane_extraction", "ventilation_requirements", "safety_systems"]
            },
            "electrical": {
                "name": "Электротехнические расчеты",
                "description": "Расчеты электрических нагрузок, заземления и молниезащиты",
                "categories": ["electrical_loads", "cable_calculation", "grounding", "lightning_protection", "energy_efficiency"]
            },
            "water_supply": {
                "name": "Водоснабжение и водоотведение",
                "description": "Расчеты систем водоснабжения и водоотведения согласно СП 30.13330.2016",
                "categories": ["water_consumption", "pipe_calculation", "sewage_treatment", "water_pressure", "drainage"]
            },
            "fire_safety": {
                "name": "Пожарная безопасность",
                "description": "Расчеты пожарной безопасности согласно СП 4.13130.2013, СП 5.13130.2009",
                "categories": ["evacuation", "fire_suppression", "smoke_control", "fire_resistance", "emergency_systems"]
            },
            "acoustic": {
                "name": "Акустические расчеты",
                "description": "Расчеты звукоизоляции и акустики согласно СП 51.13330.2011",
                "categories": ["sound_insulation", "noise_control", "vibration_control", "acoustic_treatment", "reverberation"]
            },
            "lighting": {
                "name": "Освещение и инсоляция",
                "description": "Расчеты освещения и инсоляции согласно СП 52.13330.2016",
                "categories": ["artificial_lighting", "natural_lighting", "insolation", "luminaire_calculation", "energy_efficiency"]
            },
            "geological": {
                "name": "Инженерно-геологические расчеты",
                "description": "Расчеты оснований и грунтов согласно СП 22.13330.2016",
                "categories": ["bearing_capacity", "settlement", "slope_stability", "seismic_analysis", "groundwater"]
            }
        }
    
    def get_calculation_types(self) -> List[CalculationTypeInfo]:
        """Получение доступных типов расчетов"""
        return [
            CalculationTypeInfo(
                type=calc_type,
                name=info["name"],
                description=info["description"],
                parameters_schema=self._get_parameters_schema(calc_type),
                categories=info["categories"]
            )
            for calc_type, info in self.calculation_types.items()
        ]
    
    def get_calculation_categories(self, calculation_type: str) -> List[CalculationCategoryInfo]:
        """Получение категорий для типа расчета"""
        if calculation_type not in self.calculation_types:
            return []
        
        categories = self.calculation_types[calculation_type]["categories"]
        return [
            CalculationCategoryInfo(
                category=category,
                name=self._get_category_name(category),
                description=self._get_category_description(category),
                calculation_types=[calculation_type]
            )
            for category in categories
        ]
    
    def _get_parameters_schema(self, calculation_type: str) -> Dict[str, Any]:
        """Получение схемы параметров для типа расчета"""
        schemas = {
            "structural": {
                "type": "object",
                "properties": {
                    "beam_length": {"type": "number", "title": "Длина балки (м)"},
                    "beam_width": {"type": "number", "title": "Ширина балки (м)"},
                    "beam_height": {"type": "number", "title": "Высота балки (м)"},
                    "material_strength": {"type": "number", "title": "Прочность материала (МПа)"},
                    "load_value": {"type": "number", "title": "Нагрузка (кН/м)"},
                    "safety_factor": {"type": "number", "title": "Коэффициент безопасности", "default": 1.5},
                    "deflection_limit": {"type": "number", "title": "Предел прогиба", "default": 1.0/250}
                },
                "required": ["beam_length", "beam_width", "beam_height", "material_strength", "load_value"]
            },
            "foundation": {
                "type": "object",
                "properties": {
                    "foundation_width": {"type": "number", "title": "Ширина фундамента (м)"},
                    "foundation_length": {"type": "number", "title": "Длина фундамента (м)"},
                    "foundation_depth": {"type": "number", "title": "Глубина заложения (м)"},
                    "soil_cohesion": {"type": "number", "title": "Сцепление грунта (кПа)"},
                    "soil_friction_angle": {"type": "number", "title": "Угол внутреннего трения (град)"},
                    "soil_density": {"type": "number", "title": "Плотность грунта (т/м³)"},
                    "safety_factor": {"type": "number", "title": "Коэффициент безопасности", "default": 2.0},
                    "water_table_depth": {"type": "number", "title": "Глубина залегания грунтовых вод (м)"}
                },
                "required": ["foundation_width", "foundation_length", "foundation_depth", 
                           "soil_cohesion", "soil_friction_angle", "soil_density"]
            },
            "thermal": {
                "type": "object",
                "properties": {
                    "building_type": {"type": "string", "title": "Тип здания", "enum": ["жилое", "общественное", "производственное"]},
                    "building_area": {"type": "number", "title": "Площадь здания (м²)"},
                    "building_volume": {"type": "number", "title": "Объем здания (м³)"},
                    "number_of_floors": {"type": "integer", "title": "Количество этажей"},
                    "wall_thickness": {"type": "number", "title": "Толщина стены (м)"},
                    "wall_material": {"type": "string", "title": "Материал стены"},
                    "thermal_conductivity": {"type": "number", "title": "Теплопроводность (Вт/(м·К))"},
                    "wall_area": {"type": "number", "title": "Площадь стен (м²)"},
                    "window_area": {"type": "number", "title": "Площадь окон (м²)", "default": 0},
                    "window_thermal_conductivity": {"type": "number", "title": "Теплопроводность окон (Вт/(м²·К))", "default": 2.8},
                    "floor_area": {"type": "number", "title": "Площадь пола (м²)"},
                    "floor_thickness": {"type": "number", "title": "Толщина пола (м)", "default": 0.2},
                    "floor_thermal_conductivity": {"type": "number", "title": "Теплопроводность пола (Вт/(м·К))", "default": 1.5},
                    "ceiling_area": {"type": "number", "title": "Площадь потолка (м²)"},
                    "ceiling_thickness": {"type": "number", "title": "Толщина потолка (м)", "default": 0.3},
                    "ceiling_thermal_conductivity": {"type": "number", "title": "Теплопроводность потолка (Вт/(м·К))", "default": 0.8},
                    "indoor_temperature": {"type": "number", "title": "Внутренняя температура (°C)", "default": 20},
                    "outdoor_temperature": {"type": "number", "title": "Наружная температура (°C)", "default": -25},
                    "relative_humidity": {"type": "number", "title": "Относительная влажность (%)", "default": 55},
                    "wind_speed": {"type": "number", "title": "Скорость ветра (м/с)", "default": 5.0},
                    "air_exchange_rate": {"type": "number", "title": "Кратность воздухообмена (1/ч)", "default": 0.5},
                    "heat_emission_people": {"type": "number", "title": "Тепловыделения от людей (Вт)", "default": 0},
                    "heat_emission_equipment": {"type": "number", "title": "Тепловыделения от оборудования (Вт)", "default": 0},
                    "heat_emission_lighting": {"type": "number", "title": "Тепловыделения от освещения (Вт)", "default": 0},
                    "normative_heat_transfer_resistance": {"type": "number", "title": "Нормативное сопротивление теплопередаче (м²·К/Вт)", "default": 3.2},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 50.13330.2012"}
                },
                "required": ["building_type", "building_area", "building_volume", "number_of_floors", 
                           "wall_thickness", "wall_material", "thermal_conductivity", "wall_area", 
                           "floor_area", "ceiling_area"]
            },
            "ventilation": {
                "type": "object",
                "properties": {
                    "room_volume": {"type": "number", "title": "Объем помещения (м³)"},
                    "room_area": {"type": "number", "title": "Площадь помещения (м²)"},
                    "room_height": {"type": "number", "title": "Высота помещения (м)"},
                    "room_type": {"type": "string", "title": "Тип помещения", "enum": ["жилое", "общественное", "производственное"]},
                    "occupancy": {"type": "integer", "title": "Количество людей в помещении", "default": 1},
                    "air_exchange_rate": {"type": "number", "title": "Кратность воздухообмена (1/ч)"},
                    "air_exchange_per_person": {"type": "number", "title": "Воздухообмен на человека (м³/ч·чел)"},
                    "air_exchange_per_area": {"type": "number", "title": "Воздухообмен на площадь (м³/ч·м²)"},
                    "supply_air_temperature": {"type": "number", "title": "Температура приточного воздуха (°C)", "default": 20},
                    "exhaust_air_temperature": {"type": "number", "title": "Температура вытяжного воздуха (°C)", "default": 22},
                    "outdoor_temperature": {"type": "number", "title": "Температура наружного воздуха (°C)", "default": -25},
                    "co2_emission_per_person": {"type": "number", "title": "Выделение CO₂ на человека (м³/ч)", "default": 0.02},
                    "moisture_emission_per_person": {"type": "number", "title": "Выделение влаги на человека (кг/ч)", "default": 0.05},
                    "heat_emission_per_person": {"type": "number", "title": "Тепловыделения на человека (Вт)", "default": 120},
                    "heat_emission_from_equipment": {"type": "number", "title": "Тепловыделения от оборудования (Вт)", "default": 0},
                    "relative_humidity": {"type": "number", "title": "Относительная влажность (%)", "default": 50},
                    "air_velocity": {"type": "number", "title": "Скорость движения воздуха (м/с)", "default": 0.2},
                    "air_density": {"type": "number", "title": "Плотность воздуха (кг/м³)", "default": 1.2},
                    "specific_heat": {"type": "number", "title": "Удельная теплоемкость воздуха (Дж/(кг·К))", "default": 1005},
                    "ventilation_type": {"type": "string", "title": "Тип вентиляции", "enum": ["natural", "mechanical", "mixed"], "default": "mechanical"},
                    "heat_recovery_efficiency": {"type": "number", "title": "КПД рекуперации тепла (0-1)", "default": 0},
                    "fan_efficiency": {"type": "number", "title": "КПД вентилятора (0-1)", "default": 0.7},
                    "smoke_ventilation_required": {"type": "boolean", "title": "Требуется ли противодымная вентиляция", "default": False},
                    "evacuation_route": {"type": "boolean", "title": "Является ли помещение эвакуационным путем", "default": False},
                    "fire_compartment_area": {"type": "number", "title": "Площадь пожарного отсека (м²)"},
                    "noise_level_limit": {"type": "number", "title": "Предельный уровень шума (дБА)", "default": 40},
                    "energy_efficiency_class": {"type": "string", "title": "Класс энергоэффективности", "enum": ["A", "B", "C", "D", "E"], "default": "B"},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 60.13330.2016"}
                },
                "required": ["room_volume", "room_area", "room_height", "room_type"]
            },
            "degasification": {
                "type": "object",
                "properties": {
                    "mine_depth": {"type": "number", "title": "Глубина шахты (м)"},
                    "mine_area": {"type": "number", "title": "Площадь шахты (м²)"},
                    "coal_seam_thickness": {"type": "number", "title": "Мощность угольного пласта (м)"},
                    "methane_content": {"type": "number", "title": "Содержание метана в угле (%)"},
                    "extraction_rate": {"type": "number", "title": "Скорость отработки (м/сут)"},
                    "methane_emission_rate": {"type": "number", "title": "Интенсивность выделения метана (м³/т)"},
                    "ventilation_air_flow": {"type": "number", "title": "Расход вентиляционного воздуха (м³/с)"},
                    "methane_concentration_limit": {"type": "number", "title": "Предельная концентрация метана (%)", "default": 1.0},
                    "safety_factor": {"type": "number", "title": "Коэффициент безопасности", "default": 2.0},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "ГОСТ Р 55154-2012"},
                    "safety_requirements": {"type": "string", "title": "Правила безопасности", "default": "ПБ 05-618-03"}
                },
                "required": ["mine_depth", "mine_area", "coal_seam_thickness", "methane_content", 
                           "extraction_rate", "methane_emission_rate", "ventilation_air_flow"]
            },
            "electrical": {
                "type": "object",
                "properties": {
                    "building_type": {"type": "string", "title": "Тип здания", "enum": ["жилое", "общественное"]},
                    "total_area": {"type": "number", "title": "Общая площадь здания (м²)"},
                    "number_of_floors": {"type": "integer", "title": "Количество этажей"},
                    "number_of_apartments": {"type": "integer", "title": "Количество квартир", "default": 0},
                    "lighting_load": {"type": "number", "title": "Нагрузка освещения (Вт/м²)"},
                    "power_load": {"type": "number", "title": "Силовая нагрузка (Вт/м²)"},
                    "heating_load": {"type": "number", "title": "Нагрузка отопления (Вт/м²)", "default": 0},
                    "ventilation_load": {"type": "number", "title": "Нагрузка вентиляции (Вт/м²)", "default": 0},
                    "demand_factor": {"type": "number", "title": "Коэффициент спроса", "default": 0.7},
                    "diversity_factor": {"type": "number", "title": "Коэффициент разновременности", "default": 0.8},
                    "power_factor": {"type": "number", "title": "Коэффициент мощности", "default": 0.9},
                    "load_current": {"type": "number", "title": "Расчетный ток нагрузки (А)"},
                    "voltage": {"type": "number", "title": "Номинальное напряжение (В)", "default": 380},
                    "power": {"type": "number", "title": "Мощность нагрузки (кВт)"},
                    "cable_length": {"type": "number", "title": "Длина кабеля (м)"},
                    "soil_resistivity": {"type": "number", "title": "Удельное сопротивление грунта (Ом·м)"},
                    "building_height": {"type": "number", "title": "Высота здания (м)"},
                    "building_length": {"type": "number", "title": "Длина здания (м)"},
                    "building_width": {"type": "number", "title": "Ширина здания (м)"},
                    "annual_electricity_consumption": {"type": "number", "title": "Годовое потребление электроэнергии (кВт·ч)"},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 31.110-2003"}
                },
                "required": ["building_type", "total_area", "number_of_floors", "lighting_load", "power_load"]
            },
            "water_supply": {
                "type": "object",
                "properties": {
                    "building_type": {"type": "string", "title": "Тип здания", "enum": ["жилое", "общественное", "производственное"]},
                    "building_area": {"type": "number", "title": "Площадь здания (м²)"},
                    "number_of_floors": {"type": "integer", "title": "Количество этажей"},
                    "number_of_apartments": {"type": "integer", "title": "Количество квартир", "default": 0},
                    "number_of_people": {"type": "integer", "title": "Количество людей"},
                    "water_consumption_per_person": {"type": "number", "title": "Норма водопотребления на человека (л/сут)", "default": 200},
                    "hot_water_consumption_per_person": {"type": "number", "title": "Норма горячей воды на человека (л/сут)", "default": 100},
                    "cold_water_consumption_per_person": {"type": "number", "title": "Норма холодной воды на человека (л/сут)", "default": 100},
                    "consumption_coefficient": {"type": "number", "title": "Коэффициент неравномерности потребления", "default": 1.2},
                    "simultaneity_coefficient": {"type": "number", "title": "Коэффициент одновременности", "default": 0.3},
                    "peak_coefficient": {"type": "number", "title": "Коэффициент пикового потребления", "default": 2.5},
                    "water_pressure": {"type": "number", "title": "Требуемое давление воды (МПа)", "default": 0.3},
                    "pipe_diameter": {"type": "number", "title": "Диаметр трубопровода (м)", "default": 0.05},
                    "pipe_length": {"type": "number", "title": "Длина трубопровода (м)", "default": 100},
                    "pipe_material": {"type": "string", "title": "Материал трубопровода", "default": "сталь"},
                    "sewage_flow_rate": {"type": "number", "title": "Расход сточных вод (л/с)", "default": 0.8},
                    "sewage_concentration": {"type": "number", "title": "Концентрация загрязнений (мг/л)", "default": 500},
                    "treatment_efficiency": {"type": "number", "title": "Эффективность очистки", "default": 0.95},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 30.13330.2016"}
                },
                "required": ["building_type", "building_area", "number_of_floors", "number_of_people"]
            },
            "fire_safety": {
                "type": "object",
                "properties": {
                    "building_type": {"type": "string", "title": "Тип здания", "enum": ["жилое", "общественное", "производственное"]},
                    "building_area": {"type": "number", "title": "Площадь здания (м²)"},
                    "building_volume": {"type": "number", "title": "Объем здания (м³)"},
                    "number_of_floors": {"type": "integer", "title": "Количество этажей"},
                    "building_height": {"type": "number", "title": "Высота здания (м)"},
                    "fire_resistance_rating": {"type": "string", "title": "Степень огнестойкости", "enum": ["I", "II", "III", "IV", "V"], "default": "II"},
                    "fire_compartment_area": {"type": "number", "title": "Площадь пожарного отсека (м²)", "default": 1000},
                    "evacuation_time": {"type": "number", "title": "Время эвакуации (с)", "default": 300},
                    "evacuation_capacity": {"type": "integer", "title": "Вместимость эвакуационных путей (чел)", "default": 100},
                    "sprinkler_density": {"type": "number", "title": "Плотность орошения спринклерами (л/(с·м²))", "default": 0.12},
                    "fire_hydrant_flow": {"type": "number", "title": "Расход пожарного гидранта (л/с)", "default": 2.5},
                    "fire_extinguisher_count": {"type": "integer", "title": "Количество огнетушителей", "default": 10},
                    "smoke_detector_count": {"type": "integer", "title": "Количество дымовых извещателей", "default": 50},
                    "evacuation_route_width": {"type": "number", "title": "Ширина эвакуационного пути (м)", "default": 1.2},
                    "evacuation_route_length": {"type": "number", "title": "Длина эвакуационного пути (м)", "default": 50},
                    "emergency_exit_count": {"type": "integer", "title": "Количество аварийных выходов", "default": 4},
                    "fire_load_density": {"type": "number", "title": "Плотность пожарной нагрузки (МДж/м²)", "default": 50},
                    "smoke_generation_rate": {"type": "number", "title": "Скорость образования дыма (кг/с)", "default": 0.1},
                    "heat_release_rate": {"type": "number", "title": "Скорость тепловыделения (кВт)", "default": 1000},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 4.13130.2013"}
                },
                "required": ["building_type", "building_area", "building_volume", "number_of_floors", "building_height"]
            },
            "acoustic": {
                "type": "object",
                "properties": {
                    "room_type": {"type": "string", "title": "Тип помещения", "enum": ["жилое", "общественное", "производственное"]},
                    "room_area": {"type": "number", "title": "Площадь помещения (м²)"},
                    "room_volume": {"type": "number", "title": "Объем помещения (м³)"},
                    "room_height": {"type": "number", "title": "Высота помещения (м)"},
                    "noise_level_limit": {"type": "number", "title": "Предельный уровень шума (дБА)", "default": 40},
                    "background_noise_level": {"type": "number", "title": "Уровень фонового шума (дБА)", "default": 35},
                    "noise_source_power": {"type": "number", "title": "Мощность источника шума (дБ)", "default": 80},
                    "noise_source_distance": {"type": "number", "title": "Расстояние до источника шума (м)", "default": 5},
                    "wall_thickness": {"type": "number", "title": "Толщина стены (м)", "default": 0.2},
                    "wall_material": {"type": "string", "title": "Материал стены", "default": "бетон"},
                    "wall_sound_insulation": {"type": "number", "title": "Звукоизоляция стены (дБ)", "default": 50},
                    "floor_sound_insulation": {"type": "number", "title": "Звукоизоляция пола (дБ)", "default": 55},
                    "ceiling_sound_insulation": {"type": "number", "title": "Звукоизоляция потолка (дБ)", "default": 60},
                    "sound_absorption_coefficient": {"type": "number", "title": "Коэффициент звукопоглощения", "default": 0.3},
                    "reverberation_time": {"type": "number", "title": "Время реверберации (с)", "default": 0.8},
                    "acoustic_treatment_area": {"type": "number", "title": "Площадь акустической обработки (м²)", "default": 0},
                    "vibration_level": {"type": "number", "title": "Уровень вибрации (дБ)", "default": 70},
                    "vibration_frequency": {"type": "number", "title": "Частота вибрации (Гц)", "default": 50},
                    "vibration_insulation": {"type": "number", "title": "Виброизоляция (дБ)", "default": 20},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 51.13330.2011"}
                },
                "required": ["room_type", "room_area", "room_volume", "room_height"]
            },
            "lighting": {
                "type": "object",
                "properties": {
                    "room_type": {"type": "string", "title": "Тип помещения", "enum": ["жилое", "общественное", "производственное"]},
                    "room_area": {"type": "number", "title": "Площадь помещения (м²)"},
                    "room_height": {"type": "number", "title": "Высота помещения (м)"},
                    "room_length": {"type": "number", "title": "Длина помещения (м)"},
                    "room_width": {"type": "number", "title": "Ширина помещения (м)"},
                    "required_illuminance": {"type": "number", "title": "Нормативная освещенность (лк)", "default": 300},
                    "lighting_type": {"type": "string", "title": "Тип освещения", "enum": ["естественное", "искусственное", "комбинированное"], "default": "искусственное"},
                    "light_source_type": {"type": "string", "title": "Тип источника света", "enum": ["LED", "люминесцентные", "накаливания"], "default": "LED"},
                    "light_source_power": {"type": "number", "title": "Мощность источника света (Вт)", "default": 20},
                    "light_source_efficiency": {"type": "number", "title": "Световая отдача (лм/Вт)", "default": 100},
                    "window_area": {"type": "number", "title": "Площадь окон (м²)", "default": 0},
                    "window_height": {"type": "number", "title": "Высота окон (м)", "default": 1.5},
                    "window_width": {"type": "number", "title": "Ширина окон (м)", "default": 1.2},
                    "window_count": {"type": "integer", "title": "Количество окон", "default": 0},
                    "window_orientation": {"type": "string", "title": "Ориентация окон", "enum": ["север", "юг", "восток", "запад"], "default": "юг"},
                    "shading_factor": {"type": "number", "title": "Коэффициент затенения", "default": 0.8},
                    "insolation_duration": {"type": "number", "title": "Продолжительность инсоляции (ч)", "default": 3},
                    "insolation_angle": {"type": "number", "title": "Угол инсоляции (градусы)", "default": 30},
                    "building_spacing": {"type": "number", "title": "Расстояние между зданиями (м)", "default": 20},
                    "building_height_adjacent": {"type": "number", "title": "Высота соседнего здания (м)", "default": 15},
                    "luminaire_count": {"type": "integer", "title": "Количество светильников", "default": 0},
                    "luminaire_efficiency": {"type": "number", "title": "КПД светильника", "default": 0.8},
                    "luminaire_height": {"type": "number", "title": "Высота подвеса светильников (м)", "default": 2.5},
                    "luminaire_spacing": {"type": "number", "title": "Шаг светильников (м)", "default": 3},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 52.13330.2016"}
                },
                "required": ["room_type", "room_area", "room_height", "room_length", "room_width"]
            },
            "geological": {
                "type": "object",
                "properties": {
                    "site_area": {"type": "number", "title": "Площадь участка (м²)"},
                    "site_length": {"type": "number", "title": "Длина участка (м)"},
                    "site_width": {"type": "number", "title": "Ширина участка (м)"},
                    "groundwater_level": {"type": "number", "title": "Уровень грунтовых вод (м)", "default": 2},
                    "soil_type": {"type": "string", "title": "Тип грунта", "enum": ["глина", "песок", "суглинок", "супесь"]},
                    "soil_density": {"type": "number", "title": "Плотность грунта (кг/м³)", "default": 1800},
                    "soil_moisture": {"type": "number", "title": "Влажность грунта (%)", "default": 15},
                    "soil_plasticity_index": {"type": "number", "title": "Показатель пластичности", "default": 10},
                    "soil_consistency": {"type": "string", "title": "Консистенция грунта", "enum": ["твердая", "полутвердая", "мягкопластичная"], "default": "твердая"},
                    "compression_modulus": {"type": "number", "title": "Модуль деформации (МПа)", "default": 10},
                    "angle_of_internal_friction": {"type": "number", "title": "Угол внутреннего трения (градусы)", "default": 25},
                    "cohesion": {"type": "number", "title": "Сцепление (кПа)", "default": 20},
                    "bearing_capacity": {"type": "number", "title": "Несущая способность (кПа)", "default": 200},
                    "foundation_type": {"type": "string", "title": "Тип фундамента", "enum": ["ленточный", "плитный", "свайный"], "default": "ленточный"},
                    "foundation_width": {"type": "number", "title": "Ширина фундамента (м)", "default": 0.6},
                    "foundation_depth": {"type": "number", "title": "Глубина заложения фундамента (м)", "default": 1.5},
                    "foundation_length": {"type": "number", "title": "Длина фундамента (м)", "default": 20},
                    "building_weight": {"type": "number", "title": "Вес здания (кН)", "default": 1000},
                    "live_load": {"type": "number", "title": "Полезная нагрузка (кН/м²)", "default": 200},
                    "snow_load": {"type": "number", "title": "Снеговая нагрузка (кН/м²)", "default": 100},
                    "wind_load": {"type": "number", "title": "Ветровая нагрузка (кН/м²)", "default": 50},
                    "seismic_intensity": {"type": "integer", "title": "Сейсмическая интенсивность (баллы)", "default": 6},
                    "seismic_coefficient": {"type": "number", "title": "Сейсмический коэффициент", "default": 0.1},
                    "normative_document": {"type": "string", "title": "Нормативный документ", "default": "СП 22.13330.2016"}
                },
                "required": ["site_area", "site_length", "site_width", "soil_type"]
            }
        }
        return schemas.get(calculation_type, {})
    
    def _get_category_name(self, category: str) -> str:
        """Получение названия категории"""
        names = {
            "beam": "Балки",
            "column": "Колонны", 
            "slab": "Плиты",
            "foundation": "Фундаменты",
            "bearing_capacity": "Несущая способность",
            "settlement": "Осадки",
            "stability": "Устойчивость",
            "heat_loss": "Теплопотери",
            "thermal_insulation": "Теплоизоляция",
            "condensation": "Конденсация",
            "air_flow": "Воздухообмен",
            "heat_recovery": "Рекуперация тепла",
            "air_conditioning": "Кондиционирование",
            "methane_extraction": "Извлечение метана",
            "ventilation_requirements": "Требования вентиляции",
            "safety_systems": "Системы безопасности",
            "electrical_loads": "Электрические нагрузки",
            "cable_calculation": "Расчет кабелей",
            "grounding": "Заземление",
            "lightning_protection": "Молниезащита",
            "energy_efficiency": "Энергоэффективность",
            "water_consumption": "Водопотребление",
            "pipe_calculation": "Расчет трубопроводов",
            "sewage_treatment": "Очистка сточных вод",
            "water_pressure": "Давление воды",
            "drainage": "Дренаж",
            "evacuation": "Эвакуация",
            "fire_suppression": "Пожаротушение",
            "smoke_control": "Противодымная защита",
            "fire_resistance": "Огнестойкость",
            "emergency_systems": "Аварийные системы",
            "sound_insulation": "Звукоизоляция",
            "noise_control": "Контроль шума",
            "vibration_control": "Виброизоляция",
            "acoustic_treatment": "Акустическая обработка",
            "reverberation": "Реверберация",
            "artificial_lighting": "Искусственное освещение",
            "natural_lighting": "Естественное освещение",
            "insolation": "Инсоляция",
            "luminaire_calculation": "Расчет светильников",
            "bearing_capacity": "Несущая способность",
            "settlement": "Осадки",
            "slope_stability": "Устойчивость склонов",
            "seismic_analysis": "Сейсмический анализ",
            "groundwater": "Грунтовые воды"
        }
        return names.get(category, category)
    
    def _get_category_description(self, category: str) -> str:
        """Получение описания категории"""
        descriptions = {
            "beam": "Расчеты балок на прочность и жесткость",
            "column": "Расчеты колонн на сжатие и устойчивость",
            "slab": "Расчеты плит на изгиб и прогиб",
            "foundation": "Расчеты фундаментов на несущую способность",
            "bearing_capacity": "Расчет несущей способности оснований",
            "settlement": "Расчет осадок фундаментов",
            "stability": "Расчет устойчивости откосов и склонов",
            "heat_loss": "Расчет теплопотерь через ограждающие конструкции",
            "thermal_insulation": "Расчет теплоизоляции зданий",
            "condensation": "Расчет конденсации влаги в конструкциях",
            "air_exchange": "Расчет воздухообмена по вредным выделениям (СП 60.13330.2016)",
            "smoke_ventilation": "Расчет противодымной вентиляции (СП 7.13130.2013)",
            "residential_ventilation": "Расчет вентиляции жилых зданий (СП 54.13330.2016)",
            "energy_efficiency": "Расчет энергоэффективности вентиляционных систем",
            "acoustic_calculations": "Акустические расчеты вентиляционных систем",
            "heat_recovery": "Расчет рекуперации тепла в системах вентиляции",
            "air_conditioning": "Расчет систем кондиционирования воздуха",
            "methane_extraction": "Расчет систем извлечения метана из угольных пластов",
            "ventilation_requirements": "Расчет требований к вентиляции шахт",
            "safety_systems": "Расчет систем безопасности и газового контроля",
            "electrical_loads": "Расчет электрических нагрузок зданий (СП 31.110-2003)",
            "cable_calculation": "Расчет сечений проводов и кабелей (СП 31.110-2003)",
            "grounding": "Расчет заземления и зануления (СП 31.110-2003)",
            "lightning_protection": "Расчет молниезащиты зданий (СП 437.1325800.2018)",
            "energy_efficiency": "Расчет энергоэффективности электротехнических систем (СП 256.1325800.2016)",
            "water_consumption": "Расчет водопотребления зданий (СП 30.13330.2016)",
            "pipe_calculation": "Расчет диаметров трубопроводов водоснабжения (СП 30.13330.2016)",
            "sewage_treatment": "Расчет систем очистки сточных вод (СП 32.13330.2018)",
            "water_pressure": "Расчет давления в системах водоснабжения (СП 30.13330.2016)",
            "drainage": "Расчет систем водоотведения (СП 32.13330.2018)",
            "evacuation": "Расчет эвакуационных путей и выходов (СП 1.13130.2020)",
            "fire_suppression": "Расчет систем пожаротушения (СП 5.13130.2009)",
            "smoke_control": "Расчет противодымной защиты (СП 7.13130.2013)",
            "fire_resistance": "Расчет огнестойкости конструкций (СП 2.13130.2020)",
            "emergency_systems": "Расчет аварийных систем безопасности (СП 4.13130.2013)",
            "sound_insulation": "Расчет звукоизоляции ограждающих конструкций (СП 51.13330.2011)",
            "noise_control": "Расчет защиты от шума (СП 51.13330.2011)",
            "vibration_control": "Расчет виброизоляции оборудования (СП 51.13330.2011)",
            "acoustic_treatment": "Расчет акустической обработки помещений (СП 51.13330.2011)",
            "reverberation": "Расчет времени реверберации (СП 51.13330.2011)",
            "artificial_lighting": "Расчет искусственного освещения (СП 52.13330.2016)",
            "natural_lighting": "Расчет естественного освещения (СП 52.13330.2016)",
            "insolation": "Расчет инсоляции помещений (СП 52.13330.2016)",
            "luminaire_calculation": "Расчет размещения светильников (СП 52.13330.2016)",
            "bearing_capacity": "Расчет несущей способности грунтов (СП 22.13330.2016)",
            "settlement": "Расчет осадок фундаментов (СП 22.13330.2016)",
            "slope_stability": "Расчет устойчивости склонов (СП 22.13330.2016)",
            "seismic_analysis": "Сейсмический анализ оснований (СП 14.13330.2018)",
            "groundwater": "Расчет влияния грунтовых вод (СП 22.13330.2016)"
        }
        return descriptions.get(category, f"Расчеты категории {category}")
    
    def execute_calculation(self, calculation_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета"""
        start_time = time.time()
        
        try:
            # Получение расчета из базы данных
            calculation = db_manager.get_calculation(calculation_id)
            if not calculation:
                raise ValueError(f"Calculation {calculation_id} not found")
            
            logger.info(f"🔍 [DEBUG] Calculation object: {calculation}")
            logger.info(f"🔍 [DEBUG] Calculation type: {calculation.type}, ID: {calculation_id}")
            logger.info(f"🔍 [DEBUG] Calculation type class: {type(calculation.type)}")
            
            # Обновление статуса на "выполняется"
            db_manager.update_calculation_results(calculation_id, {}, "running")
            
            # Выполнение расчета в зависимости от типа
            if calculation.type == "structural":
                results = self._execute_structural_calculation(parameters)
            elif calculation.type == "dynamic":
                # Динамический расчет - это подтип структурного расчета
                parameters['calculation_type'] = 'dynamic'
                results = self._execute_structural_calculation(parameters)
            elif calculation.type == "strength":
                # Расчет на прочность - это подтип структурного расчета
                parameters['calculation_type'] = 'strength'
                results = self._execute_structural_calculation(parameters)
            elif calculation.type == "stability":
                # Расчет на устойчивость - это подтип структурного расчета
                parameters['calculation_type'] = 'stability'
                results = self._execute_structural_calculation(parameters)
            elif calculation.type == "stiffness":
                # Расчет на жесткость - это подтип структурного расчета
                parameters['calculation_type'] = 'stiffness'
                results = self._execute_structural_calculation(parameters)
            elif calculation.type == "cracking":
                # Расчет на трещиностойкость - это подтип структурного расчета
                parameters['calculation_type'] = 'cracking'
                results = self._execute_structural_calculation(parameters)
            elif calculation.type == "foundation":
                results = self._execute_foundation_calculation(parameters)
            elif calculation.type == "thermal":
                results = self._execute_thermal_calculation(parameters)
            elif calculation.type == "ventilation":
                results = self._execute_ventilation_calculation(parameters)
            elif calculation.type == "degasification":
                # Преобразование параметров в модель
                degas_params = DegasificationCalculationParams(**parameters)
                results = self._execute_degasification_calculation(degas_params)
            elif calculation.type == "electrical":
                results = self._execute_electrical_calculation(parameters)
            elif calculation.type == "water_supply":
                results = self._execute_water_supply_calculation(parameters)
            elif calculation.type == "fire_safety":
                results = self._execute_fire_safety_calculation(parameters)
            elif calculation.type == "acoustic":
                results = self._execute_acoustic_calculation(parameters)
            elif calculation.type == "lighting":
                results = self._execute_lighting_calculation(parameters)
            elif calculation.type == "geological":
                results = self._execute_geological_calculation(parameters)
            else:
                raise ValueError(f"Unknown calculation type: {calculation.type}")
            
            # Добавление метаданных
            execution_time = time.time() - start_time
            results.update({
                "execution_time": execution_time,
                "calculation_id": calculation_id,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            })
            
            # Сохранение результатов
            db_manager.update_calculation_results(calculation_id, results, "completed")
            
            logger.info(f"✅ Calculation {calculation_id} completed in {execution_time:.2f}s")
            return results
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_results = {
                "error": str(e),
                "execution_time": execution_time,
                "calculation_id": calculation_id,
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            db_manager.update_calculation_results(calculation_id, error_results, "failed")
            logger.error(f"❌ Calculation {calculation_id} failed: {e}")
            raise
    
    def execute_calculation_by_type(self, calculation_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета по типу (для совместимости с фронтендом)"""
        start_time = time.time()
        
        try:
            # Выполнение расчета в зависимости от типа
            if calculation_type == "structural":
                results = self._execute_structural_calculation(parameters)
            elif calculation_type == "dynamic":
                # Динамический расчет - это подтип структурного расчета
                # Устанавливаем тип расчета в параметрах
                parameters['calculation_type'] = 'dynamic'
                results = self._execute_structural_calculation(parameters)
            elif calculation_type == "strength":
                # Расчет на прочность - это подтип структурного расчета
                parameters['calculation_type'] = 'strength'
                results = self._execute_structural_calculation(parameters)
            elif calculation_type == "stability":
                # Расчет на устойчивость - это подтип структурного расчета
                parameters['calculation_type'] = 'stability'
                results = self._execute_structural_calculation(parameters)
            elif calculation_type == "stiffness":
                # Расчет на жесткость - это подтип структурного расчета
                parameters['calculation_type'] = 'stiffness'
                results = self._execute_structural_calculation(parameters)
            elif calculation_type == "cracking":
                # Расчет на трещиностойкость - это подтип структурного расчета
                parameters['calculation_type'] = 'cracking'
                results = self._execute_structural_calculation(parameters)
            elif calculation_type == "foundation":
                results = self._execute_foundation_calculation(parameters)
            elif calculation_type == "thermal":
                results = self._execute_thermal_calculation(parameters)
            elif calculation_type == "ventilation":
                results = self._execute_ventilation_calculation(parameters)
            elif calculation_type == "degasification":
                # Преобразование параметров в модель
                degas_params = DegasificationCalculationParams(**parameters)
                results = self._execute_degasification_calculation(degas_params)
            elif calculation_type == "electrical":
                results = self._execute_electrical_calculation(parameters)
            elif calculation_type == "water_supply":
                results = self._execute_water_supply_calculation(parameters)
            elif calculation_type == "fire_safety":
                results = self._execute_fire_safety_calculation(parameters)
            elif calculation_type == "acoustic":
                results = self._execute_acoustic_calculation(parameters)
            elif calculation_type == "lighting":
                results = self._execute_lighting_calculation(parameters)
            elif calculation_type == "geological":
                results = self._execute_geological_calculation(parameters)
            else:
                raise ValueError(f"Unknown calculation type: {calculation_type}")
            
            # Добавление метаданных
            execution_time = time.time() - start_time
            results.update({
                "execution_time": execution_time,
                "calculation_type": calculation_type,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            })
            
            logger.info(f"✅ Calculation type {calculation_type} completed in {execution_time:.2f}s")
            return results
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_results = {
                "error": str(e),
                "execution_time": execution_time,
                "calculation_type": calculation_type,
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            logger.error(f"❌ Calculation type {calculation_type} failed: {e}")
            raise
    
    def _execute_structural_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета строительных конструкций"""
        try:
            # Проверяем тип расчета
            calculation_type = parameters.get('calculation_type', 'strength')
            
            if calculation_type == 'dynamic':
                return self._execute_dynamic_calculation(parameters)
            elif calculation_type == 'strength':
                return self._execute_strength_calculation(parameters)
            elif calculation_type == 'stability':
                return self._execute_stability_calculation(parameters)
            elif calculation_type == 'stiffness':
                return self._execute_stiffness_calculation(parameters)
            elif calculation_type == 'cracking':
                return self._execute_cracking_calculation(parameters)
            else:
                # По умолчанию выполняем расчет на прочность
                return self._execute_strength_calculation(parameters)
            
        except Exception as e:
            logger.error(f"❌ Structural calculation error: {e}")
            raise
    
    def _execute_dynamic_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение динамического расчета на сейсмические воздействия"""
        try:
            # Извлекаем параметры
            seismic_zone = int(parameters.get('seismic_zone', 6))
            soil_category = parameters.get('soil_category', 'B')
            structure_weight = float(parameters.get('structure_weight', 100.0))
            natural_period = float(parameters.get('natural_period', 0.5))
            
            # Коэффициенты сейсмичности по СП 14.13330
            seismic_coefficients = {
                6: 0.05,
                7: 0.1,
                8: 0.2,
                9: 0.4
            }
            
            # Коэффициенты грунта
            soil_coefficients = {
                'A': 1.0,  # Скальные грунты
                'B': 1.2,  # Плотные грунты
                'C': 1.5,  # Средние грунты
                'D': 2.0   # Слабые грунты
            }
            
            # Базовый коэффициент сейсмичности
            base_seismic_coefficient = seismic_coefficients.get(seismic_zone, 0.05)
            
            # Коэффициент грунта
            soil_coefficient = soil_coefficients.get(soil_category, 1.2)
            
            # Коэффициент динамичности
            if natural_period <= 0.4:
                dynamic_coefficient = 1.0 + 0.1 * seismic_zone
            elif natural_period <= 0.8:
                dynamic_coefficient = 1.0 + 0.2 * seismic_zone
            else:
                dynamic_coefficient = 1.0 + 0.3 * seismic_zone
            
            # Итоговый коэффициент сейсмичности
            seismic_coefficient = base_seismic_coefficient * soil_coefficient * dynamic_coefficient
            
            # Сейсмическая нагрузка
            seismic_load = seismic_coefficient * structure_weight * 9.81  # кН
            
            # Проверка на сейсмическую устойчивость
            # Предполагаем, что конструкция выдерживает нагрузку, если коэффициент сейсмичности < 0.3
            stability_check = seismic_coefficient < 0.3
            
            return {
                "seismic_zone": seismic_zone,
                "soil_category": soil_category,
                "base_seismic_coefficient": base_seismic_coefficient,
                "soil_coefficient": soil_coefficient,
                "dynamic_coefficient": dynamic_coefficient,
                "seismic_coefficient": seismic_coefficient,
                "seismic_load": seismic_load,
                "structure_weight": structure_weight,
                "natural_period": natural_period,
                "stability_check": stability_check,
                "normative_links": {
                    "СП 14.13330": "Строительство в сейсмических районах",
                    "EN 1998": "Еврокод 8: Проектирование сейсмостойких конструкций"
                },
                "safety_recommendations": [
                    "Увеличить жесткость конструкции для уменьшения периода колебаний",
                    "Применить демпфирующие устройства",
                    "Усилить узлы соединения элементов",
                    "Провести дополнительный расчет на сейсмические воздействия"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Dynamic calculation error: {e}")
            raise
    
    def _execute_strength_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета на прочность"""
        try:
            # Проверяем, есть ли все необходимые параметры для структурного расчета
            required_params = ['beam_length', 'beam_width', 'beam_height', 'material_strength', 'load_value']
            if not all(param in parameters for param in required_params):
                # Если нет всех параметров, используем значения по умолчанию
                default_params = {
                    'beam_length': 6.0,
                    'beam_width': 0.2,
                    'beam_height': 0.4,
                    'material_strength': 235.0,
                    'load_value': 10.0,
                    'safety_factor': 1.1,
                    'deflection_limit': 1/250
                }
                # Объединяем параметры с значениями по умолчанию
                params_dict = {**default_params, **parameters}
                params = StructuralCalculationParams(**params_dict)
            else:
                params = StructuralCalculationParams(**parameters)
            
            # Расчет момента инерции
            I = (params.beam_width * params.beam_height**3) / 12
            
            # Расчет максимального момента
            M_max = (params.load_value * params.beam_length**2) / 8
            
            # Расчет максимального напряжения
            sigma_max = (M_max * params.beam_height / 2) / I
            
            # Проверка прочности
            sigma_allowable = params.material_strength / params.safety_factor
            strength_check = sigma_max <= sigma_allowable
            
            # Расчет прогиба
            E = 200000  # Модуль упругости стали (МПа)
            deflection = (5 * params.load_value * params.beam_length**4) / (384 * E * I)
            deflection_check = deflection <= (params.beam_length * params.deflection_limit)
            
            return {
                "moment_of_inertia": I,
                "max_moment": M_max,
                "max_stress": sigma_max,
                "allowable_stress": sigma_allowable,
                "strength_check": strength_check,
                "deflection": deflection,
                "deflection_limit": params.beam_length * params.deflection_limit,
                "deflection_check": deflection_check,
                "safety_factor_used": params.safety_factor
            }
            
        except Exception as e:
            logger.error(f"❌ Strength calculation error: {e}")
            raise
    
    def _execute_stability_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета на устойчивость"""
        try:
            # Извлекаем параметры
            element_length = float(parameters.get('element_length', 3.0))
            moment_of_inertia = float(parameters.get('moment_of_inertia', 1000.0))
            elastic_modulus = float(parameters.get('elastic_modulus', 210000.0))
            end_conditions = parameters.get('end_conditions', 'pinned')
            
            # Коэффициенты длины для разных типов закрепления
            length_coefficients = {
                'pinned': 1.0,      # Шарнирное
                'fixed': 0.5,       # Жесткое
                'cantilever': 2.0   # Консольное
            }
            
            # Расчетная длина
            design_length = element_length * length_coefficients.get(end_conditions, 1.0)
            
            # Радиус инерции
            radius_of_gyration = (moment_of_inertia / 10000) ** 0.5  # см
            
            # Гибкость
            slenderness = design_length * 100 / radius_of_gyration
            
            # Критическая сила по Эйлеру
            critical_force = (3.14159**2 * elastic_modulus * moment_of_inertia) / (design_length**2)
            
            # Проверка устойчивости (гибкость должна быть < 120 для стали)
            stability_check = slenderness < 120
            
            return {
                "element_length": element_length,
                "design_length": design_length,
                "moment_of_inertia": moment_of_inertia,
                "radius_of_gyration": radius_of_gyration,
                "slenderness": slenderness,
                "critical_force": critical_force,
                "end_conditions": end_conditions,
                "stability_check": stability_check,
                "normative_links": {
                    "СП 16.13330": "Стальные конструкции",
                    "СП 63.13330": "Бетонные и железобетонные конструкции",
                    "EN 1993": "Еврокод 3: Проектирование стальных конструкций"
                },
                "safety_recommendations": [
                    "Увеличить момент инерции сечения",
                    "Уменьшить расчетную длину элемента",
                    "Применить промежуточные связи",
                    "Использовать более жесткое закрепление"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Stability calculation error: {e}")
            raise
    
    def _execute_stiffness_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета на жесткость"""
        try:
            # Извлекаем параметры
            span_length = float(parameters.get('span_length', 6.0))
            distributed_load = float(parameters.get('distributed_load', 10.0))
            moment_of_inertia = float(parameters.get('moment_of_inertia', 5000.0))
            elastic_modulus = float(parameters.get('elastic_modulus', 210000.0))
            
            # Расчет прогиба от распределенной нагрузки
            deflection = (5 * distributed_load * span_length**4) / (384 * elastic_modulus * moment_of_inertia)
            
            # Предельный прогиб (L/250 для балок)
            deflection_limit = span_length / 250
            
            # Проверка жесткости
            stiffness_check = deflection <= deflection_limit
            
            # Расчет угла поворота
            rotation_angle = (distributed_load * span_length**3) / (24 * elastic_modulus * moment_of_inertia)
            
            return {
                "span_length": span_length,
                "distributed_load": distributed_load,
                "moment_of_inertia": moment_of_inertia,
                "elastic_modulus": elastic_modulus,
                "deflection": deflection,
                "deflection_limit": deflection_limit,
                "stiffness_check": stiffness_check,
                "rotation_angle": rotation_angle,
                "normative_links": {
                    "СП 63.13330": "Бетонные и железобетонные конструкции",
                    "СП 64.13330": "Деревянные конструкции",
                    "EN 1995": "Еврокод 5: Проектирование деревянных конструкций"
                },
                "safety_recommendations": [
                    "Увеличить момент инерции сечения",
                    "Уменьшить пролет конструкции",
                    "Применить предварительное напряжение",
                    "Использовать более жесткий материал"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Stiffness calculation error: {e}")
            raise
    
    def _execute_cracking_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета на трещиностойкость"""
        try:
            # Извлекаем параметры
            reinforcement_area = float(parameters.get('reinforcement_area', 1000.0))
            concrete_class = parameters.get('concrete_class', 'B25')
            bending_moment = float(parameters.get('bending_moment', 50.0))
            crack_width_limit = float(parameters.get('crack_width_limit', 0.3))
            
            # Характеристики бетона по классам
            concrete_properties = {
                'B15': {'strength': 15, 'elastic_modulus': 24000},
                'B20': {'strength': 20, 'elastic_modulus': 27500},
                'B25': {'strength': 25, 'elastic_modulus': 30000},
                'B30': {'strength': 30, 'elastic_modulus': 32500},
                'B35': {'strength': 35, 'elastic_modulus': 34500}
            }
            
            concrete_strength = concrete_properties.get(concrete_class, concrete_properties['B25'])['strength']
            concrete_elastic_modulus = concrete_properties.get(concrete_class, concrete_properties['B25'])['elastic_modulus']
            
            # Модуль упругости арматуры
            steel_elastic_modulus = 200000  # МПа
            
            # Коэффициент армирования
            reinforcement_ratio = reinforcement_area / 10000  # в долях единицы
            
            # Расчет ширины раскрытия трещин (упрощенная формула)
            crack_width = (bending_moment * 1000) / (reinforcement_area * steel_elastic_modulus) * 0.1
            
            # Проверка трещиностойкости
            cracking_check = crack_width <= crack_width_limit
            
            return {
                "reinforcement_area": reinforcement_area,
                "concrete_class": concrete_class,
                "concrete_strength": concrete_strength,
                "concrete_elastic_modulus": concrete_elastic_modulus,
                "bending_moment": bending_moment,
                "crack_width": crack_width,
                "crack_width_limit": crack_width_limit,
                "cracking_check": cracking_check,
                "reinforcement_ratio": reinforcement_ratio,
                "normative_links": {
                    "СП 63.13330": "Бетонные и железобетонные конструкции",
                    "EN 1992": "Еврокод 2: Проектирование бетонных конструкций"
                },
                "safety_recommendations": [
                    "Увеличить площадь арматуры",
                    "Использовать бетон более высокого класса",
                    "Применить предварительно напряженную арматуру",
                    "Уменьшить изгибающий момент"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Cracking calculation error: {e}")
            raise
    
    def _execute_foundation_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета оснований и фундаментов"""
        try:
            params = FoundationCalculationParams(**parameters)
            
            # Расчет несущей способности по формуле Терцаги
            import math
            
            # Коэффициенты несущей способности
            N_c = (math.tan(math.radians(45 + params.soil_friction_angle/2))**2 - 1) / math.tan(math.radians(params.soil_friction_angle))
            N_q = math.tan(math.radians(45 + params.soil_friction_angle/2))**2
            N_gamma = 2 * (N_q + 1) * math.tan(math.radians(params.soil_friction_angle))
            
            # Несущая способность
            q_ult = params.soil_cohesion * N_c + params.soil_density * 9.81 * params.foundation_depth * N_q + 0.5 * params.soil_density * 9.81 * params.foundation_width * N_gamma
            
            # Допустимая нагрузка
            q_allowable = q_ult / params.safety_factor
            
            # Площадь фундамента
            foundation_area = params.foundation_width * params.foundation_length
            
            # Допустимая нагрузка на фундамент
            P_allowable = q_allowable * foundation_area
            
            return {
                "bearing_capacity_coefficients": {
                    "N_c": N_c,
                    "N_q": N_q,
                    "N_gamma": N_gamma
                },
                "ultimate_bearing_capacity": q_ult,
                "allowable_bearing_capacity": q_allowable,
                "foundation_area": foundation_area,
                "allowable_load": P_allowable,
                "safety_factor_used": params.safety_factor
            }
            
        except Exception as e:
            logger.error(f"❌ Foundation calculation error: {e}")
            raise
    
    def _execute_thermal_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение теплотехнических расчетов согласно СП 50.13330.2012"""
        try:
            logger.info(f"🔍 [THERMAL] Starting thermal calculation")
            params = ThermalCalculationParams(**parameters)
            
            # 1. РАСЧЕТ ТЕРМИЧЕСКИХ СОПРОТИВЛЕНИЙ ОГРАЖДАЮЩИХ КОНСТРУКЦИЙ
            wall_thermal_resistance = self._calculate_wall_thermal_resistance(params)
            window_thermal_resistance = self._calculate_window_thermal_resistance(params)
            floor_thermal_resistance = self._calculate_floor_thermal_resistance(params)
            ceiling_thermal_resistance = self._calculate_ceiling_thermal_resistance(params)
            
            # 2. РАСЧЕТ КОЭФФИЦИЕНТОВ ТЕПЛОПЕРЕДАЧИ
            heat_transfer_coefficients = self._calculate_heat_transfer_coefficients(
                wall_thermal_resistance, window_thermal_resistance, 
                floor_thermal_resistance, ceiling_thermal_resistance, params
            )
            
            # 3. РАСЧЕТ ТЕПЛОПОТЕРЬ ЧЕРЕЗ ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ
            heat_losses = self._calculate_heat_losses(heat_transfer_coefficients, params)
            
            # 4. РАСЧЕТ ТЕПЛОПОТЕРЬ НА ВЕНТИЛЯЦИЮ
            ventilation_losses = self._calculate_ventilation_heat_losses(params)
            
            # 5. РАСЧЕТ ТЕПЛОВЫДЕЛЕНИЙ
            heat_emissions = self._calculate_heat_emissions(params)
            
            # 6. РАСЧЕТ ТЕМПЕРАТУР НА ПОВЕРХНОСТЯХ
            surface_temperatures = self._calculate_surface_temperatures(heat_transfer_coefficients, params)
            
            # 7. ПРОВЕРКА НА КОНДЕНСАЦИЮ
            condensation_analysis = self._analyze_condensation(surface_temperatures, params)
            
            # 8. РАСЧЕТ ЭНЕРГОЭФФЕКТИВНОСТИ
            energy_efficiency = self._calculate_thermal_energy_efficiency(heat_losses, ventilation_losses, params)
            
            # 9. ПРОВЕРКА СООТВЕТСТВИЯ НОРМАТИВНЫМ ТРЕБОВАНИЯМ
            normative_compliance = self._check_normative_compliance(heat_transfer_coefficients, params)
            
            # Объединяем все результаты
            return {
                "thermal_resistances": {
                    "wall": wall_thermal_resistance,
                    "window": window_thermal_resistance,
                    "floor": floor_thermal_resistance,
                    "ceiling": ceiling_thermal_resistance
                },
                "heat_transfer_coefficients": heat_transfer_coefficients,
                "heat_losses": heat_losses,
                "ventilation_losses": ventilation_losses,
                "heat_emissions": heat_emissions,
                "surface_temperatures": surface_temperatures,
                "condensation_analysis": condensation_analysis,
                "energy_efficiency": energy_efficiency,
                "normative_compliance": normative_compliance,
                "normative_links": {
                    "СП 50.13330.2012": "Тепловая защита зданий",
                    "СП 23-101-2004": "Проектирование тепловой защиты зданий",
                    "ГОСТ 30494-2011": "Здания жилые и общественные. Параметры микроклимата в помещениях"
                },
                "safety_recommendations": self._get_thermal_safety_recommendations(
                    condensation_analysis, normative_compliance, energy_efficiency
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Thermal calculation error: {e}")
            raise

    def _calculate_wall_thermal_resistance(self, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет термического сопротивления стен"""
        # Сопротивление теплопередаче стены
        R_wall = params.wall_thickness / params.thermal_conductivity
        
        # Общее сопротивление теплопередаче стены
        R_total_wall = 1/params.heat_transfer_coefficient_inner + R_wall + 1/params.heat_transfer_coefficient_outer
        
        # Коэффициент теплопередачи стены
        U_wall = 1 / R_total_wall
        
        return {
            "thermal_resistance": R_wall,
            "total_resistance": R_total_wall,
            "heat_transfer_coefficient": U_wall,
            "area": params.wall_area
        }

    def _calculate_window_thermal_resistance(self, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет термического сопротивления окон"""
        if params.window_area == 0:
            return {"thermal_resistance": 0, "total_resistance": 0, "heat_transfer_coefficient": 0, "area": 0}
        
        # Сопротивление теплопередаче окна
        R_window = 1 / params.window_thermal_conductivity
        
        # Общее сопротивление теплопередаче окна
        R_total_window = 1/params.heat_transfer_coefficient_inner + R_window + 1/params.heat_transfer_coefficient_outer
        
        # Коэффициент теплопередачи окна
        U_window = 1 / R_total_window
        
        return {
            "thermal_resistance": R_window,
            "total_resistance": R_total_window,
            "heat_transfer_coefficient": U_window,
            "area": params.window_area
        }

    def _calculate_floor_thermal_resistance(self, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет термического сопротивления пола"""
        # Сопротивление теплопередаче пола
        R_floor = params.floor_thickness / params.floor_thermal_conductivity
        
        # Общее сопротивление теплопередаче пола
        R_total_floor = 1/params.heat_transfer_coefficient_inner + R_floor + 1/params.heat_transfer_coefficient_outer
        
        # Коэффициент теплопередачи пола
        U_floor = 1 / R_total_floor
        
        return {
            "thermal_resistance": R_floor,
            "total_resistance": R_total_floor,
            "heat_transfer_coefficient": U_floor,
            "area": params.floor_area
        }

    def _calculate_ceiling_thermal_resistance(self, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет термического сопротивления потолка/крыши"""
        # Сопротивление теплопередаче потолка
        R_ceiling = params.ceiling_thickness / params.ceiling_thermal_conductivity
        
        # Общее сопротивление теплопередаче потолка
        R_total_ceiling = 1/params.heat_transfer_coefficient_inner + R_ceiling + 1/params.heat_transfer_coefficient_outer
        
        # Коэффициент теплопередачи потолка
        U_ceiling = 1 / R_total_ceiling
        
        return {
            "thermal_resistance": R_ceiling,
            "total_resistance": R_total_ceiling,
            "heat_transfer_coefficient": U_ceiling,
            "area": params.ceiling_area
        }

    def _calculate_heat_transfer_coefficients(self, wall_res, window_res, floor_res, ceiling_res, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет коэффициентов теплопередачи"""
        return {
            "wall": wall_res["heat_transfer_coefficient"],
            "window": window_res["heat_transfer_coefficient"],
            "floor": floor_res["heat_transfer_coefficient"],
            "ceiling": ceiling_res["heat_transfer_coefficient"],
            "average": (wall_res["heat_transfer_coefficient"] * wall_res["area"] + 
                       window_res["heat_transfer_coefficient"] * window_res["area"] + 
                       floor_res["heat_transfer_coefficient"] * floor_res["area"] + 
                       ceiling_res["heat_transfer_coefficient"] * ceiling_res["area"]) / 
                      (wall_res["area"] + window_res["area"] + floor_res["area"] + ceiling_res["area"])
        }

    def _calculate_heat_losses(self, heat_transfer_coeffs, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет теплопотерь через ограждающие конструкции"""
        delta_t = params.indoor_temperature - params.outdoor_temperature
        
        wall_loss = heat_transfer_coeffs["wall"] * params.wall_area * delta_t
        window_loss = heat_transfer_coeffs["window"] * params.window_area * delta_t
        floor_loss = heat_transfer_coeffs["floor"] * params.floor_area * delta_t
        ceiling_loss = heat_transfer_coeffs["ceiling"] * params.ceiling_area * delta_t
        
        total_loss = wall_loss + window_loss + floor_loss + ceiling_loss
        
        return {
            "wall_heat_loss": wall_loss,
            "window_heat_loss": window_loss,
            "floor_heat_loss": floor_loss,
            "ceiling_heat_loss": ceiling_loss,
            "total_heat_loss": total_loss,
            "specific_heat_loss": total_loss / params.building_area if params.building_area > 0 else 0
        }

    def _calculate_ventilation_heat_losses(self, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет теплопотерь на вентиляцию"""
        # Объем воздуха для вентиляции
        air_volume = params.building_volume * params.air_exchange_rate
        
        # Теплоемкость воздуха
        air_heat_capacity = 1005  # Дж/(кг·К)
        air_density = 1.2  # кг/м³
        
        # Теплопотери на вентиляцию
        ventilation_loss = air_volume * air_density * air_heat_capacity * (params.indoor_temperature - params.outdoor_temperature) / 3600
        
        return {
            "air_volume": air_volume,
            "ventilation_heat_loss": ventilation_loss,
            "specific_ventilation_loss": ventilation_loss / params.building_area if params.building_area > 0 else 0
        }

    def _calculate_heat_emissions(self, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет тепловыделений"""
        total_emissions = (params.heat_emission_people + 
                          params.heat_emission_equipment + 
                          params.heat_emission_lighting)
        
        return {
            "people_emissions": params.heat_emission_people,
            "equipment_emissions": params.heat_emission_equipment,
            "lighting_emissions": params.heat_emission_lighting,
            "total_emissions": total_emissions,
            "specific_emissions": total_emissions / params.building_area if params.building_area > 0 else 0
        }

    def _calculate_surface_temperatures(self, heat_transfer_coeffs, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет температур на поверхностях"""
        delta_t = params.indoor_temperature - params.outdoor_temperature
        
        # Температура внутренней поверхности стены
        wall_inner_temp = params.indoor_temperature - (heat_transfer_coeffs["wall"] * delta_t) / params.heat_transfer_coefficient_inner
        
        # Температура внутренней поверхности окна
        window_inner_temp = params.indoor_temperature - (heat_transfer_coeffs["window"] * delta_t) / params.heat_transfer_coefficient_inner
        
        return {
            "wall_inner_temperature": wall_inner_temp,
            "window_inner_temperature": window_inner_temp,
            "indoor_temperature": params.indoor_temperature,
            "outdoor_temperature": params.outdoor_temperature
        }

    def _analyze_condensation(self, surface_temps, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Анализ конденсации влаги на поверхностях"""
        # Расчет температуры точки росы
        # Формула Магнуса
        alpha = 17.27
        beta = 237.7
        dew_point = (beta * ((alpha * params.indoor_temperature) / (beta + params.indoor_temperature) + 
                            math.log(params.relative_humidity / 100))) / (alpha - ((alpha * params.indoor_temperature) / (beta + params.indoor_temperature) + 
                                                                                  math.log(params.relative_humidity / 100)))
        
        # Проверка конденсации
        wall_condensation = surface_temps["wall_inner_temperature"] < dew_point
        window_condensation = surface_temps["window_inner_temperature"] < dew_point
        
        return {
            "dew_point_temperature": dew_point,
            "wall_condensation_risk": wall_condensation,
            "window_condensation_risk": window_condensation,
            "condensation_risk": wall_condensation or window_condensation
        }

    def _calculate_thermal_energy_efficiency(self, heat_losses: Dict[str, Any], ventilation_losses: Dict[str, Any], params: ThermalCalculationParams) -> Dict[str, Any]:
        """Расчет энергоэффективности"""
        total_heat_loss = heat_losses["total_heat_loss"] + ventilation_losses["ventilation_heat_loss"]
        total_heat_emissions = params.heat_emission_people + params.heat_emission_equipment + params.heat_emission_lighting
        
        # Тепловой баланс
        heat_balance = total_heat_emissions - total_heat_loss
        
        # Удельное энергопотребление
        specific_consumption = total_heat_loss / params.building_area if params.building_area > 0 else 0
        
        # Класс энергоэффективности
        if specific_consumption <= 50:
            efficiency_class = "A+"
        elif specific_consumption <= 75:
            efficiency_class = "A"
        elif specific_consumption <= 100:
            efficiency_class = "B"
        elif specific_consumption <= 125:
            efficiency_class = "C"
        elif specific_consumption <= 150:
            efficiency_class = "D"
        else:
            efficiency_class = "E"
        
        return {
            "total_heat_loss": total_heat_loss,
            "total_heat_emissions": total_heat_emissions,
            "heat_balance": heat_balance,
            "specific_consumption": specific_consumption,
            "efficiency_class": efficiency_class
        }

    def _check_normative_compliance(self, heat_transfer_coeffs, params: ThermalCalculationParams) -> Dict[str, Any]:
        """Проверка соответствия нормативным требованиям"""
        # Нормативное сопротивление теплопередаче
        normative_resistance = params.normative_heat_transfer_resistance
        
        # Фактическое сопротивление теплопередаче стены
        actual_resistance = 1 / heat_transfer_coeffs["wall"]
        
        # Соответствие требованиям
        meets_requirements = actual_resistance >= normative_resistance
        
        return {
            "normative_resistance": normative_resistance,
            "actual_resistance": actual_resistance,
            "meets_requirements": meets_requirements,
            "compliance_percentage": (actual_resistance / normative_resistance) * 100 if normative_resistance > 0 else 0
        }

    def _get_thermal_safety_recommendations(self, condensation_analysis, normative_compliance, energy_efficiency) -> List[str]:
        """Получение рекомендаций по безопасности теплотехнических систем"""
        recommendations = []
        
        # Проверка конденсации
        if condensation_analysis.get("condensation_risk", False):
            recommendations.append("КРИТИЧНО: Риск конденсации влаги на поверхностях")
            recommendations.append("Необходимо увеличить сопротивление теплопередаче")
            recommendations.append("Рекомендуется улучшить теплоизоляцию")
        
        # Проверка соответствия нормативным требованиям
        if not normative_compliance.get("meets_requirements", False):
            recommendations.append("ВНИМАНИЕ: Сопротивление теплопередаче ниже нормативного")
            recommendations.append("Необходимо увеличить толщину теплоизоляции")
        
        # Проверка энергоэффективности
        if energy_efficiency.get("efficiency_class", "E") in ["D", "E"]:
            recommendations.append("ВНИМАНИЕ: Низкий класс энергоэффективности")
            recommendations.append("Рекомендуется улучшить теплозащиту здания")
        
        if not recommendations:
            recommendations.append("Теплотехнические характеристики соответствуют требованиям")
            recommendations.append("Продолжить эксплуатацию с соблюдением правил")
        
        return recommendations
    
    def _execute_ventilation_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчетов вентиляции согласно СП 60.13330.2016, СП 7.13130.2013, СП 54.13330.2016"""
        try:
            params = VentilationCalculationParams(**parameters)
            
            # 1. РАСЧЕТ ВОЗДУХООБМЕНА (СП 60.13330.2016)
            air_exchange_results = self._calculate_air_exchange(params)
            
            # 2. РАСЧЕТ ПРОТИВОДЫМНОЙ ВЕНТИЛЯЦИИ (СП 7.13130.2013)
            smoke_ventilation_results = self._calculate_smoke_ventilation(params)
            
            # 3. РАСЧЕТ ВЕНТИЛЯЦИИ ЖИЛЫХ ЗДАНИЙ (СП 54.13330.2016)
            residential_ventilation_results = self._calculate_residential_ventilation(params)
            
            # 4. РАСЧЕТ ЭНЕРГОЭФФЕКТИВНОСТИ
            energy_efficiency_results = self._calculate_ventilation_energy_efficiency(params, air_exchange_results)
            
            # 5. АКУСТИЧЕСКИЕ РАСЧЕТЫ
            acoustic_results = self._calculate_acoustic_parameters(params, air_exchange_results)
            
            # 6. ТЕПЛОВЫЕ РАСЧЕТЫ
            thermal_results = self._calculate_thermal_loads(params, air_exchange_results)
            
            # 7. РЕКУПЕРАЦИЯ ТЕПЛА
            heat_recovery_results = self._calculate_heat_recovery(params, thermal_results)
            
            # Объединяем все результаты
            return {
                **air_exchange_results,
                **smoke_ventilation_results,
                **residential_ventilation_results,
                **energy_efficiency_results,
                **acoustic_results,
                **thermal_results,
                **heat_recovery_results,
                "calculation_type": "ventilation",
                "normative_documents": {
                    "СП 60.13330.2016": "Отопление, вентиляция и кондиционирование воздуха",
                    "СП 7.13130.2013": "Отопление, вентиляция и кондиционирование. Требования пожарной безопасности",
                    "СП 54.13330.2016": "Здания жилые многоквартирные"
                },
                "execution_time": time.time(),
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"❌ Ventilation calculation error: {e}")
            raise

    def _calculate_air_exchange(self, params: VentilationCalculationParams) -> Dict[str, Any]:
        """Расчет воздухообмена согласно СП 60.13330.2016"""
        # Минимальные нормы воздухообмена по типам помещений (м³/ч·чел)
        air_exchange_norms = {
            "жилое": 30,
            "общественное": 20,
            "производственное": 60
        }
        
        # Расчет по вредным выделениям
        co2_air_exchange = params.co2_emission_per_person * params.occupancy / 0.001  # м³/ч
        moisture_air_exchange = params.moisture_emission_per_person * params.occupancy * 1000 / 0.5  # м³/ч
        heat_air_exchange = (params.heat_emission_per_person * params.occupancy + params.heat_emission_from_equipment) / (params.specific_heat * params.air_density * (params.exhaust_air_temperature - params.supply_air_temperature))  # м³/ч
        
        # Расчет по кратности
        if params.air_exchange_rate:
            air_exchange_by_rate = params.room_volume * params.air_exchange_rate
        else:
            air_exchange_by_rate = 0
            
        # Расчет по площади
        if params.air_exchange_per_area:
            air_exchange_by_area = params.room_area * params.air_exchange_per_area
        else:
            air_exchange_by_area = 0
            
        # Расчет по количеству людей
        if params.air_exchange_per_person:
            air_exchange_by_person = params.occupancy * params.air_exchange_per_person
        else:
            air_exchange_by_person = params.occupancy * air_exchange_norms.get(params.room_type, 30)
        
        # Принимаем максимальное значение
        required_air_exchange = max(
            co2_air_exchange,
            moisture_air_exchange,
            heat_air_exchange,
            air_exchange_by_rate,
            air_exchange_by_area,
            air_exchange_by_person
        )
        
        return {
            "required_air_exchange": required_air_exchange,
            "air_exchange_by_co2": co2_air_exchange,
            "air_exchange_by_moisture": moisture_air_exchange,
            "air_exchange_by_heat": heat_air_exchange,
            "air_exchange_by_rate": air_exchange_by_rate,
            "air_exchange_by_area": air_exchange_by_area,
            "air_exchange_by_person": air_exchange_by_person,
            "air_exchange_rate_actual": required_air_exchange / params.room_volume if params.room_volume > 0 else 0
        }

    def _calculate_smoke_ventilation(self, params: VentilationCalculationParams) -> Dict[str, Any]:
        """Расчет противодымной вентиляции согласно СП 7.13130.2013"""
        if not params.smoke_ventilation_required:
            return {"smoke_ventilation_required": False}
        
        # Расчет удаления дыма из помещений
        smoke_removal_rate = 1.0  # м³/с на 1 м² площади пожарного отсека
        if params.fire_compartment_area:
            smoke_removal_volume = params.fire_compartment_area * smoke_removal_rate
        else:
            smoke_removal_volume = params.room_area * smoke_removal_rate
        
        # Расчет подпора воздуха в лифтовых шахтах
        elevator_shaft_pressure = 20  # Па
        elevator_shaft_air_flow = 1.0  # м³/с
        
        # Расчет удаления дыма из коридоров (эвакуационных путей)
        if params.evacuation_route:
            corridor_smoke_removal = params.room_area * 0.5  # м³/с
        else:
            corridor_smoke_removal = 0
        
        return {
            "smoke_ventilation_required": True,
            "smoke_removal_volume": smoke_removal_volume,
            "elevator_shaft_pressure": elevator_shaft_pressure,
            "elevator_shaft_air_flow": elevator_shaft_air_flow,
            "corridor_smoke_removal": corridor_smoke_removal,
            "total_smoke_ventilation": smoke_removal_volume + corridor_smoke_removal
        }

    def _calculate_residential_ventilation(self, params: VentilationCalculationParams) -> Dict[str, Any]:
        """Расчет вентиляции жилых зданий согласно СП 54.13330.2016"""
        if params.room_type != "жилое":
            return {"residential_ventilation_applicable": False}
        
        # Нормы воздухообмена для жилых помещений
        living_room_air_exchange = 3.0  # м³/ч на 1 м²
        bedroom_air_exchange = 1.0  # м³/ч на 1 м²
        kitchen_air_exchange = 60.0  # м³/ч (не менее)
        bathroom_air_exchange = 25.0  # м³/ч (не менее)
        toilet_air_exchange = 25.0  # м³/ч (не менее)
        
        # Расчет естественной вентиляции
        natural_ventilation_area = params.room_area * 0.02  # 2% от площади помещения
        
        # Расчет приточно-вытяжной вентиляции с рекуперацией
        if params.ventilation_type == "mechanical":
            mechanical_air_exchange = params.room_area * living_room_air_exchange
        else:
            mechanical_air_exchange = 0
        
        return {
            "residential_ventilation_applicable": True,
            "living_room_air_exchange": living_room_air_exchange,
            "bedroom_air_exchange": bedroom_air_exchange,
            "kitchen_air_exchange": kitchen_air_exchange,
            "bathroom_air_exchange": bathroom_air_exchange,
            "toilet_air_exchange": toilet_air_exchange,
            "natural_ventilation_area": natural_ventilation_area,
            "mechanical_air_exchange": mechanical_air_exchange,
            "recommended_air_exchange": max(mechanical_air_exchange, params.room_area * living_room_air_exchange)
        }

    def _calculate_ventilation_energy_efficiency(self, params: VentilationCalculationParams, air_exchange_results: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет энергоэффективности вентиляционной системы"""
        air_volume = air_exchange_results["required_air_exchange"]
        
        # Расчет мощности вентилятора
        fan_power = (air_volume / 3600) * 1000 / params.fan_efficiency  # Вт
        
        # Расчет энергопотребления
        annual_energy_consumption = fan_power * 8760 / 1000  # кВт·ч/год
        
        # Класс энергоэффективности
        energy_efficiency_limits = {
            "A": 50,   # кВт·ч/м²·год
            "B": 75,
            "C": 100,
            "D": 150,
            "E": 200
        }
        
        specific_energy_consumption = annual_energy_consumption / params.room_area if params.room_area > 0 else 0
        actual_class = "E"
        for class_name, limit in energy_efficiency_limits.items():
            if specific_energy_consumption <= limit:
                actual_class = class_name
                break
        
        return {
            "fan_power": fan_power,
            "annual_energy_consumption": annual_energy_consumption,
            "specific_energy_consumption": specific_energy_consumption,
            "energy_efficiency_class": actual_class,
            "energy_efficiency_rating": "Высокая" if actual_class in ["A", "B"] else "Средняя" if actual_class == "C" else "Низкая"
        }

    def _calculate_acoustic_parameters(self, params: VentilationCalculationParams, air_exchange_results: Dict[str, Any]) -> Dict[str, Any]:
        """Акустические расчеты вентиляционной системы"""
        air_volume = air_exchange_results["required_air_exchange"]
        
        # Расчет уровня шума от вентилятора
        fan_noise_level = 20 + 10 * math.log10(air_volume / 1000)  # дБА
        
        # Расчет уровня шума в помещении
        room_noise_level = fan_noise_level - 10 * math.log10(params.room_volume)  # дБА
        
        # Проверка соответствия нормам
        noise_compliance = room_noise_level <= params.noise_level_limit
        
        return {
            "fan_noise_level": fan_noise_level,
            "room_noise_level": room_noise_level,
            "noise_level_limit": params.noise_level_limit,
            "noise_compliance": noise_compliance,
            "noise_margin": params.noise_level_limit - room_noise_level
        }

    def _calculate_thermal_loads(self, params: VentilationCalculationParams, air_exchange_results: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет тепловых нагрузок вентиляционной системы"""
        air_volume = air_exchange_results["required_air_exchange"]
        air_mass_flow = air_volume * params.air_density / 3600  # кг/с
        
        # Тепловая нагрузка на нагрев приточного воздуха
        heating_load = air_mass_flow * params.specific_heat * (params.supply_air_temperature - params.outdoor_temperature)
        
        # Тепловая нагрузка на охлаждение
        cooling_load = air_mass_flow * params.specific_heat * (params.exhaust_air_temperature - params.supply_air_temperature)
        
        # Мощность нагревателя/охладителя
        heating_power = max(0, heating_load)  # Вт
        cooling_power = max(0, cooling_load)  # Вт
        
        return {
            "heating_load": heating_load,
            "cooling_load": cooling_load,
            "heating_power": heating_power,
            "cooling_power": cooling_power,
            "air_mass_flow": air_mass_flow
        }

    def _calculate_heat_recovery(self, params: VentilationCalculationParams, thermal_results: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет рекуперации тепла"""
        if params.heat_recovery_efficiency <= 0:
            return {"heat_recovery_applicable": False}
        
        # Экономия тепла за счет рекуперации
        heat_savings = thermal_results["heating_load"] * params.heat_recovery_efficiency
        
        # Экономия энергии
        energy_savings = heat_savings * 8760 / 1000  # кВт·ч/год
        
        # Экономия средств (при стоимости тепла 2000 руб/Гкал)
        cost_savings = energy_savings * 0.86 * 2000 / 1000  # руб/год
        
        return {
            "heat_recovery_applicable": True,
            "heat_recovery_efficiency": params.heat_recovery_efficiency,
            "heat_savings": heat_savings,
            "energy_savings": energy_savings,
            "cost_savings": cost_savings,
            "payback_period": 5  # лет (примерно)
        }

    def _execute_degasification_calculation(self, params: DegasificationCalculationParams) -> Dict[str, Any]:
        """Выполнение расчета дегазации угольных шахт"""
        try:
            logger.info(f"🔍 [DEGASIFICATION] Starting degasification calculation")
            
            # Расчет объема угля в шахте
            coal_volume = params.mine_area * params.coal_seam_thickness  # м³
            
            # Расчет массы угля
            coal_density = 1.4  # т/м³ (средняя плотность угля)
            coal_mass = coal_volume * coal_density  # т
            
            # Расчет общего содержания метана в угле
            total_methane_content = coal_mass * params.methane_content / 100  # т метана
            
            # Расчет выделения метана при отработке
            daily_methane_emission = params.extraction_rate * params.methane_emission_rate  # м³/сут
            
            # Расчет необходимого расхода воздуха для разбавления метана
            required_air_flow = daily_methane_emission / (params.methane_concentration_limit / 100)  # м³/с
            
            # Проверка достаточности вентиляции
            ventilation_sufficiency = params.ventilation_air_flow / required_air_flow
            
            # Расчет концентрации метана в вентиляционном воздухе
            methane_concentration = (daily_methane_emission / 86400) / params.ventilation_air_flow * 100  # %
            
            # Оценка безопасности
            safety_status = "Безопасно" if methane_concentration < params.methane_concentration_limit else "Опасность"
            
            # Расчет эффективности дегазации
            degasification_efficiency = min(100, (daily_methane_emission / (total_methane_content * 1000)) * 100)  # %
            
            # Нормативные ссылки
            normative_links = {
                "ГОСТ Р 55154-2012": "Системы газового контроля в угольных шахтах",
                "ПБ 05-618-03": "Правила безопасности в угольных шахтах",
                "ГОСТ 12.1.010-76": "Взрывобезопасность. Общие требования",
                "СП 12.13130.2009": "Определение категорий помещений по взрывопожарной опасности"
            }
            
            return {
                "coal_volume": coal_volume,
                "coal_mass": coal_mass,
                "total_methane_content": total_methane_content,
                "daily_methane_emission": daily_methane_emission,
                "required_air_flow": required_air_flow,
                "ventilation_sufficiency": ventilation_sufficiency,
                "methane_concentration": methane_concentration,
                "safety_status": safety_status,
                "degasification_efficiency": degasification_efficiency,
                "normative_links": normative_links,
                "safety_recommendations": self._get_safety_recommendations(methane_concentration, ventilation_sufficiency)
            }
            
        except Exception as e:
            logger.error(f"❌ Degasification calculation error: {e}")
            raise

    def _get_safety_recommendations(self, methane_concentration: float, ventilation_sufficiency: float) -> List[str]:
        """Получение рекомендаций по безопасности"""
        recommendations = []
        
        if methane_concentration > 1.0:
            recommendations.append("КРИТИЧНО: Концентрация метана превышает допустимую норму")
            recommendations.append("Немедленно прекратить работы и проветрить шахту")
            recommendations.append("Проверить герметичность системы дегазации")
        
        if ventilation_sufficiency < 1.0:
            recommendations.append("ВНИМАНИЕ: Недостаточный расход вентиляционного воздуха")
            recommendations.append("Увеличить мощность вентиляционной системы")
            recommendations.append("Рассмотреть дополнительные меры дегазации")
        
        if methane_concentration > 0.5:
            recommendations.append("Повысить частоту контроля концентрации метана")
            recommendations.append("Усилить мониторинг газовой обстановки")
        
        if not recommendations:
            recommendations.append("Газовая обстановка в норме")
            recommendations.append("Продолжить работы с соблюдением мер безопасности")
        
        return recommendations

    def _execute_electrical_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение электротехнических расчетов согласно СП 31.110-2003, СП 437.1325800.2018, СП 256.1325800.2016"""
        try:
            logger.info(f"🔍 [ELECTRICAL] Starting electrical calculation")
            
            # 1. РАСЧЕТ ЭЛЕКТРИЧЕСКИХ НАГРУЗОК (СП 31.110-2003)
            electrical_loads = self._calculate_electrical_loads(parameters)
            
            # 2. РАСЧЕТ СЕЧЕНИЙ КАБЕЛЕЙ (СП 31.110-2003)
            cable_calculation = self._calculate_cable_sections(parameters)
            
            # 3. РАСЧЕТ ЗАЗЕМЛЕНИЯ (СП 31.110-2003)
            grounding_calculation = self._calculate_grounding(parameters)
            
            # 4. РАСЧЕТ МОЛНИЕЗАЩИТЫ (СП 437.1325800.2018)
            lightning_protection = self._calculate_lightning_protection(parameters)
            
            # 5. РАСЧЕТ ЭНЕРГОЭФФЕКТИВНОСТИ (СП 256.1325800.2016)
            energy_efficiency = self._calculate_energy_efficiency(parameters)
            
            # Объединяем все результаты
            return {
                "electrical_loads": electrical_loads,
                "cable_calculation": cable_calculation,
                "grounding_calculation": grounding_calculation,
                "lightning_protection": lightning_protection,
                "energy_efficiency": energy_efficiency,
                "normative_links": {
                    "СП 31.110-2003": "Электроустановки жилых и общественных зданий",
                    "СП 437.1325800.2018": "Инженерные системы зданий и сооружений",
                    "СП 256.1325800.2016": "Энергоэффективность зданий"
                },
                "safety_recommendations": self._get_electrical_safety_recommendations(electrical_loads, grounding_calculation)
            }
            
        except Exception as e:
            logger.error(f"❌ Electrical calculation error: {e}")
            raise

    def _calculate_electrical_loads(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет электрических нагрузок согласно СП 31.110-2003"""
        try:
            # Основные параметры
            total_area = params.get("total_area", 0)
            lighting_load = params.get("lighting_load", 0)
            power_load = params.get("power_load", 0)
            heating_load = params.get("heating_load", 0)
            ventilation_load = params.get("ventilation_load", 0)
            
            # Коэффициенты
            demand_factor = params.get("demand_factor", 0.7)
            diversity_factor = params.get("diversity_factor", 0.8)
            power_factor = params.get("power_factor", 0.9)
            
            # Расчет нагрузок по категориям
            lighting_power = total_area * lighting_load  # Вт
            power_power = total_area * power_load  # Вт
            heating_power = total_area * heating_load  # Вт
            ventilation_power = total_area * ventilation_load  # Вт
            
            # Общая установленная мощность
            total_installed_power = lighting_power + power_power + heating_power + ventilation_power  # Вт
            
            # Расчетная мощность с учетом коэффициентов
            calculated_power = total_installed_power * demand_factor * diversity_factor  # Вт
            
            # Расчетный ток
            voltage = params.get("voltage", 380)
            if power_factor > 0:
                calculated_current = calculated_power / (voltage * power_factor * math.sqrt(3))  # А
            else:
                calculated_current = 0
            
            # Удельная нагрузка
            specific_load = calculated_power / total_area if total_area > 0 else 0  # Вт/м²
            
            return {
                "lighting_power": lighting_power,
                "power_power": power_power,
                "heating_power": heating_power,
                "ventilation_power": ventilation_power,
                "total_installed_power": total_installed_power,
                "calculated_power": calculated_power,
                "calculated_current": calculated_current,
                "specific_load": specific_load,
                "demand_factor": demand_factor,
                "diversity_factor": diversity_factor,
                "power_factor": power_factor
            }
            
        except Exception as e:
            logger.error(f"❌ Electrical loads calculation error: {e}")
            raise

    def _calculate_cable_sections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет сечений кабелей согласно СП 31.110-2003"""
        try:
            load_current = params.get("load_current", 0)
            voltage = params.get("voltage", 380)
            power = params.get("power", 0)
            cable_length = params.get("cable_length", 0)
            
            # Расчет тока по мощности
            calculated_current = power * 1000 / (voltage * math.sqrt(3)) if voltage > 0 else 0
            
            # Используем больший ток
            design_current = max(load_current, calculated_current)
            
            # Коэффициенты
            temperature_correction = params.get("temperature_correction", 1.0)
            grouping_factor = params.get("grouping_factor", 1.0)
            
            # Расчетное сечение (упрощенный расчет)
            # Для меди: S = I / (j * k1 * k2), где j = 4 А/мм²
            current_density = 4.0  # А/мм²
            required_section = design_current / (current_density * temperature_correction * grouping_factor)
            
            # Стандартные сечения кабелей
            standard_sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
            selected_section = min([s for s in standard_sections if s >= required_section], default=240)
            
            # Проверка по допустимому току
            max_current = selected_section * current_density * temperature_correction * grouping_factor
            
            return {
                "design_current": design_current,
                "required_section": required_section,
                "selected_section": selected_section,
                "max_current": max_current,
                "current_density": current_density,
                "temperature_correction": temperature_correction,
                "grouping_factor": grouping_factor,
                "cable_length": cable_length
            }
            
        except Exception as e:
            logger.error(f"❌ Cable calculation error: {e}")
            raise

    def _calculate_grounding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет заземления согласно СП 31.110-2003"""
        try:
            building_area = params.get("total_area", 0)
            soil_resistivity = params.get("soil_resistivity", 100)
            
            # Параметры заземлителя
            electrode_length = 2.5  # м
            electrode_diameter = 0.02  # м
            electrode_spacing = 5.0  # м
            
            # Расчет сопротивления одиночного вертикального электрода
            single_electrode_resistance = soil_resistivity / (2 * math.pi * electrode_length) * \
                math.log(4 * electrode_length / electrode_diameter)
            
            # Расчет количества электродов для контурного заземления
            perimeter = 4 * math.sqrt(building_area)  # м
            number_of_electrodes = int(perimeter / electrode_spacing) + 1
            
            # Коэффициент использования
            utilization_factor = 0.6  # для контурного заземления
            
            # Общее сопротивление заземления
            total_resistance = single_electrode_resistance / (number_of_electrodes * utilization_factor)
            
            # Требования
            max_resistance = 4.0  # Ом
            safety_factor = params.get("safety_factor", 1.2)
            
            # Проверка соответствия требованиям
            meets_requirements = total_resistance <= max_resistance
            
            return {
                "soil_resistivity": soil_resistivity,
                "single_electrode_resistance": single_electrode_resistance,
                "number_of_electrodes": number_of_electrodes,
                "total_resistance": total_resistance,
                "max_resistance": max_resistance,
                "meets_requirements": meets_requirements,
                "safety_factor": safety_factor,
                "electrode_length": electrode_length,
                "electrode_diameter": electrode_diameter,
                "electrode_spacing": electrode_spacing
            }
            
        except Exception as e:
            logger.error(f"❌ Grounding calculation error: {e}")
            raise

    def _calculate_lightning_protection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет молниезащиты согласно СП 437.1325800.2018"""
        try:
            building_height = params.get("building_height", 0)
            building_length = params.get("building_length", 0)
            building_width = params.get("building_width", 0)
            lightning_density = params.get("lightning_density", 4.0)
            soil_resistivity = params.get("soil_resistivity", 100)
            
            # Расчет зоны защиты
            protection_level = params.get("protection_level", "II")
            protection_radius = {
                "I": 0.8,
                "II": 0.7,
                "III": 0.6,
                "IV": 0.5
            }.get(protection_level, 0.7)
            
            # Высота молниеотвода
            lightning_rod_height = max(building_height * 1.2, 10)  # м, минимум 10м
            
            # Радиус защиты на уровне земли
            ground_protection_radius = lightning_rod_height * protection_radius
            
            # Количество молниеотводов
            building_diagonal = math.sqrt(building_length**2 + building_width**2)
            if ground_protection_radius > 0:
                number_of_rods = max(1, int(building_diagonal / (2 * ground_protection_radius)) + 1)
            else:
                number_of_rods = 1
            
            # Расчет сопротивления растеканию
            if lightning_rod_height > 0:
                grounding_resistance = soil_resistivity / (2 * math.pi * lightning_rod_height) * \
                math.log(4 * lightning_rod_height / 0.008)
            else:
                grounding_resistance = 1000  # Большое значение при отсутствии молниеотвода
            
            # Требования к сопротивлению
            max_grounding_resistance = 10.0  # Ом
            meets_requirements = grounding_resistance <= max_grounding_resistance
            
            return {
                "protection_level": protection_level,
                "lightning_rod_height": lightning_rod_height,
                "ground_protection_radius": ground_protection_radius,
                "number_of_rods": number_of_rods,
                "grounding_resistance": grounding_resistance,
                "max_grounding_resistance": max_grounding_resistance,
                "meets_requirements": meets_requirements,
                "lightning_density": lightning_density,
                "building_height": building_height,
                "building_length": building_length,
                "building_width": building_width
            }
            
        except Exception as e:
            logger.error(f"❌ Lightning protection calculation error: {e}")
            raise

    def _calculate_energy_efficiency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет энергоэффективности согласно СП 256.1325800.2016"""
        try:
            building_area = params.get("total_area", 0)
            building_volume = params.get("building_volume", 0)
            annual_consumption = params.get("annual_electricity_consumption", 0)
            
            # Удельное энергопотребление
            specific_consumption = annual_consumption / building_area if building_area > 0 else 0  # кВт·ч/м²
            
            # Нормативные значения (кВт·ч/м²·год)
            normative_consumption = {
                "жилое": 50,
                "общественное": 80
            }
            
            building_type = params.get("building_type", "жилое")
            normative_value = normative_consumption.get(building_type, 50)
            
            # Класс энергоэффективности
            if specific_consumption <= normative_value * 0.5:
                efficiency_class = "A+"
            elif specific_consumption <= normative_value * 0.75:
                efficiency_class = "A"
            elif specific_consumption <= normative_value:
                efficiency_class = "B"
            elif specific_consumption <= normative_value * 1.25:
                efficiency_class = "C"
            elif specific_consumption <= normative_value * 1.5:
                efficiency_class = "D"
            else:
                efficiency_class = "E"
            
            # Экономия энергии
            energy_savings = max(0, (normative_value - specific_consumption) * building_area)
            savings_percentage = (1 - specific_consumption / normative_value) * 100 if normative_value > 0 else 0
            
            return {
                "specific_consumption": specific_consumption,
                "normative_consumption": normative_value,
                "efficiency_class": efficiency_class,
                "energy_savings": energy_savings,
                "savings_percentage": savings_percentage,
                "building_type": building_type,
                "annual_consumption": annual_consumption,
                "building_area": building_area
            }
            
        except Exception as e:
            logger.error(f"❌ Energy efficiency calculation error: {e}")
            raise

    def _get_electrical_safety_recommendations(self, electrical_loads: Dict[str, Any], grounding: Dict[str, Any]) -> List[str]:
        """Получение рекомендаций по безопасности электротехнических систем"""
        recommendations = []
        
        # Проверка электрических нагрузок
        if electrical_loads.get("calculated_current", 0) > 100:
            recommendations.append("ВНИМАНИЕ: Высокий расчетный ток - проверьте сечение кабелей")
            recommendations.append("Рекомендуется установка автоматических выключателей")
        
        # Проверка заземления
        if not grounding.get("meets_requirements", False):
            recommendations.append("КРИТИЧНО: Сопротивление заземления превышает норму")
            recommendations.append("Необходимо увеличить количество электродов или улучшить грунт")
        
        # Проверка энергоэффективности
        if electrical_loads.get("specific_load", 0) > 100:
            recommendations.append("ВНИМАНИЕ: Высокая удельная нагрузка")
            recommendations.append("Рекомендуется оптимизация энергопотребления")
        
        if not recommendations:
            recommendations.append("Электротехнические системы соответствуют требованиям")
            recommendations.append("Продолжить эксплуатацию с соблюдением правил")
        
        return recommendations

    # ===== ВОДОСНАБЖЕНИЕ И ВОДООТВЕДЕНИЕ =====

    def _execute_water_supply_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчетов водоснабжения и водоотведения согласно СП 30.13330.2016"""
        try:
            logger.info(f"🔍 [WATER] Starting water supply calculation")
            params = WaterSupplyCalculationParams(**parameters)
            
            # 1. РАСЧЕТ ВОДОПОТРЕБЛЕНИЯ
            water_consumption = self._calculate_water_consumption(params)
            
            # 2. РАСЧЕТ ДИАМЕТРОВ ТРУБОПРОВОДОВ
            pipe_calculation = self._calculate_pipe_diameters(params)
            
            # 3. РАСЧЕТ ДАВЛЕНИЯ ВОДЫ
            pressure_calculation = self._calculate_water_pressure(params)
            
            # 4. РАСЧЕТ ВОДООТВЕДЕНИЯ
            sewage_calculation = self._calculate_sewage_system(params)
            
            # 5. РАСЧЕТ СИСТЕМЫ ОЧИСТКИ
            treatment_calculation = self._calculate_treatment_system(params)
            
            return {
                "water_consumption": water_consumption,
                "pipe_calculation": pipe_calculation,
                "pressure_calculation": pressure_calculation,
                "sewage_calculation": sewage_calculation,
                "treatment_calculation": treatment_calculation,
                "normative_links": {
                    "СП 30.13330.2016": "Внутренний водопровод и канализация зданий",
                    "СП 32.13330.2018": "Канализация. Наружные сети и сооружения",
                    "СП 31.13330.2012": "Водоснабжение. Наружные сети и сооружения"
                },
                "safety_recommendations": self._get_water_safety_recommendations(water_consumption, pressure_calculation)
            }
            
        except Exception as e:
            logger.error(f"❌ Water supply calculation error: {e}")
            raise

    def _calculate_water_consumption(self, params: WaterSupplyCalculationParams) -> Dict[str, Any]:
        """Расчет водопотребления согласно СП 30.13330.2016"""
        try:
            # Суточное потребление
            daily_consumption = params.number_of_people * params.water_consumption_per_person  # л/сут
            hot_water_daily = params.number_of_people * params.hot_water_consumption_per_person  # л/сут
            cold_water_daily = params.number_of_people * params.cold_water_consumption_per_person  # л/сут
            
            # Часовое потребление
            hourly_consumption = daily_consumption * params.consumption_coefficient / 24  # л/ч
            peak_hourly_consumption = hourly_consumption * params.peak_coefficient  # л/ч
            
            # Секундное потребление
            second_consumption = peak_hourly_consumption / 3600  # л/с
            
            # Удельное потребление
            specific_consumption = daily_consumption / params.building_area if params.building_area > 0 else 0  # л/(м²·сут)
            
            return {
                "daily_consumption": daily_consumption,
                "hot_water_daily": hot_water_daily,
                "cold_water_daily": cold_water_daily,
                "hourly_consumption": hourly_consumption,
                "peak_hourly_consumption": peak_hourly_consumption,
                "second_consumption": second_consumption,
                "specific_consumption": specific_consumption,
                "consumption_coefficient": params.consumption_coefficient,
                "peak_coefficient": params.peak_coefficient
            }
            
        except Exception as e:
            logger.error(f"❌ Water consumption calculation error: {e}")
            raise

    def _calculate_pipe_diameters(self, params: WaterSupplyCalculationParams) -> Dict[str, Any]:
        """Расчет диаметров трубопроводов"""
        try:
            # Расчетный расход
            design_flow = params.number_of_people * params.water_consumption_per_person * params.simultaneity_coefficient / 3600  # л/с
            
            # Скорость воды в трубе (оптимальная 1-2 м/с)
            water_velocity = 1.5  # м/с
            
            # Расчет диаметра по формуле: D = sqrt(4*Q/(π*v))
            if water_velocity > 0:
                pipe_diameter_calculated = math.sqrt(4 * design_flow / (math.pi * water_velocity * 1000))  # м
            else:
                pipe_diameter_calculated = 0.05
            
            # Стандартные диаметры труб
            standard_diameters = [0.015, 0.020, 0.025, 0.032, 0.040, 0.050, 0.065, 0.080, 0.100, 0.125, 0.150]
            selected_diameter = min([d for d in standard_diameters if d >= pipe_diameter_calculated], default=0.050)
            
            # Потери напора
            friction_factor = 0.02  # коэффициент трения
            head_loss = friction_factor * (params.pipe_length / selected_diameter) * (water_velocity**2) / (2 * 9.81)  # м
            
            return {
                "design_flow": design_flow,
                "water_velocity": water_velocity,
                "calculated_diameter": pipe_diameter_calculated,
                "selected_diameter": selected_diameter,
                "head_loss": head_loss,
                "pipe_length": params.pipe_length,
                "pipe_material": params.pipe_material
            }
            
        except Exception as e:
            logger.error(f"❌ Pipe diameter calculation error: {e}")
            raise

    def _calculate_water_pressure(self, params: WaterSupplyCalculationParams) -> Dict[str, Any]:
        """Расчет давления воды в системе"""
        try:
            # Требуемое давление
            required_pressure = params.water_pressure * 1000  # кПа
            
            # Статическое давление
            static_pressure = 9.81 * params.number_of_floors * 3  # кПа (3м на этаж)
            
            # Динамическое давление
            dynamic_pressure = 50  # кПа (потери в системе)
            
            # Общее требуемое давление
            total_pressure = static_pressure + dynamic_pressure  # кПа
            
            # Проверка достаточности давления
            pressure_sufficient = total_pressure <= required_pressure * 1000
            
            return {
                "required_pressure": required_pressure,
                "static_pressure": static_pressure,
                "dynamic_pressure": dynamic_pressure,
                "total_pressure": total_pressure,
                "pressure_sufficient": pressure_sufficient,
                "pressure_margin": (required_pressure * 1000 - total_pressure) if pressure_sufficient else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Water pressure calculation error: {e}")
            raise

    def _calculate_sewage_system(self, params: WaterSupplyCalculationParams) -> Dict[str, Any]:
        """Расчет системы водоотведения"""
        try:
            # Расход сточных вод
            sewage_flow = params.sewage_flow_rate  # л/с
            
            # Концентрация загрязнений
            pollution_load = sewage_flow * params.sewage_concentration / 1000  # кг/с
            
            # Объем сточных вод в сутки
            daily_sewage_volume = sewage_flow * 3600 * 24 / 1000  # м³/сут
            
            # Требуемая производительность очистных сооружений
            treatment_capacity = daily_sewage_volume * 1.2  # м³/сут (с запасом)
            
            return {
                "sewage_flow": sewage_flow,
                "pollution_load": pollution_load,
                "daily_sewage_volume": daily_sewage_volume,
                "treatment_capacity": treatment_capacity,
                "sewage_concentration": params.sewage_concentration,
                "treatment_efficiency": params.treatment_efficiency
            }
            
        except Exception as e:
            logger.error(f"❌ Sewage system calculation error: {e}")
            raise

    def _calculate_treatment_system(self, params: WaterSupplyCalculationParams) -> Dict[str, Any]:
        """Расчет системы очистки сточных вод"""
        try:
            # Производительность очистных сооружений
            treatment_capacity = params.sewage_flow_rate * 3600 * 24 / 1000  # м³/сут
            
            # Эффективность очистки
            removal_efficiency = params.treatment_efficiency
            
            # Концентрация после очистки
            treated_concentration = params.sewage_concentration * (1 - removal_efficiency)  # мг/л
            
            # Объем илового осадка
            sludge_volume = treatment_capacity * 0.05  # м³/сут (5% от объема)
            
            return {
                "treatment_capacity": treatment_capacity,
                "removal_efficiency": removal_efficiency,
                "treated_concentration": treated_concentration,
                "sludge_volume": sludge_volume,
                "treatment_type": "биологическая очистка"
            }
            
        except Exception as e:
            logger.error(f"❌ Treatment system calculation error: {e}")
            raise

    def _get_water_safety_recommendations(self, water_consumption: Dict[str, Any], pressure: Dict[str, Any]) -> List[str]:
        """Рекомендации по безопасности водоснабжения"""
        recommendations = []
        
        if not pressure.get("pressure_sufficient", False):
            recommendations.append("КРИТИЧНО: Недостаточное давление в системе водоснабжения")
            recommendations.append("Рекомендуется установка повысительной насосной станции")
        
        if water_consumption.get("specific_consumption", 0) > 50:
            recommendations.append("ВНИМАНИЕ: Высокое удельное водопотребление")
            recommendations.append("Рекомендуется установка приборов учета воды")
        
        recommendations.append("Установите обратные клапаны на вводе")
        recommendations.append("Обеспечьте резервирование водоснабжения")
        
        return recommendations

    # ===== ПОЖАРНАЯ БЕЗОПАСНОСТЬ =====

    def _execute_fire_safety_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчетов пожарной безопасности согласно СП 4.13130.2013, СП 5.13130.2009"""
        try:
            logger.info(f"🔍 [FIRE] Starting fire safety calculation")
            params = FireSafetyCalculationParams(**parameters)
            
            # 1. РАСЧЕТ ЭВАКУАЦИИ
            evacuation_calculation = self._calculate_evacuation_requirements(params)
            
            # 2. РАСЧЕТ СИСТЕМ ПОЖАРОТУШЕНИЯ
            fire_suppression = self._calculate_fire_suppression_systems(params)
            
            # 3. РАСЧЕТ ПРОТИВОДЫМНОЙ ЗАЩИТЫ
            smoke_control = self._calculate_smoke_control_systems(params)
            
            # 4. РАСЧЕТ ОГНЕСТОЙКОСТИ
            fire_resistance = self._calculate_fire_resistance_requirements(params)
            
            # 5. РАСЧЕТ АВАРИЙНЫХ СИСТЕМ
            emergency_systems = self._calculate_emergency_systems(params)
            
            return {
                "evacuation_calculation": evacuation_calculation,
                "fire_suppression": fire_suppression,
                "smoke_control": smoke_control,
                "fire_resistance": fire_resistance,
                "emergency_systems": emergency_systems,
                "normative_links": {
                    "СП 4.13130.2013": "Системы противопожарной защиты",
                    "СП 5.13130.2009": "Системы пожарной сигнализации и пожаротушения",
                    "СП 1.13130.2020": "Эвакуационные пути и выходы"
                },
                "safety_recommendations": self._get_fire_safety_recommendations(evacuation_calculation, fire_suppression)
            }
            
        except Exception as e:
            logger.error(f"❌ Fire safety calculation error: {e}")
            raise

    def _calculate_evacuation_requirements(self, params: FireSafetyCalculationParams) -> Dict[str, Any]:
        """Расчет требований к эвакуации"""
        try:
            # Время эвакуации
            evacuation_time = params.evacuation_time  # с
            
            # Ширина эвакуационных путей
            required_width = params.evacuation_capacity / 100  # м (100 чел/м)
            actual_width = params.evacuation_route_width
            
            # Длина эвакуационного пути
            max_evacuation_distance = 40 if params.building_type == "жилое" else 60  # м
            actual_distance = params.evacuation_route_length
            
            # Количество эвакуационных выходов
            required_exits = max(2, int(params.evacuation_capacity / 50))  # 1 выход на 50 чел
            actual_exits = params.emergency_exit_count
            
            # Проверка соответствия требованиям
            width_sufficient = actual_width >= required_width
            distance_sufficient = actual_distance <= max_evacuation_distance
            exits_sufficient = actual_exits >= required_exits
            
            return {
                "evacuation_time": evacuation_time,
                "required_width": required_width,
                "actual_width": actual_width,
                "width_sufficient": width_sufficient,
                "max_evacuation_distance": max_evacuation_distance,
                "actual_distance": actual_distance,
                "distance_sufficient": distance_sufficient,
                "required_exits": required_exits,
                "actual_exits": actual_exits,
                "exits_sufficient": exits_sufficient,
                "evacuation_capacity": params.evacuation_capacity
            }
            
        except Exception as e:
            logger.error(f"❌ Evacuation calculation error: {e}")
            raise

    def _calculate_fire_suppression_systems(self, params: FireSafetyCalculationParams) -> Dict[str, Any]:
        """Расчет систем пожаротушения"""
        try:
            # Площадь защищаемой зоны
            protected_area = params.fire_compartment_area  # м²
            
            # Требуемый расход воды для спринклеров
            sprinkler_flow = protected_area * params.sprinkler_density  # л/с
            
            # Количество спринклеров
            sprinkler_coverage = 12  # м² на спринклер
            sprinkler_count = int(protected_area / sprinkler_coverage) + 1
            
            # Требуемый расход для гидрантов
            hydrant_flow = params.fire_hydrant_flow  # л/с
            hydrant_count = max(2, int(sprinkler_flow / hydrant_flow))
            
            # Общий расход воды
            total_water_flow = sprinkler_flow + hydrant_flow * hydrant_count  # л/с
            
            # Объем воды для тушения
            water_volume = total_water_flow * 3600  # л (на 1 час)
            
            return {
                "protected_area": protected_area,
                "sprinkler_flow": sprinkler_flow,
                "sprinkler_count": sprinkler_count,
                "hydrant_flow": hydrant_flow,
                "hydrant_count": hydrant_count,
                "total_water_flow": total_water_flow,
                "water_volume": water_volume,
                "sprinkler_density": params.sprinkler_density
            }
            
        except Exception as e:
            logger.error(f"❌ Fire suppression calculation error: {e}")
            raise

    def _calculate_smoke_control_systems(self, params: FireSafetyCalculationParams) -> Dict[str, Any]:
        """Расчет противодымной защиты"""
        try:
            # Объем защищаемого помещения
            room_volume = params.building_volume  # м³
            
            # Скорость образования дыма
            smoke_generation = params.smoke_generation_rate  # кг/с
            
            # Требуемая производительность дымоудаления
            smoke_removal_rate = smoke_generation * 1000  # м³/с (плотность дыма ~1 кг/м³)
            
            # Количество дымовых извещателей
            detector_coverage = 25  # м² на извещатель
            detector_count = int(params.building_area / detector_coverage) + 1
            
            # Время заполнения дымом
            smoke_fill_time = room_volume / smoke_removal_rate if smoke_removal_rate > 0 else 0  # с
            
            return {
                "room_volume": room_volume,
                "smoke_generation": smoke_generation,
                "smoke_removal_rate": smoke_removal_rate,
                "detector_count": detector_count,
                "smoke_fill_time": smoke_fill_time,
                "detector_coverage": detector_coverage
            }
            
        except Exception as e:
            logger.error(f"❌ Smoke control calculation error: {e}")
            raise

    def _calculate_fire_resistance_requirements(self, params: FireSafetyCalculationParams) -> Dict[str, Any]:
        """Расчет требований к огнестойкости"""
        try:
            # Требуемые пределы огнестойкости по степени огнестойкости
            fire_resistance_limits = {
                "I": {"walls": 150, "floors": 120, "beams": 90},
                "II": {"walls": 120, "floors": 90, "beams": 60},
                "III": {"walls": 90, "floors": 60, "beams": 45},
                "IV": {"walls": 60, "floors": 45, "beams": 30},
                "V": {"walls": 30, "floors": 30, "beams": 15}
            }
            
            required_limits = fire_resistance_limits.get(params.fire_resistance_rating, fire_resistance_limits["II"])
            
            # Плотность пожарной нагрузки
            fire_load_density = params.fire_load_density  # МДж/м²
            
            # Класс пожарной опасности
            if fire_load_density <= 180:
                fire_hazard_class = "В1"
            elif fire_load_density <= 1400:
                fire_hazard_class = "В2"
            else:
                fire_hazard_class = "В3"
            
            return {
                "fire_resistance_rating": params.fire_resistance_rating,
                "required_limits": required_limits,
                "fire_load_density": fire_load_density,
                "fire_hazard_class": fire_hazard_class,
                "heat_release_rate": params.heat_release_rate
            }
            
        except Exception as e:
            logger.error(f"❌ Fire resistance calculation error: {e}")
            raise

    def _calculate_emergency_systems(self, params: FireSafetyCalculationParams) -> Dict[str, Any]:
        """Расчет аварийных систем"""
        try:
            # Система оповещения
            notification_zones = max(1, int(params.building_area / 1000))  # зон
            
            # Аварийное освещение
            emergency_lighting_power = params.building_area * 0.5  # Вт/м²
            
            # Система дымоудаления
            smoke_removal_fans = max(1, int(params.building_area / 500))  # вентиляторов
            
            # Система пожаротушения
            fire_extinguishers = params.fire_extinguisher_count
            required_extinguishers = max(1, int(params.building_area / 200))  # 1 на 200 м²
            
            return {
                "notification_zones": notification_zones,
                "emergency_lighting_power": emergency_lighting_power,
                "smoke_removal_fans": smoke_removal_fans,
                "fire_extinguishers": fire_extinguishers,
                "required_extinguishers": required_extinguishers,
                "extinguishers_sufficient": fire_extinguishers >= required_extinguishers
            }
            
        except Exception as e:
            logger.error(f"❌ Emergency systems calculation error: {e}")
            raise

    def _get_fire_safety_recommendations(self, evacuation: Dict[str, Any], suppression: Dict[str, Any]) -> List[str]:
        """Рекомендации по пожарной безопасности"""
        recommendations = []
        
        if not evacuation.get("width_sufficient", False):
            recommendations.append("КРИТИЧНО: Недостаточная ширина эвакуационных путей")
        
        if not evacuation.get("exits_sufficient", False):
            recommendations.append("КРИТИЧНО: Недостаточное количество эвакуационных выходов")
        
        if suppression.get("water_volume", 0) < 10000:
            recommendations.append("ВНИМАНИЕ: Недостаточный объем воды для пожаротушения")
        
        recommendations.append("Установите систему автоматической пожарной сигнализации")
        recommendations.append("Обеспечьте регулярное обслуживание противопожарных систем")
        
        return recommendations

    # ===== АКУСТИЧЕСКИЕ РАСЧЕТЫ =====

    def _execute_acoustic_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение акустических расчетов согласно СП 51.13330.2011"""
        try:
            logger.info(f"🔍 [ACOUSTIC] Starting acoustic calculation")
            params = AcousticCalculationParams(**parameters)
            
            # 1. РАСЧЕТ ЗВУКОИЗОЛЯЦИИ
            sound_insulation = self._calculate_sound_insulation(params)
            
            # 2. РАСЧЕТ КОНТРОЛЯ ШУМА
            noise_control = self._calculate_noise_control(params)
            
            # 3. РАСЧЕТ ВИБРОИЗОЛЯЦИИ
            vibration_control = self._calculate_vibration_control(params)
            
            # 4. РАСЧЕТ АКУСТИЧЕСКОЙ ОБРАБОТКИ
            acoustic_treatment = self._calculate_acoustic_treatment(params)
            
            # 5. РАСЧЕТ РЕВЕРБЕРАЦИИ
            reverberation = self._calculate_reverberation(params)
            
            return {
                "sound_insulation": sound_insulation,
                "noise_control": noise_control,
                "vibration_control": vibration_control,
                "acoustic_treatment": acoustic_treatment,
                "reverberation": reverberation,
                "normative_links": {
                    "СП 51.13330.2011": "Защита от шума",
                    "СН 2.2.4/2.1.8.562-96": "Шум на рабочих местах",
                    "СН 2.2.4/2.1.8.583-96": "Инфразвук на рабочих местах"
                },
                "safety_recommendations": self._get_acoustic_safety_recommendations(sound_insulation, noise_control)
            }
            
        except Exception as e:
            logger.error(f"❌ Acoustic calculation error: {e}")
            raise

    def _calculate_sound_insulation(self, params: AcousticCalculationParams) -> Dict[str, Any]:
        """Расчет звукоизоляции"""
        try:
            # Звукоизоляция стен
            wall_insulation = params.wall_sound_insulation  # дБ
            
            # Звукоизоляция пола
            floor_insulation = params.floor_sound_insulation  # дБ
            
            # Звукоизоляция потолка
            ceiling_insulation = params.ceiling_sound_insulation  # дБ
            
            # Общая звукоизоляция
            total_insulation = (wall_insulation + floor_insulation + ceiling_insulation) / 3  # дБ
            
            # Требуемая звукоизоляция по типу помещения
            required_insulation = {
                "жилое": 45,
                "общественное": 50,
                "производственное": 55
            }.get(params.room_type, 50)
            
            # Проверка соответствия требованиям
            meets_requirements = total_insulation >= required_insulation
            
            return {
                "wall_insulation": wall_insulation,
                "floor_insulation": floor_insulation,
                "ceiling_insulation": ceiling_insulation,
                "total_insulation": total_insulation,
                "required_insulation": required_insulation,
                "meets_requirements": meets_requirements,
                "wall_thickness": params.wall_thickness,
                "wall_material": params.wall_material
            }
            
        except Exception as e:
            logger.error(f"❌ Sound insulation calculation error: {e}")
            raise

    def _calculate_noise_control(self, params: AcousticCalculationParams) -> Dict[str, Any]:
        """Расчет контроля шума"""
        try:
            # Уровень шума от источника
            source_noise_level = params.noise_source_power  # дБ
            
            # Расстояние до источника
            distance = params.noise_source_distance  # м
            
            # Ослабление звука с расстоянием
            distance_attenuation = 20 * math.log10(distance) if distance > 0 else 0  # дБ
            
            # Уровень шума в помещении
            room_noise_level = source_noise_level - distance_attenuation  # дБ
            
            # Фоновый уровень шума
            background_level = params.background_noise_level  # дБ
            
            # Предельный уровень шума
            noise_limit = params.noise_level_limit  # дБ
            
            # Проверка превышения норм
            exceeds_limit = room_noise_level > noise_limit
            exceeds_background = room_noise_level > background_level + 10  # дБ
            
            return {
                "source_noise_level": source_noise_level,
                "distance_attenuation": distance_attenuation,
                "room_noise_level": room_noise_level,
                "background_level": background_level,
                "noise_limit": noise_limit,
                "exceeds_limit": exceeds_limit,
                "exceeds_background": exceeds_background,
                "noise_reduction_required": max(0, room_noise_level - noise_limit)
            }
            
        except Exception as e:
            logger.error(f"❌ Noise control calculation error: {e}")
            raise

    def _calculate_vibration_control(self, params: AcousticCalculationParams) -> Dict[str, Any]:
        """Расчет виброизоляции"""
        try:
            # Уровень вибрации
            vibration_level = params.vibration_level  # дБ
            
            # Частота вибрации
            frequency = params.vibration_frequency  # Гц
            
            # Виброизоляция
            vibration_insulation = params.vibration_insulation  # дБ
            
            # Уровень вибрации после изоляции
            isolated_vibration = vibration_level - vibration_insulation  # дБ
            
            # Предельный уровень вибрации
            vibration_limit = 80  # дБ
            
            # Проверка соответствия требованиям
            meets_vibration_requirements = isolated_vibration <= vibration_limit
            
            return {
                "vibration_level": vibration_level,
                "frequency": frequency,
                "vibration_insulation": vibration_insulation,
                "isolated_vibration": isolated_vibration,
                "vibration_limit": vibration_limit,
                "meets_requirements": meets_vibration_requirements
            }
            
        except Exception as e:
            logger.error(f"❌ Vibration control calculation error: {e}")
            raise

    def _calculate_acoustic_treatment(self, params: AcousticCalculationParams) -> Dict[str, Any]:
        """Расчет акустической обработки"""
        try:
            # Площадь помещения
            room_area = params.room_area  # м²
            
            # Площадь акустической обработки
            treatment_area = params.acoustic_treatment_area  # м²
            
            # Коэффициент звукопоглощения
            absorption_coefficient = params.sound_absorption_coefficient
            
            # Общее звукопоглощение
            total_absorption = treatment_area * absorption_coefficient  # м²
            
            # Рекомендуемая площадь обработки
            recommended_treatment_area = room_area * 0.3  # 30% от площади
            
            # Эффективность обработки
            treatment_efficiency = treatment_area / recommended_treatment_area if recommended_treatment_area > 0 else 0
            
            return {
                "room_area": room_area,
                "treatment_area": treatment_area,
                "absorption_coefficient": absorption_coefficient,
                "total_absorption": total_absorption,
                "recommended_treatment_area": recommended_treatment_area,
                "treatment_efficiency": treatment_efficiency
            }
            
        except Exception as e:
            logger.error(f"❌ Acoustic treatment calculation error: {e}")
            raise

    def _calculate_reverberation(self, params: AcousticCalculationParams) -> Dict[str, Any]:
        """Расчет времени реверберации"""
        try:
            # Объем помещения
            room_volume = params.room_volume  # м³
            
            # Площадь помещения
            room_area = params.room_area  # м²
            
            # Коэффициент звукопоглощения
            absorption_coefficient = params.sound_absorption_coefficient
            
            # Время реверберации по формуле Сэбина
            if absorption_coefficient > 0:
                reverberation_time = 0.16 * room_volume / (room_area * absorption_coefficient)  # с
            else:
                reverberation_time = 2.0  # с (большое значение при отсутствии поглощения)
            
            # Оптимальное время реверберации
            optimal_reverberation = {
                "жилое": 0.6,
                "общественное": 0.8,
                "производственное": 1.0
            }.get(params.room_type, 0.8)
            
            # Проверка соответствия требованиям
            meets_requirements = abs(reverberation_time - optimal_reverberation) <= 0.2
            
            return {
                "reverberation_time": reverberation_time,
                "optimal_reverberation": optimal_reverberation,
                "meets_requirements": meets_requirements,
                "room_volume": room_volume,
                "absorption_coefficient": absorption_coefficient
            }
            
        except Exception as e:
            logger.error(f"❌ Reverberation calculation error: {e}")
            raise

    def _get_acoustic_safety_recommendations(self, sound_insulation: Dict[str, Any], noise_control: Dict[str, Any]) -> List[str]:
        """Рекомендации по акустической безопасности"""
        recommendations = []
        
        if not sound_insulation.get("meets_requirements", False):
            recommendations.append("КРИТИЧНО: Недостаточная звукоизоляция")
            recommendations.append("Рекомендуется увеличение толщины стен или использование звукоизоляционных материалов")
        
        if noise_control.get("exceeds_limit", False):
            recommendations.append("КРИТИЧНО: Превышение предельного уровня шума")
            recommendations.append("Рекомендуется установка шумопоглощающих экранов")
        
        recommendations.append("Установите виброизоляцию для оборудования")
        recommendations.append("Обеспечьте акустическую обработку помещений")
        
        return recommendations

    # ===== ОСВЕЩЕНИЕ И ИНСОЛЯЦИЯ =====

    def _execute_lighting_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчетов освещения и инсоляции согласно СП 52.13330.2016"""
        try:
            logger.info(f"🔍 [LIGHTING] Starting lighting calculation")
            params = LightingCalculationParams(**parameters)
            
            # 1. РАСЧЕТ ИСКУССТВЕННОГО ОСВЕЩЕНИЯ
            artificial_lighting = self._calculate_artificial_lighting(params)
            
            # 2. РАСЧЕТ ЕСТЕСТВЕННОГО ОСВЕЩЕНИЯ
            natural_lighting = self._calculate_natural_lighting(params)
            
            # 3. РАСЧЕТ ИНСОЛЯЦИИ
            insolation = self._calculate_insolation(params)
            
            # 4. РАСЧЕТ СВЕТИЛЬНИКОВ
            luminaire_calculation = self._calculate_luminaires(params)
            
            # 5. РАСЧЕТ ЭНЕРГОЭФФЕКТИВНОСТИ ОСВЕЩЕНИЯ
            energy_efficiency = self._calculate_lighting_energy_efficiency(params, artificial_lighting)
            
            return {
                "artificial_lighting": artificial_lighting,
                "natural_lighting": natural_lighting,
                "insolation": insolation,
                "luminaire_calculation": luminaire_calculation,
                "energy_efficiency": energy_efficiency,
                "normative_links": {
                    "СП 52.13330.2016": "Естественное и искусственное освещение",
                    "СНиП 23-05-95": "Естественное и искусственное освещение",
                    "СП 131.13330.2018": "Строительная климатология"
                },
                "safety_recommendations": self._get_lighting_safety_recommendations(artificial_lighting, natural_lighting)
            }
            
        except Exception as e:
            logger.error(f"❌ Lighting calculation error: {e}")
            raise

    def _calculate_artificial_lighting(self, params: LightingCalculationParams) -> Dict[str, Any]:
        """Расчет искусственного освещения"""
        try:
            # Требуемая освещенность
            required_illuminance = params.required_illuminance  # лк
            
            # Площадь помещения
            room_area = params.room_area  # м²
            
            # Световой поток светильника
            luminaire_flux = params.light_source_power * params.light_source_efficiency  # лм
            
            # КПД светильника
            luminaire_efficiency = params.luminaire_efficiency
            
            # Коэффициент использования
            utilization_factor = 0.6  # зависит от типа помещения и светильника
            
            # Коэффициент запаса
            maintenance_factor = 0.8  # учитывает загрязнение и старение
            
            # Требуемый световой поток
            required_flux = (required_illuminance * room_area) / (utilization_factor * maintenance_factor)  # лм
            
            # Количество светильников
            luminaire_count = int(required_flux / (luminaire_flux * luminaire_efficiency)) + 1
            
            # Фактическая освещенность
            actual_illuminance = (luminaire_count * luminaire_flux * luminaire_efficiency * utilization_factor * maintenance_factor) / room_area  # лк
            
            # Проверка соответствия требованиям
            meets_requirements = actual_illuminance >= required_illuminance
            
            return {
                "required_illuminance": required_illuminance,
                "actual_illuminance": actual_illuminance,
                "luminaire_count": luminaire_count,
                "luminaire_flux": luminaire_flux,
                "utilization_factor": utilization_factor,
                "maintenance_factor": maintenance_factor,
                "meets_requirements": meets_requirements,
                "light_source_type": params.light_source_type,
                "light_source_power": params.light_source_power
            }
            
        except Exception as e:
            logger.error(f"❌ Artificial lighting calculation error: {e}")
            raise

    def _calculate_natural_lighting(self, params: LightingCalculationParams) -> Dict[str, Any]:
        """Расчет естественного освещения"""
        try:
            # Площадь окон
            window_area = params.window_area  # м²
            
            # Площадь помещения
            room_area = params.room_area  # м²
            
            # Коэффициент естественной освещенности
            daylight_factor = (window_area / room_area) * 100 if room_area > 0 else 0  # %
            
            # Коэффициент затенения
            shading_factor = params.shading_factor
            
            # Эффективная площадь остекления
            effective_window_area = window_area * shading_factor  # м²
            
            # Световой коэффициент
            light_coefficient = effective_window_area / room_area if room_area > 0 else 0
            
            # Требуемый коэффициент естественной освещенности
            required_daylight_factor = {
                "жилое": 0.5,
                "общественное": 1.0,
                "производственное": 2.0
            }.get(params.room_type, 1.0)
            
            # Проверка соответствия требованиям
            meets_requirements = daylight_factor >= required_daylight_factor
            
            return {
                "window_area": window_area,
                "effective_window_area": effective_window_area,
                "daylight_factor": daylight_factor,
                "required_daylight_factor": required_daylight_factor,
                "light_coefficient": light_coefficient,
                "shading_factor": shading_factor,
                "meets_requirements": meets_requirements,
                "window_count": params.window_count,
                "window_orientation": params.window_orientation
            }
            
        except Exception as e:
            logger.error(f"❌ Natural lighting calculation error: {e}")
            raise

    def _calculate_insolation(self, params: LightingCalculationParams) -> Dict[str, Any]:
        """Расчет инсоляции"""
        try:
            # Продолжительность инсоляции
            insolation_duration = params.insolation_duration  # ч
            
            # Угол инсоляции
            insolation_angle = params.insolation_angle  # градусы
            
            # Расстояние между зданиями
            building_spacing = params.building_spacing  # м
            
            # Высота соседнего здания
            adjacent_height = params.building_height_adjacent  # м
            
            # Угол затенения
            shading_angle = math.degrees(math.atan(adjacent_height / building_spacing)) if building_spacing > 0 else 0  # градусы
            
            # Эффективность инсоляции
            insolation_efficiency = max(0, 1 - (shading_angle / 90))  # 0-1
            
            # Требуемая продолжительность инсоляции
            required_insolation = {
                "жилое": 3.0,
                "общественное": 2.0,
                "производственное": 1.0
            }.get(params.room_type, 2.0)
            
            # Проверка соответствия требованиям
            meets_requirements = insolation_duration >= required_insolation
            
            return {
                "insolation_duration": insolation_duration,
                "required_insolation": required_insolation,
                "insolation_angle": insolation_angle,
                "shading_angle": shading_angle,
                "insolation_efficiency": insolation_efficiency,
                "meets_requirements": meets_requirements,
                "building_spacing": building_spacing,
                "adjacent_height": adjacent_height
            }
            
        except Exception as e:
            logger.error(f"❌ Insolation calculation error: {e}")
            raise

    def _calculate_luminaires(self, params: LightingCalculationParams) -> Dict[str, Any]:
        """Расчет светильников"""
        try:
            # Площадь помещения
            room_area = params.room_area  # м²
            
            # Шаг светильников
            luminaire_spacing = params.luminaire_spacing  # м
            
            # Высота подвеса
            luminaire_height = params.luminaire_height  # м
            
            # Количество светильников по длине
            length_count = int(params.room_length / luminaire_spacing) + 1
            
            # Количество светильников по ширине
            width_count = int(params.room_width / luminaire_spacing) + 1
            
            # Общее количество светильников
            total_luminaires = length_count * width_count
            
            # Равномерность освещения
            uniformity = min(1.0, total_luminaires / (room_area / (luminaire_spacing ** 2)))  # 0-1
            
            return {
                "total_luminaires": total_luminaires,
                "length_count": length_count,
                "width_count": width_count,
                "luminaire_spacing": luminaire_spacing,
                "luminaire_height": luminaire_height,
                "uniformity": uniformity,
                "luminaire_efficiency": params.luminaire_efficiency
            }
            
        except Exception as e:
            logger.error(f"❌ Luminaire calculation error: {e}")
            raise

    def _calculate_lighting_energy_efficiency(self, params: LightingCalculationParams, artificial_lighting: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет энергоэффективности освещения"""
        try:
            # Общая мощность освещения
            total_power = artificial_lighting.get("luminaire_count", 0) * params.light_source_power  # Вт
            
            # Удельная мощность освещения
            specific_power = total_power / params.room_area if params.room_area > 0 else 0  # Вт/м²
            
            # Нормативная удельная мощность
            normative_specific_power = {
                "жилое": 10,
                "общественное": 15,
                "производственное": 20
            }.get(params.room_type, 15)
            
            # Класс энергоэффективности
            if specific_power <= normative_specific_power * 0.5:
                efficiency_class = "A+"
            elif specific_power <= normative_specific_power * 0.7:
                efficiency_class = "A"
            elif specific_power <= normative_specific_power:
                efficiency_class = "B"
            elif specific_power <= normative_specific_power * 1.3:
                efficiency_class = "C"
            else:
                efficiency_class = "D"
            
            # Энергосбережение
            energy_savings = max(0, (specific_power - normative_specific_power) * params.room_area)  # Вт
            
            return {
                "total_power": total_power,
                "specific_power": specific_power,
                "normative_specific_power": normative_specific_power,
                "efficiency_class": efficiency_class,
                "energy_savings": energy_savings,
                "meets_requirements": specific_power <= normative_specific_power
            }
            
        except Exception as e:
            logger.error(f"❌ Lighting energy efficiency calculation error: {e}")
            raise

    def _get_lighting_safety_recommendations(self, artificial_lighting: Dict[str, Any], natural_lighting: Dict[str, Any]) -> List[str]:
        """Рекомендации по безопасности освещения"""
        recommendations = []
        
        if not artificial_lighting.get("meets_requirements", False):
            recommendations.append("КРИТИЧНО: Недостаточная освещенность")
            recommendations.append("Рекомендуется увеличение количества светильников или их мощности")
        
        if not natural_lighting.get("meets_requirements", False):
            recommendations.append("ВНИМАНИЕ: Недостаточное естественное освещение")
            recommendations.append("Рекомендуется увеличение площади окон")
        
        recommendations.append("Обеспечьте равномерность освещения")
        recommendations.append("Используйте энергоэффективные источники света")
        
        return recommendations

    # ===== ИНЖЕНЕРНО-ГЕОЛОГИЧЕСКИЕ РАСЧЕТЫ =====

    def _execute_geological_calculation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение инженерно-геологических расчетов согласно СП 22.13330.2016"""
        try:
            logger.info(f"🔍 [GEOLOGICAL] Starting geological calculation")
            params = GeologicalCalculationParams(**parameters)
            
            # 1. РАСЧЕТ НЕСУЩЕЙ СПОСОБНОСТИ
            bearing_capacity = self._calculate_bearing_capacity(params)
            
            # 2. РАСЧЕТ ОСАДОК
            settlement = self._calculate_settlement(params)
            
            # 3. РАСЧЕТ УСТОЙЧИВОСТИ СКЛОНОВ
            slope_stability = self._calculate_slope_stability(params)
            
            # 4. СЕЙСМИЧЕСКИЙ АНАЛИЗ
            seismic_analysis = self._calculate_seismic_analysis(params)
            
            # 5. РАСЧЕТ ГРУНТОВЫХ ВОД
            groundwater = self._calculate_groundwater(params)
            
            return {
                "bearing_capacity": bearing_capacity,
                "settlement": settlement,
                "slope_stability": slope_stability,
                "seismic_analysis": seismic_analysis,
                "groundwater": groundwater,
                "normative_links": {
                    "СП 22.13330.2016": "Основания зданий и сооружений",
                    "СП 20.13330.2016": "Нагрузки и воздействия",
                    "СП 14.13330.2018": "Строительство в сейсмических районах"
                },
                "safety_recommendations": self._get_geological_safety_recommendations(bearing_capacity, settlement)
            }
            
        except Exception as e:
            logger.error(f"❌ Geological calculation error: {e}")
            raise

    def _calculate_bearing_capacity(self, params: GeologicalCalculationParams) -> Dict[str, Any]:
        """Расчет несущей способности грунта"""
        try:
            # Параметры грунта
            soil_density = params.soil_density  # кг/м³
            angle_of_friction = params.angle_of_internal_friction  # градусы
            cohesion = params.cohesion  # кПа
            bearing_capacity = params.bearing_capacity  # кПа
            
            # Параметры фундамента
            foundation_width = params.foundation_width  # м
            foundation_depth = params.foundation_depth  # м
            
            # Нагрузки
            building_weight = params.building_weight  # кН
            live_load = params.live_load  # кН/м²
            
            # Площадь фундамента
            foundation_area = foundation_width * params.foundation_length  # м²
            
            # Напряжение под подошвой фундамента
            foundation_pressure = (building_weight + live_load * foundation_area) / foundation_area  # кПа
            
            # Коэффициент безопасности
            safety_factor = 2.5  # для жилых зданий
            
            # Допустимое давление
            allowable_pressure = bearing_capacity / safety_factor  # кПа
            
            # Проверка несущей способности
            meets_requirements = foundation_pressure <= allowable_pressure
            
            return {
                "soil_density": soil_density,
                "angle_of_friction": angle_of_friction,
                "cohesion": cohesion,
                "bearing_capacity": bearing_capacity,
                "foundation_pressure": foundation_pressure,
                "allowable_pressure": allowable_pressure,
                "safety_factor": safety_factor,
                "meets_requirements": meets_requirements,
                "foundation_area": foundation_area,
                "soil_type": params.soil_type
            }
            
        except Exception as e:
            logger.error(f"❌ Bearing capacity calculation error: {e}")
            raise

    def _calculate_settlement(self, params: GeologicalCalculationParams) -> Dict[str, Any]:
        """Расчет осадок фундамента"""
        try:
            # Модуль деформации грунта
            compression_modulus = params.compression_modulus  # МПа
            
            # Напряжение под подошвой фундамента
            foundation_pressure = params.building_weight / (params.foundation_width * params.foundation_length)  # кПа
            
            # Коэффициент Пуассона
            poisson_ratio = 0.3  # для большинства грунтов
            
            # Коэффициент формы фундамента
            shape_factor = 1.0  # для ленточного фундамента
            
            # Осадка по методу послойного суммирования
            settlement = (foundation_pressure * params.foundation_width * shape_factor) / (compression_modulus * 1000)  # м
            
            # Предельная осадка
            max_settlement = {
                "ленточный": 0.1,
                "плитный": 0.15,
                "свайный": 0.08
            }.get(params.foundation_type, 0.1)  # м
            
            # Проверка соответствия требованиям
            meets_requirements = settlement <= max_settlement
            
            return {
                "settlement": settlement,
                "max_settlement": max_settlement,
                "compression_modulus": compression_modulus,
                "foundation_pressure": foundation_pressure,
                "meets_requirements": meets_requirements,
                "poisson_ratio": poisson_ratio,
                "shape_factor": shape_factor
            }
            
        except Exception as e:
            logger.error(f"❌ Settlement calculation error: {e}")
            raise

    def _calculate_slope_stability(self, params: GeologicalCalculationParams) -> Dict[str, Any]:
        """Расчет устойчивости склонов"""
        try:
            # Параметры грунта
            soil_density = params.soil_density  # кг/м³
            angle_of_friction = math.radians(params.angle_of_internal_friction)  # радианы
            cohesion = params.cohesion  # кПа
            
            # Угол склона (предполагаемый)
            slope_angle = math.radians(30)  # радианы
            
            # Высота склона
            slope_height = 5.0  # м
            
            # Коэффициент устойчивости по методу Феллениуса
            stability_factor = (cohesion + (soil_density * 9.81 * slope_height * math.cos(slope_angle) * math.tan(angle_of_friction))) / (soil_density * 9.81 * slope_height * math.sin(slope_angle))
            
            # Минимальный коэффициент устойчивости
            min_stability_factor = 1.3
            
            # Проверка устойчивости
            is_stable = stability_factor >= min_stability_factor
            
            return {
                "stability_factor": stability_factor,
                "min_stability_factor": min_stability_factor,
                "is_stable": is_stable,
                "slope_angle": math.degrees(slope_angle),
                "slope_height": slope_height,
                "soil_density": soil_density,
                "angle_of_friction": params.angle_of_internal_friction
            }
            
        except Exception as e:
            logger.error(f"❌ Slope stability calculation error: {e}")
            raise

    def _calculate_seismic_analysis(self, params: GeologicalCalculationParams) -> Dict[str, Any]:
        """Сейсмический анализ"""
        try:
            # Сейсмическая интенсивность
            seismic_intensity = params.seismic_intensity  # баллы
            
            # Сейсмический коэффициент
            seismic_coefficient = params.seismic_coefficient
            
            # Высота здания
            building_height = 10.0  # м (предполагаемая)
            
            # Коэффициент динамичности
            dynamic_coefficient = 1.0 + 0.1 * seismic_intensity
            
            # Сейсмическая нагрузка
            seismic_load = seismic_coefficient * dynamic_coefficient * params.building_weight  # кН
            
            # Требования к сейсмостойкости
            seismic_requirements_met = seismic_intensity <= 7  # для большинства зданий
            
            return {
                "seismic_intensity": seismic_intensity,
                "seismic_coefficient": seismic_coefficient,
                "dynamic_coefficient": dynamic_coefficient,
                "seismic_load": seismic_load,
                "seismic_requirements_met": seismic_requirements_met,
                "building_height": building_height
            }
            
        except Exception as e:
            logger.error(f"❌ Seismic analysis calculation error: {e}")
            raise

    def _calculate_groundwater(self, params: GeologicalCalculationParams) -> Dict[str, Any]:
        """Расчет влияния грунтовых вод"""
        try:
            # Уровень грунтовых вод
            groundwater_level = params.groundwater_level  # м
            
            # Глубина заложения фундамента
            foundation_depth = params.foundation_depth  # м
            
            # Влияние грунтовых вод на фундамент
            water_affects_foundation = groundwater_level < foundation_depth
            
            # Подъемная сила
            buoyancy_force = 9.81 * 1000 * params.site_area * (foundation_depth - groundwater_level) if water_affects_foundation else 0  # кН
            
            # Рекомендации по дренажу
            drainage_required = groundwater_level < foundation_depth + 0.5  # м
            
            return {
                "groundwater_level": groundwater_level,
                "foundation_depth": foundation_depth,
                "water_affects_foundation": water_affects_foundation,
                "buoyancy_force": buoyancy_force,
                "drainage_required": drainage_required,
                "site_area": params.site_area
            }
            
        except Exception as e:
            logger.error(f"❌ Groundwater calculation error: {e}")
            raise

    def _get_geological_safety_recommendations(self, bearing_capacity: Dict[str, Any], settlement: Dict[str, Any]) -> List[str]:
        """Рекомендации по геологической безопасности"""
        recommendations = []
        
        if not bearing_capacity.get("meets_requirements", False):
            recommendations.append("КРИТИЧНО: Недостаточная несущая способность грунта")
            recommendations.append("Рекомендуется увеличение площади фундамента или замена грунта")
        
        if not settlement.get("meets_requirements", False):
            recommendations.append("КРИТИЧНО: Превышение допустимых осадок")
            recommendations.append("Рекомендуется устройство свайного фундамента")
        
        recommendations.append("Проведите дополнительные геологические изыскания")
        recommendations.append("Обеспечьте дренаж при высоком уровне грунтовых вод")
        
        return recommendations


# Глобальный экземпляр движка расчетов
calculation_engine = CalculationEngine()
