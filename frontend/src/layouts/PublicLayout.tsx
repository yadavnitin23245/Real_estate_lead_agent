import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import ChatWidget from "../components/ChatWidget";
import { Logo } from "../components/domain";
import { IconHeart, IconLogout, IconMenu, IconX } from "../components/icons";
import { Avatar, ButtonLink, cx } from "../components/ui";
import { homeFor, useAuth } from "../lib/auth";
import { ROLE_LABEL } from "../lib/format";

const navClass = ({ isActive }: { isActive: boolean }) =>
  cx(
    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
    isActive ? "text-brand-800 bg-brand-50" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
  );

export default function PublicLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const links = (
    <>
      <NavLink to="/listings" className={navClass} onClick={() => setOpen(false)}>
        Buy
      </NavLink>
      <NavLink to="/sell" className={navClass} onClick={() => setOpen(false)}>
        Sell with us
      </NavLink>
      {user?.role === "buyer" && (
        <NavLink to="/saved" className={navClass} onClick={() => setOpen(false)}>
          Saved
        </NavLink>
      )}
      {user && user.role !== "buyer" && (
        <NavLink to={homeFor(user.role)} className={navClass} onClick={() => setOpen(false)}>
          Console
        </NavLink>
      )}
    </>
  );

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-4 sm:px-6">
          <Link to="/" aria-label="HomeMatch home">
            <Logo />
          </Link>
          <nav className="hidden items-center gap-1 md:flex">{links}</nav>
          <div className="ml-auto hidden items-center gap-2 md:flex">
            {user ? (
              <>
                {user.role === "buyer" && (
                  <Link to="/saved" className="rounded-md p-2 text-slate-500 hover:bg-slate-100" aria-label="Saved homes">
                    <IconHeart className="size-5" />
                  </Link>
                )}
                <div className="flex items-center gap-2.5 rounded-md py-1 pr-1 pl-2">
                  <div className="text-right leading-tight">
                    <p className="text-sm font-medium text-slate-900">{user.name}</p>
                    <p className="text-[11px] text-slate-500">{ROLE_LABEL[user.role]}</p>
                  </div>
                  <Avatar name={user.name} />
                </div>
                <button
                  onClick={() => {
                    logout();
                    navigate("/");
                  }}
                  className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                  aria-label="Sign out"
                  title="Sign out"
                >
                  <IconLogout className="size-5" />
                </button>
              </>
            ) : (
              <>
                <ButtonLink to="/login" variant="ghost">
                  Sign in
                </ButtonLink>
                <ButtonLink to="/signup">Create account</ButtonLink>
              </>
            )}
          </div>
          <button className="ml-auto rounded-md p-2 text-slate-600 md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Menu">
            {open ? <IconX className="size-5" /> : <IconMenu className="size-5" />}
          </button>
        </div>
        {open && (
          <div className="border-t border-slate-200 bg-white px-4 py-3 md:hidden">
            <nav className="flex flex-col gap-1">{links}</nav>
            <div className="mt-3 flex gap-2 border-t border-slate-100 pt-3">
              {user ? (
                <button
                  className="text-sm font-medium text-slate-700"
                  onClick={() => {
                    logout();
                    setOpen(false);
                    navigate("/");
                  }}
                >
                  Sign out ({user.name})
                </button>
              ) : (
                <>
                  <ButtonLink to="/login" variant="secondary" className="flex-1">
                    Sign in
                  </ButtonLink>
                  <ButtonLink to="/signup" className="flex-1">
                    Create account
                  </ButtonLink>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-4">
          <div className="md:col-span-2">
            <Logo />
            <p className="mt-3 max-w-sm text-sm text-slate-500">
              Verified homes across Pune, matched to what you actually need — and a real agent when you're ready to
              visit.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold tracking-wide text-slate-900 uppercase">Explore</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              <li><Link to="/listings" className="hover:text-slate-900">All properties</Link></li>
              <li><Link to="/listings?property_type=villa" className="hover:text-slate-900">Villas</Link></li>
              <li><Link to="/listings?property_type=plot_land" className="hover:text-slate-900">Plots</Link></li>
              <li><Link to="/sell" className="hover:text-slate-900">List your property</Link></li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold tracking-wide text-slate-900 uppercase">Company</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              <li>GreenKey Realty, Baner, Pune</li>
              <li>MahaRERA: A0000-DEMO</li>
              <li><Link to="/login" className="hover:text-slate-900">Staff sign in</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-100 py-4 text-center text-xs text-slate-400">
          © {new Date().getFullYear()} GreenKey Realty (fictional brokerage, demo data)
        </div>
      </footer>
      <ChatWidget />
    </div>
  );
}
