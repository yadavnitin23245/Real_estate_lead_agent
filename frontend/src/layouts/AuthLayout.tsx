import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../components/domain";
import { IconShield, IconSparkle, IconUsers } from "../components/icons";

const POINTS = [
  { icon: <IconSparkle />, title: "Matched, not just listed", body: "Tell us what you need once — we shortlist homes that fit." },
  { icon: <IconShield />, title: "Every listing verified", body: "Our team reviews each property before it goes live." },
  { icon: <IconUsers />, title: "A real agent, when you're ready", body: "Book a site visit and a GreenKey agent takes it from there." },
];

export default function AuthLayout({ title, subtitle, children }: { title: string; subtitle: ReactNode; children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_minmax(0,560px)]">
      <aside className="relative hidden overflow-hidden bg-ink-950 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div
          aria-hidden
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        <div aria-hidden className="absolute -right-32 -bottom-32 size-[520px] rounded-full bg-brand-700/30 blur-3xl" />
        <Link to="/" className="relative">
          <Logo dark />
        </Link>
        <div className="relative max-w-md">
          <h2 className="text-3xl leading-tight font-semibold tracking-tight text-white">
            Pune's homes, matched to the way you live.
          </h2>
          <ul className="mt-10 space-y-6">
            {POINTS.map((p) => (
              <li key={p.title} className="flex gap-4">
                <span className="grid size-9 shrink-0 place-items-center rounded-md bg-white/10 text-lg text-brand-200">
                  {p.icon}
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{p.title}</p>
                  <p className="mt-0.5 text-sm text-slate-400">{p.body}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-slate-500">© GreenKey Realty · Baner, Pune</p>
      </aside>

      <main className="flex flex-col bg-white">
        <div className="p-6 lg:hidden">
          <Link to="/">
            <Logo />
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-center px-4 py-10 sm:px-12">
          <div className="w-full max-w-sm">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
            <p className="mt-1.5 text-sm text-slate-500">{subtitle}</p>
            <div className="mt-8">{children}</div>
          </div>
        </div>
      </main>
    </div>
  );
}
