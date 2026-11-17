import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Logo } from "../components/domain";
import {
  IconBuilding,
  IconCheckSquare,
  IconGrid,
  IconInbox,
  IconLogout,
  IconMenu,
  IconPlus,
  IconSearch,
  IconUsers,
} from "../components/icons";
import { Avatar, cx } from "../components/ui";
import { useAuth } from "../lib/auth";
import { ROLE_LABEL } from "../lib/format";
import type { Role } from "../lib/types";

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  end?: boolean;
}

const NAV: Record<Exclude<Role, "buyer">, { section: string; items: NavItem[] }[]> = {
  admin: [
    {
      section: "Overview",
      items: [{ to: "/console", label: "Dashboard", icon: <IconGrid />, end: true }],
    },
    {
      section: "Operations",
      items: [
        { to: "/console/approvals", label: "Listing approvals", icon: <IconCheckSquare /> },
        { to: "/console/leads", label: "All leads", icon: <IconInbox /> },
        { to: "/console/users", label: "Users & staff", icon: <IconUsers /> },
      ],
    },
  ],
  sales_agent: [
    {
      section: "Sales",
      items: [{ to: "/console/leads", label: "My leads", icon: <IconInbox /> }],
    },
  ],
  seller: [
    {
      section: "Selling",
      items: [
        { to: "/console/listings", label: "My listings", icon: <IconBuilding />, end: true },
        { to: "/console/listings/new", label: "New listing", icon: <IconPlus /> },
      ],
    },
  ],
};

export default function ConsoleLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  useEffect(() => setMobileOpen(false), [location.pathname]);

  if (!user || user.role === "buyer") return null;
  const sections = NAV[user.role];

  const sidebar = (
    <div className="flex h-full flex-col bg-ink-950 text-slate-300">
      <div className="flex h-16 items-center px-5">
        <Link to="/console" className="contents">
          <Logo dark />
        </Link>
      </div>
      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
        {sections.map((s) => (
          <div key={s.section}>
            <p className="px-2 pb-2 text-[10.5px] font-semibold tracking-wider text-slate-500 uppercase">{s.section}</p>
            <ul className="space-y-0.5">
              {s.items.map((i) => (
                <li key={i.to}>
                  <NavLink
                    to={i.to}
                    end={i.end}
                    className={({ isActive }) =>
                      cx(
                        "flex items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium transition-colors [&_svg]:size-[18px]",
                        isActive ? "bg-ink-800 text-white" : "text-slate-400 hover:bg-ink-900 hover:text-slate-100",
                      )
                    }
                  >
                    {i.icon}
                    {i.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
        <div>
          <p className="px-2 pb-2 text-[10.5px] font-semibold tracking-wider text-slate-500 uppercase">Public site</p>
          <Link
            to="/listings"
            className="flex items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium text-slate-400 hover:bg-ink-900 hover:text-slate-100 [&_svg]:size-[18px]"
          >
            <IconSearch /> Browse catalogue
          </Link>
        </div>
      </nav>
      <div className="border-t border-white/10 p-3">
        <div className="flex items-center gap-3 rounded-md px-2 py-2">
          <Avatar name={user.name} className="bg-brand-700 text-white" />
          <div className="min-w-0 flex-1 leading-tight">
            <p className="truncate text-sm font-medium text-white">{user.name}</p>
            <p className="truncate text-xs text-slate-500">{ROLE_LABEL[user.role]}</p>
          </div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="rounded p-1.5 text-slate-500 hover:bg-ink-800 hover:text-slate-200"
            title="Sign out"
            aria-label="Sign out"
          >
            <IconLogout className="size-[18px]" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 lg:block">{sidebar}</aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-slate-950/50" onClick={() => setMobileOpen(false)} />
          <aside className="relative h-full w-64">{sidebar}</aside>
        </div>
      )}
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:hidden">
          <button onClick={() => setMobileOpen(true)} className="rounded p-1.5 text-slate-600" aria-label="Open menu">
            <IconMenu className="size-5" />
          </button>
          <Logo compact />
          <span className="text-sm font-semibold">Console</span>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
