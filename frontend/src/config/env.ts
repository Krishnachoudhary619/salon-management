import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z
    .string()
    .url("NEXT_PUBLIC_API_BASE_URL must be a valid URL")
    .refine((value) => value.endsWith("/api/v1"), {
      message: "NEXT_PUBLIC_API_BASE_URL must include the /api/v1 prefix",
    }),
  NEXT_PUBLIC_APP_NAME: z.string().min(1),
  NEXT_PUBLIC_ENABLE_QUERY_DEVTOOLS: z.boolean(),
});

export type ClientEnv = z.infer<typeof envSchema>;

function parseEnv(): ClientEnv {
  const parsed = envSchema.safeParse({
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME ?? "Salon Management",
    NEXT_PUBLIC_ENABLE_QUERY_DEVTOOLS:
      process.env.NEXT_PUBLIC_ENABLE_QUERY_DEVTOOLS === "true",
  });

  if (!parsed.success) {
    const message = parsed.error.issues.map((issue) => issue.message).join("; ");
    throw new Error(`Invalid frontend environment: ${message}`);
  }

  return parsed.data;
}

export const env = parseEnv();
