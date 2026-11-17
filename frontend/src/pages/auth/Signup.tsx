import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { IconBuilding, IconHome } from "../../components/icons";
import { Alert, Button, Field, Input, cx } from "../../components/ui";
import AuthLayout from "../../layouts/AuthLayout";
import { homeFor, useAuth } from "../../lib/auth";

type AccountType = "buyer" | "seller";

const TYPES: { value: AccountType; title: string; body: string; icon: React.ReactNode }[] = [
  { value: "buyer", title: "I want to buy", body: "Browse, shortlist and book visits", icon: <IconHome /> },
  { value: "seller", title: "I want to sell", body: "List a property for review", icon: <IconBuilding /> },
];

export default function Signup() {
  const { user, signup } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [role, setRole] = useState<AccountType>(params.get("role") === "seller" ? "seller" : "buyer");
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homeFor(user.role)} replace />;

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const u = await signup({ ...form, phone: form.phone || undefined, role });
      navigate(homeFor(u.role), { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle={
        <>
          Already have one?{" "}
          <Link to="/login" className="font-medium text-brand-700 hover:text-brand-800">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-5">
        {error && <Alert>{error}</Alert>}
        <fieldset>
          <legend className="mb-1.5 text-[13px] font-medium text-slate-700">Account type</legend>
          <div className="grid grid-cols-2 gap-2">
            {TYPES.map((t) => (
              <label
                key={t.value}
                className={cx(
                  "relative cursor-pointer rounded-lg p-3 ring-1 transition",
                  role === t.value ? "bg-brand-50/60 ring-2 ring-brand-600" : "ring-slate-300 hover:ring-slate-400",
                )}
              >
                <input
                  type="radio"
                  name="role"
                  value={t.value}
                  checked={role === t.value}
                  onChange={() => setRole(t.value)}
                  className="sr-only"
                />
                <span className={cx("text-lg", role === t.value ? "text-brand-700" : "text-slate-400")}>{t.icon}</span>
                <span className="mt-1 block text-sm font-medium text-slate-900">{t.title}</span>
                <span className="block text-xs text-slate-500">{t.body}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <Field label="Full name" htmlFor="name">
          <Input id="name" autoComplete="name" required minLength={2} value={form.name} onChange={set("name")} className="h-10" />
        </Field>
        <Field label="Email address" htmlFor="email">
          <Input id="email" type="email" autoComplete="email" required value={form.email} onChange={set("email")} className="h-10" />
        </Field>
        <Field label="Mobile number" htmlFor="phone" hint="Optional — so an agent can call you back.">
          <Input
            id="phone"
            type="tel"
            autoComplete="tel"
            placeholder="+91 98xxx xxxxx"
            value={form.phone}
            onChange={set("phone")}
            className="h-10"
          />
        </Field>
        <Field label="Password" htmlFor="password" hint="At least 8 characters.">
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={form.password}
            onChange={set("password")}
            className="h-10"
          />
        </Field>
        <Button type="submit" size="lg" loading={busy} className="w-full">
          Create account
        </Button>
        <p className="text-center text-xs text-slate-500">
          Sales agents and admins are added by an administrator.
        </p>
      </form>
    </AuthLayout>
  );
}
