import React, { useState } from 'react'
import { registerUser, loginUser, saveToken } from '../api'

export default function Auth({ onLogin }) {
    const [isRegister, setIsRegister] = useState(false)
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [remember, setRemember] = useState(true)
    const [loading, setLoading] = useState(false)

    async function submit(e) {
        e.preventDefault()
        setLoading(true)
        try {
            if (isRegister) {
                const r = await registerUser(username, password)
                alert(r.data?.message || 'Registered')
                setIsRegister(false)
            } else {
                const r = await loginUser(username, password)
                const token = r.data?.token
                if (!token) throw new Error('Token not received')
                saveToken(token, remember)
                onLogin(token)
            }
        } catch (err) {
            alert(err?.response?.data?.message || err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="card auth-card">
            <h2>{isRegister ? 'Регистрация' : 'Вход'}</h2>
            <form onSubmit={submit} className="form">
                <label>
                    Логин
                    <input value={username} onChange={(e) => setUsername(e.target.value)} required />
                </label>
                <label>
                    Пароль
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                </label>
                <label className="row">
                    <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /> Запомнить меня
                </label>
                <div className="row space-between">
                    <button className="btn" type="submit" disabled={loading}>{loading ? '...' : (isRegister ? 'Зарегистрироваться' : 'Войти')}</button>
                    <button type="button" className="link" onClick={() => setIsRegister((s) => !s)}>{isRegister ? 'Есть аккаунт? Войти' : 'Нет аккаунта? Зарегистрироваться'}</button>
                </div>
            </form>
        </div>
    )
}
