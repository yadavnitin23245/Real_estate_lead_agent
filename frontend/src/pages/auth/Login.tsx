import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { Alert, Button, Field, Input } from "../../components/ui";
import AuthLayout from "../../layouts/AuthLayout";
import { homeFor, useAuth } from "../../lib/auth";

const DEMO = [
  { label: "Admin", email: "admin@greenkey.example" },
  { label: "Sales agent", email: "demo.agent@greenkey.example" },
  { label: "Seller", email: "demo.seller@greenkey.example" },
  { label: "Buyer", email: "demo.buyer@greenkey.example" },
];

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={next || homeFor(user.role)} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const u = await login(email, password);
      navigate(next && next.startsWith("/") ? next : homeFor(u.role), { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Sign in"
      subtitle={
        <>
          New to HomeMatch?{" "}
          <Link to="/signup" className="font-medium text-brand-700 hover:text-brand-800">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-5">
        {error && <Alert>{error}</Alert>}
        <Field label="Email address" htmlFor="email">
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-10"
          />
        </Field>
        <Field label="Password" htmlFor="password">
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-10"
          />
        </Field>
        <Button type="submit" size="lg" loading={busy} className="w-full">
          Sign in
        </Button>
      </form>

      <div className="mt-10 rounded-lg border border-dashed border-slate-300 p-4">
        <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Demo accounts</p>
        <p className="mt-1 text-xs text-slate-500">
          Passwords are <code className="font-mono">ADMIN_PASSWORD</code> /{" "}
          <code className="font-mono">DEMO_PASSWORD</code> from <code className="font-mono">backend/.env</code>.
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {DEMO.map((d) => (
            <button
              key={d.email}
              type="button"
              onClick={() => setEmail(d.email)}
              className="rounded-md bg-slate-50 px-2.5 py-2 text-left ring-1 ring-slate-200 hover:bg-slate-100"
            >
              <span className="block text-xs font-medium text-slate-800">{d.label}</span>
              <span className="block truncate text-[11px] text-slate-500">{d.email}</span>
            </button>
          ))}
        </div>
      </div>
    </AuthLayout>
  );
}
