"""
Pydantic модели для calculation_service
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CalculationCreate(BaseModel):
    """Модель для создания расчета"""
    name: str = Field(..., description="Название расчета")
    description: Optional[str] = Field(None, description="Описание расчета")
    type: str = Field(..., description="Тип расчета")
    category: str = Field(..., description="Категория расчета")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры расчета")


class CalculationResponse(BaseModel):
    """Модель для ответа с данными расчета"""
    id: int
    name: str
    description: Optional[str]
    type: str
    category: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int]


class CalculationUpdate(BaseModel):
    """Модель для обновления расчета"""
    name: Optional[str] = Field(None, description="Название расчета")
    description: Optional[str] = Field(None, description="Описание расчета")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Параметры расчета")


class CalculationExecute(BaseModel):
    """Модель для выполнения расчета"""
    parameters: Dict[str, Any] = Field(..., description="Параметры для выполнения расчета")


class CalculationResult(BaseModel):
    """Модель для результата расчета"""
    calculation_id: int
    results: Dict[str, Any]
    execution_time: float
    status: str
    error_message: Optional[str] = None


class User(BaseModel):
    """Модель пользователя"""
    id: str
    username: str
    email: str
    role: str
    permissions: List[str]


class TokenData(BaseModel):
    """Модель данных токена"""
    username: str
    user_id: str
    role: str


class HealthResponse(BaseModel):
    """Модель для ответа health check"""
    status: str
    timestamp: datetime
    uptime: float
    version: str
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    """Модель для ответа с ошибкой"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class StructuralCalculationParams(BaseModel):
    """Параметры для расчета строительных конструкций"""
    # Основные параметры
    beam_length: float = Field(..., description="Длина балки (м)")
    beam_width: float = Field(..., description="Ширина балки (м)")
    beam_height: float = Field(..., description="Высота балки (м)")
    material_strength: float = Field(..., description="Прочность материала (МПа)")
    load_value: float = Field(..., description="Нагрузка (кН/м)")
    
    # Дополнительные параметры
    safety_factor: float = Field(1.5, description="Коэффициент безопасности")
    deflection_limit: float = Field(1.0/250, description="Предел прогиба")


class FoundationCalculationParams(BaseModel):
    """Параметры для расчета оснований и фундаментов"""
    # Основные параметры
    foundation_width: float = Field(..., description="Ширина фундамента (м)")
    foundation_length: float = Field(..., description="Длина фундамента (м)")
    foundation_depth: float = Field(..., description="Глубина заложения (м)")
    soil_cohesion: float = Field(..., description="Сцепление грунта (кПа)")
    soil_friction_angle: float = Field(..., description="Угол внутреннего трения (град)")
    soil_density: float = Field(..., description="Плотность грунта (т/м³)")
    
    # Дополнительные параметры
    safety_factor: float = Field(2.0, description="Коэффициент безопасности")
    water_table_depth: Optional[float] = Field(None, description="Глубина залегания грунтовых вод (м)")


