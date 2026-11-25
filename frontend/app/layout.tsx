import type { Metadata } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://machli.spotiva.co.in";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Fresh Fish Delivery in Kochi & Ernakulam | Machli",
  description: "Order fresh sea fish and freshwater fish from Munambam, Kerala. Choose your quantity and cleaning or cutting preferences, with local delivery across Kochi and Ernakulam.",
  applicationName: "machli",
  icons: {
    icon: "/images/machli-logo.jpeg",
    apple: "/images/machli-logo.jpeg",
  },
  keywords: ["fresh fish Munambam", "fresh fish Kochi", "fish delivery Ernakulam", "sea fish Kerala", "freshwater fish Kochi", "cleaned fish delivery", "fish cleaning and cutting"],
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "en_IN",
    siteName: "machli",
    title: "Fresh Fish Delivery in Kochi & Ernakulam | Machli",
    description: "Fresh sea and freshwater fish from Munambam, cleaned and cut to your preference, with local delivery.",
    url: siteUrl,
  },
  twitter: {
    card: "summary",
    title: "Fresh Fish Delivery in Kochi & Ernakulam | Machli",
    description: "Fresh sea and freshwater fish from Munambam, cleaned and cut to your preference, with local delivery.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en-IN"><head><link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" /><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&family=Noto+Sans+Malayalam:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet" /></head><body>{children}</body></html>;
}
