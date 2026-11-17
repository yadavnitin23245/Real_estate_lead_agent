import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Amenities, Thumb } from "../../components/domain";
import { openChat } from "../../components/ChatWidget";
import { IconBath, IconBed, IconCalendar, IconChevronLeft, IconPin, IconRuler, IconShield, IconSparkle } from "../../components/icons";
import { SaveButton, useSavedIds } from "../../components/SaveButton";
import { Button, ButtonLink, Card, EmptyState, Loading, cx } from "../../components/ui";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { area, date, inr, PROPERTY_LABEL } from "../../lib/format";
import type { ListingDetail as Detail } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

export default function ListingDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { data: l, error, loading } = useAsync(() => api<Detail>(`/api/listings/${id}`), [id]);
  const { ids, toggle } = useSavedIds();
  const [active, setActive] = useState(0);

  if (loading) return <Loading />;
  if (error || !l)
    return (
      <EmptyState
        title="Listing not found"
        body={error ?? "It may have been removed."}
        action={<ButtonLink to="/listings">Back to listings</ButtonLink>}
      />
    );

  const isPlot = l.property_type === "plot_land";
  const facts: [string, string][] = [
    ["Property type", PROPERTY_LABEL[l.property_type]],
    ["Locality", `${l.locality}, ${l.city}`],
    ["Area", area(l.area_value, l.area_unit)],
    ...(!isPlot
      ? ([
          ["Bedrooms", l.bedrooms ? `${l.bedrooms}` : "—"],
          ["Bathrooms", l.bathrooms ? `${l.bathrooms}` : "—"],
          ["Furnishing", l.furnishing ? l.furnishing.replace("_", "-").replace(/^./, (c) => c.toUpperCase()) : "—"],
        ] as [string, string][])
      : []),
    ["Price per sq ft", l.area_value && l.area_unit === "sqft" ? inr(Math.round(l.price_inr / l.area_value)) : "—"],
    ["Listed on", date(l.created_at)],
    ["Reference", l.ref_code],
  ];
  const hero = l.images[active] ?? l.images[0];

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <Link to="/listings" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800">
        <IconChevronLeft className="size-4" /> All properties
      </Link>

      <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_200px]">
        <div className="relative aspect-[16/10] overflow-hidden rounded-xl bg-slate-100">
          <Thumb src={hero?.url ?? null} alt={l.title} className="size-full" />
          {l.status === "sold" && (
            <span className="absolute top-4 left-4 rounded bg-slate-900/85 px-2 py-1 text-xs font-semibold text-white">SOLD</span>
          )}
        </div>
        <div className="flex gap-3 overflow-x-auto lg:flex-col">
          {l.images.map((img, i) => (
            <button
              key={img.id}
              onClick={() => setActive(i)}
              className={cx(
                "aspect-[3/2] w-32 shrink-0 overflow-hidden rounded-lg ring-2 lg:w-full",
                i === active ? "ring-brand-600" : "ring-transparent opacity-80 hover:opacity-100",
              )}
            >
              <img src={img.thumb_url} alt="" className="size-full object-cover" />
            </button>
          ))}
        </div>
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_360px]">
        <div>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-xs text-slate-500">{l.ref_code}</p>
              <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">{l.title}</h1>
              <p className="mt-2 flex items-center gap-1 text-sm text-slate-500">
                <IconPin className="size-4" /> {l.locality}, {l.city}
              </p>
            </div>
            <SaveButton variant="inline" saved={ids.has(l.id)} onToggle={() => toggle(l.id)} />
          </div>

          <div className="mt-6 flex flex-wrap gap-6 border-y border-slate-200 py-4 text-sm">
            {!isPlot && l.bedrooms !== null && (
              <span className="flex items-center gap-2"><IconBed className="size-5 text-slate-400" /> {l.bedrooms} Bedrooms</span>
            )}
            {!isPlot && l.bathrooms !== null && (
              <span className="flex items-center gap-2"><IconBath className="size-5 text-slate-400" /> {l.bathrooms} Bathrooms</span>
            )}
            <span className="flex items-center gap-2"><IconRuler className="size-5 text-slate-400" /> {area(l.area_value, l.area_unit)}</span>
          </div>

          <section className="mt-8">
            <h2 className="text-base font-semibold">About this property</h2>
            <p className="mt-3 text-[15px] leading-relaxed whitespace-pre-line text-slate-700">{l.description || "No description yet."}</p>
          </section>

          <section className="mt-8">
            <h2 className="text-base font-semibold">Key facts</h2>
            <dl className="mt-3 grid overflow-hidden rounded-lg ring-1 ring-slate-200 sm:grid-cols-2">
              {facts.map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-slate-100 bg-white px-4 py-3 text-sm sm:odd:border-r">
                  <dt className="text-slate-500">{k}</dt>
                  <dd className="text-right font-medium text-slate-900">{v}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="mt-8">
            <h2 className="text-base font-semibold">Amenities</h2>
            <div className="mt-3">
              <Amenities l={l} />
              {!l.has_parking && !l.near_metro && !l.near_school && <p className="text-sm text-slate-500">None listed.</p>}
            </div>
          </section>
        </div>

        <aside>
          <Card className="sticky top-24 p-6">
            <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Asking price</p>
            <p className="mt-1 text-3xl font-semibold tracking-tight tabular">{inr(l.price_inr)}</p>
            <p className="mt-1 text-xs text-slate-500">Negotiable · Registration & stamp duty extra</p>
            <div className="mt-6 space-y-2">
              {l.status === "sold" ? (
                <p className="rounded-md bg-slate-100 px-3 py-2.5 text-center text-sm text-slate-600">This property has been sold.</p>
              ) : user && user.role !== "buyer" ? (
                <p className="rounded-md bg-slate-50 px-3 py-2.5 text-sm text-slate-600 ring-1 ring-slate-200">
                  You're signed in as staff. Buyers can book visits and chat with the assistant here.
                </p>
              ) : (
                <>
                  <Button size="lg" className="w-full" onClick={() => openChat(`I'd like to book a site visit for ${l.ref_code}`)}>
                    <IconCalendar className="size-4" /> Book a site visit
                  </Button>
                  <Button
                    size="lg"
                    variant="secondary"
                    className="w-full"
                    onClick={() => openChat(`Tell me more about ${l.ref_code}. Is it a good fit for me?`)}
                  >
                    <IconSparkle className="size-4" /> Ask about this property
                  </Button>
                </>
              )}
            </div>
            <div className="mt-6 flex items-start gap-3 border-t border-slate-100 pt-5 text-sm">
              <IconShield className="mt-0.5 size-5 shrink-0 text-brand-700" />
              <p className="text-slate-600">
                <span className="font-medium text-slate-900">Verified by GreenKey.</span> Documents and ownership were
                checked before this listing went live.
              </p>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}
