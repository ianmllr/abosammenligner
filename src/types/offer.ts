export interface Offer {
    link: string | undefined
    product_name: string
    image_url: string
    provider: string
    price_with_subscription: number | null
    price_without_subscription: number
    discount_on_product: number
    min_cost_6_months: number
    market_price: number | null
    subscription_price_monthly: number | null
    subscription_price_monthly_after_promo: number | null
}

export type SortOrder =
    | 'asc'
    | 'desc'
    | 'saved_desc'
    | 'saved_asc'
    | 'market_asc'
    | 'market_desc'
    | 'name_asc'
    | 'name_desc'
