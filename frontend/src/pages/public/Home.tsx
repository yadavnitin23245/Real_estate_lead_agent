import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ListingCard } from "../../components/domain";
import { IconArrowRight, IconCalendar, IconSearch, IconShield, IconSparkle } from "../../components/icons";
import { SaveButton, useSavedIds } from "../../components/SaveButton";
import { Button, ButtonLink, Select } from "../../components/ui";
import { api, qs } from "../../lib/api";
import type { Facets, ListingPage } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

const BUDGETS = [
  { label: "Any budget", value: "" },
  { label: "Up to ₹60 L", value: "6000000" },
  { label: "Up to ₹1 Cr", value: "10000000" },
  { label: "Up to ₹1.5 Cr", value: "15000000" },
  { label: "Up to ₹2.5 Cr", value: "25000000" },
];

export default function Home() {
  const navigate = useNavigate();
  const facets = useAsync(() => api<Facets>("/api/listings/facets"), []);
  const featured = useAsync(() => api<ListingPage>(`/api/listings${qs({ page_size: 8 })}`), []);
  const { ids, toggle } = useSavedIds();
  const [locality, setLocality] = useState("");
  const [type, setType] = useState("");
  const [max, setMax] = useState("");

  function search(e: FormEvent) {
    e.preventDefault();
    navigate(`/listings${qs({ locality: locality ? [locality] : [], property_type: type, price_max: max })}`);
  }

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-ink-950">
        <div
          aria-hidden
          className="absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
            backgroundSize: "56px 56px",
          }}
        />
        <div aria-hidden className="absolute -top-40 right-0 size-[600px] rounded-full bg-brand-700/25 blur-3xl" />
        <div className="relative mx-auto max-w-7xl px-4 pt-20 pb-24 sm:px-6 lg:pt-28 lg:pb-32">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/5 px-3 py-1 text-xs font-medium text-brand-200 ring-1 ring-white/10">
            <span className="size-1.5 rounded-full bg-brand-500" />
            {featured.data ? `${featured.data.total} verified homes live in Pune` : "Verified homes across Pune"}
          </p>
          <h1 className="mt-5 max-w-3xl text-4xl leading-[1.1] font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Find the home that fits — <span className="text-brand-500">not just the filters.</span>
          </h1>
          <p className="mt-5 max-w-xl text-base text-slate-400 sm:text-lg">
            Browse verified listings across 12 Pune localities. Shortlist what you like and a GreenKey agent will
            arrange the visit.
          </p>

          <form
            onSubmit={search}
            className="mt-10 grid max-w-4xl gap-2 rounded-xl bg-white p-2 shadow-2xl shadow-black/30 sm:grid-cols-[1fr_1fr_1fr_auto]"
          >
            <Select value={locality} onChange={(e) => setLocality(e.target.value)} className="h-11 ring-0 shadow-none sm:border-r sm:border-slate-200" aria-label="Locality">
              <option value="">All localities</option>
              {facets.data?.localities.map((l) => (
                <option key={l}>{l}</option>
              ))}
            </Select>
            <Select value={type} onChange={(e) => setType(e.target.value)} className="h-11 ring-0 shadow-none" aria-label="Property type">
              <option value="">Any property type</option>
              <option value="apartment">Apartment</option>
              <option value="house">Independent house</option>
              <option value="villa">Villa</option>
              <option value="plot_land">Plot / land</option>
              <option value="commercial">Commercial</option>
            </Select>
            <Select value={max} onChange={(e) => setMax(e.target.value)} className="h-11 ring-0 shadow-none" aria-label="Budget">
              {BUDGETS.map((b) => (
                <option key={b.label} value={b.value}>
                  {b.label}
                </option>
              ))}
            </Select>
            <Button type="submit" size="lg" className="h-11">
              <IconSearch className="size-4" /> Search
            </Button>
          </form>

          {facets.data && (
            <div className="mt-6 flex flex-wrap items-center gap-2 text-sm text-slate-400">
              <span>Popular:</span>
              {facets.data.localities.slice(0, 6).map((l) => (
                <Link
                  key={l}
                  to={`/listings?locality=${encodeURIComponent(l)}`}
                  className="rounded-full px-2.5 py-1 text-slate-300 ring-1 ring-white/15 hover:bg-white/5 hover:text-white"
                >
                  {l}
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Featured */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-wider text-brand-700 uppercase">Just listed</p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight">Fresh on the market</h2>
          </div>
          <Link to="/listings" className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-800">
            View all <IconArrowRight className="size-4" />
          </Link>
        </div>
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {featured.loading &&
            Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-80 animate-pulse rounded-lg bg-slate-200/60" />
            ))}
          {featured.data?.items.map((l) => (
            <ListingCard
              key={l.id}
              listing={l}
              action={<SaveButton saved={ids.has(l.id)} onToggle={() => toggle(l.id)} />}
            />
          ))}
        </div>
        {featured.error && <p className="mt-6 text-sm text-red-600">Couldn't load listings: {featured.error}</p>}
      </section>

      {/* How it works */}
      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
          <h2 className="text-2xl font-semibold tracking-tight">How HomeMatch works</h2>
          <div className="mt-10 grid gap-8 md:grid-cols-3">
            {[
              { n: "01", icon: <IconSparkle />, t: "Tell us what matters", b: "Budget, locality, BHK, school or metro nearby — set it once." },
              { n: "02", icon: <IconShield />, t: "See verified matches", b: "Every listing is reviewed by our team before it goes live." },
              { n: "03", icon: <IconCalendar />, t: "Visit with an agent", b: "Book a site visit; a GreenKey agent confirms and accompanies you." },
            ].map((s) => (
              <div key={s.n} className="relative rounded-lg border border-slate-200 p-6">
                <span className="font-mono text-xs text-slate-400">{s.n}</span>
                <div className="mt-3 grid size-10 place-items-center rounded-md bg-brand-50 text-xl text-brand-700">{s.icon}</div>
                <h3 className="mt-4 font-semibold">{s.t}</h3>
                <p className="mt-1 text-sm text-slate-500">{s.b}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Seller CTA */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="flex flex-col items-start justify-between gap-6 rounded-xl bg-brand-800 px-8 py-10 md:flex-row md:items-center">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-white">Selling a property in Pune?</h2>
            <p className="mt-1 text-brand-100/80">List it with GreenKey — reviewed within 48 hours, matched to qualified buyers.</p>
          </div>
          <ButtonLink to="/signup?role=seller" variant="secondary" size="lg">
            List your property
          </ButtonLink>
        </div>
      </section>
    </>
  );
}
