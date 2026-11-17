import { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardHeader, Loading, PageHeader } from "../../components/ui";
import { api } from "../../lib/api";
import { ROLE_LABEL, SCORE_LABEL, STATUS_LABEL } from "../../lib/format";
import type { AdminStats, LeadScore, LeadStatus, Role } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

function Kpi({ label, value, sub, to }: { label: string; value: string | number; sub?: string; to?: string }) {
  const body = (
    <Card className="h-full px-5 py-4 transition hover:ring-slate-300">
      <p className="text-[13px] text-slate-500">{label}</p>
      <p className="mt-1.5 text-[28px] leading-none font-semibold tracking-tight tabular">{value}</p>
      {sub && <p className="mt-2 text-xs text-slate-500">{sub}</p>}
    </Card>
  );
  return to ? <Link to={to}>{body}</Link> : body;
}

/** Single-series daily bar chart with per-bar hover tooltip. */
function LeadsChart({ data }: { data: AdminStats["leads_per_day"] }) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(1, ...data.map((d) => d.leads));
  const ticks = max <= 4 ? Array.from({ length: max + 1 }, (_, i) => i) : [0, Math.round(max / 2), max];
  const fmt = (iso: string) => new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" });

  return (
    <div className="relative px-5 pt-4 pb-3">
      <div className="relative ml-6 h-48">
        {ticks.map((t) => (
          <div key={t} className="absolute inset-x-0 border-t border-slate-100" style={{ bottom: `${(t / max) * 100}%` }}>
            <span className="absolute -top-2 -left-6 w-4 text-right text-[10.5px] text-slate-400 tabular">{t}</span>
          </div>
        ))}
        <div className="absolute inset-0 flex items-end gap-[2px]">
          {data.map((d, i) => (
            <div
              key={d.date}
              className="relative flex h-full flex-1 items-end justify-center"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            >
              <div
                className="w-full max-w-7 rounded-t-[4px] bg-brand-600 transition-colors"
                style={{ height: `${(d.leads / max) * 100}%`, opacity: hover === null || hover === i ? 1 : 0.45 }}
              />
              {hover === i && (
                <div className="pointer-events-none absolute bottom-full z-10 mb-2 rounded-md bg-slate-900 px-2.5 py-1.5 text-xs whitespace-nowrap text-white shadow-lg"
                  style={{ bottom: `${(d.leads / max) * 100}%` }}>
                  <span className="text-slate-300">{fmt(d.date)}</span> · <span className="font-semibold tabular">{d.leads}</span> lead{d.leads === 1 ? "" : "s"}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-2 ml-6 flex justify-between text-[10.5px] text-slate-400">
        <span>{fmt(data[0]!.date)}</span>
        <span>{fmt(data[data.length - 1]!.date)}</span>
      </div>
    </div>
  );
}

function Breakdown({ rows, total }: { rows: [string, number][]; total: number }) {
  return (
    <ul className="space-y-3 px-5 py-4">
      {rows.map(([label, n]) => (
        <li key={label}>
          <div className="flex justify-between text-sm">
            <span className="text-slate-700">{label}</span>
            <span className="font-medium tabular">{n}</span>
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-brand-600" style={{ width: `${total ? (n / total) * 100 : 0}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function Overview() {
  const { data: s, loading, error } = useAsync(() => api<AdminStats>("/api/admin/stats"), []);
  if (loading) return <Loading />;
  if (error || !s) return <p className="text-sm text-red-600">{error}</p>;

  const pending = s.listings_by_approval.pending ?? 0;
  const hot = s.leads_by_score.hot ?? 0;
  const last14 = s.leads_per_day.reduce((a, d) => a + d.leads, 0);
  const maxLoad = Math.max(1, ...s.agent_load.map((a) => a.leads));

  return (
    <>
      <PageHeader title="Dashboard" description="Catalogue, lead pipeline and team workload at a glance." />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        <Kpi label="Live listings" value={s.listings_live} sub={`${s.listings_sold} sold`} />
        <Kpi label="Awaiting approval" value={pending} sub={pending ? "Review now →" : "Queue is clear"} to="/console/approvals" />
        <Kpi label="Total leads" value={s.leads_total} sub={`${last14} in last 14 days`} to="/console/leads" />
        <Kpi label="Hot leads" value={hot} sub="Budget + ≤3 mo + loan" to="/console/leads?score=hot" />
        <Kpi label="Unassigned leads" value={s.leads_unassigned} to="/console/leads?unassigned=true" />
        <Kpi label="Open site visits" value={s.visits_open} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="New leads per day" sub="Last 14 days" />
          <LeadsChart data={s.leads_per_day} />
        </Card>
        <Card>
          <CardHeader title="Lead quality" sub="Scored by rules, not the LLM" />
          <Breakdown
            total={s.leads_total}
            rows={(["hot", "warm", "cold"] as LeadScore[]).map((k) => [SCORE_LABEL[k], s.leads_by_score[k] ?? 0])}
          />
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader title="Pipeline" sub="Leads by status" />
          <Breakdown
            total={s.leads_total}
            rows={(Object.keys(STATUS_LABEL) as LeadStatus[]).map((k) => [STATUS_LABEL[k], s.leads_by_status[k] ?? 0])}
          />
        </Card>
        <Card>
          <CardHeader title="Agent workload" sub="Assigned leads" />
          <ul className="space-y-3 px-5 py-4">
            {s.agent_load.map((a) => (
              <li key={a.id}>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-700">{a.name}</span>
                  <span className="font-medium tabular">{a.leads}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-brand-600" style={{ width: `${(a.leads / maxLoad) * 100}%` }} />
                </div>
              </li>
            ))}
            {s.agent_load.length === 0 && <li className="text-sm text-slate-500">No sales agents yet.</li>}
          </ul>
        </Card>
        <Card>
          <CardHeader title="Platform" />
          <dl className="divide-y divide-slate-100 text-sm">
            {(Object.keys(ROLE_LABEL) as Role[]).map((r) => (
              <div key={r} className="flex justify-between px-5 py-2.5">
                <dt className="text-slate-500">{ROLE_LABEL[r]}s</dt>
                <dd className="font-medium tabular">{s.users_by_role[r] ?? 0}</dd>
              </div>
            ))}
            <div className="flex justify-between px-5 py-2.5">
              <dt className="text-slate-500">LLM spend</dt>
              <dd className="font-medium tabular">${s.llm_cost_usd.toFixed(2)}</dd>
            </div>
            <div className="flex justify-between px-5 py-2.5">
              <dt className="text-slate-500">LLM tokens</dt>
              <dd className="font-medium tabular">{s.llm_tokens.toLocaleString("en-IN")}</dd>
            </div>
          </dl>
        </Card>
      </div>
    </>
  );
}
