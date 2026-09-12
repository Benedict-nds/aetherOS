import { useMemo, useState } from "react"
import { Search } from "lucide-react"
import { CartPanel } from "../components/CartPanel"
import type { CartLine } from "../components/CartPanel"
import { ProductCard } from "../components/ProductCard"
import type { CatalogueItem } from "../components/ProductCard"



const CATALOGUE: CatalogueItem[] =[
  {
    id: 'paracetamol-500',
    name: 'Paracetamol 500mg',
    brand: 'Panadol',
    stockLeft: 1240,
    unitPrice: 0.12,
    barcode: '8901234500123',
    category: 'Analgesics',
  },
  {
    id: 'amoxicillin-500',
    name: 'Amoxicillin 500mg',
    brand: 'Amoxil',
    stockLeft: 1240,
    unitPrice: 0.35,
    barcode: '8901234500224',
    category: 'Antibiotics',
  },
  {
    id: 'atorvastatin-20',
    name: 'Atorvastatin 20mg',
    brand: 'Lipitor',
    stockLeft: 210,
    unitPrice: 0.62,
    barcode: '8901234500325',
    category: 'Cardiovascular',
  },
  {
    id: 'metformin-850',
    name: 'Metformin 850mg',
    brand: 'Glucophage',
    stockLeft: 90,
    unitPrice: 0.28,
    barcode: '8901234500426',
    category: 'Antidiabetic',
  },
  {
    id: 'salbutamol-inhaler',
    name: 'Salbutamol Inhaler',
    brand: 'Ventolin',
    stockLeft: 64,
    unitPrice: 4.9,
    barcode: '8901234500527',
    category: 'Respiratory',
  },
  {
    id: 'vitamin-d3',
    name: 'Vitamin D3 1000IU',
    brand: 'Cavit-D',
    stockLeft: 1560,
    unitPrice: 0.22,
    barcode: '8901234500628',
    category: 'Vitamins',
  },
  {
    id: 'omeprazole-20',
    name: 'Omeprazole 20mg',
    brand: 'Losec',
    stockLeft: 720,
    unitPrice: 0.44,
    barcode: '8901234500729',
    category: 'Gastrointestinal',
  },
  {
    id: 'azithromycin-250',
    name: 'Azithromycin 250mg',
    brand: 'Zithromax',
    stockLeft: 38,
    unitPrice: 0.95,
    barcode: '8901234500830',
    category: 'Antibiotics',
  },
]

export function PosPage() {
  const [query, setQuery] = useState("")
  const [cart, setCart] = useState<CartLine[]>([])


  const filtered = useMemo(()=>{
    const q = query.trim().toLowerCase()
    if (!q) return CATALOGUE
    return CATALOGUE.filter(
      (item)=>
        item.name.toLowerCase().includes(q) ||
        item.brand.toLowerCase().includes(q) ||
        item.barcode.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q),
      )
  }, [query])


  const addToCart = (item: CatalogueItem) => {
    setCart((prev) => {
      const existing = prev.find((line) => line.id === item.id)
      if (existing){
        return prev.map((line)=>
          line.id === item.id ? {...line, qty:line.qty + 1} : line,
        )
      }
      return [
        ...prev,
        {id:item.id, name:item.name, unitPrice:item.unitPrice, qty:1},
      ]
    })
  }


  const increment = (id:string) => {
    setCart((prev)=>
    prev
    . map((line)=> (line.id === id ? {...line, qty:line.qty + 1} : line))
  )
  }

  const decrement = (id:string) => {
    setCart((prev)=>
    prev
    . map((line)=> (line.id === id ? {...line, qty:line.qty - 1} : line))
      .filter((line) => line.qty > 0),
  )
  }

  const removeLine = (id: string) => {
    setCart((prev) => prev.filter((line) => line.id !== id))
  } 


  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <div className="flex min-w-0 flex-1 flex-col gap-5">
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted"
            strokeWidth={1.75}
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search medicine or scan barcode..."
            className="w-full rounded-lg border border-subtle bg-elevated py-2.5 pl-10 pr-4 text-body text-fg outline-none placeholder:text-muted focus:border-accent"
          />
        </div>
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          {filtered.map((item) => (
            <ProductCard key={item.id} item={item} onAdd={addToCart} />
          ))}
        </div>
      </div>
      <CartPanel lines={cart} onIncrement={increment} onDecrement={decrement} onRemove={removeLine} />
    </div>
  )
}