class ThermalCalculationParams(BaseModel):
    """Параметры для теплотехнических расчетов согласно СП 50.13330.2012"""
    # Основные параметры здания
    building_type: str = Field(..., description="Тип здания (жилое/общественное/производственное)")
    building_area: float = Field(..., description="Площадь здания (м²)")
    building_volume: float = Field(..., description="Объем здания (м³)")
    number_of_floors: int = Field(..., description="Количество этажей")
    
    # Параметры ограждающих конструкций
    wall_thickness: float = Field(..., description="Толщина стены (м)")
    wall_material: str = Field(..., description="Материал стены")
    thermal_conductivity: float = Field(..., description="Теплопроводность (Вт/(м·К))")
    wall_area: float = Field(..., description="Площадь стен (м²)")
    
    # Параметры окон
    window_area: float = Field(0, description="Площадь окон (м²)")
    window_thermal_conductivity: float = Field(2.8, description="Теплопроводность окон (Вт/(м²·К))")
    window_frame_material: str = Field("ПВХ", description="Материал оконных рам")
    
    # Параметры пола
    floor_area: float = Field(..., description="Площадь пола (м²)")
    floor_thickness: float = Field(0.2, description="Толщина пола (м)")
    floor_thermal_conductivity: float = Field(1.5, description="Теплопроводность пола (Вт/(м·К))")
    
    # Параметры потолка/крыши
    ceiling_area: float = Field(..., description="Площадь потолка (м²)")
    ceiling_thickness: float = Field(0.3, description="Толщина потолка (м)")
    ceiling_thermal_conductivity: float = Field(0.8, description="Теплопроводность потолка (Вт/(м·К))")
    
    # Климатические параметры
    indoor_temperature: float = Field(20, description="Внутренняя температура (°C)")
    outdoor_temperature: float = Field(-25, description="Наружная температура (°C)")
    relative_humidity: float = Field(55, description="Относительная влажность (%)")
    wind_speed: float = Field(5.0, description="Скорость ветра (м/с)")
    
    # Коэффициенты теплоотдачи
    heat_transfer_coefficient_inner: float = Field(8.7, description="Коэффициент теплоотдачи внутренней поверхности (Вт/(м²·К))")
    heat_transfer_coefficient_outer: float = Field(23, description="Коэффициент теплоотдачи наружной поверхности (Вт/(м²·К))")
    
    # Параметры вентиляции
    air_exchange_rate: float = Field(0.5, description="Кратность воздухообмена (1/ч)")
    ventilation_heat_loss: float = Field(0, description="Теплопотери на вентиляцию (Вт)")
    
    # Тепловыделения
    heat_emission_people: float = Field(0, description="Тепловыделения от людей (Вт)")
    heat_emission_equipment: float = Field(0, description="Тепловыделения от оборудования (Вт)")
    heat_emission_lighting: float = Field(0, description="Тепловыделения от освещения (Вт)")
    
    # Нормативные требования
    normative_heat_transfer_resistance: float = Field(3.2, description="Нормативное сопротивление теплопередаче (м²·К/Вт)")
    energy_efficiency_class: str = Field("B", description="Класс энергоэффективности")
    
    # Нормативные документы
    normative_document: str = Field("СП 50.13330.2012", description="Нормативный документ")


class VentilationCalculationParams(BaseModel):
    """Параметры для расчета вентиляции согласно СП 60.13330.2016"""
    # Основные параметры помещения
    room_volume: float = Field(..., description="Объем помещения (м³)")
    room_area: float = Field(..., description="Площадь помещения (м²)")
    room_height: float = Field(..., description="Высота помещения (м)")
    room_type: str = Field(..., description="Тип помещения (жилое, общественное, производственное)")
    occupancy: int = Field(1, description="Количество людей в помещении")
    
    # Параметры воздухообмена
    air_exchange_rate: Optional[float] = Field(None, description="Кратность воздухообмена (1/ч)")
    air_exchange_per_person: Optional[float] = Field(None, description="Воздухообмен на человека (м³/ч·чел)")
    air_exchange_per_area: Optional[float] = Field(None, description="Воздухообмен на площадь (м³/ч·м²)")
    
    # Температурные параметры
    supply_air_temperature: float = Field(20, description="Температура приточного воздуха (°C)")
    exhaust_air_temperature: float = Field(22, description="Температура вытяжного воздуха (°C)")
    outdoor_temperature: float = Field(-25, description="Температура наружного воздуха (°C)")
    
    # Вредные выделения (СП 60.13330.2016)
    co2_emission_per_person: float = Field(0.02, description="Выделение CO₂ на человека (м³/ч)")
    moisture_emission_per_person: float = Field(0.05, description="Выделение влаги на человека (кг/ч)")
    heat_emission_per_person: float = Field(120, description="Тепловыделения на человека (Вт)")
    heat_emission_from_equipment: float = Field(0, description="Тепловыделения от оборудования (Вт)")
    
    # Параметры микроклимата
    relative_humidity: float = Field(50, description="Относительная влажность (%)")
    air_velocity: float = Field(0.2, description="Скорость движения воздуха (м/с)")
    
    # Физические свойства воздуха
    air_density: float = Field(1.2, description="Плотность воздуха (кг/м³)")
    specific_heat: float = Field(1005, description="Удельная теплоемкость воздуха (Дж/(кг·К))")
    
    # Параметры системы вентиляции
    ventilation_type: str = Field("mechanical", description="Тип вентиляции (natural, mechanical, mixed)")
    heat_recovery_efficiency: float = Field(0, description="КПД рекуперации тепла (0-1)")
    fan_efficiency: float = Field(0.7, description="КПД вентилятора (0-1)")
    
    # Противодымная вентиляция (НПБ 250-97)
    smoke_ventilation_required: bool = Field(False, description="Требуется ли противодымная вентиляция")
    evacuation_route: bool = Field(False, description="Является ли помещение эвакуационным путем")
    fire_compartment_area: Optional[float] = Field(None, description="Площадь пожарного отсека (м²)")
    
    # Акустические параметры
    noise_level_limit: float = Field(40, description="Предельный уровень шума (дБА)")
    
    # Энергоэффективность
    energy_efficiency_class: str = Field("B", description="Класс энергоэффективности (A, B, C, D, E)")


