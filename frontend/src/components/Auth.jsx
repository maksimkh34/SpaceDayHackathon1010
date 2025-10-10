import React, { useState } from 'react'
import { registerUser, loginUser, saveToken } from '../api'

export default function Auth({ onLogin }) {
    const [isRegister, setIsRegister] = useState(false)
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [remember, setRemember] = useState(true)
    const [loading, setLoading] = useState(false)
    const [usernameError, setUsernameError] = useState('')
    const [passwordError, setPasswordError] = useState('')

    // Функция для проверки на наличие только ASCII символов
    const isASCII = (str) => {
        return /^[\x00-\x7F]*$/.test(str)
    }

    const handleUsernameChange = (e) => {
        const value = e.target.value
        if (isASCII(value)) {
            setUsername(value)
            setUsernameError('')
        } else {
            setUsernameError('Только латинские буквы, цифры и символы')
        }
    }

    const handlePasswordChange = (e) => {
        const value = e.target.value
        if (isASCII(value)) {
            setPassword(value)
            setPasswordError('')
        } else {
            setPasswordError('Только латинские буквы, цифры и символы')
        }
    }

    async function submit(e) {
        e.preventDefault()

        // Дополнительная проверка перед отправкой
        if (!isASCII(username) || !isASCII(password)) {
            alert('Пожалуйста, используйте только латинские буквы, цифры и стандартные символы')
            return
        }

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
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '30px'}}>
            <div style={{
                fontSize: '42px',
                fontWeight: '800',
                background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                textAlign: 'center',
                letterSpacing: '2px'
            }}>
                HealthPix
            </div>
            <div className="card auth-card">
                <h2 style={{textAlign: 'center', marginBottom: '20px', color: '#1e293b'}}>
                    {isRegister ? 'Регистрация' : 'Вход'}
                </h2>
                <form onSubmit={submit} className="form">
                    <label>
                        Логин
                        <input
                            value={username}
                            onChange={handleUsernameChange}
                            required
                            placeholder="Только латинские буквы и цифры"
                            style={{
                                borderColor: usernameError ? '#ef4444' : '',
                                marginBottom: usernameError ? '4px' : '0'
                            }}
                        />
                        {usernameError && (
                            <div style={{
                                color: '#ef4444',
                                fontSize: '12px',
                                marginTop: '4px'
                            }}>
                                {usernameError}
                            </div>
                        )}
                    </label>

                    <label>
                        Пароль
                        <input
                            type="password"
                            value={password}
                            onChange={handlePasswordChange}
                            required
                            placeholder="Только латинские буквы и цифры"
                            style={{
                                borderColor: passwordError ? '#ef4444' : '',
                                marginBottom: passwordError ? '4px' : '0'
                            }}
                        />
                        {passwordError && (
                            <div style={{
                                color: '#ef4444',
                                fontSize: '12px',
                                marginTop: '4px'
                            }}>
                                {passwordError}
                            </div>
                        )}
                    </label>

                    <label className="row" style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
                        <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)}/>
                        запомнить меня
                    </label>

                    <div className="row space-between" style={{marginTop: '20px'}}>
                        <button className="btn" type="submit"
                                disabled={loading || usernameError || passwordError}>
                            {loading ? 'Один момент..' : (isRegister ? 'Зарегистрироваться' : 'Войти')}
                        </button>
                        <button type="button" className="link"
                                onClick={() => setIsRegister((s) => !s)}>
                            {isRegister ? 'Есть аккаунт? Войти' : 'Нет аккаунта? Зарегистрироваться'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}