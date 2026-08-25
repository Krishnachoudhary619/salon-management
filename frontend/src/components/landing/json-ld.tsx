import { brand, services } from "@/lib/landing/content";

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
      streetAddress: "Level 12, Gate Avenue, DIFC",
      addressLocality: "Dubai",
      addressCountry: "AE",
    },
    openingHours: "Mo-Su 10:00-22:00",
    priceRange: "AED 220–AED 1,800",
    description: brand.tagline,
    hasOfferCatalog: {
      "@type": "OfferCatalog",
      name: "Grooming rituals",
      itemListElement: services.map((service) => ({
        "@type": "Offer",
        itemOffered: {
          "@type": "Service",
          name: service.name,
          description: service.description,
        },
      })),
    },
  };

  return (
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />
  );
}
