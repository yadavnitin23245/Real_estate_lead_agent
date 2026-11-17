import { Navigate, Route, Routes } from "react-router-dom";
import { ButtonLink, EmptyState, Loading } from "./components/ui";
import ConsoleLayout from "./layouts/ConsoleLayout";
import PublicLayout from "./layouts/PublicLayout";
import RequireRole from "./layouts/RequireRole";
import { homeFor, useAuth } from "./lib/auth";
import Approvals from "./pages/admin/Approvals";
import Overview from "./pages/admin/Overview";
import Users from "./pages/admin/Users";
import Login from "./pages/auth/Login";
import Signup from "./pages/auth/Signup";
import LeadDetail from "./pages/leads/LeadDetail";
import LeadInbox from "./pages/leads/LeadInbox";
import Home from "./pages/public/Home";
import ListingDetail from "./pages/public/ListingDetail";
import Listings from "./pages/public/Listings";
import Saved from "./pages/public/Saved";
import Sell from "./pages/public/Sell";
import ListingForm from "./pages/seller/ListingForm";
import MyListings from "./pages/seller/MyListings";

function ConsoleHome() {
  const { user } = useAuth();
  if (user?.role === "admin") return <Overview />;
  return <Navigate to={user ? homeFor(user.role) : "/login"} replace />;
}

function NotFound() {
  return (
    <div className="py-24">
      <EmptyState
        title="Page not found"
        body="The page you're looking for doesn't exist or has moved."
        action={<ButtonLink to="/">Go home</ButtonLink>}
      />
    </div>
  );
}

export default function App() {
  const { ready } = useAuth();
  if (!ready) return <Loading />;

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route element={<PublicLayout />}>
        <Route index element={<Home />} />
        <Route path="listings" element={<Listings />} />
        <Route path="listings/:id" element={<ListingDetail />} />
        <Route path="sell" element={<Sell />} />
        <Route
          path="saved"
          element={
            <RequireRole roles={["buyer"]}>
              <Saved />
            </RequireRole>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>

      <Route
        path="console"
        element={
          <RequireRole roles={["seller", "sales_agent", "admin"]}>
            <ConsoleLayout />
          </RequireRole>
        }
      >
        <Route index element={<ConsoleHome />} />
        <Route path="listings" element={<RequireRole roles={["seller", "admin"]}><MyListings /></RequireRole>} />
        <Route path="listings/new" element={<RequireRole roles={["seller", "admin"]}><ListingForm /></RequireRole>} />
        <Route path="listings/:id" element={<RequireRole roles={["seller", "admin"]}><ListingForm key="edit" /></RequireRole>} />
        <Route path="leads" element={<RequireRole roles={["sales_agent", "admin"]}><LeadInbox /></RequireRole>} />
        <Route path="leads/:id" element={<RequireRole roles={["sales_agent", "admin"]}><LeadDetail /></RequireRole>} />
        <Route path="approvals" element={<RequireRole roles={["admin"]}><Approvals /></RequireRole>} />
        <Route path="users" element={<RequireRole roles={["admin"]}><Users /></RequireRole>} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
