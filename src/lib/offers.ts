
import telmore from '../../data/telmore/telmore_offers.json'
import oister from '../../data/oister/oister_offers.json'
import elgiganten from '../../data/elgiganten/elgiganten_offers.json'
import cbb from '../../data/cbb/cbb_offers.json'
import prisjagt from '../../data/prisjagt/prisjagt_prices.json'
import type { Offer } from '@/types/offer'

const prisjagtLookup = prisjagt as Record<string, { market_price: number | null }>

export const allOffers: Offer[] = [
    ...telmore.map(o => ({
        link: o.link,
        product_name: o.product_name,
        image_url: o.image_url,
        provider: 'Telmore' as const,
        price_with_subscription: o.price_with_subscription,
        price_without_subscription: o.price_without_subscription,
        discount_on_product: o.discount_on_product,
        min_cost_6_months: o.min_cost_6_months,
    })),
    ...oister.map(o => ({
        link: o.link,
        product_name: o.product_name,
        image_url: o.image_url,
        provider: 'Oister' as const,
        price_with_subscription: o.price_with_subscription,
        price_without_subscription: o.price_without_subscription,
        discount_on_product: o.discount_on_product,
        min_cost_6_months: o.min_cost_6_months,
    })),
    ...elgiganten.map(o => ({
        link: o.link,
        product_name: o.product,
        image_url: o.image_url,
        provider: 'Elgiganten' as const,
        price_with_subscription: o.price_with_subscription,
        price_without_subscription: o.price_without_subscription,
        discount_on_product: o.discount_on_product,
        min_cost_6_months: o.min_cost_6_months,
    })),
    ...cbb.map(o => ({
        link: o.link,
        product_name: o.product_name,
        image_url: o.image_url,
        provider: 'CBB' as const,
        price_with_subscription: o.price_with_subscription,
        price_without_subscription: o.price_without_subscription,
        discount_on_product: o.discount_on_product,
        min_cost_6_months: o.min_cost_6_months,
    })),
].map(offer => ({
    ...offer,
    market_price: prisjagtLookup[offer.product_name]?.market_price ?? null,
}))

export const PROVIDERS = ['Alle', 'Telmore', 'Oister', 'Elgiganten'] as const
