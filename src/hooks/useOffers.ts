import { useState, useMemo } from 'react'
import { allOffers } from '@/lib/offers'
import type { SortOrder } from '@/types/offer'

export function useOffers() {
    const [selectedProvider, setSelectedProvider] = useState('Alle')
    const [sortOrder, setSortOrder] = useState<SortOrder>('asc')

    const filtered = useMemo(() =>
            allOffers
                .filter(o => selectedProvider === 'Alle' || o.provider === selectedProvider)
                .filter(o => o.price_with_subscription !== null && o.price_with_subscription !== undefined)
                .sort((a, b) => {
                    if (sortOrder === 'saved_desc' || sortOrder === 'saved_asc') {
                        const aSaved = (a.market_price ?? a.price_without_subscription) - a.min_cost_6_months
                        const bSaved = (b.market_price ?? b.price_without_subscription) - b.min_cost_6_months
                        return sortOrder === 'saved_desc' ? bSaved - aSaved : aSaved - bSaved
                    }
                    return sortOrder === 'asc'
                        ? Number(a.price_with_subscription) - Number(b.price_with_subscription)
                        : Number(b.price_with_subscription) - Number(a.price_with_subscription)
                }),
        [selectedProvider, sortOrder]
    )

    return { filtered, selectedProvider, setSelectedProvider, sortOrder, setSortOrder }
}
