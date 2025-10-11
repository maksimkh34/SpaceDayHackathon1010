import axios from 'axios'

// Для разработки с proxy используем относительные пути
// Автоматическое определение базового URL
export const API_BASE = 'http://26.1.225.234:8080';

// Уберите MOCK_BACKEND для продакшена
export const MOCK_BACKEND = false;
// token helpers
export function saveToken(token, remember) {
    if (remember) localStorage.setItem('token', token)
    else sessionStorage.setItem('token', token)
}
export function readToken() {
    return localStorage.getItem('token') || sessionStorage.getItem('token') || null
}
export function clearToken() {
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
}

const axiosInstance = axios.create({ 
  baseURL: API_BASE,
  timeout: 10000
})

axiosInstance.interceptors.request.use((cfg) => {
    const token = readToken()
    if (token) cfg.headers.Authorization = `Bearer ${token}`
    return cfg
})

axiosInstance.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API functions - УБЕДИТЕСЬ ЧТО ЭТИ ФУНКЦИИ ЭКСПОРТИРУЮТСЯ
export async function registerUser(username, password) {
    if (MOCK_BACKEND) return { data: { message: 'User created' } }
    return axiosInstance.post('/auth/register', { username, password })
}

export async function loginUser(username, password) {
    if (MOCK_BACKEND) return { data: { token: 'mock-token-123' } }
    return axiosInstance.post('/auth/login', { username, password })
}

export async function uploadImage(file, onUploadProgress) {
    if (MOCK_BACKEND) {
        await new Promise((r) => setTimeout(r, 1200))
        return {
            data: {
                status: 'success',
                result: 'MOCK: Осмотр внешнего вида в норме. Рекомендации: отдых, вода, обследование при жалобах.',
                timestamp: new Date().toISOString(),
            },
        }
    }
    const form = new FormData()
    form.append('file', file)
    return axiosInstance.post('/api/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress,
    })
}

export async function getAiStatus() {
    if (MOCK_BACKEND) return { data: { ai_status: 'running' } }
    return axiosInstance.get('/api/status')
}

export async function getHistory() {
    if (MOCK_BACKEND)
        return { data: [ { id: 1, result: 'OK', date: new Date().toISOString() } ] }
    return axiosInstance.get('/api/history')
}