import type { Metadata } from "next";

import { brand } from "@/lib/landing/content";

export const metadata: Metadata = {
  title: "Golden Premium Salon | Luxury Grooming in Dubai",
  description:
    "Private executive grooming in DIFC. Golden Premium Salon offers closed-door suites and master craftsmen for Dubai’s most discerning guests.",
  keywords: [
    "luxury salon Dubai",
    "executive grooming DIFC",
    "premium barber Dubai",
    "Golden Premium Salon",
    "private salon Dubai",
  ],
  openGraph: {
    title: "Golden Premium Salon | Luxury Grooming in Dubai",
    description: brand.tagline,
    type: "website",
    locale: "en_AE",
    images: [{ url: brand.logo, alt: `${brand.name} emblem` }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Golden Premium Salon",
    description: brand.tagline,
  },
  alternates: {
    canonical: "/",
  },
};

export default function MarketingLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}
