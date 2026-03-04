'use client'
import { useRef, useCallback, useEffect } from 'react'

interface Props {
    min: number
    max: number
    value: [number, number]
    onChange: (value: [number, number]) => void
    label?: string
}

export default function PriceRangeSlider({ min, max, value, onChange, label = '6 mdr.' }: Props) {
    const [lo, hi] = value
    const range = max - min || 1
    const trackRef = useRef<HTMLDivElement>(null)
    const valueRef = useRef(value)
    useEffect(() => { valueRef.current = value }, [value])

    const toPercent = (v: number) => ((v - min) / range) * 100
    const loPercent = toPercent(lo)
    const hiPercent = toPercent(hi)

    const getVal = useCallback((clientX: number) => {
        const rect = trackRef.current?.getBoundingClientRect()
        if (!rect) return 0
        return Math.round(min + Math.max(0, Math.min(1, (clientX - rect.left) / rect.width)) * range)
    }, [min, range])

    const startDrag = useCallback((thumb: 'lo' | 'hi') => (e: React.PointerEvent) => {
        e.currentTarget.setPointerCapture(e.pointerId)
        const onMove = (ev: PointerEvent) => {
            const v = getVal(ev.clientX)
            const [l, h] = valueRef.current
            onChange(thumb === 'lo' ? [Math.min(v, h - 1), h] : [l, Math.max(v, l + 1)])
        }
        const onUp = () => {
            window.removeEventListener('pointermove', onMove)
            window.removeEventListener('pointerup', onUp)
        }
        window.addEventListener('pointermove', onMove)
        window.addEventListener('pointerup', onUp)
    }, [onChange, getVal])

    const fmt = (n: number) => n.toLocaleString('da-DK')

    return (
        <div className="flex flex-col gap-1 min-w-[220px]">
            {/* label + value badge */}
            <div className="flex items-center justify-between">
                <span className="text-xs text-[#7d8fa0]">{label}</span>
                <span className="text-xs text-[#cdd6e0] bg-[#2a3340] px-2 py-0.5 rounded-full border border-[#334155]">
                    {fmt(lo)} – {fmt(hi)} kr
                </span>
            </div>

            {/* track */}
            <div ref={trackRef} className="relative h-1.5 rounded-full bg-[#334155]">
                <div
                    className="absolute h-full rounded-full bg-[#4a90b8]"
                    style={{ left: `${loPercent}%`, width: `${hiPercent - loPercent}%` }}
                />
                {(['lo', 'hi'] as const).map(thumb => (
                    <div
                        key={thumb}
                        onPointerDown={startDrag(thumb)}
                        className="absolute top-1/2 w-4 h-4 -translate-y-1/2 rounded-full bg-[#4a90b8] border-2 border-[#20262f] cursor-grab active:cursor-grabbing shadow-md hover:scale-110 transition-transform"
                        style={{
                            left: `calc(${thumb === 'lo' ? loPercent : hiPercent}% - 8px)`,
                            zIndex: thumb === 'hi' ? 4 : 3,
                            touchAction: 'none',
                        }}
                    />
                ))}
            </div>
        </div>
    )
}
