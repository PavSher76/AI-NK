/**
 * Утилита для авторизации в calculation service
 */

const CALCULATION_API_BASE = 'https://localhost/api/calculation';

/**
 * Получение токена для calculation service
 */
export const getCalculationToken = async (username, password) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${CALCULATION_API_BASE}/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Ошибка авторизации в calculation service');
    }

    const data = await response.json();
    return {
      access_token: data.access_token,
      token_type: data.token_type,
      user: data.user
    };
  } catch (error) {
    console.error('🔍 [CALCULATION_AUTH] Error getting calculation token:', error);
    throw error;
  }
};

/**
 * Проверка валидности токена calculation service
 */
export const validateCalculationToken = async (token) => {
  try {
    const response = await fetch(`${CALCULATION_API_BASE}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    return response.ok;
  } catch (error) {
    console.error('🔍 [CALCULATION_AUTH] Error validating calculation token:', error);
    return false;
  }
};

/**
 * Получение информации о текущем пользователе calculation service
 */
export const getCalculationUserInfo = async (token) => {
  try {
    const response = await fetch(`${CALCULATION_API_BASE}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error('Ошибка получения информации о пользователе');
    }

    return await response.json();
  } catch (error) {
    console.error('🔍 [CALCULATION_AUTH] Error getting calculation user info:', error);
    throw error;
  }
};