class DegasificationCalculationParams(BaseModel):
    """Параметры для расчета дегазации угольных шахт"""
    # Основные параметры шахты
    mine_depth: float = Field(..., description="Глубина шахты (м)")
    mine_area: float = Field(..., description="Площадь шахты (м²)")
    coal_seam_thickness: float = Field(..., description="Мощность угольного пласта (м)")
    methane_content: float = Field(..., description="Содержание метана в угле (%)")
    
    # Параметры дегазации
    extraction_rate: float = Field(..., description="Скорость отработки (м/сут)")
    methane_emission_rate: float = Field(..., description="Интенсивность выделения метана (м³/т)")
    ventilation_air_flow: float = Field(..., description="Расход вентиляционного воздуха (м³/с)")
    
    # Безопасность
    methane_concentration_limit: float = Field(1.0, description="Предельная концентрация метана (%)")
    safety_factor: float = Field(2.0, description="Коэффициент безопасности")
    
    # Нормативные требования
    normative_document: str = Field("ГОСТ Р 55154-2012", description="Нормативный документ")
    safety_requirements: str = Field("ПБ 05-618-03", description="Правила безопасности")


class ElectricalLoadCalculationParams(BaseModel):
    """Параметры для расчета электрических нагрузок (СП 31.110-2003)"""
    # Основные параметры здания
    building_type: str = Field(..., description="Тип здания (жилое/общественное)")
    total_area: float = Field(..., description="Общая площадь здания (м²)")
    number_of_floors: int = Field(..., description="Количество этажей")
    number_of_apartments: int = Field(0, description="Количество квартир")
    
    # Электрические нагрузки
    lighting_load: float = Field(..., description="Нагрузка освещения (Вт/м²)")
    power_load: float = Field(..., description="Силовая нагрузка (Вт/м²)")
    heating_load: float = Field(0, description="Нагрузка отопления (Вт/м²)")
    ventilation_load: float = Field(0, description="Нагрузка вентиляции (Вт/м²)")
    
    # Коэффициенты
    demand_factor: float = Field(0.7, description="Коэффициент спроса")
    diversity_factor: float = Field(0.8, description="Коэффициент разновременности")
    power_factor: float = Field(0.9, description="Коэффициент мощности")
    
    # Нормативные документы
    normative_document: str = Field("СП 31.110-2003", description="Нормативный документ")


class CableCalculationParams(BaseModel):
    """Параметры для расчета сечений кабелей (СП 31.110-2003)"""
    # Параметры нагрузки
    load_current: float = Field(..., description="Расчетный ток нагрузки (А)")
    voltage: float = Field(380, description="Номинальное напряжение (В)")
    power: float = Field(..., description="Мощность нагрузки (кВт)")
    
    # Параметры прокладки
    installation_method: str = Field("в трубе", description="Способ прокладки")
    ambient_temperature: float = Field(25, description="Температура окружающей среды (°C)")
    cable_length: float = Field(..., description="Длина кабеля (м)")
    number_of_cores: int = Field(3, description="Количество жил")
    
    # Материал кабеля
    conductor_material: str = Field("медь", description="Материал проводника")
    insulation_material: str = Field("ПВХ", description="Материал изоляции")
    
    # Коэффициенты
    temperature_correction: float = Field(1.0, description="Температурный коэффициент")
    grouping_factor: float = Field(1.0, description="Коэффициент группировки")
    
    # Нормативные документы
    normative_document: str = Field("СП 31.110-2003", description="Нормативный документ")


