export const brand = {
  name: "Golden Premium Salon",
  shortName: "Golden Premium",
  tagline: "The private atelier of executive grooming.",
  city: "Dubai",
  phone: "+971 4 555 0180",
  phoneHref: "tel:+97145550180",
  whatsappHref: "https://wa.me/97145550180",
  email: "reservations@goldenpremiumsalon.ae",
  address: "Level 12, Gate Avenue, DIFC, Dubai, UAE",
  hours: "Daily, 10:00 — 22:00",
  logo: "/brand/golden-premium-salon-logo.jpg",
} as const;

export const navLinks = [
  { href: "#why-us", label: "The House" },
  { href: "#services", label: "Services" },
  { href: "#about", label: "About" },
  { href: "#team", label: "Masters" },
  { href: "#gallery", label: "Atelier" },
  { href: "#contact", label: "Contact" },
] as const;

export const reasons = [
  {
    title: "Personalized Grooming",
    copy: "Every appointment is tailored to your style, routine, and preferences, ensuring a consistent experience with every visit.",
  },
  {
    title: "Master craftsmen",
    copy: "Our stylists train in London, Milan, and Beirut. Technique is inherited, never improvised.",
  },
  {
    title: "House formulations",
    copy: "Oils, tonics, and finishing products mixed for Gulf climate — never mass-market bottles on a trolley.",
  },
  {
    title: "Executive timing",
    copy: "Punctual starts, no overbooking, and a chauffeur-ready finish before your next engagement.",
  },
] as const;

export const team = [
  {
    name: "Priya Sharma",
    role: "Creative Director",
    image:
      "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?auto=format&fit=crop&w=900&q=80",
    bio: "Fifteen years across Mayfair and DIFC. Known for architectural cuts that photograph as well as they wear.",
  },
  {
    name: "Rohan Mehta",
    role: "Master Barber",
    image:
      "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=900&q=80",
    bio: "Hot-towel traditionalist with a modern edge. Trusted by financiers who refuse a hurried chair.",
  },
  {
    name: "Ananya Iyer",
    role: "Colour Atelier",
    image:
      "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=900&q=80",
    bio: "Quiet colour — lived-in brunettes, silver blending, and sun-softened highlights for Dubai light.",
  },
  {
    name: "Khalid Rahman",
    role: "Executive Stylist",
    image:
      "https://images.unsplash.com/photo-1605497788044-5a32c7078486?auto=format&fit=crop&w=900&q=80",
    bio: "The house specialist for private clients, hotel residences, and last-minute gala preparation.",
  },
] as const;

export const gallery = [
  {
    src: "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&w=1400&q=80",
    alt: "Dark marble grooming suite with gold fixtures",
  },
  {
    src: "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=1400&q=80",
    alt: "Master barber at work in a private chair",
  },
  {
    src: "https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?auto=format&fit=crop&w=1400&q=80",
    alt: "Luxury salon interior with leather seating",
  },
  {
    src: "https://images.unsplash.com/photo-1599351431202-1e0f0137899a?auto=format&fit=crop&w=1400&q=80",
    alt: "Precision beard grooming",
  },
  {
    src: "https://images.unsplash.com/photo-1562322140-8baeececf3df?auto=format&fit=crop&w=1400&q=80",
    alt: "Colour atelier finishing",
  },
  {
    src: "https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?auto=format&fit=crop&w=1400&q=80",
    alt: "Evening grooming ritual",
  },
] as const;

export const testimonials = [
  {
    quote:
      "The only chair in Dubai I trust before a board presentation. Silence, precision, and they never run late.",
    name: "James Al-Hariri",
    title: "Managing Partner, DIFC",
  },
  {
    quote:
      "It feels closer to a private members’ club than a salon. The Black Reserve is how I prepare for gala season.",
    name: "Elena Voskresenskaya",
    title: "Palm Jumeirah",
  },
  {
    quote:
      "Discreet, exacting, and entirely uninterested in trends. That is why I keep a standing Friday appointment.",
    name: "Omar bin Rashid",
    title: "Family Office, Emirates Hills",
  },
] as const;
