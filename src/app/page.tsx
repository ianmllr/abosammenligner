'use client'

import { useState } from 'react'
import telmore from '../../data/telmore/telmore_offers.json'
import oister from '../../data/oister/oister_offers.json'
import elgiganten from '../../data/elgiganten/elgiganten_offers.json'

const allOffers = [
    ...telmore.map(o => ({ ...o, product_name: o.product_name, provider: 'Telmore' })),
    ...oister.map(o => ({ ...o, product_name: o.product_name, provider: 'Oister' })),
    ...elgiganten.map(o => ({ ...o, product_name: o.product, provider: 'Elgiganten' })),
]

const providers = ['Alle', 'Telmore', 'Oister', 'Elgiganten']

export default function Home() {
    const [selectedProvider, setSelectedProvider] = useState('Alle')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

    const filtered = allOffers
        .filter(o => selectedProvider === 'Alle' || o.provider === selectedProvider)
        .filter(o => o.price_with_subscription !== null && o.price_with_subscription !== undefined && Number(o.price_with_subscription) > 0)        .sort((a, b) => {
            const aPrice = Number(a.price_with_subscription)
            const bPrice = Number(b.price_with_subscription)
            return sortOrder === 'asc' ? aPrice - bPrice : bPrice - aPrice
        })

    return (
        <main style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>
            <h1 style={{ marginBottom: '1.5rem' }}>Mobiltelefoner med abonnement</h1>

            {/* filters */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
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

                <select
                    value={sortOrder}
                    onChange={e => setSortOrder(e.target.value as 'asc' | 'desc')}
                    style={{ padding: '0.5rem 1rem', borderRadius: 6, border: '1px solid #ccc' }}
                >
                    <option value="asc">Pris: lav til høj</option>
                    <option value="desc">Pris: høj til lav</option>
                </select>
            </div>

            {/* card grid */}
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
                        <p style={{ margin: 0, fontSize: 13, color: '#555' }}>
                            Uden abonnement: {offer.price_without_subscription} kr.
                        </p>
                        {offer.min_cost_6_months && (
                            <p style={{ margin: 0, fontSize: 13, color: '#555' }}>
                                Mindstepris: {offer.min_cost_6_months} kr.
                            </p>
                        )}
                    </div>
                ))}
            </div>
        </main>
    )
}