class GroundingCalculationParams(BaseModel):
    """Параметры для расчета заземления (СП 31.110-2003)"""
    # Параметры здания
    building_type: str = Field(..., description="Тип здания")
    building_area: float = Field(..., description="Площадь здания (м²)")
    soil_resistivity: float = Field(..., description="Удельное сопротивление грунта (Ом·м)")
    
    # Параметры заземлителя
    grounding_type: str = Field("контурный", description="Тип заземлителя")
    electrode_material: str = Field("сталь", description="Материал электродов")
    electrode_diameter: float = Field(0.02, description="Диаметр электродов (м)")
    electrode_length: float = Field(2.5, description="Длина электродов (м)")
    electrode_spacing: float = Field(5.0, description="Расстояние между электродами (м)")
    
    # Требования
    max_ground_resistance: float = Field(4.0, description="Максимальное сопротивление заземления (Ом)")
    safety_factor: float = Field(1.2, description="Коэффициент безопасности")
    
    # Нормативные документы
    normative_document: str = Field("СП 31.110-2003", description="Нормативный документ")


class LightningProtectionCalculationParams(BaseModel):
    """Параметры для расчета молниезащиты (СП 437.1325800.2018)"""
    # Параметры здания
    building_height: float = Field(..., description="Высота здания (м)")
    building_length: float = Field(..., description="Длина здания (м)")
    building_width: float = Field(..., description="Ширина здания (м)")
    building_type: str = Field(..., description="Тип здания")
    
    # Параметры молниезащиты
    protection_level: str = Field("II", description="Уровень молниезащиты")
    lightning_density: float = Field(4.0, description="Плотность разрядов молнии (1/(км²·год))")
    soil_resistivity: float = Field(100, description="Удельное сопротивление грунта (Ом·м)")
    
    # Материалы
    conductor_material: str = Field("сталь", description="Материал токоотводов")
    conductor_diameter: float = Field(0.008, description="Диаметр токоотводов (м)")
    
    # Коэффициенты
    safety_factor: float = Field(1.3, description="Коэффициент безопасности")
    
    # Нормативные документы
    normative_document: str = Field("СП 437.1325800.2018", description="Нормативный документ")


class EnergyEfficiencyCalculationParams(BaseModel):
    """Параметры для расчета энергоэффективности (СП 256.1325800.2016)"""
    # Параметры здания
    building_type: str = Field(..., description="Тип здания")
    building_area: float = Field(..., description="Площадь здания (м²)")
    building_volume: float = Field(..., description="Объем здания (м³)")
    number_of_floors: int = Field(..., description="Количество этажей")
    
    # Энергопотребление
    annual_electricity_consumption: float = Field(..., description="Годовое потребление электроэнергии (кВт·ч)")
    lighting_consumption: float = Field(..., description="Потребление освещения (кВт·ч/год)")
    hvac_consumption: float = Field(..., description="Потребление ОВК (кВт·ч/год)")
    equipment_consumption: float = Field(..., description="Потребление оборудования (кВт·ч/год)")
    
    # Энергоэффективность
    energy_efficiency_class: str = Field("B", description="Класс энергоэффективности")
    renewable_energy_share: float = Field(0, description="Доля ВИЭ (%)")
    
    # Нормативные документы
    normative_document: str = Field("СП 256.1325800.2016", description="Нормативный документ")


class CalculationTypeInfo(BaseModel):
    """Информация о типе расчета"""
    type: str
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    categories: List[str]


class CalculationCategoryInfo(BaseModel):
    """Информация о категории расчета"""
    category: str
    name: str
    description: str
    calculation_types: List[str]


# ===== ВОДОСНАБЖЕНИЕ И ВОДООТВЕДЕНИЕ =====

