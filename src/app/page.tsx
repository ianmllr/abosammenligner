'use client'
import { useState } from 'react'
import telmore from '../../data/telmore/telmore_offers.json'
import oister from '../../data/oister/oister_offers.json'
import elgiganten from '../../data/elgiganten/elgiganten_offers.json'
import prisjagt from '../../data/prisjagt/prisjagt_prices.json'

const prisjagtLookup = prisjagt as Record<string, { market_price: number | null }>

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
    ...offer,
    market_price: prisjagtLookup[offer.product_name]?.market_price ?? null
}))

const providers = ['Alle', 'Telmore', 'Oister', 'Elgiganten']

export default function Home() {
    const [selectedProvider, setSelectedProvider] = useState('Alle')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
    const [openTooltip, setOpenTooltip] = useState<{ index: number, type: string } | null>(null)

    const filtered = allOffers
        .filter(o => selectedProvider === 'Alle' || o.provider === selectedProvider)
        .filter(o => o.price_with_subscription !== null && o.price_with_subscription !== undefined)
        .sort((a, b) => {
            const aPrice = Number(a.price_with_subscription)
            const bPrice = Number(b.price_with_subscription)
            return sortOrder === 'asc' ? aPrice - bPrice : bPrice - aPrice
        })

    return (
        <main style={{ minHeight: '100vh', background: '#f5f5f5', padding: '2rem' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <h1 style={{ marginBottom: '1.5rem' }}>Mobiltelefoner med abonnement</h1>

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

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
                gap: '1.5rem'
            }}>
                {filtered.map((offer, index) => (
                    <div key={index} style={{
                        border: '1px solid #e0e0e0',
                        borderRadius: 12,
                        padding: '1rem',
                        display: 'flex',
                        flexDirection: 'row',
                        alignItems: 'flex-start',
                        gap: '1rem',
                        background: '#fff',
                    }}>
                        {/* Left: image */}
                        {offer.image_url && (
                            <img
                                src={offer.image_url}
                                alt={offer.product_name}
                                style={{ width: 100, height: 100, objectFit: 'contain', flexShrink: 0, alignSelf: 'center' }}
                            />
                        )}

                        {/* Right: all info */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', flex: 1, minWidth: 0 }}>
                            <p style={{ fontSize: 11, color: '#888', margin: 0 }}>{offer.provider}</p>
                            <h2 style={{ fontSize: 15, margin: 0, lineHeight: 1.3 }}>{offer.product_name}</h2>

                            <p style={{ margin: 0, fontSize: 14 }}>
                                <strong>{offer.price_with_subscription} kr.</strong> med abonnement
                            </p>
                            <p style={{ margin: 0, fontSize: 12, color: '#555' }}>
                                Rabat på telefonen: {offer.discount_on_product} kr.
                            </p>

                            <hr style={{ border: 'none', borderTop: '1px solid #eee', margin: '0.3rem 0' }} />

                            <p style={{ margin: 0, fontSize: 12, color: '#555', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                Pris uden abonnement: {offer.price_without_subscription} kr.
                                <span style={{ position: 'relative', display: 'inline-flex' }}>
                                    <span
                                        onClick={() => setOpenTooltip(openTooltip?.index === index && openTooltip?.type === 'price' ? null : { index, type: 'price' })}
                                        style={{
                                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                            width: 15, height: 15, borderRadius: '50%', border: '1px solid #999',
                                            fontSize: 9, color: '#999', cursor: 'pointer', flexShrink: 0,
                                            lineHeight: 1, userSelect: 'none',
                                        }}
                                    >i</span>
                                    {openTooltip?.index === index && openTooltip?.type === 'price' && (
                                        <span style={{
                                            position: 'absolute', bottom: '120%', left: '50%', transform: 'translateX(-50%)',
                                            background: '#333', color: '#fff', fontSize: 11, padding: '4px 8px',
                                            borderRadius: 6, whiteSpace: 'nowrap', zIndex: 10, pointerEvents: 'none',
                                        }}>
                                            Ifølge abonnementudbyderen
                                            <span style={{ position: 'absolute', top: '100%', left: '50%', transform: 'translateX(-50%)', border: '5px solid transparent', borderTopColor: '#333' }} />
                                        </span>
                                    )}
                                </span>
                            </p>

                            <p style={{ margin: 0, fontSize: 12, color: '#555', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                {offer.market_price ? (
                                    <>
                                        Markedspris: {offer.market_price} kr.
                                        <span style={{ position: 'relative', display: 'inline-flex' }}>
                                            <span
                                                onClick={() => setOpenTooltip(openTooltip?.index === index && openTooltip?.type === 'market' ? null : { index, type: 'market' })}
                                                style={{
                                                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                                    width: 15, height: 15, borderRadius: '50%', border: '1px solid #999',
                                                    fontSize: 9, color: '#999', cursor: 'pointer', flexShrink: 0,
                                                    lineHeight: 1, userSelect: 'none',
                                                }}
                                            >i</span>
                                            {openTooltip?.index === index && openTooltip?.type === 'market' && (
                                                <span style={{
                                                    position: 'absolute', bottom: '120%', left: '50%', transform: 'translateX(-50%)',
                                                    background: '#333', color: '#fff', fontSize: 11, padding: '4px 8px',
                                                    borderRadius: 6, whiteSpace: 'nowrap', zIndex: 10, pointerEvents: 'none',
                                                }}>
                                                    Billigste tilbud lige nu iflg. pricerunner/prisjagt
                                                    <span style={{ position: 'absolute', top: '100%', left: '50%', transform: 'translateX(-50%)', border: '5px solid transparent', borderTopColor: '#333' }} />
                                                </span>
                                            )}
                                        </span>
                                    </>
                                ) : (
                                    <span style={{ color: '#999', fontStyle: 'italic' }}>Ingen markedspris fundet</span>
                                )}
                            </p>

                            {offer.min_cost_6_months && (
                                <p style={{ margin: 0, fontSize: 12, color: '#555' }}>
                                    Mindstepris i 6 mdr.: {offer.min_cost_6_months} kr.
                                </p>
                            )}

                            <hr style={{ border: 'none', borderTop: '1px solid #eee', margin: '0.3rem 0' }} />

                            <p style={{ margin: 0, fontSize: 13, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                Penge reelt sparet efter 6 mdr.:{' '}
                                {(() => {
                                    const base = offer.market_price ?? offer.price_without_subscription
                                    const saved = base - offer.min_cost_6_months
                                    const isFallback = offer.market_price === null
                                    return (
                                        <>
                                            <span style={{ fontWeight: 'bold', fontSize: 15, color: saved > 0 ? '#2e7d32' : '#c62828' }}>
                                                {saved} kr.
                                            </span>
                                            {isFallback && (
                                                <span style={{ position: 'relative', display: 'inline-flex' }}>
                                                    <span
                                                        onClick={() => setOpenTooltip(openTooltip?.index === index && openTooltip?.type === 'saved' ? null : { index, type: 'saved' })}
                                                        style={{
                                                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                                            width: 15, height: 15, borderRadius: '50%', border: '1px solid #999',
                                                            fontSize: 9, color: '#999', cursor: 'pointer', flexShrink: 0,
                                                            lineHeight: 1, userSelect: 'none',
                                                        }}
                                                    >i</span>
                                                    {openTooltip?.index === index && openTooltip?.type === 'saved' && (
                                                        <span style={{
                                                            position: 'absolute', bottom: '120%', left: '50%', transform: 'translateX(-50%)',
                                                            background: '#333', color: '#fff', fontSize: 11, padding: '4px 8px',
                                                            borderRadius: 6, whiteSpace: 'nowrap', zIndex: 10, pointerEvents: 'none',
                                                        }}>
                                                            Ingen markedspris fundet. Resultatet er ud fra udbyderens tal.
                                                            <span style={{ position: 'absolute', top: '100%', left: '50%', transform: 'translateX(-50%)', border: '5px solid transparent', borderTopColor: '#333' }} />
                                                        </span>
                                                    )}
                                                </span>
                                            )}
                                        </>
                                    )
                                })()}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
        </main>
    )
}
