'use client'
import { useState, useRef, useEffect } from 'react'
import { PROVIDERS } from '@/lib/offers'

interface ProviderFilterProps {
    selected: string[]
    onChange: (providers: string[]) => void
}

export default function ProviderFilter({ selected, onChange }: ProviderFilterProps) {
    const [open, setOpen] = useState(false)
    const ref = useRef<HTMLDivElement>(null)
    const allSelected = selected.length === PROVIDERS.length

    const toggleAll = () => onChange(allSelected ? [] : [...PROVIDERS])
    const toggleOne = (provider: string) => {
        if (selected.includes(provider)) {
            onChange(selected.filter(p => p !== provider))
        } else {
            onChange([...selected, provider])
        }
    }

    // close on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
        }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    const label = allSelected
        ? 'Alle udbydere'
        : selected.length === 0
            ? 'Ingen udbydere'
            : selected.length === 1
                ? selected[0]
                : `${selected.length} udbydere`

    return (
        <div ref={ref} className="relative">
            <button
                onClick={() => setOpen(v => !v)}
                className="flex items-center gap-2 px-4 py-2 rounded-md border border-[#334155] bg-[#2a3340] text-[#cdd6e0] text-sm hover:border-[#4a90b8] transition-colors cursor-pointer"
            >
                <span>{label}</span>
                <svg
                    className={`w-3 h-3 text-[#7d8fa0] transition-transform ${open ? 'rotate-180' : ''}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
                >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {open && (
                <div className="absolute top-full mt-1 left-0 z-50 min-w-[170px] bg-[#2a3340] border border-[#334155] rounded-md shadow-lg py-1">
                    <button
                        onClick={toggleAll}
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[#cdd6e0] hover:bg-[#334155] transition-colors cursor-pointer"
                    >
                        <span className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${allSelected ? 'bg-[#4a90b8] border-[#4a90b8]' : 'border-[#7d8fa0]'}`}>
                            {allSelected && <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>}
                        </span>
                        Alle
                    </button>
                    <div className="border-t border-[#334155] my-1" />
                    {PROVIDERS.map(p => {
                        const checked = selected.includes(p)
                        return (
                            <button
                                key={p}
                                onClick={() => toggleOne(p)}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[#cdd6e0] hover:bg-[#334155] transition-colors cursor-pointer"
                            >
                                <span className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${checked ? 'bg-[#4a90b8] border-[#4a90b8]' : 'border-[#7d8fa0]'}`}>
                                    {checked && <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>}
                                </span>
                                {p}
                            </button>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
