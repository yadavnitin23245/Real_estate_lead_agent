import { useState } from "react";
import { Link } from "react-router-dom";
import { Amenities, ApprovalBadge, Thumb } from "../../components/domain";
import { IconCheckSquare } from "../../components/icons";
import { Alert, Button, Card, EmptyState, Field, Loading, Modal, PageHeader, Textarea, cx } from "../../components/ui";
import { api } from "../../lib/api";
import { area, inr, relative, specLine } from "../../lib/format";
import type { ApprovalStatus, ListingDetail } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

const TABS: { value: ApprovalStatus; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "rejected", label: "Rejected" },
  { value: "approved", label: "Approved" },
];

export default function Approvals() {
  const [tab, setTab] = useState<ApprovalStatus>("pending");
  const { data, loading, error, setData } = useAsync(
    () => api<ListingDetail[]>(`/api/admin/listings?approval=${tab}`),
    [tab],
  );
  const [busy, setBusy] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<ListingDetail | null>(null);
  const [reason, setReason] = useState("");

  async function act(l: ListingDetail, action: "approve" | "reject", body?: unknown) {
    setBusy(l.id);
    setActionError(null);
    try {
      await api(`/api/admin/listings/${l.id}/${action}`, { method: "POST", body: body ?? {} });
      setData((rows) => rows?.filter((r) => r.id !== l.id) ?? null);
      setRejecting(null);
      setReason("");
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader
        title="Listing approvals"
        description="Check every seller listing before buyers can see it. Approving also indexes it for AI matching."
      />

      <div className="mb-5 flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={cx(
              "-mb-px border-b-2 px-3 py-2 text-sm font-medium",
              tab === t.value ? "border-brand-700 text-brand-800" : "border-transparent text-slate-500 hover:text-slate-800",
            )}
          >
            {t.label}
            {tab === t.value && data && <span className="ml-1.5 text-xs text-slate-400 tabular">{data.length}</span>}
          </button>
        ))}
      </div>

      {actionError && <div className="mb-4"><Alert>{actionError}</Alert></div>}
      {loading && <Loading />}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {data && data.length === 0 && (
        <Card>
          <EmptyState icon={<IconCheckSquare />} title="Nothing here" body={tab === "pending" ? "The review queue is clear." : "No listings in this state."} />
        </Card>
      )}

      <div className="space-y-4">
        {data?.map((l) => (
          <Card key={l.id} className="overflow-hidden">
            <div className="grid md:grid-cols-[260px_1fr]">
              <div className="relative bg-slate-100">
                <Thumb src={l.thumb_url} alt="" className="aspect-[3/2] size-full md:aspect-auto" />
                {l.images.length > 1 && (
                  <span className="absolute right-2 bottom-2 rounded bg-slate-900/75 px-1.5 py-0.5 text-[11px] text-white">
                    {l.images.length} photos
                  </span>
                )}
              </div>
              <div className="flex flex-col p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-500">{l.ref_code}</span>
                      <ApprovalBadge status={l.approval_status} sold={l.status === "sold"} />
                    </div>
                    <h3 className="mt-1 text-base font-semibold text-slate-900">{l.title}</h3>
                    <p className="text-sm text-slate-500">
                      {specLine(l)} · {l.locality}, {l.city}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-semibold tabular">{inr(l.price_inr)}</p>
                    {l.area_value && l.area_unit === "sqft" && (
                      <p className="text-xs text-slate-500">{inr(Math.round(l.price_inr / l.area_value))}/sq ft</p>
                    )}
                  </div>
                </div>
                <p className="mt-3 line-clamp-3 text-sm text-slate-600">{l.description || <em>No description.</em>}</p>
                <div className="mt-3"><Amenities l={l} /></div>
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                  <p className="text-xs text-slate-500">
                    Seller <span className="font-medium text-slate-700">{l.owner_name ?? "—"}</span> · Area {area(l.area_value, l.area_unit)} ·
                    updated {relative(l.created_at)}
                    {l.approval_status === "approved" && (
                      <> · <Link to={`/listings/${l.id}`} target="_blank" className="text-brand-700 hover:underline">View live</Link></>
                    )}
                  </p>
                  <div className="flex gap-2">
                    {l.approval_status !== "rejected" && (
                      <Button variant="secondary" size="sm" disabled={busy === l.id} onClick={() => setRejecting(l)}>
                        Reject
                      </Button>
                    )}
                    {l.approval_status !== "approved" && (
                      <Button size="sm" loading={busy === l.id} onClick={() => act(l, "approve")}>
                        Approve & publish
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Modal
        open={!!rejecting}
        title={`Reject ${rejecting?.ref_code ?? ""}`}
        onClose={() => setRejecting(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setRejecting(null)}>Cancel</Button>
            <Button variant="danger" loading={busy === rejecting?.id} onClick={() => rejecting && act(rejecting, "reject", { reason: reason || null })}>
              Reject listing
            </Button>
          </>
        }
      >
        <Field label="Reason (internal)" hint="Logged in the audit trail. The seller can edit and resubmit.">
          <Textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Photos missing, price looks wrong" />
        </Field>
      </Modal>
    </>
  );
}
