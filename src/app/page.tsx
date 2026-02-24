'use client'
import { useState } from 'react'
import telmore from '../../data/telmore/telmore_offers.json'
import oister from '../../data/oister/oister_offers.json'
import elgiganten from '../../data/elgiganten/elgiganten_offers.json'
import prisjagt from '../../data/prisjagt/prisjagt_prices.json'

// prisjagt_prices.json is an object keyed by product name, e.g:
// { "iPhone 15": { market_price: 4999, looked_up_at: "..." }, ... }
// so we can look up any product's market price by name
const prisjagtLookup = prisjagt as Record<string, { market_price: number | null }>

// combine all offers into one list with a consistent shape
const allOffers = [
    ...telmore.map(o => ({
        product_name: o.product_name,
        image_url: o.image_url,
        provider: 'Telmore',
        price_with_subscription: o.price_with_subscription,
        price_without_subscription: o.price_without_subscription,
        discount_on_product: o.discount_on_product,
        min_cost_6_months: o.min_cost_6_months,
    })),
    ...oister.map(o => ({
        product_name: o.product_name,
        image_url: o.image_url,
        provider: 'Oister',
        price_with_subscription: o.price_with_subscription,
        price_without_subscription: o.price_without_subscription,
        discount_on_product: o.discount_on_product,
        min_cost_6_months: o.min_cost_6_months,
    })),
    ...elgiganten.map(o => ({
        product_name: o.product,
        image_url: o.image_url,
        provider: 'Elgiganten',
        price_with_subscription: o.price_with_subscription,
        price_without_subscription: o.price_without_subscription,
        discount_on_product: o.discount_on_product,
        min_cost_6_months: o.min_cost_6_months,
    })),
].map(offer => ({
    // add market price from prisjagt lookup for each offer
    ...offer,
    market_price: prisjagtLookup[offer.product_name]?.market_price ?? null
}))

const providers = ['Alle', 'Telmore', 'Oister', 'Elgiganten']

export default function Home() {
    // useState stores values that can change — when they change, the page re-renders
    const [selectedProvider, setSelectedProvider] = useState('Alle')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

    // filter and sort the offers based on current state
    const filtered = allOffers
        .filter(o => selectedProvider === 'Alle' || o.provider === selectedProvider)
        .filter(o => o.price_with_subscription !== null && o.price_with_subscription !== undefined && o.price_with_subscription !== '')
        .sort((a, b) => {
            const aPrice = Number(a.price_with_subscription)
            const bPrice = Number(b.price_with_subscription)
            return sortOrder === 'asc' ? aPrice - bPrice : bPrice - aPrice
        })

    return (
        <main style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>
            <h1 style={{ marginBottom: '1.5rem' }}>Mobiltelefoner med abonnement</h1>

            {/* filter bar */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>

                {/* provider buttons */}
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {providers.map(p => (
                        <button
                            key={p}
                            onClick={() => setSelectedProvider(p)}
                            style={{
                                padding: '0.5rem 1rem',
                                borderRadius: 6,
                                border: '1px solid #ccc',
                                background: selectedProvider === p ? '#000' : '#fff',
                                color: selectedProvider === p ? '#fff' : '#000',
                                cursor: 'pointer'
                            }}
                        >
                            {p}
                        </button>
                    ))}
                </div>

                {/* sort dropdown */}
                <select
                    value={sortOrder}
                    onChange={e => setSortOrder(e.target.value as 'asc' | 'desc')}
                    style={{ padding: '0.5rem 1rem', borderRadius: 6, border: '1px solid #ccc' }}
                >
                    <option value="asc">Pris: lav til høj</option>
                    <option value="desc">Pris: høj til lav</option>
                </select>
            </div>

            {/* card grid — auto-fill means as many columns as fit */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                gap: '1.5rem'
            }}>
                {filtered.map((offer, index) => (
                    <div key={index} style={{
                        border: '1px solid #e0e0e0',
                        borderRadius: 12,
                        padding: '1rem',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}>
                        {offer.image_url && (
                            <img
                                src={offer.image_url}
                                alt={offer.product_name}
                                style={{ width: 120, height: 120, objectFit: 'contain' }}
                            />
                        )}

                        <p style={{ fontSize: 12, color: '#888', margin: 0 }}>{offer.provider}</p>
                        <h2 style={{ fontSize: 15, textAlign: 'center', margin: 0 }}>{offer.product_name}</h2>

                        <p style={{ margin: 0 }}>
                            <strong>{offer.price_with_subscription} kr.</strong> med abonnement
                        </p>

                        {offer.discount_on_product && (
                            <p style={{ margin: 0 }}>{offer.discount_on_product} kr. rabat</p>
                        )}

                        {offer.market_price ? (
                            <p style={{ margin: 0, fontSize: 13, color: '#2e7d32' }}>
                                Markedspris: {offer.market_price} kr.
                            </p>
                        ) : (
                            <p style={{ margin: 0, fontSize: 13, color: '#999', fontStyle: 'italic' }}>
                                Ingen markedspris fundet
                            </p>
                        )}

                        <p style={{ margin: 0, fontSize: 13, color: '#555' }}>
                            Uden abonnement: {offer.price_without_subscription} kr.
                        </p>

                        {offer.min_cost_6_months && (
                            <p style={{ margin: 0, fontSize: 13, color: '#555' }}>
                                Mindstepris i 6 mdr.: {offer.min_cost_6_months} kr.
                            </p>
                        )}
                    </div>
                ))}
            </div>
        </main>
    )
}