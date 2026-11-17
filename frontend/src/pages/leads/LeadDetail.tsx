import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { LeadStatusBadge, ScoreBadge, Thumb, VisitBadge } from "../../components/domain";
import { IconCalendar, IconMail, IconPhone } from "../../components/icons";
import { Alert, Button, Card, CardHeader, EmptyState, Loading, PageHeader, Select, Textarea, cx } from "../../components/ui";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { budget, date, dateTime, inr, PROPERTY_LABEL, specLine, STATUS_LABEL, timeline } from "../../lib/format";
import type { LeadDetail as Lead, LeadStatus, VisitStatus } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

const MUST: Record<string, string> = { has_parking: "Parking", near_metro: "Near metro", near_school: "Near school" };

export default function LeadDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const { data: lead, error, loading, setData } = useAsync(() => api<Lead>(`/api/leads/${id}`), [id]);
  const agents = useAsync(
    () => (isAdmin ? api<{ id: number; name: string }[]>("/api/leads/agents") : Promise.resolve([])),
    [isAdmin],
  );
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => setNotes(lead?.notes ?? ""), [lead?.id, lead?.notes]);

  async function patch(body: Record<string, unknown>, key: string) {
    setSaving(key);
    setActionError(null);
    try {
      setData(await api<Lead>(`/api/leads/${id}`, { method: "PATCH", body }));
      if (key === "notes") setSavedAt(new Date().toISOString());
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setSaving(null);
    }
  }

  async function setVisit(visitId: number, status: VisitStatus) {
    setActionError(null);
    try {
      setData(await api<Lead>(`/api/leads/${id}/visits/${visitId}`, { method: "PATCH", body: { status } }));
    } catch (e) {
      setActionError((e as Error).message);
    }
  }

  if (loading && !lead) return <Loading />;
  if (error || !lead)
    return <EmptyState title="Lead not found" body={error ?? undefined} action={<Link to="/console/leads" className="text-sm font-medium text-brand-700">Back to leads</Link>} />;

  const profile: [string, React.ReactNode][] = [
    ["Looking for", `${lead.bedrooms && lead.property_type !== "plot_land" ? `${lead.bedrooms} BHK ` : ""}${lead.property_type ? PROPERTY_LABEL[lead.property_type] : "—"}`],
    ["Localities", lead.preferred_localities.join(", ") || "Any"],
    ["Budget", budget(lead.budget_min, lead.budget_max)],
    ["Timeline", timeline(lead.timeline_months)],
    ["Home loan", lead.loan_preapproved === null ? "Unknown" : lead.loan_preapproved ? "Pre-approved" : "Not pre-approved"],
    ["Must-haves", Object.entries(lead.must_haves).filter(([, v]) => v).map(([k]) => MUST[k] ?? k).join(", ") || "—"],
    ["Preferences", lead.soft_preferences || "—"],
  ];

  return (
    <>
      <PageHeader
        breadcrumb={<Link to="/console/leads" className="hover:text-slate-800">{isAdmin ? "All leads" : "My leads"}</Link>}
        title={
          <span className="flex flex-wrap items-center gap-3">
            {lead.name ?? "Anonymous visitor"}
            <ScoreBadge score={lead.score} />
            <LeadStatusBadge status={lead.status} />
          </span>
        }
        description={`Lead #${lead.id} · created ${date(lead.created_at)}${lead.handed_off_at ? ` · handed off ${date(lead.handed_off_at)}` : ""}`}
        actions={
          <>
            {lead.phone && (
              <a href={`tel:${lead.phone.replace(/\s/g, "")}`} className="inline-flex h-9 items-center gap-2 rounded-md bg-brand-700 px-3.5 text-sm font-medium text-white shadow-sm hover:bg-brand-800">
                <IconPhone className="size-4" /> Call
              </a>
            )}
            {lead.email && (
              <a href={`mailto:${lead.email}`} className="inline-flex h-9 items-center gap-2 rounded-md bg-white px-3.5 text-sm font-medium text-slate-800 shadow-sm ring-1 ring-slate-300 ring-inset hover:bg-slate-50">
                <IconMail className="size-4" /> Email
              </a>
            )}
          </>
        }
      />

      {actionError && <div className="mb-4"><Alert>{actionError}</Alert></div>}

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          {lead.summary && (
            <Card>
              <CardHeader title="Hand-off summary" sub="Written by HomeMatch from the conversation" />
              <pre className="overflow-x-auto px-5 py-4 font-sans text-sm leading-relaxed whitespace-pre-wrap text-slate-700">{lead.summary}</pre>
            </Card>
          )}

          <Card>
            <CardHeader title="Top matches" sub={`${lead.matches.length} listings`} />
            {lead.matches.length === 0 ? (
              <p className="px-5 py-6 text-sm text-slate-500">No matches yet.</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {lead.matches.map((m) => (
                  <li key={m.listing.id} className="flex gap-4 px-5 py-4">
                    <span className="mt-1 font-mono text-xs text-slate-400">#{m.rank}</span>
                    <Thumb src={m.listing.thumb_url} alt="" className="h-16 w-24 shrink-0 rounded-md" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <Link to={`/listings/${m.listing.id}`} target="_blank" className="truncate font-medium text-slate-900 hover:text-brand-700">
                          {m.listing.title}
                        </Link>
                        <span className="text-sm font-semibold tabular">{inr(m.listing.price_inr)}</span>
                      </div>
                      <p className="text-xs text-slate-500">
                        <span className="font-mono">{m.listing.ref_code}</span> · {specLine(m.listing)} · {m.listing.locality}
                      </p>
                      <p className="mt-1.5 text-sm text-slate-600">{m.reason}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <CardHeader title="Conversation" sub={`${lead.messages.length} messages with the HomeMatch assistant`} />
            <div className="max-h-[480px] space-y-3 overflow-y-auto bg-slate-50/60 px-5 py-4">
              {lead.messages.length === 0 && <p className="text-sm text-slate-500">No messages.</p>}
              {lead.messages.map((m) => (
                <div key={m.id} className={cx("flex", m.role === "user" ? "justify-end" : "justify-start")}>
                  <div
                    className={cx(
                      "max-w-[80%] rounded-lg px-3.5 py-2 text-sm",
                      m.role === "user" ? "bg-brand-700 text-white" : "bg-white text-slate-800 ring-1 ring-slate-200",
                    )}
                  >
                    <p className="whitespace-pre-line">{m.content}</p>
                    <p className={cx("mt-1 text-[10.5px]", m.role === "user" ? "text-brand-100/70" : "text-slate-400")}>
                      {m.role === "user" ? lead.name ?? "Visitor" : "Assistant"} · {dateTime(m.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader title="Pipeline" />
            <div className="space-y-4 p-5">
              <div>
                <label className="mb-1.5 block text-[13px] font-medium text-slate-700">Status</label>
                <Select
                  value={lead.status}
                  disabled={saving === "status"}
                  onChange={(e) => patch({ status: e.target.value as LeadStatus }, "status")}
                >
                  {(Object.keys(STATUS_LABEL) as LeadStatus[]).map((s) => (
                    <option key={s} value={s}>{STATUS_LABEL[s]}</option>
                  ))}
                </Select>
              </div>
              {isAdmin && (
                <div>
                  <label className="mb-1.5 block text-[13px] font-medium text-slate-700">Assigned agent</label>
                  <Select
                    value={lead.assigned_agent?.id ?? ""}
                    disabled={saving === "agent"}
                    onChange={(e) => patch({ assigned_agent_id: e.target.value ? Number(e.target.value) : null }, "agent")}
                  >
                    <option value="">Unassigned</option>
                    {agents.data?.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </Select>
                </div>
              )}
              {!isAdmin && lead.assigned_agent && (
                <p className="text-xs text-slate-500">Assigned to you ({lead.assigned_agent.name})</p>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Buyer profile" />
            <dl className="divide-y divide-slate-100 text-sm">
              <div className="px-5 py-3">
                <dt className="text-xs text-slate-500">Contact</dt>
                <dd className="mt-0.5 text-slate-900">{lead.phone ?? "—"}</dd>
                <dd className="text-slate-600">{lead.email ?? ""}</dd>
              </div>
              {profile.map(([k, v]) => (
                <div key={k} className="px-5 py-3">
                  <dt className="text-xs text-slate-500">{k}</dt>
                  <dd className="mt-0.5 text-slate-900">{v}</dd>
                </div>
              ))}
            </dl>
          </Card>

          <Card>
            <CardHeader title="Site visits" />
            {lead.visits.length === 0 ? (
              <p className="px-5 py-4 text-sm text-slate-500">No visits requested.</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {lead.visits.map((v) => (
                  <li key={v.id} className="space-y-2 px-5 py-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{v.listing.title}</p>
                        <p className="flex items-center gap-1 text-xs text-slate-500">
                          <IconCalendar className="size-3.5" /> {v.preferred_time}
                        </p>
                      </div>
                      <VisitBadge status={v.status} />
                    </div>
                    {(v.status === "requested" || v.status === "confirmed") && (
                      <div className="flex gap-2">
                        {v.status === "requested" && (
                          <Button size="sm" onClick={() => setVisit(v.id, "confirmed")}>Confirm</Button>
                        )}
                        {v.status === "confirmed" && (
                          <Button size="sm" onClick={() => setVisit(v.id, "completed")}>Mark done</Button>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => setVisit(v.id, "cancelled")}>Cancel</Button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <CardHeader title="Agent notes" sub="Visible to sales team and admins only" />
            <div className="p-5">
              <Textarea rows={5} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Call outcome, objections, next step…" />
              <div className="mt-3 flex items-center justify-between">
                <span className="text-xs text-slate-400">{savedAt ? "Saved" : ""}</span>
                <Button
                  size="sm"
                  variant="secondary"
                  loading={saving === "notes"}
                  disabled={notes === (lead.notes ?? "")}
                  onClick={() => patch({ notes }, "notes")}
                >
                  Save notes
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
