import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { inr, specLine } from "../lib/format";
import type { ChatMessage, ChatState, ListingCard } from "../lib/types";
import { Thumb } from "./domain";
import { IconArrowRight, IconSparkle, IconX } from "./icons";
import { cx } from "./ui";

const GUEST_KEY = "hm.guest";
const OPEN_EVENT = "hm:chat";

/** Open the assistant from anywhere, optionally sending a message. */
export function openChat(message?: string) {
  window.dispatchEvent(new CustomEvent(OPEN_EVENT, { detail: message }));
}

function guestId(): string {
  try {
    let id = localStorage.getItem(GUEST_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(GUEST_KEY, id);
    }
    return id;
  } catch {
    return (window as unknown as { __hmGuest?: string }).__hmGuest ??= crypto.randomUUID();
  }
}

const SUGGESTIONS = [
  "2 BHK in Wakad under ₹80 L",
  "Villa in Bavdhan with a garden",
  "Kothrud mein metro ke paas 3 BHK",
  "Plot for a weekend home",
];

/** Tiny, safe formatter: **bold**, line breaks and "- " bullets. */
function RichText({ text }: { text: string }) {
  const inline = (s: string, key: number): ReactNode => (
    <span key={key}>
      {s.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
        part.startsWith("**") && part.endsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
      )}
    </span>
  );
  const lines = text.split("\n").filter((l, i, a) => l.trim() || (i > 0 && a[i - 1]!.trim()));
  return (
    <div className="space-y-1">
      {lines.map((l, i) =>
        /^\s*[-*•]\s+/.test(l) ? (
          <div key={i} className="flex gap-1.5 pl-1">
            <span className="text-slate-400">•</span>
            {inline(l.replace(/^\s*[-*•]\s+/, ""), i)}
          </div>
        ) : l.trim() ? (
          <p key={i}>{inline(l, i)}</p>
        ) : null,
      )}
    </div>
  );
}

function MiniCard({ l, onVisit }: { l: ListingCard; onVisit: () => void }) {
  return (
    <div className="w-56 shrink-0 overflow-hidden rounded-lg bg-white ring-1 ring-slate-200">
      <Link to={`/listings/${l.id}`} className="block">
        <Thumb src={l.thumb_url} alt={l.title} className="aspect-[3/2] w-full" />
      </Link>
      <div className="p-2.5">
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-sm font-semibold tabular">{inr(l.price_inr)}</span>
          <span className="font-mono text-[10px] text-slate-400">{l.ref_code}</span>
        </div>
        <Link to={`/listings/${l.id}`} className="mt-0.5 line-clamp-1 text-xs font-medium text-slate-800 hover:text-brand-700">
          {l.title}
        </Link>
        <p className="truncate text-[11px] text-slate-500">
          {specLine(l)} · {l.locality}
        </p>
        <button
          onClick={onVisit}
          className="mt-2 w-full rounded-md bg-brand-50 py-1.5 text-xs font-medium text-brand-800 ring-1 ring-brand-200 hover:bg-brand-100"
        >
          Book a visit
        </button>
      </div>
    </div>
  );
}

