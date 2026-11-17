export type Role = "buyer" | "seller" | "sales_agent" | "admin";
export type PropertyType = "apartment" | "house" | "villa" | "plot_land" | "commercial";
export type ApprovalStatus = "pending" | "approved" | "rejected";
export type ListingStatus = "available" | "sold";
export type Furnishing = "unfurnished" | "semi_furnished" | "fully_furnished";
export type AreaUnit = "sqft" | "sqm" | "sqyd" | "guntha" | "acre";
export type LeadScore = "hot" | "warm" | "cold";
export type LeadStatus = "new" | "qualifying" | "handed_off" | "nurture" | "closed";
export type VisitStatus = "requested" | "confirmed" | "completed" | "cancelled";

export interface User {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface TokenOut {
  access_token: string;
  expires_in: number;
  user: User;
}

export interface ListingCard {
  id: number;
  ref_code: string;
  title: string;
  city: string;
  locality: string;
  property_type: PropertyType;
  bedrooms: number | null;
  bathrooms: number | null;
  area_value: number | null;
  area_unit: AreaUnit;
  price_inr: number;
  furnishing: Furnishing | null;
  has_parking: boolean;
  near_school: boolean;
  near_metro: boolean;
  status: ListingStatus;
  approval_status: ApprovalStatus;
  thumb_url: string | null;
  created_at: string;
}

export interface ListingDetail extends ListingCard {
  description: string;
  images: { id: number; url: string; thumb_url: string }[];
  owner_name: string | null;
}

export interface ListingPage {
  items: ListingCard[];
  total: number;
  page: number;
  page_size: number;
}

export interface Facets {
  localities: string[];
  property_types: PropertyType[];
  price_min: number;
  price_max: number;
}

export interface ListingInput {
  title: string;
  city: string;
  locality: string;
  property_type: PropertyType;
  bedrooms: number | null;
  bathrooms: number | null;
  area_value: number | null;
  area_unit: AreaUnit;
  price_inr: number;
  furnishing: Furnishing | null;
  has_parking: boolean;
  near_school: boolean;
  near_metro: boolean;
  description: string;
}

export interface LeadRow {
  id: number;
  name: string | null;
  phone: string | null;
  email: string | null;
  budget_min: number | null;
  budget_max: number | null;
  preferred_localities: string[];
  property_type: PropertyType | null;
  bedrooms: number | null;
  timeline_months: number | null;
  loan_preapproved: boolean | null;
  score: LeadScore;
  status: LeadStatus;
  assigned_agent: { id: number; name: string } | null;
  handed_off_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadDetail extends LeadRow {
  must_haves: Record<string, boolean>;
  soft_preferences: string | null;
  summary: string | null;
  notes: string | null;
  city: string | null;
  messages: { id: number; role: "user" | "assistant"; content: string; created_at: string }[];
  matches: {
    rank: number;
    reason: string;
    matched_filters: Record<string, unknown> | null;
    listing: ListingCard;
  }[];
  visits: {
    id: number;
    preferred_time: string;
    status: VisitStatus;
    created_at: string;
    listing: ListingCard;
  }[];
}

export interface AdminStats {
  users_by_role: Partial<Record<Role, number>>;
  listings_by_approval: Partial<Record<ApprovalStatus, number>>;
  listings_live: number;
  listings_sold: number;
  leads_by_score: Partial<Record<LeadScore, number>>;
  leads_by_status: Partial<Record<LeadStatus, number>>;
  leads_total: number;
  leads_unassigned: number;
  visits_open: number;
  llm_cost_usd: number;
  llm_tokens: number;
  leads_per_day: { date: string; leads: number }[];
  agent_load: { id: number; name: string; leads: number }[];
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  listings: ListingCard[];
}

export interface ChatState {
  lead_id: number | null;
  messages: ChatMessage[];
  handed_off_to: string | null;
}
