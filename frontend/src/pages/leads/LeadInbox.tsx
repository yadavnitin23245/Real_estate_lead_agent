import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { LeadStatusBadge, ScoreBadge } from "../../components/domain";
import { IconInbox, IconSearch } from "../../components/icons";
import { Card, EmptyState, Input, Loading, PageHeader, Select, Table, Td, Th, cx } from "../../components/ui";
import { api, qs } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { budget, PROPERTY_LABEL, relative, STATUS_LABEL, timeline } from "../../lib/format";
import type { LeadRow, LeadScore, LeadStatus } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

const SCORES: ("" | LeadScore)[] = ["", "hot", "warm", "cold"];

export default function LeadInbox() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const score = (params.get("score") ?? "") as "" | LeadScore;
  const status = params.get("status") ?? "";
  const unassigned = params.get("unassigned") === "true";

  const query = qs({ score, status, q: params.get("q"), unassigned });
  const { data, loading, error } = useAsync(() => api<LeadRow[]>(`/api/leads${query}`), [query]);
  const all = useAsync(() => api<LeadRow[]>("/api/leads"), []);

  const setParam = (k: string, v: string) => {
    const n = new URLSearchParams(params);
    if (v) n.set(k, v);
    else n.delete(k);
    setParams(n);
  };
  const countBy = (s: LeadScore) => all.data?.filter((l) => l.score === s).length ?? 0;

  return (
    <>
      <PageHeader
        title={isAdmin ? "All leads" : "My leads"}
        description={
          isAdmin
            ? "Every lead captured by HomeMatch. Assign them to sales agents from the lead page."
            : "Leads handed to you by the HomeMatch assistant. Hot leads are listed first."
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="inline-flex overflow-hidden rounded-md bg-white ring-1 ring-slate-300">
          {SCORES.map((s) => (
            <button
              key={s || "all"}
              onClick={() => setParam("score", s)}
              className={cx(
                "flex items-center gap-1.5 border-r border-slate-200 px-3 py-1.5 text-sm font-medium last:border-r-0",
                score === s ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50",
              )}
            >
              {s ? s[0]!.toUpperCase() + s.slice(1) : "All"}
              <span className={cx("text-xs tabular", score === s ? "text-slate-300" : "text-slate-400")}>
                {s ? countBy(s) : (all.data?.length ?? 0)}
              </span>
            </button>
          ))}
        </div>
        <Select value={status} onChange={(e) => setParam("status", e.target.value)} className="w-44" aria-label="Status">
          <option value="">Any status</option>
          {(Object.keys(STATUS_LABEL) as LeadStatus[]).map((s) => (
            <option key={s} value={s}>{STATUS_LABEL[s]}</option>
          ))}
        </Select>
        {isAdmin && (
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={unassigned}
              onChange={(e) => setParam("unassigned", e.target.checked ? "true" : "")}
              className="size-4 accent-brand-700"
            />
            Unassigned only
          </label>
        )}
        <form
          className="relative ml-auto w-full sm:w-64"
          onSubmit={(e) => {
            e.preventDefault();
            setParam("q", q.trim());
          }}
        >
          <IconSearch className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, email or phone" className="pl-9" />
        </form>
      </div>

      <Card>
        {loading && !data && <Loading />}
        {error && <p className="p-5 text-sm text-red-600">{error}</p>}
        {data && data.length === 0 && (
          <EmptyState icon={<IconInbox />} title="No leads here" body="Nothing matches these filters right now." />
        )}
        {data && data.length > 0 && (
          <Table>
            <thead>
              <tr>
                <Th>Lead</Th>
                <Th>Score</Th>
                <Th>Looking for</Th>
                <Th>Budget</Th>
                <Th>Timeline</Th>
                <Th>Status</Th>
                {isAdmin && <Th>Agent</Th>}
                <Th>Updated</Th>
              </tr>
            </thead>
            <tbody className={cx("divide-y divide-slate-100", loading && "opacity-60")}>
              {data.map((l) => (
                <tr
                  key={l.id}
                  onClick={() => navigate(`/console/leads/${l.id}`)}
                  className="cursor-pointer hover:bg-slate-50/80"
                >
                  <Td>
                    <p className="font-medium text-slate-900">{l.name ?? "Anonymous visitor"}</p>
                    <p className="text-xs text-slate-500">{l.phone ?? l.email ?? "No contact yet"}</p>
                  </Td>
                  <Td><ScoreBadge score={l.score} /></Td>
                  <Td>
                    <p className="text-slate-800">
                      {l.bedrooms && l.property_type !== "plot_land" ? `${l.bedrooms} BHK ` : ""}
                      {l.property_type ? PROPERTY_LABEL[l.property_type] : "—"}
                    </p>
                    <p className="max-w-[16rem] truncate text-xs text-slate-500">{l.preferred_localities.join(", ") || "Any locality"}</p>
                  </Td>
                  <Td className="whitespace-nowrap tabular">{budget(l.budget_min, l.budget_max)}</Td>
                  <Td className="whitespace-nowrap">
                    {timeline(l.timeline_months)}
                    {l.loan_preapproved && <span className="ml-1.5 text-xs text-brand-700">· Loan ✓</span>}
                  </Td>
                  <Td><LeadStatusBadge status={l.status} /></Td>
                  {isAdmin && (
                    <Td className="whitespace-nowrap">
                      {l.assigned_agent?.name ?? <span className="text-amber-700">Unassigned</span>}
                    </Td>
                  )}
                  <Td className="whitespace-nowrap text-slate-500">{relative(l.updated_at)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  );
}
