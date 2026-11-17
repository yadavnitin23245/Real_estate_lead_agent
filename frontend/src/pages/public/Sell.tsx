import { IconCheckSquare, IconUpload, IconUsers } from "../../components/icons";
import { ButtonLink } from "../../components/ui";
import { useAuth } from "../../lib/auth";

const STEPS = [
  { icon: <IconUpload />, t: "Add your property", b: "Details, price and up to 8 photos. Takes about five minutes." },
  { icon: <IconCheckSquare />, t: "We verify it", b: "Our team reviews every listing, usually within 48 hours." },
  { icon: <IconUsers />, t: "Meet qualified buyers", b: "We match your home to buyers whose budget and needs fit." },
];

export default function Sell() {
  const { user } = useAuth();
  const cta =
    user?.role === "seller" || user?.role === "admin"
      ? { to: "/console/listings/new", label: "Create a listing" }
      : { to: "/signup?role=seller", label: "Create a seller account" };

  return (
    <>
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
          <p className="text-xs font-semibold tracking-wider text-brand-700 uppercase">For property owners</p>
          <h1 className="mt-3 max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
            Sell to buyers who are actually ready.
          </h1>
          <p className="mt-4 max-w-xl text-lg text-slate-500">
            GreenKey qualifies every buyer on budget, timeline and loan status before they reach you.
          </p>
          <div className="mt-8 flex gap-3">
            <ButtonLink to={cta.to} size="lg">{cta.label}</ButtonLink>
            {!user && <ButtonLink to="/login" variant="secondary" size="lg">I already have an account</ButtonLink>}
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <div key={s.t} className="rounded-lg border border-slate-200 bg-white p-6">
              <div className="flex items-center justify-between">
                <div className="grid size-10 place-items-center rounded-md bg-brand-50 text-xl text-brand-700">{s.icon}</div>
                <span className="font-mono text-xs text-slate-400">STEP {i + 1}</span>
              </div>
              <h3 className="mt-4 font-semibold">{s.t}</h3>
              <p className="mt-1 text-sm text-slate-500">{s.b}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
