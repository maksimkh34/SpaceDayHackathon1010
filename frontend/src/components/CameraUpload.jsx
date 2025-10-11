import React, { useEffect, useRef, useState } from 'react'
import { uploadImage } from '../api'

export default function CameraUpload({ onNewReport }) {
    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const fileInputRef = useRef(null)

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
            if (previewURL) try { URL.revokeObjectURL(previewURL) } catch (e) {}
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    // Отзыв старого previewURL при изменении
    useEffect(() => {
        return () => {
            if (previewURL) {
                try { URL.revokeObjectURL(previewURL) } catch (e) {}
            }
        }
    }, [previewURL])

    // NEW: Этот хук отвечает за подключение потока к видеоэлементу
    // Он сработает после рендера, когда videoRef.current будет гарантированно доступен
    useEffect(() => {
        if (cameraOn && streamObj && videoRef.current) {
            videoRef.current.srcObject = streamObj
            videoRef.current.play().catch(err => {
                console.warn('Video play was prevented:', err)
            })
        }
    }, [cameraOn, streamObj])


    // MODIFIED: Функция теперь только получает стрим и обновляет состояние
    async function startCamera() {
        try {
            const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
            setStreamObj(s)
            setCameraOn(true) // Это изменение вызовет срабатывание useEffect выше
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
            if (previewURL) {
                try { URL.revokeObjectURL(previewURL) } catch (e) {}
            }
            setPreviewURL(null)
            setFile(null)
            setStreamObj(null)
            setCameraOn(false)
        }
    }


    function capture() {
        const v = videoRef.current
        const canvas = canvasRef.current
        if (!v || !canvas) return

        const videoWidth = v.videoWidth
        const videoHeight = v.videoHeight
        const side = Math.min(videoWidth, videoHeight)

        canvas.width = 1080
        canvas.height = 1080

        const sx = (videoWidth - side) / 2
        const sy = (videoHeight - side) / 2

        const ctx = canvas.getContext('2d')
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(v, sx, sy, side, side, 0, 0, canvas.width, canvas.height)

        canvas.toBlob((blob) => {
            if (!blob) return
            const f = new File([blob], `selfie_${Date.now()}.jpg`, { type: 'image/jpeg' })

            if (previewURL) {
                try { URL.revokeObjectURL(previewURL) } catch (e) {}
            }
            const url = URL.createObjectURL(blob)
            setFile(f)
            setPreviewURL(url)
        }, 'image/jpeg', 0.95)
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
        } catch (err) {
            alert('Ошибка при загрузке: ' + (err?.response?.data?.message || err.message))
        } finally {
            setUploading(false)
            setProgress(0)
        }
    }

    function resetPhoto() {
        if (previewURL) {
            try { URL.revokeObjectURL(previewURL) } catch (e) {}
        }
        setPreviewURL(null)
        setFile(null)
        if (!cameraOn) {
            startCamera()
        } else {
            try {
                videoRef.current?.play().catch(() => {})
            } catch (e) {}
        }
    }

    const mediaCommonStyle = {
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        borderRadius: 8,
        transition: 'opacity 300ms ease, transform 300ms ease',
    }

    return (
        <div className="card">
            <h3>Селфи / Загрузка</h3>
            <div className="controls">
                <div className="row" style={{ gap: '20px', marginTop: '10px' }}>
                    {!cameraOn ? (
                        <button className="btn" onClick={startCamera}>Включить камеру</button>
                    ) : (
                        <button className="btn" onClick={stopCamera}>Отключить камеру</button>
                    )}
                    <label className="btn file-btn">
                        Выбрать фото
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            onChange={onFile}
                            style={{ display: 'none' }}
                        />
                    </label>
                </div>
                <div className={`preview ${!cameraOn && !previewURL ? 'camera-idle' : ''}`} style={{ marginTop: 12 }}>
                    <div className="camera-box" style={{
                        position: 'relative',
                        width: '100%',
                        aspectRatio: '1 / 1',
                        overflow: 'hidden',
                        backgroundColor: '#eee'
                    }}>
                        <img
                            src={previewURL || ''}
                            alt="preview"
                            style={{
                                ...mediaCommonStyle,
                                opacity: previewURL ? 1 : 0,
                                transform: previewURL ? 'translateY(0)' : 'translateY(8px)',
                                zIndex: previewURL ? 3 : 1,
                                pointerEvents: previewURL ? 'auto' : 'none',
                                backgroundColor: '#eee',
                            }}
                        />
                        <video
                            ref={videoRef}
                            playsInline
                            muted
                            style={{
                                ...mediaCommonStyle,
                                opacity: previewURL ? 0 : (cameraOn ? 1 : 0),
                                transform: previewURL ? 'translateY(8px)' : 'translateY(0)',
                                zIndex: 2,
                                pointerEvents: previewURL ? 'none' : 'auto',
                                display: 'block',
                            }}
                        />
                        {!previewURL && !cameraOn && (
                            <div className="hint" style={{
                                position: 'absolute',
                                inset: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                zIndex: 4
                            }}>
                                Камера не включена. Можно выбрать файл.
                            </div>
                        )}
                        <div style={{position: 'absolute', right: 12, bottom: 12, zIndex: 5}}>
                            {!previewURL ? (
                                cameraOn ? (
                                    <button className="btn small" onClick={capture}>Сделать фото</button>
                                ) : (
                                    <div style={{display: 'flex', gap: 8}}>

                                    </div>
                                )
                            ) : (
                                <div className="row gap">
                                    <button className="btn" onClick={doUpload}
                                            disabled={uploading}>{uploading ? 'Загрузка...' : 'Загрузить'}</button>
                                    <button style={{backgroundColor: 'white'}} className="btn outline"
                                            onClick={resetPhoto}>Сделать заново
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
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