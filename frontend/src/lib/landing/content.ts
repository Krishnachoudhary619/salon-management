export const brand = {
  name: "Golden Premium Salon",
  shortName: "Golden Premium",
  tagline: "The private atelier of executive grooming.",
  city: "Al Khobar",
  phone: "+966 54 708 5374",
  phoneHref: "tel:+966547085374",
  whatsappHref: "https://wa.me/966547085374",
  email: "goldensaloonkhobar@gmail.com",
  address: "Near GRAND RESTAURANT, 22nd Street, Al Khobar Al Janubiyah 34622",
  hours: "Daily, 11:30 AM — 12:00 AM",
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
    name: "Sabit",
    role: "Creative Director",
    image: "/brand/director-image.jpg",
    bio: "Known for delivering refined grooming experiences with meticulous attention to detail and personal style.",
  },
  {
    name: "Yahiya",
    role: "Master Barber",
    image:
      "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=900&q=80",
    bio: "Combining traditional barbering craftsmanship with modern techniques for a distinguished finish.",
  },
  {
    name: "Fahad",
    role: "Executive Stylist",
    image:
      "https://images.unsplash.com/photo-1605497788044-5a32c7078486?auto=format&fit=crop&w=900&q=80",
    bio: "Creating sophisticated, contemporary looks tailored to each client's lifestyle and preferences.",
  },
] as const;

export const gallery = [
  {
    src: "/brand/workshop-image.png",
    alt: "Golden Premium Salon workshop interior",
  },
  {
    src: "/brand/house-story-image.jpeg",
    alt: "Golden Premium Salon house details",
  },
  {
    src: "/brand/workshop-image-2.png",
    alt: "Golden Premium Salon grooming station",
  },
  {
    src: "/brand/workshop-image-3.png",
    alt: "Golden Premium Salon barber at work",
  },
] as const;

export const testimonials = [
  {
    quote:
      "A luxurious saloon with cheaper price range and wide range of options. Very professional service.",
    name: "Althaf VA",
  },
  {
    quote:
      "New saloon in Al Khobar! The staff is friendly, the space is clean, and the service was excellent. I'm really happy with my experience and will definitely be coming back for sure.",
    name: "Badusha P.H",
  },
  {
    quote:
      "Amazing experience! The service was quick, professional, and top quality. The team was very welcoming, and the salon atmosphere was great. Definitely one of the best salons I've visited!",
    name: "Abdulla P A",
  },
] as const;
