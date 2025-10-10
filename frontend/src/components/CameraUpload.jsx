// FILE: src/components/CameraUpload.jsx
import React, { useEffect, useRef, useState } from 'react'
import { uploadImage } from '../api'

export default function CameraUpload({ onNewReport }) {
    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const [cameraOn, setCameraOn] = useState(false)
    const [streamObj, setStreamObj] = useState(null)
    const [file, setFile] = useState(null)
    const [previewURL, setPreviewURL] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)

    // Очистка при размонтировании
    useEffect(() => {
        return () => {
            stopCamera()
            if (previewURL) URL.revokeObjectURL(previewURL)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    // Отзыв старого previewURL при изменении
    useEffect(() => {
        return () => {
            if (previewURL) {
                URL.revokeObjectURL(previewURL)
            }
        }
    }, [previewURL])

    async function startCamera() {
        try {
            const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
            setStreamObj(s)
            setCameraOn(true)
            if (videoRef.current) {
                videoRef.current.srcObject = s
                try {
                    await videoRef.current.play()
                } catch (playErr) {
                    console.warn('video.play() failed:', playErr)
                }
            }
        } catch (err) {
            console.error('camera start error', err)
            alert('Не удалось включить камеру: ' + (err.message || err))
            setCameraOn(false)
            if (streamObj) stopCamera()
        }
    }

    function stopCamera() {
        try {
            if (streamObj) {
                streamObj.getTracks().forEach((t) => t.stop())
            } else {
                const s = videoRef.current?.srcObject
                if (s && s.getTracks) s.getTracks().forEach((t) => t.stop())
            }
        } catch (e) {
            console.warn('stopCamera error', e)
        } finally {
            if (videoRef.current) {
                try { videoRef.current.srcObject = null } catch (e) {}
            }
            setStreamObj(null)
            setCameraOn(false)
        }
    }

    function capture() {
        const v = videoRef.current
        const canvas = canvasRef.current
        if (!v || !canvas) return
        canvas.width = v.videoWidth || 640
        canvas.height = v.videoHeight || 480
        const ctx = canvas.getContext('2d')
        ctx.drawImage(v, 0, 0, canvas.width, canvas.height)
        canvas.toBlob((blob) => {
            if (!blob) return
            const f = new File([blob], `selfie_${Date.now()}.jpg`, { type: 'image/jpeg' })
            // revoke previous preview if есть
            if (previewURL) {
                try { URL.revokeObjectURL(previewURL) } catch (e) {}
            }
            const url = URL.createObjectURL(blob)
            setFile(f)
            setPreviewURL(url)
            // не останавливаем камеру — пользователь может сделать заново без повторного запроса прав
        }, 'image/jpeg', 0.9)
    }

    function onFile(e) {
        const f = e.target.files && e.target.files[0]
        if (!f) return
        if (previewURL) {
            try { URL.revokeObjectURL(previewURL) } catch (e) {}
        }
        const url = URL.createObjectURL(f)
        setFile(f)
        setPreviewURL(url)
    }

    function resetPhoto() {
        // удалить текущую фотографию и вернуть камеру (если была включена)
        if (previewURL) {
            try { URL.revokeObjectURL(previewURL) } catch (e) {}
        }
        setPreviewURL(null)
        setFile(null)
        // если камера была выключена — можно оставить выключенной; пользователь сам включит
    }

    async function doUpload() {
        if (!file) return alert('Сначала выберите фото')
        setUploading(true)
        setProgress(0)
        try {
            const res = await uploadImage(file, (evt) => {
                if (evt.total) setProgress(Math.round((evt.loaded / evt.total) * 100))
            })
            const data = res.data
            const report = {
                id: Date.now().toString(36),
                result: data.result,
                timestamp: data.timestamp || new Date().toISOString(),
                imageURL: previewURL || URL.createObjectURL(file),
                imageName: file.name,
            }
            onNewReport(report)
            // после успешной отправки можно очистить превью, если нужно:
            // resetPhoto()
        } catch (err) {
            alert('Ошибка при загрузке: ' + (err?.response?.data?.message || err.message))
        } finally {
            setUploading(false)
            setProgress(0)
        }
    }

    return (
        <div className="card">
            <h3>Селфи / Загрузка</h3>

            <div className="controls">
                <div className="row" style={{ gap: '10px', marginTop: '10px' }}>
                    {!cameraOn ? (
                        <button className="btn" onClick={startCamera}>Включить камеру</button>
                    ) : (
                        <button className="btn" onClick={stopCamera}>Отключить камеру</button>
                    )}

                    <label className="btn file-btn">
                        Выбрать фото
                        <input type="file" accept="image/*" onChange={onFile} />
                    </label>
                </div>

                <div className="preview">
                    {/* camera-box: видео или превью занимают одно и то же место */}
                    <div className="camera-box" style={{ position: 'relative'}}>
                        {/* Показываем превью, если есть файл */}
                        {previewURL ? (
                            <>
                                <img
                                    src={previewURL}
                                    alt="preview"
                                    style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 8 }}
                                />
                                <div style={{ position: 'absolute', right: 12, bottom: 12 }}>
                                    {/* Кнопки при показе превью */}
                                    <div className="row gap">
                                        <button className="btn" onClick={doUpload} disabled={uploading}>
                                            {uploading ? 'Загрузка...' : 'Загрузить'}
                                        </button>
                                        <button style={{backgroundColor: 'white'}} className="btn outline" onClick={resetPhoto}>Сделать заново</button>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <>
                                {/* Показываем видео только если камера включена и нет превью */}
                                <video
                                    ref={videoRef}
                                    style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 8, display: cameraOn ? 'block' : 'none' }}
                                    playsInline
                                    muted
                                />
                                {!cameraOn && <div className="hint">Камера не включена. Можно выбрать файл.</div>}
                                {cameraOn && (
                                    <button className="btn small" onClick={capture} style={{ position: 'absolute', right: 12, bottom: 12 }}>
                                        Сделать фото
                                    </button>
                                )}
                            </>
                        )}
                    </div>

                    {/* Дополнительный прогресс, показываем отдельно */}
                    {uploading && (
                        <div className="progress" style={{ marginTop: 8 }}>
                            <div className="bar" style={{ width: `${progress}%` }}></div>
                            <span>{progress}%</span>
                        </div>
                    )}
                </div>

                <canvas ref={canvasRef} style={{ display: 'none' }} />
            </div>
        </div>
    )
}
