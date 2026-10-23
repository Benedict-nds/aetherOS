import { Plus } from "lucide-react";
import { Card } from "@/components/ui";

export type CatalogueItem = {
    id: string
    name:string
    brand:string
    stockLeft:number
    unitPrice:number
    barcode:string
    category:string
}


type ProductCardProps = {
    item: CatalogueItem
    onAdd: (item: CatalogueItem) => void
}


function formatMoney(value:number){
    return `GH₵ ${value.toFixed(2)}`
}


export const ProductCard = ({item, onAdd}: ProductCardProps) =>{
    return (
        <button
        type="button"
        onClick={() => onAdd(item)}
        className="w-full rounded-[14px] text-left outline-none hover:ring-1 hover:ring-subtle focus-visible:ring-1 focus-visible:ring-accent"
        >
            <Card className="gap-1.5 p-3.5">
            <span className="text-body text-fg">{item.name}</span>
            <span className="text-caption text-muted">
                {item.brand ? `${item.brand} · ` : ''}{item.stockLeft.toLocaleString()} left
            </span>
            <span className="mt-1 flex items-center justify-between">
                <span className="text-body text-fg">{formatMoney(item.unitPrice)}</span>
                <span 
                aria-hidden= "true"
                className="flex size-6 items-center justify-center rounded-full bg-accent text-[var(--bg-base)]">
                    <Plus className="size-3.5" strokeWidth={2.5} /> 
                </span>
            </span>
            </Card>
        </button>
    )
}
