import { useCallback, useEffect, useMemo, useState } from "react"
import { Search } from "lucide-react"
import { Alert, Input, Skeleton } from "@/components/ui"
import { CartPanel } from "../components/CartPanel"
import type { CartLine } from "../components/CartPanel"
import { ProductCard } from "../components/ProductCard"
import type { CatalogueItem } from "../components/ProductCard"
import { getErrorMessage } from "@/lib/api/client"
import { listMedicineBatchesRequest, listMedicinesRequest } from "@/lib/api/medicines"
import type { Medicine, MedicineBatch } from "@/lib/api/types"

// local calendar date as YYYY-MM-DD, comparable with the API's expiry_date strings
function todayIso() {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// earliest expiry first (FEFO); batches without an expiry go last
function compareExpiry(a: MedicineBatch, b: MedicineBatch) {
  if (a.expiry_date === b.expiry_date) return 0
  if (!a.expiry_date) return 1
  if (!b.expiry_date) return -1
  return a.expiry_date < b.expiry_date ? -1 : 1
}

function toCatalogueItem(
  medicine: Medicine,
  batches: MedicineBatch[],
  today: string,
): CatalogueItem | null {
  const sellable = batches
    .filter(
      (batch) =>
        batch.status !== "void" &&
        Number(batch.quantity_on_hand) > 0 &&
        (!batch.expiry_date || batch.expiry_date.slice(0, 10) >= today),
    )
    .sort(compareExpiry)

  const first = sellable[0]
  if (!first) return null

  return {
    id: String(medicine.id),
    name: medicine.name,
    brand: medicine.brand_name ?? medicine.generic_name ?? "",
    stockLeft: sellable.reduce((sum, batch) => sum + Number(batch.quantity_on_hand), 0),
    unitPrice: Number(first.selling_price),
    barcode: medicine.barcode ?? "",
    category: medicine.category_name ?? "",
  }
}

export function PosPage() {
  const [query, setQuery] = useState("")
  const [cart, setCart] = useState<CartLine[]>([])

  const [catalogue, setCatalogue] = useState<CatalogueItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  // silent = refresh in the background (after a sale) without flashing the loading state
  const loadCatalogue = useCallback(async (silent = false) => {
    if (!silent) setIsLoading(true)
    setLoadError(null)
    try {
      const res = await listMedicinesRequest()
      const medicines = res.data ?? []
      const today = todayIso()

      const items = await Promise.all(
        // a medicine with zero on hand can't have sellable batches, so skip its request
        medicines
          .filter((medicine) => medicine.quantity_on_hand > 0)
          .map(async (medicine) => {
            try {
              const batchRes = await listMedicineBatchesRequest(medicine.id)
              return toCatalogueItem(medicine, batchRes.data ?? [], today)
            } catch {
              // one medicine failing to load shouldn't blank the whole grid
              return null
            }
          }),
      )

      setCatalogue(items.filter((item): item is CatalogueItem => item !== null))
    } catch (err) {
      setLoadError(getErrorMessage(err, "Could not load medicines"))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadCatalogue()
  }, [loadCatalogue])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return catalogue
    return catalogue.filter(
      (item) =>
        item.name.toLowerCase().includes(q) ||
        item.brand.toLowerCase().includes(q) ||
        item.barcode.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q),
    )
  }, [query, catalogue])

  const addToCart = (item: CatalogueItem) => {
    setCart((prev) => {
      const existing = prev.find((line) => line.id === item.id)
      if (existing) {
        return prev.map((line) =>
          line.id === item.id ? { ...line, qty: line.qty + 1 } : line,
        )
      }
      return [
        ...prev,
        { id: item.id, name: item.name, unitPrice: item.unitPrice, qty: 1 },
      ]
    })
  }

  const increment = (id: string) => {
    setCart((prev) =>
      prev.map((line) => (line.id === id ? { ...line, qty: line.qty + 1 } : line)),
    )
  }

  const decrement = (id: string) => {
    setCart((prev) =>
      prev
        .map((line) => (line.id === id ? { ...line, qty: line.qty - 1 } : line))
        .filter((line) => line.qty > 0),
    )
  }

  const removeLine = (id: string) => {
    setCart((prev) => prev.filter((line) => line.id !== id))
  }

  const handleSaleComplete = () => {
    setCart([])
    // stock changed, so refresh the grid's leftover quantities and prices
    void loadCatalogue(true)
  }

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <div className="flex min-w-0 flex-1 flex-col gap-5">
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted"
            strokeWidth={1.75}
          />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search medicine or scan barcode..."
            className="py-2.5 pr-4 pl-10"
          />
        </div>
        {isLoading ? (
          <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
            {Array.from({ length: 8 }, (_, index) => (
              <Skeleton key={index} className="h-28 rounded-xl" />
            ))}
          </div>
        ) : loadError ? (
          <Alert variant="destructive">{loadError}</Alert>
        ) : filtered.length === 0 ? (
          <Alert>
            {catalogue.length === 0 ? "No medicines in stock" : "No medicines match your search"}
          </Alert>
        ) : (
          <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
            {filtered.map((item) => (
              <ProductCard key={item.id} item={item} onAdd={addToCart} />
            ))}
          </div>
        )}
      </div>
      <CartPanel
        lines={cart}
        onIncrement={increment}
        onDecrement={decrement}
        onRemove={removeLine}
        onSaleComplete={handleSaleComplete}
      />
    </div>
  )
}