class WaterSupplyCalculationParams(BaseModel):
    """Параметры для расчета водоснабжения согласно СП 30.13330.2016"""
    # Основные параметры здания
    building_type: str = Field(..., description="Тип здания (жилое/общественное/производственное)")
    building_area: float = Field(..., description="Площадь здания (м²)")
    number_of_floors: int = Field(..., description="Количество этажей")
    number_of_apartments: int = Field(0, description="Количество квартир")
    number_of_people: int = Field(..., description="Количество людей")
    
    # Параметры водопотребления
    water_consumption_per_person: float = Field(200, description="Норма водопотребления на человека (л/сут)")
    hot_water_consumption_per_person: float = Field(100, description="Норма горячей воды на человека (л/сут)")
    cold_water_consumption_per_person: float = Field(100, description="Норма холодной воды на человека (л/сут)")
    
    # Коэффициенты
    consumption_coefficient: float = Field(1.2, description="Коэффициент неравномерности потребления")
    simultaneity_coefficient: float = Field(0.3, description="Коэффициент одновременности")
    peak_coefficient: float = Field(2.5, description="Коэффициент пикового потребления")
    
    # Параметры системы
    water_pressure: float = Field(0.3, description="Требуемое давление воды (МПа)")
    pipe_diameter: float = Field(0.05, description="Диаметр трубопровода (м)")
    pipe_length: float = Field(100, description="Длина трубопровода (м)")
    pipe_material: str = Field("сталь", description="Материал трубопровода")
    
    # Параметры водоотведения
    sewage_flow_rate: float = Field(0.8, description="Расход сточных вод (л/с)")
    sewage_concentration: float = Field(500, description="Концентрация загрязнений (мг/л)")
    treatment_efficiency: float = Field(0.95, description="Эффективность очистки")
    
    # Нормативные документы
    normative_document: str = Field("СП 30.13330.2016", description="Нормативный документ")


class FireSafetyCalculationParams(BaseModel):
    """Параметры для расчета пожарной безопасности согласно 123-ФЗ, ГОСТ 12.1.004-91"""
    # Основные параметры здания
    building_type: str = Field(..., description="Тип здания (жилое/общественное/производственное)")
    building_area: float = Field(..., description="Площадь здания (м²)")
    building_volume: float = Field(..., description="Объем здания (м³)")
    number_of_floors: int = Field(..., description="Количество этажей")
    building_height: float = Field(..., description="Высота здания (м)")
    
    # Параметры пожарной безопасности
    fire_resistance_rating: str = Field("II", description="Степень огнестойкости (I, II, III, IV, V)")
    fire_compartment_area: float = Field(1000, description="Площадь пожарного отсека (м²)")
    evacuation_time: float = Field(300, description="Время эвакуации (с)")
    evacuation_capacity: int = Field(100, description="Вместимость эвакуационных путей (чел)")
    
    # Параметры противопожарных систем
    sprinkler_density: float = Field(0.12, description="Плотность орошения спринклерами (л/(с·м²))")
    fire_hydrant_flow: float = Field(2.5, description="Расход пожарного гидранта (л/с)")
    fire_extinguisher_count: int = Field(10, description="Количество огнетушителей")
    smoke_detector_count: int = Field(50, description="Количество дымовых извещателей")
    
    # Параметры эвакуации
    evacuation_route_width: float = Field(1.2, description="Ширина эвакуационного пути (м)")
    evacuation_route_length: float = Field(50, description="Длина эвакуационного пути (м)")
    emergency_exit_count: int = Field(4, description="Количество аварийных выходов")
    
    # Параметры горючести
    fire_load_density: float = Field(50, description="Плотность пожарной нагрузки (МДж/м²)")
    smoke_generation_rate: float = Field(0.1, description="Скорость образования дыма (кг/с)")
    heat_release_rate: float = Field(1000, description="Скорость тепловыделения (кВт)")
    
    # Нормативные документы
    normative_document: str = Field("123-ФЗ", description="Нормативный документ")


