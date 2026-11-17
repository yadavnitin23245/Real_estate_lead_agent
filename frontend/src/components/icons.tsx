// Minimal stroke icon set (24px grid, 1.75 stroke) so we don't pull an icon library.
import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement>;

function Icon({ children, ...p }: P & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...p}
    >
      {children}
    </svg>
  );
}

export const IconHome = (p: P) => (
  <Icon {...p}><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" /></Icon>
);
export const IconSearch = (p: P) => (
  <Icon {...p}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></Icon>
);
export const IconHeart = (p: P) => (
  <Icon {...p}><path d="M12 20s-7-4.35-7-10a4 4 0 0 1 7-2.65A4 4 0 0 1 19 10c0 5.65-7 10-7 10z" /></Icon>
);
export const IconGrid = (p: P) => (
  <Icon {...p}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></Icon>
);
export const IconInbox = (p: P) => (
  <Icon {...p}><path d="M3 13h5l1.5 3h5L16 13h5" /><path d="M5.5 5h13L21 13v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-6z" /></Icon>
);
export const IconCheckSquare = (p: P) => (
  <Icon {...p}><rect x="3" y="3" width="18" height="18" rx="3" /><path d="m8 12 3 3 5-6" /></Icon>
);
export const IconUsers = (p: P) => (
  <Icon {...p}><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 3.5 6" /></Icon>
);
export const IconBuilding = (p: P) => (
  <Icon {...p}><rect x="4" y="3" width="16" height="18" rx="1.5" /><path d="M9 7h1M14 7h1M9 11h1M14 11h1M9 15h1M14 15h1M10 21v-3h4v3" /></Icon>
);
export const IconPlus = (p: P) => <Icon {...p}><path d="M12 5v14M5 12h14" /></Icon>;
export const IconLogout = (p: P) => (
  <Icon {...p}><path d="M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4" /><path d="M10 17l5-5-5-5M15 12H3" /></Icon>
);
export const IconBed = (p: P) => (
  <Icon {...p}><path d="M3 18V7M3 14h18v4M21 14v-3a3 3 0 0 0-3-3h-7v6" /><circle cx="7" cy="11" r="1.5" /></Icon>
);
export const IconBath = (p: P) => (
  <Icon {...p}><path d="M4 12h16v3a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4zM6 12V6a2 2 0 0 1 4 0M6 19l-1 2M18 19l1 2" /></Icon>
);
export const IconRuler = (p: P) => (
  <Icon {...p}><path d="m3 17 14-14 4 4L7 21z" /><path d="m7 13 2 2M10 10l2 2M13 7l2 2" /></Icon>
);
export const IconPin = (p: P) => (
  <Icon {...p}><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></Icon>
);
export const IconCar = (p: P) => (
  <Icon {...p}><path d="M5 16V11l2-5h10l2 5v5M3 16h18v3H3zM5 11h14" /></Icon>
);
export const IconTrain = (p: P) => (
  <Icon {...p}><rect x="5" y="3" width="14" height="13" rx="3" /><path d="M5 10h14M8 20l-2 2M16 20l2 2M9 13h.01M15 13h.01" /></Icon>
);
export const IconSchool = (p: P) => (
  <Icon {...p}><path d="m2 9 10-5 10 5-10 5z" /><path d="M6 11v5c3 2 9 2 12 0v-5" /></Icon>
);
export const IconChevronLeft = (p: P) => <Icon {...p}><path d="m15 18-6-6 6-6" /></Icon>;
export const IconChevronRight = (p: P) => <Icon {...p}><path d="m9 18 6-6-6-6" /></Icon>;
export const IconMenu = (p: P) => <Icon {...p}><path d="M4 6h16M4 12h16M4 18h16" /></Icon>;
export const IconX = (p: P) => <Icon {...p}><path d="M6 6l12 12M18 6 6 18" /></Icon>;
export const IconPhone = (p: P) => (
  <Icon {...p}><path d="M5 3h3l2 5-2.5 1.5a11 11 0 0 0 5 5L14 12l5 2v3a2 2 0 0 1-2 2A15 15 0 0 1 3 5a2 2 0 0 1 2-2z" /></Icon>
);
export const IconMail = (p: P) => (
  <Icon {...p}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></Icon>
);
export const IconUpload = (p: P) => (
  <Icon {...p}><path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" /></Icon>
);
export const IconTrash = (p: P) => (
  <Icon {...p}><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></Icon>
);
export const IconShield = (p: P) => (
  <Icon {...p}><path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6z" /><path d="m9 12 2 2 4-4" /></Icon>
);
export const IconSparkle = (p: P) => (
  <Icon {...p}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6" /></Icon>
);
export const IconCalendar = (p: P) => (
  <Icon {...p}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></Icon>
);
export const IconArrowRight = (p: P) => <Icon {...p}><path d="M5 12h14M13 6l6 6-6 6" /></Icon>;
export const IconAlert = (p: P) => (
  <Icon {...p}><path d="M12 3 2 20h20z" /><path d="M12 10v4M12 17h.01" /></Icon>
);
