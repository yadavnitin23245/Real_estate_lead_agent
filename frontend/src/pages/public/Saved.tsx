import { ListingCard } from "../../components/domain";
import { IconHeart } from "../../components/icons";
import { SaveButton, useSavedIds } from "../../components/SaveButton";
import { ButtonLink, EmptyState, Loading } from "../../components/ui";
import { api } from "../../lib/api";
import type { ListingCard as Listing } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

export default function Saved() {
  const { data, loading, error } = useAsync(() => api<Listing[]>("/api/me/shortlist"), []);
  const { ids, toggle } = useSavedIds();

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <h1 className="text-2xl font-semibold tracking-tight">Saved homes</h1>
      <p className="mt-1 text-sm text-slate-500">Your shortlist. Our agents use it to plan site visits with you.</p>
      {loading && <Loading />}
      {error && <p className="mt-6 text-sm text-red-600">{error}</p>}
      {data && data.length === 0 && (
        <EmptyState
          icon={<IconHeart />}
          title="Nothing saved yet"
          body="Tap the heart on any property to keep it here."
          action={<ButtonLink to="/listings">Browse properties</ButtonLink>}
        />
      )}
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {data?.map((l) => (
          <ListingCard key={l.id} listing={l} action={<SaveButton saved={ids.has(l.id)} onToggle={() => toggle(l.id)} />} />
        ))}
      </div>
    </div>
  );
}
