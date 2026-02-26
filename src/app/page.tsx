'use client'
import OfferCard from '@/components/OfferCard'
import ProviderFilter from '@/components/ProviderFilter'
import SortSelect from '@/components/SortSelect'
import { useOffers } from '@/hooks/useOffers'

export default function Home() {
    const { filtered, selectedProvider, setSelectedProvider, sortOrder, setSortOrder } = useOffers()

    return (
        <main className="min-h-screen bg-[#0a0a0a] p-8">
            <div className="max-w-[1200px] mx-auto">
                <h1 className="mb-6 text-[#ededed]">Mobiltelefoner med abonnement</h1>

                <div className="flex gap-4 mb-8 flex-wrap items-center">
                    <ProviderFilter selected={selectedProvider} onChange={setSelectedProvider} />
                    <SortSelect value={sortOrder} onChange={setSortOrder} />
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
    )
}
