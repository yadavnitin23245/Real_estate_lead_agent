import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { ApprovalBadge } from "../../components/domain";
import { IconTrash, IconUpload } from "../../components/icons";
import { Alert, Button, Card, CardHeader, Checkbox, Field, Input, Loading, PageHeader, Select, Textarea } from "../../components/ui";
import { api } from "../../lib/api";
import { inr, PROPERTY_LABEL } from "../../lib/format";
import type { Facets, ListingDetail, ListingInput, PropertyType } from "../../lib/types";
import { useAsync } from "../../lib/useAsync";

const EMPTY: ListingInput = {
  title: "",
  city: "Pune",
  locality: "",
  property_type: "apartment",
  bedrooms: 2,
  bathrooms: 2,
  area_value: null,
  area_unit: "sqft",
  price_inr: 0,
  furnishing: "semi_furnished",
  has_parking: true,
  near_school: false,
  near_metro: false,
  description: "",
};

export default function ListingForm() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const facets = useAsync(() => api<Facets>("/api/listings/facets"), []);
  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [form, setForm] = useState<ListingInput>(EMPTY);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();
  const [notice, setNotice] = useState<string | null>(
    (location.state as { created?: boolean } | null)?.created
      ? "Listing submitted for review. Add photos below — listings with photos are approved faster."
      : null,
  );
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isNew) return;
    api<ListingDetail>(`/api/seller/listings/${id}`)
      .then((l) => {
        setListing(l);
        setForm({
          title: l.title,
          city: l.city,
          locality: l.locality,
          property_type: l.property_type,
          bedrooms: l.bedrooms,
          bathrooms: l.bathrooms,
          area_value: l.area_value,
          area_unit: l.area_unit,
          price_inr: l.price_inr,
          furnishing: l.furnishing,
          has_parking: l.has_parking,
          near_school: l.near_school,
          near_metro: l.near_metro,
          description: l.description,
        });
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const set = <K extends keyof ListingInput>(k: K, v: ListingInput[K]) => setForm((f) => ({ ...f, [k]: v }));
  const num = (v: string) => (v === "" ? null : Number(v));
  const isPlot = form.property_type === "plot_land";
  const isCommercial = form.property_type === "commercial";

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const body = { ...form, title: form.title.trim(), locality: form.locality.trim() };
      if (isNew) {
        const created = await api<ListingDetail>("/api/seller/listings", { method: "POST", body });
        navigate(`/console/listings/${created.id}`, { replace: true, state: { created: true } });
        return;
      }
      const updated = await api<ListingDetail>(`/api/seller/listings/${id}`, { method: "PUT", body });
      setListing(updated);
      setNotice("Changes saved. The listing is back in review and will go live once approved.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function upload(files: FileList | null) {
    if (!files || !listing) return;
    setUploading(true);
    setError(null);
    try {
      let latest = listing;
      for (const file of Array.from(files)) {
        const fd = new FormData();
        fd.append("file", file);
        latest = await api<ListingDetail>(`/api/seller/listings/${listing.id}/images`, { method: "POST", form: fd });
      }
      setListing(latest);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function removeImage(imageId: number) {
    if (!listing) return;
    try {
      setListing(await api<ListingDetail>(`/api/seller/listings/${listing.id}/images/${imageId}`, { method: "DELETE" }));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function markSold() {
    if (!listing || !confirm("Mark this property as sold? It will be hidden from buyers.")) return;
    try {
      setListing(await api<ListingDetail>(`/api/seller/listings/${listing.id}/sold`, { method: "POST" }));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (loading) return <Loading />;

  return (
    <>
      <PageHeader
        breadcrumb={
          <Link to="/console/listings" className="hover:text-slate-800">
            My listings
          </Link>
        }
        title={
          isNew ? (
            "New listing"
          ) : (
            <span className="flex flex-wrap items-center gap-3">
              {listing?.title}
              {listing && <ApprovalBadge status={listing.approval_status} sold={listing.status === "sold"} />}
            </span>
          )
        }
        description={isNew ? "Fill in the details below. You can add photos after saving." : <span className="font-mono">{listing?.ref_code}</span>}
        actions={
          listing && listing.status !== "sold" && listing.approval_status === "approved" ? (
            <Button variant="secondary" onClick={markSold}>
              Mark as sold
            </Button>
          ) : undefined
        }
      />

      <div className="space-y-4">
        {error && <Alert>{error}</Alert>}
        {notice && <Alert tone="success">{notice}</Alert>}
        {listing?.approval_status === "rejected" && (
          <Alert>This listing was not approved. Update the details and save to send it for review again.</Alert>
        )}
      </div>

      <form onSubmit={submit} className="mt-4 grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <Card>
            <CardHeader title="Basics" />
            <div className="grid gap-5 p-5 sm:grid-cols-2">
              <Field label="Listing title" className="sm:col-span-2" hint="e.g. Sunlit 3 BHK with balcony near Baner Road">
                <Input required minLength={5} maxLength={200} value={form.title} onChange={(e) => set("title", e.target.value)} />
              </Field>
              <Field label="Property type">
                <Select
                  value={form.property_type}
                  onChange={(e) => {
                    const t = e.target.value as PropertyType;
                    setForm((f) => ({
                      ...f,
                      property_type: t,
                      ...(t === "plot_land" ? { bedrooms: null, bathrooms: null, furnishing: null } : {}),
                      ...(t !== "plot_land" && f.property_type === "plot_land" ? { bedrooms: 2, bathrooms: 2, area_unit: "sqft" as const } : {}),
                    }));
                  }}
                >
                  {Object.entries(PROPERTY_LABEL).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </Select>
              </Field>
              <Field label="Locality">
                <Input
                  required
                  list="localities"
                  value={form.locality}
                  onChange={(e) => set("locality", e.target.value)}
                  placeholder="e.g. Baner"
                />
                <datalist id="localities">
                  {facets.data?.localities.map((l) => <option key={l} value={l} />)}
                </datalist>
              </Field>
              <Field label="Asking price (₹)" hint={form.price_inr > 0 ? inr(form.price_inr) : "Full amount in rupees"}>
                <Input
                  type="number"
                  required
                  min={1}
                  step={1}
                  value={form.price_inr || ""}
                  onChange={(e) => set("price_inr", Number(e.target.value))}
                />
              </Field>
              <Field label="City">
                <Input value={form.city} onChange={(e) => set("city", e.target.value)} />
              </Field>
            </div>
          </Card>

          <Card>
            <CardHeader title="Size & layout" />
            <div className="grid gap-5 p-5 sm:grid-cols-3">
              <Field label={isPlot ? "Plot area" : "Carpet area"}>
                <Input
                  type="number"
                  min={1}
                  step="any"
                  required={isPlot}
                  value={form.area_value ?? ""}
                  onChange={(e) => set("area_value", num(e.target.value))}
                />
              </Field>
              <Field label="Unit">
                <Select value={form.area_unit} onChange={(e) => set("area_unit", e.target.value as ListingInput["area_unit"])}>
                  <option value="sqft">sq ft</option>
                  <option value="sqm">sq m</option>
                  <option value="sqyd">sq yd</option>
                  <option value="guntha">guntha</option>
                  <option value="acre">acre</option>
                </Select>
              </Field>
              {!isPlot && (
                <Field label="Furnishing">
                  <Select
                    value={form.furnishing ?? ""}
                    onChange={(e) => set("furnishing", (e.target.value || null) as ListingInput["furnishing"])}
                  >
                    <option value="">Not specified</option>
                    <option value="unfurnished">Unfurnished</option>
                    <option value="semi_furnished">Semi-furnished</option>
                    <option value="fully_furnished">Fully furnished</option>
                  </Select>
                </Field>
              )}
              {!isPlot && !isCommercial && (
                <Field label="Bedrooms (BHK)">
                  <Input type="number" min={0} max={20} value={form.bedrooms ?? ""} onChange={(e) => set("bedrooms", num(e.target.value))} />
                </Field>
              )}
              {!isPlot && (
                <Field label="Bathrooms">
                  <Input type="number" min={0} max={20} value={form.bathrooms ?? ""} onChange={(e) => set("bathrooms", num(e.target.value))} />
                </Field>
              )}
            </div>
            <div className="flex flex-wrap gap-6 border-t border-slate-100 px-5 py-4">
              <Checkbox label="Car parking" checked={form.has_parking} onChange={(v) => set("has_parking", v)} />
              <Checkbox label="Near metro" checked={form.near_metro} onChange={(v) => set("near_metro", v)} />
              <Checkbox label="Near a school" checked={form.near_school} onChange={(v) => set("near_school", v)} />
            </div>
          </Card>

          <Card>
            <CardHeader title="Description" sub="What makes this property worth a visit? Buyers and our matching engine both read this." />
            <div className="p-5">
              <Textarea rows={7} maxLength={5000} value={form.description} onChange={(e) => set("description", e.target.value)} />
              <p className="mt-1 text-right text-xs text-slate-400 tabular">{form.description.length}/5000</p>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader title="Photos" sub="JPG, PNG or WebP · up to 5 MB each · max 8" />
            <div className="p-5">
              {isNew ? (
                <p className="text-sm text-slate-500">Save the listing first, then add photos here.</p>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-2">
                    {listing?.images.map((img) => (
                      <div key={img.id} className="group relative aspect-[3/2] overflow-hidden rounded-md bg-slate-100">
                        <img src={img.thumb_url} alt="" className="size-full object-cover" />
                        <button
                          type="button"
                          onClick={() => removeImage(img.id)}
                          className="absolute top-1 right-1 grid size-7 place-items-center rounded bg-white/95 text-slate-600 opacity-0 shadow group-hover:opacity-100 hover:text-red-600 focus:opacity-100"
                          aria-label="Remove photo"
                        >
                          <IconTrash className="size-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    multiple
                    hidden
                    onChange={(e) => upload(e.target.files)}
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    className="mt-3 w-full"
                    loading={uploading}
                    disabled={(listing?.images.length ?? 0) >= 8}
                    onClick={() => fileRef.current?.click()}
                  >
                    <IconUpload className="size-4" /> Upload photos
                  </Button>
                </>
              )}
            </div>
          </Card>

          <Card className="p-5">
            <p className="text-sm text-slate-600">
              {isNew
                ? "Your listing will be sent to the GreenKey team for review."
                : "Saving changes sends the listing for review again."}
            </p>
            <Button type="submit" className="mt-4 w-full" size="lg" loading={saving}>
              {isNew ? "Submit for review" : "Save changes"}
            </Button>
          </Card>
        </div>
      </form>
    </>
  );
}
