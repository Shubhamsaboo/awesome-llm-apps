import { NextRequest, NextResponse } from "next/server";

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL;

export async function middleware(request: NextRequest) {
  // If BASE_URL is not set, use the request URL's origin
  const baseUrl = BASE_URL || new URL(request.url).origin;

  console.log("Host: ", baseUrl);

  const url = `${baseUrl}/api/auth/get-session`;

  console.log("URL: ", url);

  try {
    const response = await fetch(url, {
      headers: {
        cookie: request.headers.get("cookie") || "",
      },
    });

    if (!response.ok) {
      return NextResponse.redirect(new URL("/auth", request.url));
    }

    const session = await response.json();

    if (!session) {
      return NextResponse.redirect(new URL("/auth", request.url));
    }

    return NextResponse.next();
  } catch (error) {
    console.error("Error fetching session:", error);
    return NextResponse.redirect(new URL("/auth", request.url));
  }
}

export const config = {
  matcher: ["/plan",],
};