class AcousticCalculationParams(BaseModel):
    """Параметры для акустических расчетов согласно СП 51.13330.2011"""
    # Основные параметры помещения
    room_type: str = Field(..., description="Тип помещения (жилое/общественное/производственное)")
    room_area: float = Field(..., description="Площадь помещения (м²)")
    room_volume: float = Field(..., description="Объем помещения (м³)")
    room_height: float = Field(..., description="Высота помещения (м)")
    
    # Параметры шума
    noise_level_limit: float = Field(40, description="Предельный уровень шума (дБА)")
    background_noise_level: float = Field(35, description="Уровень фонового шума (дБА)")
    noise_source_power: float = Field(80, description="Мощность источника шума (дБ)")
    noise_source_distance: float = Field(5, description="Расстояние до источника шума (м)")
    
    # Параметры звукоизоляции
    wall_thickness: float = Field(0.2, description="Толщина стены (м)")
    wall_material: str = Field("бетон", description="Материал стены")
    wall_sound_insulation: float = Field(50, description="Звукоизоляция стены (дБ)")
    floor_sound_insulation: float = Field(55, description="Звукоизоляция пола (дБ)")
    ceiling_sound_insulation: float = Field(60, description="Звукоизоляция потолка (дБ)")
    
    # Параметры звукопоглощения
    sound_absorption_coefficient: float = Field(0.3, description="Коэффициент звукопоглощения")
    reverberation_time: float = Field(0.8, description="Время реверберации (с)")
    acoustic_treatment_area: float = Field(0, description="Площадь акустической обработки (м²)")
    
    # Параметры вибрации
    vibration_level: float = Field(70, description="Уровень вибрации (дБ)")
    vibration_frequency: float = Field(50, description="Частота вибрации (Гц)")
    vibration_insulation: float = Field(20, description="Виброизоляция (дБ)")
    
    # Нормативные документы
    normative_document: str = Field("СП 51.13330.2011", description="Нормативный документ")


class LightingCalculationParams(BaseModel):
    """Параметры для расчета освещения и инсоляции согласно СП 52.13330.2016"""
    # Основные параметры помещения
    room_type: str = Field(..., description="Тип помещения (жилое/общественное/производственное)")
    room_area: float = Field(..., description="Площадь помещения (м²)")
    room_height: float = Field(..., description="Высота помещения (м)")
    room_length: float = Field(..., description="Длина помещения (м)")
    room_width: float = Field(..., description="Ширина помещения (м)")
    
    # Параметры освещения
    required_illuminance: float = Field(300, description="Нормативная освещенность (лк)")
    lighting_type: str = Field("искусственное", description="Тип освещения (естественное/искусственное/комбинированное)")
    light_source_type: str = Field("LED", description="Тип источника света (LED/люминесцентные/накаливания)")
    light_source_power: float = Field(20, description="Мощность источника света (Вт)")
    light_source_efficiency: float = Field(100, description="Световая отдача (лм/Вт)")
    
    # Параметры естественного освещения
    window_area: float = Field(0, description="Площадь окон (м²)")
    window_height: float = Field(1.5, description="Высота окон (м)")
    window_width: float = Field(1.2, description="Ширина окон (м)")
    window_count: int = Field(0, description="Количество окон")
    window_orientation: str = Field("юг", description="Ориентация окон (север/юг/восток/запад)")
    shading_factor: float = Field(0.8, description="Коэффициент затенения")
    
    # Параметры инсоляции
    insolation_duration: float = Field(3, description="Продолжительность инсоляции (ч)")
    insolation_angle: float = Field(30, description="Угол инсоляции (градусы)")
    building_spacing: float = Field(20, description="Расстояние между зданиями (м)")
    building_height_adjacent: float = Field(15, description="Высота соседнего здания (м)")
    
    # Параметры светильников
    luminaire_count: int = Field(0, description="Количество светильников")
    luminaire_efficiency: float = Field(0.8, description="КПД светильника")
    luminaire_height: float = Field(2.5, description="Высота подвеса светильников (м)")
    luminaire_spacing: float = Field(3, description="Шаг светильников (м)")
    
    # Нормативные документы
    normative_document: str = Field("СП 52.13330.2016", description="Нормативный документ")


