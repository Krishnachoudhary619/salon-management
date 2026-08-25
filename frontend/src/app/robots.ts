import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/dashboard", "/appointments", "/login", "/customers", "/staff", "/reports"],
    },
    sitemap: "https://goldenpremiumsalon.ae/sitemap.xml",
  };
}
