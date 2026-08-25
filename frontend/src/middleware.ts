import { NextResponse } from "next/server";

/**
 * Auth tokens live in localStorage, so route protection runs client-side via
 * `RouteGuard`. This middleware is reserved for future cookie-based auth or
 * lightweight redirects once login routes exist.
 */
export function middleware() {
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
