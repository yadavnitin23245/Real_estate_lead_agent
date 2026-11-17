import { useState, type FormEvent } from "react";
import { IconPlus, IconSearch } from "../../components/icons";
import { Alert, Avatar, Badge, Button, Card, Field, Input, Loading, Modal, PageHeader, Select, Table, Td, Th } from "../../components/ui";
import { api, qs } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { date, ROLE_LABEL } from "../../lib/format";
import type { Role, User } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

const ROLE_TONE = { admin: "violet", sales_agent: "green", seller: "blue", buyer: "gray" } as const;

export default function Users() {
  const { user: me } = useAuth();
  const [role, setRole] = useState<"" | Role>("");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const { data, loading, error, setData } = useAsync(
    () => api<User[]>(`/api/admin/users${qs({ role, q: search })}`),
    [role, search],
  );
  const [actionError, setActionError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", role: "sales_agent" as Role });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  async function toggleActive(u: User) {
    setActionError(null);
    try {
      const updated = await api<User>(`/api/admin/users/${u.id}`, { method: "PATCH", body: { is_active: !u.is_active } });
      setData((rows) => rows?.map((r) => (r.id === u.id ? updated : r)) ?? null);
    } catch (e) {
      setActionError((e as Error).message);
    }
  }

  async function create(e: FormEvent) {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      const u = await api<User>("/api/admin/users", { method: "POST", body: { ...form, phone: form.phone || null } });
      setData((rows) => [u, ...(rows ?? [])]);
      setOpen(false);
      setForm({ name: "", email: "", phone: "", password: "", role: "sales_agent" });
    } catch (err) {
      setCreateError((err as Error).message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Users & staff"
        description="Buyers and sellers sign up themselves. Add sales agents and admins here."
        actions={
          <Button onClick={() => setOpen(true)}>
            <IconPlus className="size-4" /> Add staff member
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <Select value={role} onChange={(e) => setRole(e.target.value as "" | Role)} className="w-44" aria-label="Role">
          <option value="">All roles</option>
          {(Object.keys(ROLE_LABEL) as Role[]).map((r) => (
            <option key={r} value={r}>{ROLE_LABEL[r]}</option>
          ))}
        </Select>
        <form
          className="relative w-full sm:w-72"
          onSubmit={(e) => {
            e.preventDefault();
            setSearch(q.trim());
          }}
        >
          <IconSearch className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name or email" className="pl-9" />
        </form>
      </div>

      {actionError && <div className="mb-4"><Alert>{actionError}</Alert></div>}

      <Card>
        {loading && !data && <Loading />}
        {error && <p className="p-5 text-sm text-red-600">{error}</p>}
        {data && (
          <Table>
            <thead>
              <tr>
                <Th>User</Th>
                <Th>Role</Th>
                <Th>Phone</Th>
                <Th>Joined</Th>
                <Th>Status</Th>
                <Th className="text-right">&nbsp;</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50/70">
                  <Td>
                    <div className="flex items-center gap-3">
                      <Avatar name={u.name} />
                      <div className="min-w-0">
                        <p className="font-medium text-slate-900">{u.name}{u.id === me?.id && <span className="ml-1.5 text-xs text-slate-400">(you)</span>}</p>
                        <p className="text-xs text-slate-500">{u.email}</p>
                      </div>
                    </div>
                  </Td>
                  <Td><Badge tone={ROLE_TONE[u.role]}>{ROLE_LABEL[u.role]}</Badge></Td>
                  <Td className="whitespace-nowrap text-slate-600">{u.phone ?? "—"}</Td>
                  <Td className="whitespace-nowrap text-slate-500">{date(u.created_at)}</Td>
                  <Td>{u.is_active ? <Badge tone="green" dot>Active</Badge> : <Badge tone="gray" dot>Deactivated</Badge>}</Td>
                  <Td className="text-right">
                    {u.id !== me?.id && (
                      <button onClick={() => toggleActive(u)} className="text-sm font-medium text-slate-600 hover:text-slate-900">
                        {u.is_active ? "Deactivate" : "Reactivate"}
                      </button>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
        {data && data.length === 0 && <p className="px-5 py-8 text-center text-sm text-slate-500">No users found.</p>}
      </Card>

      <Modal
        open={open}
        title="Add staff member"
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" form="staff-form" loading={creating}>Create account</Button>
          </>
        }
      >
        <form id="staff-form" onSubmit={create} className="space-y-4">
          {createError && <Alert>{createError}</Alert>}
          <Field label="Full name">
            <Input required minLength={2} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Work email">
            <Input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Phone">
              <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </Field>
            <Field label="Role">
              <Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
                <option value="sales_agent">Sales agent</option>
                <option value="admin">Admin</option>
              </Select>
            </Field>
          </div>
          <Field label="Temporary password" hint="At least 8 characters. Share it securely.">
            <Input type="text" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </Field>
        </form>
      </Modal>
    </>
  );
}
