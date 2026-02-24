import type { SortOrder } from '@/types/offer'

interface SortSelectProps {
    value: SortOrder
    onChange: (value: SortOrder) => void
}

const SORT_OPTIONS: { value: SortOrder; label: string }[] = [
    { value: 'asc', label: 'Pris: lav til høj' },
    { value: 'desc', label: 'Pris: høj til lav' },
    { value: 'saved_desc', label: 'Mest sparet: høj til lav' },
    { value: 'saved_asc', label: 'Mest sparet: lav til høj' },
]

export default function SortSelect({ value, onChange }: SortSelectProps) {
    return (
        <select
            value={value}
            onChange={e => onChange(e.target.value as SortOrder)}
            className="px-4 py-2 rounded-md border border-gray-400 bg-white text-black text-sm"
        >
            {SORT_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
            ))}
        </select>
    )
}