export default function ChatWidget() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<ChatState | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [error, setError] = useState<{ text: string; retry: string } | null>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const headers = { "X-Guest-Id": guestId() };

  // Load history whenever the identity changes (guest -> signed-in buyer attaches the chat).
  useEffect(() => {
    api<ChatState>("/api/chat", { headers })
      .then(setState)
      .catch(() => setState({ lead_id: null, messages: [], handed_off_to: null }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [state?.messages.length, pending, open]);

  const send = useCallback(
    async (text: string) => {
      const msg = text.trim();
      if (!msg || pending) return;
      setPending(msg);
      setError(null);
      setInput("");
      try {
        setState(await api<ChatState>("/api/chat", { method: "POST", body: { message: msg }, headers }));
      } catch (e) {
        setError({ text: (e as Error).message, retry: msg });
      } finally {
        setPending(null);
        inputRef.current?.focus();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [pending],
  );

  useEffect(() => {
    const onOpen = (e: Event) => {
      setOpen(true);
      const text = (e as CustomEvent<string | undefined>).detail;
      if (text) void send(text);
      else setTimeout(() => inputRef.current?.focus(), 50);
    };
    window.addEventListener(OPEN_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_EVENT, onOpen);
  }, [send]);

  if (user && user.role !== "buyer") return null;

  const messages: ChatMessage[] = state?.messages ?? [];
  const empty = messages.length === 0 && !pending;

  function submit(e: FormEvent) {
    e.preventDefault();
    void send(input);
  }

  return (
    <>
      {!open && (
        <button
          onClick={() => {
            setOpen(true);
            setTimeout(() => inputRef.current?.focus(), 50);
          }}
          className="fixed right-4 bottom-4 z-40 flex items-center gap-2.5 rounded-full bg-ink-950 py-3 pr-5 pl-3.5 text-sm font-medium text-white shadow-xl shadow-ink-950/25 transition hover:bg-ink-900 sm:right-6 sm:bottom-6"
        >
          <span className="relative grid size-7 place-items-center rounded-full bg-brand-600">
            <IconSparkle className="size-4" />
            <span className="absolute -top-0.5 -right-0.5 size-2.5 rounded-full bg-brand-500 ring-2 ring-ink-950" />
          </span>
          {messages.length ? "Continue chat" : "Find my home"}
        </button>
      )}

      {open && (
        <section
          className="fixed inset-0 z-50 flex flex-col bg-white sm:inset-auto sm:right-6 sm:bottom-6 sm:h-[min(680px,calc(100vh-3rem))] sm:w-[400px] sm:rounded-xl sm:shadow-2xl sm:ring-1 sm:ring-slate-200"
          aria-label="HomeMatch assistant"
        >
          <header className="flex items-center gap-3 bg-ink-950 px-4 py-3 text-white sm:rounded-t-xl">
            <span className="grid size-9 place-items-center rounded-full bg-brand-600">
              <IconSparkle className="size-[18px]" />
            </span>
            <div className="min-w-0 flex-1 leading-tight">
              <p className="text-sm font-semibold">HomeMatch Assistant</p>
              <p className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="size-1.5 rounded-full bg-brand-500" />
                {state?.handed_off_to ? `${state.handed_off_to.split(" ")[0]} from GreenKey will call you` : "Replies in seconds · English / हिंदी"}
              </p>
            </div>
            <button onClick={() => setOpen(false)} className="rounded p-1.5 text-slate-400 hover:bg-white/10 hover:text-white" aria-label="Close chat">
              <IconX className="size-5" />
            </button>
          </header>

          <div ref={scroller} className="flex-1 space-y-4 overflow-y-auto bg-slate-50 px-4 py-4">
            {/* Welcome (client-side, not stored) */}
            <div className="max-w-[88%] rounded-2xl rounded-tl-sm bg-white px-3.5 py-2.5 text-sm text-slate-800 ring-1 ring-slate-200">
              Hi{user ? ` ${user.name.split(" ")[0]}` : ""}! I can help you find a home in Pune. Tell me what you're
              looking for: locality, budget, BHK. Hindi or Hinglish is fine too.
            </div>
            {empty && (
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="rounded-full bg-white px-3 py-1.5 text-xs text-slate-700 ring-1 ring-slate-300 hover:bg-brand-50 hover:text-brand-800 hover:ring-brand-300"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {messages.map((m) => (
              <div key={m.id} className="space-y-2">
                <div className={cx("flex", m.role === "user" ? "justify-end" : "justify-start")}>
                  <div
                    className={cx(
                      "max-w-[88%] px-3.5 py-2.5 text-sm",
                      m.role === "user"
                        ? "rounded-2xl rounded-tr-sm bg-brand-700 text-white"
                        : "rounded-2xl rounded-tl-sm bg-white text-slate-800 ring-1 ring-slate-200",
                    )}
                  >
                    {m.role === "assistant" ? <RichText text={m.content} /> : <p className="whitespace-pre-line">{m.content}</p>}
                  </div>
                </div>
                {m.listings.length > 0 && (
                  <div className="-mx-4 flex gap-2.5 overflow-x-auto px-4 pb-1">
                    {m.listings.map((l) => (
                      <MiniCard key={l.id} l={l} onVisit={() => send(`I'd like to visit ${l.ref_code}`)} />
                    ))}
                  </div>
                )}
              </div>
            ))}

            {pending && (
              <>
                <div className="flex justify-end">
                  <div className="max-w-[88%] rounded-2xl rounded-tr-sm bg-brand-700/80 px-3.5 py-2.5 text-sm text-white">{pending}</div>
                </div>
                <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-white px-4 py-3 ring-1 ring-slate-200 w-fit" aria-label="Assistant is typing">
                  {[0, 150, 300].map((d) => (
                    <span key={d} className="size-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: `${d}ms` }} />
                  ))}
                </div>
              </>
            )}

            {error && (
              <div className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-800 ring-1 ring-red-200">
                {error.text}{" "}
                <button onClick={() => send(error.retry)} className="font-semibold underline">
                  Retry
                </button>
              </div>
            )}

            {state?.handed_off_to && !pending && (
              <div className="flex items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 text-xs text-brand-900 ring-1 ring-brand-200">
                <IconSparkle className="size-4 shrink-0 text-brand-700" />
                Your details are with {state.handed_off_to}, your GreenKey agent. Keep chatting anytime.
              </div>
            )}
          </div>

          <form onSubmit={submit} className="border-t border-slate-200 bg-white p-3 sm:rounded-b-xl">
            <div className="flex items-end gap-2 rounded-xl bg-slate-50 p-1.5 ring-1 ring-slate-200 focus-within:ring-2 focus-within:ring-brand-600">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                maxLength={1000}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void send(input);
                  }
                }}
                placeholder="e.g. 3 BHK in Baner, 1.5 Cr, near a school"
                className="max-h-28 min-h-9 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={!input.trim() || !!pending}
                className="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-700 text-white transition hover:bg-brand-800 disabled:bg-slate-300"
                aria-label="Send"
              >
                <IconArrowRight className="size-4" />
              </button>
            </div>
            <p className="mt-1.5 text-center text-[10.5px] text-slate-400">
              AI assistant · listings are verified, but confirm details with your agent
            </p>
          </form>
        </section>
      )}
    </>
  );
}
