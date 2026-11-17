import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { ButtonLink, EmptyState, Loading } from "../components/ui";
import { IconShield } from "../components/icons";
import { homeFor, useAuth } from "../lib/auth";
import type { Role } from "../lib/types";

export default function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready) return <Loading />;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  if (!roles.includes(user.role)) {
    return (
      <div className="py-10">
        <EmptyState
          icon={<IconShield />}
          title="You don't have access to this page"
          body="This area is for a different account type."
          action={<ButtonLink to={homeFor(user.role)}>Go to my workspace</ButtonLink>}
        />
      </div>
    );
  }
  return <>{children}</>;
}
