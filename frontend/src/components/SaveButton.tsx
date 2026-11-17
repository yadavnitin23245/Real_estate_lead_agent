import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { ListingCard } from "../lib/types";
import { IconHeart } from "./icons";
import { cx } from "./ui";

/** IDs of the signed-in buyer's shortlisted listings (empty for everyone else). */
export function useSavedIds() {
  const { user } = useAuth();
  const [ids, setIds] = useState<Set<number>>(new Set());
  useEffect(() => {
    if (user?.role !== "buyer") {
      setIds(new Set());
      return;
    }
    api<ListingCard[]>("/api/me/shortlist")
      .then((rows) => setIds(new Set(rows.map((r) => r.id))))
      .catch(() => undefined);
  }, [user]);

  const toggle = async (id: number) => {
    const on = !ids.has(id);
    setIds((s) => {
      const n = new Set(s);
      if (on) n.add(id);
      else n.delete(id);
      return n;
    });
    try {
      await api(`/api/me/shortlist/${id}`, { method: on ? "PUT" : "DELETE" });
    } catch {
      setIds((s) => {
        const n = new Set(s);
        if (on) n.delete(id);
        else n.add(id);
        return n;
      });
    }
  };
  return { ids, toggle };
}

export function SaveButton({
  saved,
  onToggle,
  variant = "overlay",
}: {
  saved: boolean;
  onToggle: () => void;
  variant?: "overlay" | "inline";
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  if (user && user.role !== "buyer") return null;

  const click = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!user) navigate(`/login?next=${encodeURIComponent(location.pathname + location.search)}`);
    else onToggle();
  };

  if (variant === "inline") {
    return (
      <button
        onClick={click}
        className={cx(
          "inline-flex h-9 items-center gap-2 rounded-md px-3.5 text-sm font-medium ring-1 ring-inset transition",
          saved ? "bg-red-50 text-red-700 ring-red-200" : "bg-white text-slate-700 ring-slate-300 hover:bg-slate-50",
        )}
      >
        <IconHeart className={cx("size-4", saved && "fill-current")} />
        {saved ? "Saved" : "Save"}
      </button>
    );
  }
  return (
    <button
      onClick={click}
      aria-label={saved ? "Remove from saved" : "Save"}
      aria-pressed={saved}
      className={cx(
        "grid size-8 place-items-center rounded-full bg-white/95 shadow-sm transition hover:scale-105",
        saved ? "text-red-600" : "text-slate-600",
      )}
    >
      <IconHeart className={cx("size-4", saved && "fill-current")} />
    </button>
  );
}
