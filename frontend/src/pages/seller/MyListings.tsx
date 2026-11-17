import { Link } from "react-router-dom";
import { ApprovalBadge, Thumb } from "../../components/domain";
import { IconBuilding, IconPlus } from "../../components/icons";
import { ButtonLink, Card, EmptyState, Loading, PageHeader, Table, Td, Th } from "../../components/ui";
import { api } from "../../lib/api";
import { date, inr, specLine } from "../../lib/format";
import type { ListingCard } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

export default function MyListings() {
  const { data, loading, error } = useAsync(() => api<ListingCard[]>("/api/seller/listings"), []);
  const count = (f: (l: ListingCard) => boolean) => data?.filter(f).length ?? 0;

  return (
    <>
      <PageHeader
        title="My listings"
        description="Everything you've listed with GreenKey. New and edited listings are reviewed before going live."
        actions={
          <ButtonLink to="/console/listings/new">
            <IconPlus className="size-4" /> New listing
          </ButtonLink>
        }
      />

      {data && data.length > 0 && (
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ["Total", data.length],
            ["Live", count((l) => l.approval_status === "approved" && l.status === "available")],
            ["In review", count((l) => l.approval_status === "pending")],
            ["Sold", count((l) => l.status === "sold")],
          ].map(([k, v]) => (
            <Card key={k} className="px-4 py-3">
              <p className="text-xs text-slate-500">{k}</p>
              <p className="mt-1 text-2xl font-semibold tabular">{v}</p>
            </Card>
          ))}
        </div>
      )}

      <Card>
        {loading && <Loading />}
        {error && <p className="p-5 text-sm text-red-600">{error}</p>}
        {data && data.length === 0 && (
          <EmptyState
            icon={<IconBuilding />}
            title="No listings yet"
            body="Add your first property. Our team will review it within 48 hours."
            action={<ButtonLink to="/console/listings/new">Create listing</ButtonLink>}
          />
        )}
        {data && data.length > 0 && (
          <Table>
            <thead>
              <tr>
                <Th>Property</Th>
                <Th>Price</Th>
                <Th>Status</Th>
                <Th>Created</Th>
                <Th className="text-right">&nbsp;</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50/70">
                  <Td>
                    <div className="flex items-center gap-3">
                      <Thumb src={l.thumb_url} alt="" className="h-10 w-14 shrink-0 rounded" />
                      <div className="min-w-0">
                        <Link to={`/console/listings/${l.id}`} className="block truncate font-medium text-slate-900 hover:text-brand-700">
                          {l.title}
                        </Link>
                        <p className="truncate text-xs text-slate-500">
                          <span className="font-mono">{l.ref_code}</span> · {specLine(l)} · {l.locality}
                        </p>
                      </div>
                    </div>
                  </Td>
                  <Td className="font-medium tabular">{inr(l.price_inr)}</Td>
                  <Td><ApprovalBadge status={l.approval_status} sold={l.status === "sold"} /></Td>
                  <Td className="text-slate-500">{date(l.created_at)}</Td>
                  <Td className="text-right">
                    <Link to={`/console/listings/${l.id}`} className="text-sm font-medium text-brand-700 hover:text-brand-800">
                      Edit
                    </Link>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  );
}
