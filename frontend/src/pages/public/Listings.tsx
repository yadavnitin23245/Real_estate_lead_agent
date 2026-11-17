import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ListingCard } from "../../components/domain";
import { IconChevronLeft, IconChevronRight, IconSearch, IconX } from "../../components/icons";
import { SaveButton, useSavedIds } from "../../components/SaveButton";
import { Button, Checkbox, EmptyState, Input, Select, cx } from "../../components/ui";
import { api, qs } from "../../lib/api";
import { PROPERTY_LABEL } from "../../lib/format";
import type { Facets, ListingPage, PropertyType } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

const PRICE_STEPS = [
  ["", "No min"],
  ["3000000", "₹30 L"],
  ["5000000", "₹50 L"],
  ["7500000", "₹75 L"],
  ["10000000", "₹1 Cr"],
  ["15000000", "₹1.5 Cr"],
  ["25000000", "₹2.5 Cr"],
  ["50000000", "₹5 Cr"],
] as const;

export default function Listings() {
  const [params, setParams] = useSearchParams();
  const facets = useAsync(() => api<Facets>("/api/listings/facets"), []);
  const { ids, toggle } = useSavedIds();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [q, setQ] = useState(params.get("q") ?? "");
  useEffect(() => setQ(params.get("q") ?? ""), [params]);

  const page = Number(params.get("page") ?? 1);
  const localities = params.getAll("locality");
  const query = qs({
    q: params.get("q"),
    locality: localities,
    property_type: params.get("property_type"),
    bedrooms: params.get("bedrooms"),
    price_min: params.get("price_min"),
    price_max: params.get("price_max"),
    has_parking: params.get("has_parking") === "true",
    near_metro: params.get("near_metro") === "true",
    near_school: params.get("near_school") === "true",
    sort: params.get("sort"),
    page,
    page_size: 12,
  });
  const result = useAsync(() => api<ListingPage>(`/api/listings${query}`), [query]);

  function update(changes: Record<string, string | string[] | null>) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(changes)) {
      next.delete(k);
      if (Array.isArray(v)) v.forEach((x) => next.append(k, x));
      else if (v) next.set(k, v);
    }
    if (!("page" in changes)) next.delete("page");
    setParams(next);
  }

  const activeCount = [...params.keys()].filter((k) => !["page", "sort", "q"].includes(k)).length;
  const totalPages = result.data ? Math.max(1, Math.ceil(result.data.total / result.data.page_size)) : 1;

  const filters = (
    <div className="space-y-6">
      <div>
        <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Property type</h3>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {(["", ...Object.keys(PROPERTY_LABEL)] as ("" | PropertyType)[]).map((t) => {
            const active = (params.get("property_type") ?? "") === t;
            return (
              <button
                key={t || "any"}
                onClick={() => update({ property_type: t || null })}
                className={cx(
                  "rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition",
                  active ? "bg-brand-700 text-white ring-brand-700" : "bg-white text-slate-700 ring-slate-300 hover:bg-slate-50",
                )}
              >
                {t ? PROPERTY_LABEL[t] : "Any"}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Bedrooms</h3>
        <div className="mt-2 grid grid-cols-5 overflow-hidden rounded-md ring-1 ring-slate-300">
          {["", "1", "2", "3", "4"].map((b) => {
            const active = (params.get("bedrooms") ?? "") === b;
            return (
              <button
                key={b || "any"}
                onClick={() => update({ bedrooms: b || null })}
                className={cx(
                  "border-r border-slate-300 py-1.5 text-xs font-medium last:border-r-0",
                  active ? "bg-slate-900 text-white" : "bg-white text-slate-700 hover:bg-slate-50",
                )}
              >
                {b ? (b === "4" ? "4+" : b) : "Any"}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Budget</h3>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <Select value={params.get("price_min") ?? ""} onChange={(e) => update({ price_min: e.target.value })} aria-label="Minimum price">
            {PRICE_STEPS.map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </Select>
          <Select value={params.get("price_max") ?? ""} onChange={(e) => update({ price_max: e.target.value })} aria-label="Maximum price">
            {PRICE_STEPS.map(([v, l]) => (
              <option key={v} value={v}>{v ? l : "No max"}</option>
            ))}
          </Select>
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Must have</h3>
        <div className="mt-2 space-y-2">
          {([
            ["has_parking", "Car parking"],
            ["near_metro", "Near metro"],
            ["near_school", "Near a school"],
          ] as const).map(([k, l]) => (
            <Checkbox key={k} label={l} checked={params.get(k) === "true"} onChange={(v) => update({ [k]: v ? "true" : null })} />
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Locality</h3>
        <div className="mt-2 max-h-64 space-y-2 overflow-y-auto pr-1">
          {facets.data?.localities.map((l) => (
            <Checkbox
              key={l}
              label={l}
              checked={localities.includes(l)}
              onChange={(v) => update({ locality: v ? [...localities, l] : localities.filter((x) => x !== l) })}
            />
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Properties for sale in Pune</h1>
          <p className="mt-1 text-sm text-slate-500 tabular">
            {result.data ? `${result.data.total.toLocaleString("en-IN")} results` : "Searching…"}
          </p>
        </div>
        <form
          className="flex w-full gap-2 sm:w-auto"
          onSubmit={(e) => {
            e.preventDefault();
            update({ q: q.trim() || null });
          }}
        >
          <div className="relative flex-1 sm:w-72">
            <IconSearch className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search title, locality or ref code" className="pl-9" />
          </div>
          <Select
            value={params.get("sort") ?? "newest"}
            onChange={(e) => update({ sort: e.target.value === "newest" ? null : e.target.value })}
            className="w-auto"
            aria-label="Sort"
          >
            <option value="newest">Newest</option>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
          </Select>
        </form>
      </div>

      <div className="mt-6 flex items-center gap-2 lg:hidden">
        <Button variant="secondary" onClick={() => setFiltersOpen(true)}>
          Filters {activeCount > 0 && <span className="rounded-full bg-brand-700 px-1.5 text-[11px] text-white">{activeCount}</span>}
        </Button>
      </div>

      <div className="mt-6 grid gap-8 lg:grid-cols-[240px_1fr]">
        <aside className="hidden lg:block">
          <div className="sticky top-24">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Filters</h2>
              {activeCount > 0 && (
                <button onClick={() => setParams(new URLSearchParams())} className="text-xs font-medium text-brand-700 hover:underline">
                  Clear all
                </button>
              )}
            </div>
            {filters}
          </div>
        </aside>

        <section>
          {result.error && <p className="text-sm text-red-600">{result.error}</p>}
          <div className={cx("grid gap-5 sm:grid-cols-2 xl:grid-cols-3", result.loading && result.data && "opacity-60")}>
            {result.loading && !result.data &&
              Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-80 animate-pulse rounded-lg bg-slate-200/60" />)}
            {result.data?.items.map((l) => (
              <ListingCard key={l.id} listing={l} action={<SaveButton saved={ids.has(l.id)} onToggle={() => toggle(l.id)} />} />
            ))}
          </div>
          {result.data && result.data.items.length === 0 && (
            <EmptyState
              icon={<IconSearch />}
              title="No properties match these filters"
              body="Try widening the budget or removing a locality."
              action={<Button variant="secondary" onClick={() => setParams(new URLSearchParams())}>Reset filters</Button>}
            />
          )}
          {result.data && totalPages > 1 && (
            <nav className="mt-10 flex items-center justify-between border-t border-slate-200 pt-5">
              <Button variant="secondary" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>
                <IconChevronLeft className="size-4" /> Previous
              </Button>
              <span className="text-sm text-slate-500 tabular">
                Page {page} of {totalPages}
              </span>
              <Button variant="secondary" disabled={page >= totalPages} onClick={() => update({ page: String(page + 1) })}>
                Next <IconChevronRight className="size-4" />
              </Button>
            </nav>
          )}
        </section>
      </div>

      {filtersOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-slate-950/40" onClick={() => setFiltersOpen(false)} />
          <div className="absolute inset-y-0 right-0 flex w-80 max-w-[90vw] flex-col bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <h2 className="text-sm font-semibold">Filters</h2>
              <button onClick={() => setFiltersOpen(false)} aria-label="Close filters" className="p-1 text-slate-500">
                <IconX className="size-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">{filters}</div>
            <div className="flex gap-2 border-t border-slate-200 p-3">
              <Button variant="secondary" className="flex-1" onClick={() => setParams(new URLSearchParams())}>Clear</Button>
              <Button className="flex-1" onClick={() => setFiltersOpen(false)}>Show results</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
