// Domain-specific building blocks: logo, status badges, listing card.
import { Link } from "react-router-dom";
import { inr, SCORE_LABEL, specLine, STATUS_LABEL } from "../lib/format";
import type { ApprovalStatus, LeadScore, LeadStatus, ListingCard as Listing, VisitStatus } from "../lib/types";
import { IconCar, IconPin, IconSchool, IconTrain } from "./icons";
import { Badge, cx, type BadgeTone } from "./ui";

export function Logo({ dark, compact }: { dark?: boolean; compact?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <span className="grid size-8 place-items-center rounded-md bg-brand-700 text-white shadow-sm">
        <svg viewBox="0 0 24 24" className="size-[18px]" fill="currentColor" aria-hidden>
          <path d="M4 11.2 12 4.5l8 6.7V19a1 1 0 0 1-1 1h-4.6v-5.4H9.6V20H5a1 1 0 0 1-1-1z" />
        </svg>
      </span>
      {!compact && (
        <span className="leading-none">
          <span className={cx("block text-[15px] font-semibold tracking-tight", dark ? "text-white" : "text-slate-900")}>
            HomeMatch
          </span>
          <span className={cx("mt-0.5 block text-[10.5px] font-medium tracking-wide uppercase", dark ? "text-brand-200/70" : "text-slate-500")}>
            GreenKey Realty
          </span>
        </span>
      )}
    </span>
  );
}

const SCORE_TONE: Record<LeadScore, BadgeTone> = { hot: "red", warm: "amber", cold: "blue" };
export function ScoreBadge({ score }: { score: LeadScore }) {
  return (
    <Badge tone={SCORE_TONE[score]} dot>
      {SCORE_LABEL[score]}
    </Badge>
  );
}

const STATUS_TONE: Record<LeadStatus, BadgeTone> = {
  new: "violet",
  qualifying: "blue",
  handed_off: "green",
  nurture: "amber",
  closed: "gray",
};
export function LeadStatusBadge({ status }: { status: LeadStatus }) {
  return <Badge tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Badge>;
}

const APPROVAL: Record<ApprovalStatus, [BadgeTone, string]> = {
  pending: ["amber", "In review"],
  approved: ["green", "Live"],
  rejected: ["red", "Rejected"],
};
export function ApprovalBadge({ status, sold }: { status: ApprovalStatus; sold?: boolean }) {
  if (sold) return <Badge tone="gray">Sold</Badge>;
  const [tone, label] = APPROVAL[status];
  return (
    <Badge tone={tone} dot>
      {label}
    </Badge>
  );
}

const VISIT: Record<VisitStatus, BadgeTone> = {
  requested: "amber",
  confirmed: "green",
  completed: "gray",
  cancelled: "red",
};
export function VisitBadge({ status }: { status: VisitStatus }) {
  return <Badge tone={VISIT[status]}>{status[0]!.toUpperCase() + status.slice(1)}</Badge>;
}

export function Thumb({ src, alt, className }: { src: string | null; alt: string; className?: string }) {
  return src ? (
    <img src={src} alt={alt} loading="lazy" className={cx("object-cover", className)} />
  ) : (
    <div className={cx("grid place-items-center bg-slate-100 text-xs text-slate-400", className)}>No photo</div>
  );
}

export function Amenities({ l }: { l: Pick<Listing, "has_parking" | "near_metro" | "near_school"> }) {
  const items = [
    l.has_parking && { icon: <IconCar />, label: "Parking" },
    l.near_metro && { icon: <IconTrain />, label: "Near metro" },
    l.near_school && { icon: <IconSchool />, label: "Near school" },
  ].filter(Boolean) as { icon: React.ReactNode; label: string }[];
  if (!items.length) return null;
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
      {items.map((i) => (
        <span key={i.label} className="inline-flex items-center gap-1 [&_svg]:size-3.5 [&_svg]:text-slate-400">
          {i.icon}
          {i.label}
        </span>
      ))}
    </div>
  );
}

export function ListingCard({
  listing,
  action,
}: {
  listing: Listing;
  action?: React.ReactNode;
}) {
  const sold = listing.status === "sold";
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-lg bg-white ring-1 ring-slate-200 transition hover:shadow-md hover:ring-slate-300">
      <div className="relative aspect-[3/2] overflow-hidden bg-slate-100">
        <Thumb
          src={listing.thumb_url}
          alt={listing.title}
          className="size-full transition duration-300 group-hover:scale-[1.03]"
        />
        <div className="absolute top-2.5 left-2.5 flex gap-1.5">
          <span className="rounded bg-white/95 px-1.5 py-0.5 font-mono text-[10.5px] font-medium text-slate-700 shadow-sm">
            {listing.ref_code}
          </span>
          {sold && <span className="rounded bg-slate-900/85 px-1.5 py-0.5 text-[10.5px] font-semibold text-white">SOLD</span>}
        </div>
        {action && <div className="absolute top-2 right-2 z-10">{action}</div>}
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-baseline justify-between gap-2">
          <p className="text-lg font-semibold tracking-tight text-slate-900 tabular">{inr(listing.price_inr)}</p>
          <p className="truncate text-xs text-slate-500">{specLine(listing)}</p>
        </div>
        <h3 className="line-clamp-1 text-sm font-medium text-slate-800">
          <Link to={`/listings/${listing.id}`} className="after:absolute after:inset-0">
            {listing.title}
          </Link>
        </h3>
        <p className="flex items-center gap-1 text-xs text-slate-500">
          <IconPin className="size-3.5" /> {listing.locality}, {listing.city}
        </p>
        <div className="mt-auto border-t border-slate-100 pt-2.5">
          <Amenities l={listing} />
        </div>
      </div>
    </article>
  );
}
