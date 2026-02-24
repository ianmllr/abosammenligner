import type { Offer } from '@/types/offer'
import Tooltip from './Tooltip'

interface OfferCardProps {
    offer: Offer
}

export default function OfferCard({ offer }: OfferCardProps) {
    const base = offer.market_price ?? offer.price_without_subscription
    const saved = base - offer.min_cost_6_months
    const isFallback = offer.market_price === null

    return (
        <div className="border border-[#2a2a2a] rounded-xl p-4 flex flex-row items-start gap-4 bg-[#1a1a1a]">
            {offer.image_url && (
                <img
                    src={offer.image_url}
                    alt={offer.product_name}
                    className="w-24 h-24 object-contain flex-shrink-0 self-center"
                />
            )}

            <div className="flex flex-col gap-1 flex-1 min-w-0">
                <p className="text-[11px] text-gray-500 m-0">{offer.provider}</p>
                <h2 className="text-[15px] leading-snug text-[#ededed] m-0 font-semibold">{offer.product_name}</h2>

                <p className="text-sm text-[#ededed] m-0">
                    <strong>{offer.price_with_subscription} kr.</strong> med abonnement
                </p>
                <p className="text-xs text-[#aaa] m-0">
                    Rabat på telefonen: {offer.discount_on_product} kr.
                </p>

                <hr className="border-none border-t border-[#2a2a2a] my-1" />

                <p className="text-xs text-[#aaa] m-0 flex items-center gap-1">
                    Pris uden abonnement: {offer.price_without_subscription} kr.
                    <Tooltip text="Ifølge abonnementudbyderen" />
                </p>

                <p className="text-xs text-[#aaa] m-0 flex items-center gap-1">
                    {offer.market_price ? (
                        <>
                            Markedspris: {offer.market_price} kr.
                            <Tooltip text="Billigste tilbud lige nu iflg. pricerunner/prisjagt" />
                        </>
                    ) : (
                        <span className="text-gray-500 italic">Ingen markedspris fundet</span>
                    )}
                </p>

                {offer.min_cost_6_months && (
                    <p className="text-xs text-[#aaa] m-0">
                        Mindstepris i 6 mdr.: {offer.min_cost_6_months} kr.
                    </p>
                )}

                <hr className="border-none border-t border-[#2a2a2a] my-1" />

                <p className="text-[13px] text-[#ededed] m-0 flex items-center gap-1">
                    Penge reelt sparet efter 6 mdr.:{' '}
                    <span className={`font-bold text-[15px] ${saved > 0 ? 'text-green-800' : 'text-red-800'}`}>
                        {saved} kr.
                    </span>
                    {isFallback && (
                        <Tooltip text="Ingen markedspris fundet. Resultatet er ud fra udbyderens tal." />
                    )}
                </p>

                <button className="mt-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-[13px] font-bold cursor-pointer self-start hover:bg-blue-700 transition-colors">
                    Gå til tilbud
                </button>
            </div>
        </div>
    )
}
