import Storefront from "./storefront";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://machli.spotiva.co.in";
const storePhone = process.env.NEXT_PUBLIC_STORE_PHONE?.trim();
const businessData = {
  "@context": "https://schema.org",
  "@type": "Store",
  name: "Machli",
  url: siteUrl,
  description: "Fresh sea fish and freshwater fish sourced from Munambam, Kerala, cleaned or cut to your preference, and delivered locally across Kochi and Ernakulam.",
  address: {
    "@type": "PostalAddress",
    addressLocality: "Munambam",
    addressRegion: "Kerala",
    addressCountry: "IN",
  },
  areaServed: ["Munambam", "Kochi", "Ernakulam"],
  ...(storePhone ? { telephone: storePhone } : {}),
};

export default function Home() {
  return <>
    <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(businessData).replace(/</g, "\\u003c") }} />
    <Storefront />
  </>;
}