class GeologicalCalculationParams(BaseModel):
    """Параметры для инженерно-геологических расчетов согласно СП 22.13330.2016"""
    # Основные параметры участка
    site_area: float = Field(..., description="Площадь участка (м²)")
    site_length: float = Field(..., description="Длина участка (м)")
    site_width: float = Field(..., description="Ширина участка (м)")
    groundwater_level: float = Field(2, description="Уровень грунтовых вод (м)")
    
    # Параметры грунта
    soil_type: str = Field(..., description="Тип грунта (глина/песок/суглинок/супесь)")
    soil_density: float = Field(1800, description="Плотность грунта (кг/м³)")
    soil_moisture: float = Field(15, description="Влажность грунта (%)")
    soil_plasticity_index: float = Field(10, description="Показатель пластичности")
    soil_consistency: str = Field("твердая", description="Консистенция грунта (твердая/полутвердая/мягкопластичная)")
    
    # Механические свойства грунта
    compression_modulus: float = Field(10, description="Модуль деформации (МПа)")
    angle_of_internal_friction: float = Field(25, description="Угол внутреннего трения (градусы)")
    cohesion: float = Field(20, description="Сцепление (кПа)")
    bearing_capacity: float = Field(200, description="Несущая способность (кПа)")
    
    # Параметры фундамента
    foundation_type: str = Field("ленточный", description="Тип фундамента (ленточный/плитный/свайный)")
    foundation_width: float = Field(0.6, description="Ширина фундамента (м)")
    foundation_depth: float = Field(1.5, description="Глубина заложения фундамента (м)")
    foundation_length: float = Field(20, description="Длина фундамента (м)")
    
    # Параметры нагрузки
    building_weight: float = Field(1000, description="Вес здания (кН)")
    live_load: float = Field(200, description="Полезная нагрузка (кН/м²)")
    snow_load: float = Field(100, description="Снеговая нагрузка (кН/м²)")
    wind_load: float = Field(50, description="Ветровая нагрузка (кН/м²)")
    
    # Параметры сейсмичности
    seismic_intensity: int = Field(6, description="Сейсмическая интенсивность (баллы)")
    seismic_coefficient: float = Field(0.1, description="Сейсмический коэффициент")
    
    # Нормативные документы
    normative_document: str = Field("СП 22.13330.2016", description="Нормативный документ")


class UAVShockWaveCalculationParams(BaseModel):
    """Параметры расчета воздействия ударной волны от БПЛА"""
    # Основные параметры БПЛА
    uav_mass: float = Field(..., description="Масса БПЛА (кг)")
    distance: float = Field(..., description="Расстояние до объекта (м)")
    explosive_type: str = Field(..., description="Тип взрывчатого вещества")
    explosion_height: float = Field(..., description="Высота взрыва (м)")
    
    # Параметры конструкции
    structure_material: str = Field(..., description="Материал конструкции")
    structure_thickness: float = Field(..., description="Толщина конструкции (мм)")
    structure_area: float = Field(100, description="Площадь конструкции (м²)")
    
    # Параметры взрыва
    explosive_equivalent: float = Field(1.0, description="Эквивалент взрывчатого вещества (кг ТНТ)")
    blast_pressure: float = Field(0, description="Давление взрыва (кПа)")
    
    # Результаты расчета
    shock_wave_pressure: float = Field(0, description="Давление ударной волны (кПа)")
    structural_damage: str = Field("", description="Оценка повреждений конструкции")
    safety_factor: float = Field(0, description="Коэффициент безопасности")
    
    # Нормативные документы
    normative_document: str = Field("СП 542.1325800.2024", description="Нормативный документ")


class UAVImpactPenetrationCalculationParams(BaseModel):
    """Параметры расчета попадания БПЛА в конструкцию"""
    # Основные параметры БПЛА
    uav_velocity: float = Field(..., description="Скорость БПЛА (м/с)")
    uav_mass: float = Field(..., description="Масса БПЛА (кг)")
    uav_material: str = Field(..., description="Материал БПЛА")
    uav_shape: str = Field("cylindrical", description="Форма БПЛА")
    
    # Параметры конструкции
    structure_thickness: float = Field(..., description="Толщина конструкции (мм)")
    structure_strength: float = Field(..., description="Прочность материала (МПа)")
    structure_material: str = Field(..., description="Материал конструкции")
    
    # Параметры удара
    impact_angle: float = Field(90, description="Угол удара (град)")
    impact_area: float = Field(0.01, description="Площадь контакта (м²)")
    
    # Результаты расчета
    penetration_depth: float = Field(0, description="Глубина проникновения (мм)")
    impact_force: float = Field(0, description="Сила удара (кН)")
    structural_damage: str = Field("", description="Оценка повреждений конструкции")
    penetration_probability: float = Field(0, description="Вероятность проникновения")
    
    # Нормативные документы
    normative_document: str = Field("СП 542.1325800.2024", description="Нормативный документ")
