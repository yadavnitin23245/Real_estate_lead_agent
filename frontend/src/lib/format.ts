import type { AreaUnit, LeadScore, LeadStatus, ListingCard, PropertyType, Role } from "./types";

/** 14500000 -> "₹1.45 Cr", 8500000 -> "₹85 L" */
export function inr(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "—";
  if (amount >= 1e7) return `₹${trim(amount / 1e7, 2)} Cr`;
  if (amount >= 1e5) return `₹${trim(amount / 1e5, 1)} L`;
  return `₹${amount.toLocaleString("en-IN")}`;
}

function trim(n: number, digits: number) {
  return n.toFixed(digits).replace(/\.?0+$/, "");
}

export function budget(min: number | null, max: number | null): string {
  if (min && max) return `${inr(min)} – ${inr(max)}`;
  if (max) return `up to ${inr(max)}`;
  if (min) return `from ${inr(min)}`;
  return "—";
}

export function timeline(months: number | null): string {
  if (months === null) return "—";
  if (months <= 0) return "Immediate";
  return `${months} mo`;
}

export const PROPERTY_LABEL: Record<PropertyType, string> = {
  apartment: "Apartment",
  house: "Independent house",
  villa: "Villa",
  plot_land: "Plot / land",
  commercial: "Commercial",
};

export const ROLE_LABEL: Record<Role, string> = {
  buyer: "Buyer",
  seller: "Seller",
  sales_agent: "Sales agent",
  admin: "Admin",
};

export const STATUS_LABEL: Record<LeadStatus, string> = {
  new: "New",
  qualifying: "Qualifying",
  handed_off: "Handed off",
  nurture: "Nurture",
  closed: "Closed",
};

export const SCORE_LABEL: Record<LeadScore, string> = { hot: "Hot", warm: "Warm", cold: "Cold" };

const UNIT: Record<AreaUnit, string> = {
  sqft: "sq ft",
  sqm: "sq m",
  sqyd: "sq yd",
  guntha: "guntha",
  acre: "acre",
};

export function area(value: number | null, unit: AreaUnit): string {
  if (!value) return "—";
  return `${Math.round(value).toLocaleString("en-IN")} ${UNIT[unit]}`;
}

export function specLine(l: Pick<ListingCard, "property_type" | "bedrooms" | "area_value" | "area_unit">) {
  const parts: string[] = [];
  if (l.bedrooms && l.property_type !== "plot_land" && l.property_type !== "commercial") {
    parts.push(`${l.bedrooms} BHK`);
  }
  parts.push(PROPERTY_LABEL[l.property_type]);
  if (l.area_value) parts.push(area(l.area_value, l.area_unit));
  return parts.join(" · ");
}

const dateFmt = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" });
const timeFmt = new Intl.DateTimeFormat("en-IN", { hour: "numeric", minute: "2-digit" });

export function date(iso: string | null | undefined): string {
  return iso ? dateFmt.format(new Date(iso)) : "—";
}

export function dateTime(iso: string): string {
  const d = new Date(iso);
  return `${dateFmt.format(d)}, ${timeFmt.format(d)}`;
}

export function relative(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}d ago`;
  return date(iso);
}

export function initials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join("");
}
