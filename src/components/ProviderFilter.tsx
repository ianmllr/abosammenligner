import { PROVIDERS } from '@/lib/offers'

interface ProviderFilterProps {
    selected: string
    onChange: (provider: string) => void
}

export default function ProviderFilter({ selected, onChange }: ProviderFilterProps) {
    return (
        <div className="flex gap-2">
            {PROVIDERS.map(p => (
                <button
                    key={p}
                    onClick={() => onChange(p)}
                    className={`px-4 py-2 rounded-md border border-gray-400 text-sm cursor-pointer transition-colors
                        ${selected === p ? 'bg-black text-white' : 'bg-white text-black hover:bg-gray-100'}`}
                >
                    {p}
                </button>
            ))}
        </div>
    )
}
