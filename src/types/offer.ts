export interface Offer {
    link: string | undefined
    product_name: string
    image_url: string
    provider: string
    price_with_subscription: number | null
    price_without_subscription: number | null
    discount_on_product: number | null
    min_cost_6_months: number | null
    market_price: number | null
    subscription_price_monthly: number | null
    subscription_price_monthly_after_promo: number | null
}

export type SortOrder =
    | 'asc'
    | 'desc'
    | 'saved_desc'
    | 'saved_asc'
    | 'pct_desc'
    | 'pct_asc'
    | 'market_asc'
    | 'market_desc'
    | 'name_asc'
    | 'name_desc'
