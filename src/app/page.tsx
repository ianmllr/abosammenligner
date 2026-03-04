'use client'
import OfferCard from '@/components/OfferCard'
import ProviderFilter from '@/components/ProviderFilter'
import SortSelect from '@/components/SortSelect'
import Header from '@/components/Header'
import PriceRangeSlider from '@/components/PriceRangeSlider'
import { useOffers } from '@/hooks/useOffers'

export default function Home() {
    const { filtered, selectedProviders, setSelectedProviders, sortOrder, setSortOrder, hideNegative, setHideNegative, search, setSearch, priceRange, setPriceRange, priceMin, priceMax } = useOffers()

    return (
        <>
            <Header />
            <main className="min-h-screen bg-[#20262f] p-8">
                <div suppressHydrationWarning className="max-w-[1200px] mx-auto">
                    <div className="flex gap-4 mb-8 flex-wrap items-center">
                        <button
                            onClick={() => setHideNegative(v => !v)}
                            className={`px-4 py-2 rounded-md border text-sm transition-colors ${
                                hideNegative
                                    ? 'bg-[#4a90b8] border-[#4a90b8] text-white'
                                    : 'bg-[#2a3340] border-[#334155] text-[#7d8fa0] hover:border-[#4a90b8]'
                            }`}
                        >
                            Skjul tilbud du ikke sparer penge på
                        </button>
                        <ProviderFilter selected={selectedProviders} onChange={setSelectedProviders} />
                        <SortSelect value={sortOrder} onChange={setSortOrder} />
                        <input
                            type="text"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Søg efter produkt..."
                            className="px-4 py-2 rounded-md border border-[#334155] bg-[#2a3340] text-[#cdd6e0] text-sm placeholder-[#7d8fa0] focus:outline-none focus:border-[#4a90b8]"
                        />
                        <PriceRangeSlider
                            min={priceMin}
                            max={priceMax}
                            value={priceRange}
                            onChange={setPriceRange}
                        />
                    </div>

                    <div className="grid grid-cols-[repeat(auto-fill,minmax(360px,1fr))] gap-6">
                        {filtered.map(offer => (
                            <OfferCard
                                key={`${offer.provider}-${offer.product_name}-${offer.link}`}
                                offer={offer}
                            />
                        ))}
                    </div>
                </div>
            </main>
        </>
    )
}
