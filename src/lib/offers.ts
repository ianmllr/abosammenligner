
import telmore from '../../data/telmore/telmore_offers.json'
import oister from '../../data/oister/oister_offers.json'
import elgiganten from '../../data/elgiganten/elgiganten_offers.json'
import cbb from '../../data/cbb/cbb_offers.json'
import three from '../../data/3/3_offers.json'
import prisjagt from '../../data/prisjagt/prisjagt_prices.json'
import pricerunner from '../../data/pricerunner/pricerunner_prices.json'
import type { Offer } from '@/types/offer'

const prisjagtLookup = prisjagt as Record<string, { market_price: number | null }>
const pricerunnerLookup = pricerunner as Record<string, { market_price: number | null }>

function lowestMarketPrice(productName: string): number | null {
    const a = prisjagtLookup[productName]?.market_price ?? null
    const b = pricerunnerLookup[productName]?.market_price ?? null
    if (a !== null && b !== null) return Math.min(a, b)
    return a ?? b
}

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
        subscription_price_monthly: null,
        subscription_price_monthly_after_promo: null,
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
        subscription_price_monthly: o.subscription_price_monthly,
        subscription_price_monthly_after_promo: null,
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
        subscription_price_monthly: o.subscription_price_monthly,
        subscription_price_monthly_after_promo: null,
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
        subscription_price_monthly: o.subscription_price_monthly,
        subscription_price_monthly_after_promo: (o as Record<string, unknown>).subscription_price_monthly_after_promo as number | null ?? null,
    })),
    ...(three as Array<Record<string, unknown>>).map(o => ({
        link: o.link as string | undefined,
        product_name: o.product_name as string,
        image_url: o.image_url as string,
        provider: '3' as const,
        price_with_subscription: o.price_with_subscription as number | null,
        price_without_subscription: o.price_without_subscription as number,
        discount_on_product: o.discount_on_product as number,
        min_cost_6_months: o.min_cost_6_months as number,
        subscription_price_monthly: o.subscription_price_monthly as number | null,
        subscription_price_monthly_after_promo: null,
    })),
].map(offer => ({
    ...offer,
    market_price: lowestMarketPrice(offer.product_name),
}))

export const PROVIDERS = ['Telmore', 'Oister', 'Elgiganten', 'CBB', '3'] as const
