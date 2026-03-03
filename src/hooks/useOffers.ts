import { useState, useMemo } from 'react'
import { allOffers, PROVIDERS } from '@/lib/offers'
import type { SortOrder } from '@/types/offer'

export function useOffers() {
    const [selectedProviders, setSelectedProviders] = useState<string[]>([...PROVIDERS])
    const [sortOrder, setSortOrder] = useState<SortOrder>('saved_desc')
    const [hideNegative, setHideNegative] = useState(false)
    const [search, setSearch] = useState('')

    const filtered = useMemo(() => {
        const q = search.trim().toLowerCase()
        return allOffers
                .filter(o => selectedProviders.includes(o.provider))
                .filter(o => !q || o.product_name.toLowerCase().includes(q))
                .filter(o => o.price_with_subscription !== null && o.price_with_subscription !== undefined)
                .filter(o => {
                    if (!hideNegative) return true
                    if (o.min_cost_6_months == null) return false
                    const saved = (o.market_price ?? o.price_without_subscription) - o.min_cost_6_months
                    return saved >= 0
                })
                .sort((a, b) => {
                    if (sortOrder === 'saved_desc' || sortOrder === 'saved_asc') {
                        const aSaved = a.min_cost_6_months != null ? (a.market_price ?? a.price_without_subscription) - a.min_cost_6_months : -Infinity
                        const bSaved = b.min_cost_6_months != null ? (b.market_price ?? b.price_without_subscription) - b.min_cost_6_months : -Infinity
                        return sortOrder === 'saved_desc' ? bSaved - aSaved : aSaved - bSaved
                    }
                    if (sortOrder === 'market_asc' || sortOrder === 'market_desc') {
                        const aMarket = a.market_price ?? a.price_without_subscription
                        const bMarket = b.market_price ?? b.price_without_subscription
                        return sortOrder === 'market_asc' ? aMarket - bMarket : bMarket - aMarket
                    }
                    if (sortOrder === 'name_asc' || sortOrder === 'name_desc') {
                        const cmp = a.product_name.localeCompare(b.product_name, 'da')
                        return sortOrder === 'name_asc' ? cmp : -cmp
                    }
                    return sortOrder === 'asc'
                        ? Number(a.price_with_subscription) - Number(b.price_with_subscription)
                        : Number(b.price_with_subscription) - Number(a.price_with_subscription)
                })
    }, [selectedProviders, sortOrder, hideNegative, search])

    return { filtered, selectedProviders, setSelectedProviders, sortOrder, setSortOrder, hideNegative, setHideNegative, search, setSearch }
}
