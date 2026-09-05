import { brand } from "@/lib/landing/content";

export function LandingJsonLd() {
  const data = {
    "@context": "https://schema.org",
    "@type": "HairSalon",
    name: brand.name,
    image: brand.logo,
    telephone: brand.phone,
    email: brand.email,
    url: "/",
    address: {
      "@type": "PostalAddress",
      streetAddress: "Near GRAND RESTAURANT, 22nd Street, Al Khobar Al Janubiyah",
      addressLocality: "Al Khobar",
      postalCode: "34622",
      addressCountry: "SA",
    },
    openingHours: "Mo-Su 12:00-00:00",
    priceRange: "$$",
    description: brand.tagline,
    hasOfferCatalog: {
      "@type": "OfferCatalog",
      name: "Grooming rituals",
    },
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />
  );
}
